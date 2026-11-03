"""S4-05：离线解析模型提出的工具请求，不执行工具、不发送模型请求。"""

import argparse
import ast
import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT / 'stage4_tools.py'
sys.path.insert(0, str(TESTS))
from check_s4_01 import forbidden, require
from openai.types.chat import ChatCompletionMessage


def sample(name=' 青岚 ', call_id='call_lookup_1'):
    """模拟已完整接收的非流式assistant消息；参数仍是JSON字符串。"""
    return {'role': 'assistant', 'content': None, 'tool_calls': [
        {'id': call_id, 'type': 'function', 'function': {
            'name': 'lookup_place',
            'arguments': json.dumps({'name': name}, ensure_ascii=False)}}]}


def expected(name='青岚', call_id='call_lookup_1'):
    return {'tool_call_id': call_id, 'tool_name': 'lookup_place',
            'arguments': {'name': name}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='展示假消息及解析结果，不执行查询')
    args = parser.parse_args()
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None
    cache, outcomes = {}, []

    def check(title, action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f'未通过｜{title}：{type(error).__name__}: {error}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{title}')

    def module():
        if 'app' not in cache:
            require(SOURCE.is_file(), '保留stage4_tools.py，本课只新增parse_tool_request')
            tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(a.name in {'argparse', 'copy', 'json', 'typing'} for a in node.names),
                            '工具模块仅使用标准库，不导入配置／SDK／网络')
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in {'argparse', 'copy', 'json', 'typing'},
                            '本课解析dict，不读取配置或导入旧问答入口')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile'},
                            '解析不访问文件／终端或动态执行模型给出的文本')
            app = ModuleType('stage4_tools')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(), '导入不能运行CLI或输出')
            require(callable(getattr(app, 'parse_tool_request', None)),
                    '实现parse_tool_request(assistant_message: dict) -> dict | None')
            require(callable(getattr(app, 'lookup_place', None)), '保留已验收的lookup_place')
            cache['app'] = app
        return cache['app']

    def call(message):
        app = module()
        snapshot = deepcopy(message)
        catalog = deepcopy(app.PLACE_FIXTURES)
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(app, 'lookup_place', side_effect=forbidden) as execution, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.parse_tool_request(message)
            finally:
                require(execution.call_count == 0, '只解析请求，不得调用lookup_place，即使捕获其异常也不行')
                require(not output.getvalue() and not errors.getvalue(), '解析只返回或抛异常，不打印')
                require(message == snapshot, '不能修改原assistant消息或嵌套工具字段')
                require(app.PLACE_FIXTURES == catalog, '解析不修改目录')

    def rejected(message, kind=ValueError):
        try:
            call(message)
        except Exception as error:
            require(isinstance(error, kind), f'应抛{kind.__name__}，实际{type(error).__name__}: {error}')
            if kind is ValueError:
                require(not isinstance(error, json.JSONDecodeError), '合法JSON的业务错误用ValueError，不伪造语法错误')
        else:
            raise AssertionError(f'无效输入必须抛{kind.__name__}，不能当作无调用或成功')

    def normal():
        for raw in (' 青岚 ', '\u3000赤川镇\u3000', '未收录地点', '青 岚'):
            result = call(sample(raw))
            require(isinstance(result, dict) and result == expected(raw.strip()),
                    '新三字段dict：tool_call_id/tool_name/arguments；只清理地名首尾')
            require(set(result) == {'tool_call_id', 'tool_name', 'arguments'}, '不要混入工具查询结果或模型答案')

    def no_calls():
        for message in ({'role': 'assistant'}, {'role': 'assistant', 'content': '我想调用lookup_place'},
                        {'role': 'assistant', 'tool_calls': None}, {'role': 'assistant', 'tool_calls': []}):
            require(call(message) is None, '缺失／None／空列表才表示无结构化调用，正文提及函数不算调用')

    def top_level():
        for message in (None, '', [], 1, False, b'json'):
            rejected(message, TypeError)
        for message in ({}, {'role': None}, {'role': 'user'}, {'role': 'tool'}, {'role': ' assistant '}):
            rejected(message)

    def container():
        for value in ('', {}, (), tuple(sample()['tool_calls']), 0, False,
                      [None], [[]], ['lookup_place'], [{}, {}], sample()['tool_calls'] * 2):
            message = sample()
            message['tool_calls'] = value
            rejected(message)

    def protocol():
        for key, values in [('id', [None, '', ' \t\n', 1, False, []]),
                            ('type', [None, '', 'custom', ' function ', 1]),
                            ('function', [None, '', [], 1])]:
            for value in values:
                message = sample()
                message['tool_calls'][0][key] = value
                rejected(message)
            message = sample()
            del message['tool_calls'][0][key]
            rejected(message)
        for value in (None, '', 'delete_file', ' lookup_place ', 1, False):
            message = sample()
            message['tool_calls'][0]['function']['name'] = value
            rejected(message)
        message = sample()
        del message['tool_calls'][0]['function']['name']
        rejected(message)

    def arguments_json():
        for value in (None, {}, {'name': '青岚'}, [], 1, False, b'{"name":"x"}'):
            message = sample()
            message['tool_calls'][0]['function']['arguments'] = value
            rejected(message)
        message = sample()
        del message['tool_calls'][0]['function']['arguments']
        rejected(message)
        for text in ('', ' ', '{', '{"name":}', '```json\n{"name":"青岚"}\n```'):
            message = sample()
            message['tool_calls'][0]['function']['arguments'] = text
            rejected(message, json.JSONDecodeError)

    def arguments_schema():
        for value in (None, [], '青岚', 0, False, {}, {'other': '青岚'},
                      {'name': None}, {'name': False}, {'name': 3}, {'name': []},
                      {'name': ''}, {'name': ' \t\n'}, {'name': '\u3000'},
                      {'name': '青岚', 'extra': '不要执行'}):
            message = sample()
            message['tool_calls'][0]['function']['arguments'] = json.dumps(value, ensure_ascii=False)
            rejected(message)

    def opaque_id_and_extras():
        call_id = ' call_42\t'
        message = sample(' 青岚 ', call_id)
        message.update({'reasoning_content': '假推理字段，只用于协议保留检查',
                        'refusal': None, 'future_metadata': {'nested': [1]}})
        message['tool_calls'][0]['function']['description'] = '额外字段不参与执行'
        require(call(message) == expected('青岚', call_id),
                'ID只检查非空，原样保留；容许SDK额外字段，不重写原消息')

    def no_execution():
        for name in ('青岚', '未收录地点', '青岚城附近'):
            require(call(sample(name)) == expected(name), '合法请求不先查目录，查询命中与否属于执行阶段')

    def isolation():
        message = sample()
        first, second = call(message), call(message)
        require(first is not second and first['arguments'] is not second['arguments'],
                '每次返回独立dict及arguments，不复用可变缓存')
        first['arguments']['name'] = '外部修改'
        first['tool_call_id'] = '外部修改'
        require(second == expected() and call(message) == expected(), '修改一次结果不影响原消息、其他或后续结果')

    def sdk_bridge():
        message = sample(' 赤川 ')
        message['reasoning_content'] = 'SDK保留的假扩展字段'
        dto = ChatCompletionMessage(**message)
        raw = dto.to_dict()
        require(isinstance(raw['tool_calls'][0]['function']['arguments'], str), 'to_dict不替你解码arguments字符串')
        require(call(raw) == expected('赤川'), '接受现有SDK DTO.to_dict()的真实字段结构，无客户端／网络')
        require(raw['reasoning_content'] == message['reasoning_content'], '不丢弃后续协议可能需要的原消息字段')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s405-regression-') as temporary:
            target = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py', 'stage4_live.py', 'stage4_tools.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py',
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py', 'check_s4_03b.py',
                         'check_s4_03c.py', 'check_s4_03d.py', 'check_s4_04.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(target/'test/check_s4_04.py')], cwd=target,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=240)
            require(result.returncode == 0 and '10/10 项通过' in result.stdout,
                    'S4-04及旧课不能回退：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ, {}, clear=True), patch('builtins.open', side_effect=forbidden), \
            patch('builtins.input', side_effect=forbidden), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                message = sample()
                print('离线假消息演示：只解析请求，未执行lookup_place，未请求模型。')
                print('输入：\n'+json.dumps(message, ensure_ascii=False, indent=2))
                result = call(message)
                require(result == expected(), '解析结果应为三字段请求，不是查询结果')
                print('解析结果：\n'+json.dumps(result, ensure_ascii=False, indent=2))
                result = call({'role': 'assistant', 'content': '这里没有工具调用'})
                require(result is None, '无结构化调用应返回None')
                print('无调用：'+json.dumps(result, ensure_ascii=False))
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title, action in [('有效单次请求的三字段解析与地名清理', normal),
                    ('无tool_calls返回None，正文不触发调用', no_calls),
                    ('顶层dict及assistant角色校验', top_level),
                    ('列表与单次调用边界，不静默丢弃多调用', container),
                    ('ID、function类型及唯一允许的工具名', protocol),
                    ('arguments必须字符串，语法错误保留JSONDecodeError', arguments_json),
                    ('参数恰好一个非空白name，业务错误ValueError', arguments_schema),
                    ('ID原样保留，容许额外SDK字段且原消息不变', opaque_id_and_extras),
                    ('只读请求，不执行工具或验证目录命中', no_execution),
                    ('返回结果与嵌套参数独立', isolation),
                    ('真实SDK消息DTO.to_dict离线桥接', sdk_bridge),
                    ('S4-04及此前全链回归（临时工程）', previous)]:
                check(title, action)
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before, '检查期间源文件变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；工具源码 {before[:8] if before else "未创建"}。')
    print('仅内存假消息、SDK DTO及临时旧课回归；未加载.env／Key或真实会话，未请求模型。')
    print('通过只说明读取请求符合本课契约，不代表工具已执行或模型已真实提出请求。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
