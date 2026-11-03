"""S4-06A：离线执行一次地名工具并构造回传消息，不请求模型。"""

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
SOURCE = PROJECT/'stage4_tools.py'
sys.path.insert(0, str(TESTS))
from check_s4_01 import forbidden, require
from check_s4_05 import sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='用假调用消息执行本地虚构目录工具，不调用模型')
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
            require(SOURCE.is_file(), '保留stage4_tools.py，在其中实现execute_tool_request')
            tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(a.name in {'argparse', 'copy', 'json', 'typing'} for a in node.names),
                            '本课只执行本地工具，不导入SDK／配置／网络')
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in {'argparse', 'copy', 'json', 'typing'},
                            '工具模块不导入旧问答或真实配置')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile', 'globals'},
                            '直接调用lookup_place，不动态执行工具名，不读文件或终端')
            app = ModuleType('stage4_tools')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(), '导入不能执行CLI或输出')
            require(callable(getattr(app, 'execute_tool_request', None)),
                    '实现execute_tool_request(assistant_message: dict) -> dict | None')
            cache['app'] = app
        return cache['app']

    def call(message, lookup_count=1, name='青岚'):
        app = module()
        snapshot, catalog = deepcopy(message), deepcopy(app.PLACE_FIXTURES)
        original_parse, original_lookup = app.parse_tool_request, app.lookup_place
        events = []

        def parse(value):
            events.append(('parse',))
            require(value == message, '将完整assistant消息交给已验收解析器，不丢弃协议字段')
            return original_parse(value)

        def lookup(name):
            events.append(('lookup', name))
            return original_lookup(name)

        output, errors = io.StringIO(), io.StringIO()
        incomplete = False
        with patch.object(app, 'parse_tool_request', side_effect=parse) as parsing, \
                patch.object(app, 'lookup_place', side_effect=lookup) as execution, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.execute_tool_request(message)
            except NotImplementedError:
                incomplete = True
                raise
            finally:
                require(not output.getvalue() and not errors.getvalue(), '只返回消息或抛异常，展示由调用方负责')
                require(message == snapshot and app.PLACE_FIXTURES == catalog, '不修改原assistant消息或固定目录')
                if not incomplete:
                    require(parsing.call_count == 1, '每次恰好复用parse_tool_request一次，不重复实现或跳过校验')
                    require(execution.call_count == lookup_count, f'预期工具执行{lookup_count}次，实际{execution.call_count}次；不重试')
                    wanted = [('parse',)] + ([('lookup', name)] if lookup_count else [])
                    require(events == wanted, '先解析再执行，传入解析后的name，不把JSON字符串直接传给工具')

    def shape(message, call_id, result):
        require(isinstance(message, dict) and set(message) == {'role', 'tool_call_id', 'name', 'content'},
                '返回恰好role/tool_call_id/name/content四字段新dict')
        require(message['role'] == 'tool' and message['name'] == 'lookup_place', '工具结果角色为tool，name保留工具名')
        require(message['tool_call_id'] == call_id, 'tool_call_id必须关联本次原始调用ID，不清理或重新生成')
        require(isinstance(message['content'], str), 'content为json.dumps后的字符串，不能直接塞dict')
        require(json.loads(message['content']) == result, 'content完整保留lookup_place结果，不补造或丢失来源字段')
        require(any('\u4e00' <= c <= '\u9fff' for c in message['content']), 'json.dumps使用ensure_ascii=False，保留可读中文')

    def found():
        app = module()
        for place in app.PLACE_FIXTURES:
            for name in (place['name'], *place['aliases']):
                result = {'query': name, 'found': True, 'place': deepcopy(place), 'source_status': 'fixture'}
                shape(call(sample(' '+name+' '), name=name), 'call_lookup_1', result)

    def missing():
        for name in ('未收录地点', '青岚城附近'):
            result = {'query': name, 'found': False, 'place': None, 'source_status': 'fixture'}
            shape(call(sample(name), name=name), 'call_lookup_1', result)

    def no_calls():
        for message in ({'role': 'assistant'}, {'role': 'assistant', 'content': '请lookup_place'},
                        {'role': 'assistant', 'tool_calls': None}, {'role': 'assistant', 'tool_calls': []}):
            require(call(message, lookup_count=0) is None, '没有结构化调用就返回None，不执行工具、不伪造工具消息')

    def invalid():
        cases = [(None, TypeError), ({'role': 'user'}, ValueError)]
        for edit, kind in [('unknown', ValueError), ('two', ValueError), ('blank', ValueError), ('syntax', json.JSONDecodeError)]:
            message = sample()
            function = message['tool_calls'][0]['function']
            if edit == 'unknown':
                function['name'] = 'delete_file'
            elif edit == 'two':
                message['tool_calls'] *= 2
            elif edit == 'blank':
                function['arguments'] = '{"name":" "}'
            else:
                function['arguments'] = '{'
            cases.append((message, kind))
        for message, kind in cases:
            try:
                call(message, lookup_count=0)
            except Exception as error:
                require(isinstance(error, kind), f'原解析异常应传播为{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('无效请求必须抛出原解析异常，不能执行工具或伪装未命中')

    def parser_result():
        app = module()
        parsed = {'tool_call_id': ' opaque_id\t', 'tool_name': 'lookup_place', 'arguments': {'name': '赤川'}}
        snapshot = deepcopy(parsed)
        with patch.object(app, 'parse_tool_request', return_value=parsed):
            result = call(sample('青岚'), name='赤川')
        expected = {'query': '赤川', 'found': True, 'place': deepcopy(app.PLACE_FIXTURES[1]), 'source_status': 'fixture'}
        shape(result, parsed['tool_call_id'], expected)
        require(parsed == snapshot, '不改解析器返回的请求对象；用其ID／工具名／参数继续处理')

    def correlation():
        app = module()
        for call_id in ('call_a', 'call_b', ' call_a\t'):
            message = sample('青岚', call_id)
            message['reasoning_content'] = '离线假扩展字段，仅检查原消息保留'
            expected = {'query': '青岚', 'found': True, 'place': deepcopy(app.PLACE_FIXTURES[0]), 'source_status': 'fixture'}
            shape(call(message), call_id, expected)

    def changed_tool():
        app = module()
        place = {'name': '测试城', 'aliases': ['测试别名'], 'description': '离线测试的虚构城镇'}
        with patch.object(app, 'PLACE_FIXTURES', [place]):
            expected = {'query': '测试别名', 'found': True, 'place': place, 'source_status': 'fixture'}
            shape(call(sample('测试别名'), name='测试别名'), 'call_lookup_1', expected)
        expected = {'query': '青岚', 'found': False, 'place': None, 'source_status': 'fixture', 'note': '假工具扩展信息'}
        with patch.object(app, 'lookup_place', return_value=deepcopy(expected)):
            shape(call(sample()), 'call_lookup_1', expected)

    def failures():
        app = module()
        parsing_error = ValueError('离线模拟解析器失败')
        with patch.object(app, 'parse_tool_request', side_effect=parsing_error):
            try:
                call(sample(), lookup_count=0)
            except Exception as error:
                require(error is parsing_error, '解析异常原样传播，不包装为成功工具结果')
            else:
                raise AssertionError('解析失败必须传播异常')
        execution_error = RuntimeError('离线模拟工具失败')
        with patch.object(app, 'lookup_place', side_effect=execution_error):
            try:
                call(sample())
            except Exception as error:
                require(error is execution_error, '工具异常原样传播，不重试、不调用模型或伪装未命中')
            else:
                raise AssertionError('工具失败必须传播异常')

    def isolation():
        message = sample()
        first, second = call(message), call(message)
        require(first is not second, '每次返回独立工具消息，不复用全局dict')
        first['tool_call_id'] = '调用方修改'
        first['content'] = '{}'
        require(call(message) == second, '修改一次消息不影响原数据、其他或后续消息')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s406a-regression-') as temporary:
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
                         'check_s4_03c.py', 'check_s4_03d.py', 'check_s4_04.py', 'check_s4_05.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(target/'test/check_s4_05.py')], cwd=target,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=260)
            require(result.returncode == 0 and '12/12 项通过' in result.stdout,
                    'S4-05及旧课不能回退：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ, {}, clear=True), patch('builtins.open', side_effect=forbidden), \
            patch('builtins.input', side_effect=forbidden), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                print('离线演示：输入是假模型调用；程序会实际查询本地虚构目录，不请求模型。')
                for name in (' 青岚 ', '未收录地点'):
                    message = sample(name)
                    result = call(message, name=name.strip())
                    require(isinstance(result, dict) and result.get('role') == 'tool', '先完成工具执行与消息构造')
                    print(f'\n{name!r}：parse_tool_request → lookup_place（1次） → tool消息')
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                require(call({'role': 'assistant', 'content': '无调用'}, lookup_count=0) is None, '无调用应返回None')
                print('\n无调用：None；工具执行0次。尚未把结果发送回模型生成回答。')
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title, action in [('标准名及别名：解析后实际执行一次工具', found),
                    ('未收录也回传False/None和fixture', missing),
                    ('无调用：解析一次、工具零次、返回None', no_calls),
                    ('非法协议／参数／JSON：原异常且工具零次', invalid),
                    ('复用解析后的ID及name，不重新解析原输入', parser_result),
                    ('tool角色、工具名、原始ID和JSON内容关联', correlation),
                    ('动态工具结果完整序列化，不硬编码或改来源', changed_tool),
                    ('解析／工具异常原样传播，不重试', failures),
                    ('消息与原数据隔离，不复用可变结果', isolation),
                    ('S4-05及此前全链回归（临时工程）', previous)]:
                check(title, action)
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before, '检查期间源文件变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；工具源码 {before[:8] if before else "未创建"}。')
    print('假调用消息＋本地虚构工具；未加载.env／Key或真实会话，未请求模型。')
    print('通过只证明工具执行与回传消息构造，不证明真实模型已选择工具或收到结果。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
