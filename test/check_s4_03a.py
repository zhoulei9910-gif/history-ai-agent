"""S4-03A：离线检查Kimi JSON Mode请求构造；不加载Key、不发送请求。"""

import argparse
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
SOURCE = PROJECT / 'stage4_structured.py'
sys.path.insert(0, str(TESTS))

from check_s4_01 import FIELDS, forbidden, inspect_source, require

REQUEST_FIELDS = {'model', 'messages', 'response_format', 'stream',
                  'max_completion_tokens', 'reasoning_effort'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='只显示未发送的离线请求参数，不替代完整验收')
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
            require(SOURCE.is_file(), '继续使用stage4_structured.py，不修改阶段3入口')
            tree = inspect_source(SOURCE.read_text(encoding='utf-8'))
            app = ModuleType('stage4_structured')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with patch('builtins.open', side_effect=forbidden), \
                    patch('builtins.input', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(),
                    '导入只定义函数，不打印、运行main、加载配置或请求模型')
            require(callable(getattr(app, 'build_structured_request', None)),
                    '新增build_structured_request(question: str) -> dict')
            cache['app'] = app
        return cache['app']

    def call(question):
        app = module()
        output, errors = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=forbidden), \
                patch('builtins.input', side_effect=forbidden), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.build_structured_request(question)
            finally:
                require(not output.getvalue() and not errors.getvalue(),
                        '构造函数只返回参数dict或抛错；不打印、读输入、访问文件或发送请求')

    def shape(request):
        require(isinstance(request, dict), '返回内存dict，不返回json.dumps后的字符串')
        require(set(request) == REQUEST_FIELDS, '请求恰好包含约定六字段，不带Key、tools或历史状态')
        messages = request['messages']
        require(isinstance(messages, list) and len(messages) == 2,
                'messages保持长度2的list，不提前序列化成JSON字符串')
        for item, role in zip(messages, ('system', 'user')):
            require(isinstance(item, dict) and set(item) == {'role', 'content'},
                    '每条消息为只有role/content的dict')
            require(item['role'] == role and isinstance(item['content'], str) and item['content'].strip(),
                    '消息顺序system、user，content使用非空字符串')

    def normal():
        for question in ('为什么河流会影响城市发展？', '离线结构练习，不要求核实史实'):
            shape(call(question))

    def parameters():
        request = call('请求参数练习')
        shape(request)
        require(request['model'] == 'kimi-k3', '沿用项目模型kimi-k3，不因文档新示例自动换模型')
        require(request['stream'] is False, '本课stream必须为布尔False，暂不接流式')
        require(type(request['max_completion_tokens']) is int and request['max_completion_tokens'] == 4096,
                '沿用4096输出预算，字段为max_completion_tokens，不用旧max_tokens')
        require(request['reasoning_effort'] == 'low', '沿用reasoning_effort=low')

    def json_mode():
        request = call('JSON Mode练习')
        shape(request)
        require(isinstance(request['response_format'], dict) and
                request['response_format'] == {'type': 'json_object'},
                'response_format为内存dict {"type":"json_object"}；只写提示词不够')

    def question_text():
        for question in (' \t 为什么地形影响道路？ \n', '  中文\n"引号"和反斜线\\\n内部文字  '):
            request = call(question)
            shape(request)
            require(request['messages'][1]['content'] == question.strip(),
                    'user只放首尾清理后的原问题，保持内部文字，不拼验收提示或重复system')
        first = call('问题甲：离线唯一标记-A')
        first_snapshot = deepcopy(first)
        second = call('问题乙：离线唯一标记-B')
        require(first == first_snapshot, '构造第二个请求不能改写第一个请求的问题')
        require(first['messages'][0]['content'] == second['messages'][0]['content'],
                'system提示词固定；问题单独放入user消息')

    def prompt():
        request = call('只检查提示词结构')
        shape(request)
        text = request['messages'][0]['content']
        require('json' in text.lower() and all(field in text for field in FIELDS),
                'system明确JSON和mode/answer/uncertainty/source_status/sources五字段')
        require('model' in text and 'not_retrieved' in text,
                'system说明model和not_retrieved；不能让真实模型假称mock')
        # 字段语义、中文回答、不确定性和不编造来源由导师人工审阅，关键词不能证明语义正确。

    def raw_types():
        for question in (None, 5, False, [], {}, b'question'):
            try:
                call(question)
            except TypeError:
                continue
            raise AssertionError('question非str抛TypeError，不能隐式str()转换或返回空请求')

    def blank():
        for question in ('', ' ', '\t\n\r', '\u3000'):
            try:
                call(question)
            except ValueError:
                continue
            raise AssertionError('question.strip()后为空需抛ValueError，不构造空白请求')

    def isolation():
        first = call('隔离练习甲')
        second = call('隔离练习乙')
        shape(first)
        shape(second)
        require(first is not second and first['messages'] is not second['messages'] and
                first['response_format'] is not second['response_format'] and
                all(a is not b for a, b in zip(first['messages'], second['messages'])),
                '每次新建请求dict、messages及内部消息dict、response_format；不共享可变模板')
        snapshot = deepcopy(second)
        first['messages'][0]['content'] = '调用方修改提示词'
        first['messages'][1]['content'] = '调用方修改问题'
        first['messages'].append({'role': 'user', 'content': '额外消息'})
        first['response_format']['type'] = 'text'
        first['model'] = '调用方修改模型'
        require(second == snapshot, '修改一个请求不污染另一个请求')
        third = call('隔离练习乙')
        require(third == snapshot, '修改旧请求不污染后续请求')

    def round_trip():
        request = call('中文\n"引号"与反斜线\\练习')
        shape(request)
        restored = json.loads(json.dumps(request, ensure_ascii=False))
        require(restored == request, '完整请求可JSON往返，内容与bool/int类型保持')
        require(isinstance(restored['messages'], list) and
                isinstance(restored['messages'][0], dict) and
                isinstance(restored['response_format'], dict),
                'messages和response_format在序列化前是容器，不是嵌套JSON字符串')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s403-regression-') as temporary:
            directory = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py'):
                require((PROJECT / name).is_file(), f'回归文件缺失：{name}')
                (directory / name).write_bytes((PROJECT / name).read_bytes())
            (directory / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py',
                         'check_stage_3.py', 'check_s4_01.py', 'check_s4_02.py'):
                (directory / 'test' / name).write_bytes((TESTS / name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(directory / 'test/check_s4_02.py')],
                cwd=directory, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=140)
            require(result.returncode == 0 and '10/10 项通过' in result.stdout,
                    'S4-02及此前回归不能退化：\n' + (result.stdout + result.stderr)[-2800:])

    def demo():
        request = call('为什么河流会影响城市发展？')
        shape(request)
        print('离线请求参数（未发送，不读取Key）：')
        print(json.dumps(request, ensure_ascii=False, indent=2))
        print('messages类型：', type(request['messages']).__name__)
        print('response_format类型：', type(request['response_format']).__name__)
        print('本演示不执行SDK或模型请求；完整验收请运行不带--demo的检查。')

    with patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                demo()
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            check('正常问题返回六字段请求dict及两条内存消息', normal)
            check('沿用模型、非流式和输出预算', parameters)
            check('显式开启JSON Mode，参数保持dict', json_mode)
            check('问题清理、原文保留及system/user职责分开', question_text)
            check('system包含JSON五字段及模式来源约定', prompt)
            check('question非字符串拒绝为TypeError', raw_types)
            check('空白问题拒绝为ValueError', blank)
            check('请求及所有嵌套可变对象相互隔离', isolation)
            check('整体JSON往返，不对嵌套容器提前dumps', round_trip)
            check('S4-02及此前回归（临时工程）', previous)

    require((hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None) == before,
            '检查期间入口变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8] if before else "未创建"}。')
    print('仅构造内存参数与临时旧课回归；未加载.env或真实Key、未请求模型、未读取会话。')
    print('提示词语义需人工审阅；JSON Mode参数不证明模型遵守业务契约或史实正确。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
