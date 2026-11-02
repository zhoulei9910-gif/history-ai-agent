"""S4-03B：离线检查客户端注入、响应完整性与显式模式校验；不请求模型。"""

import argparse
import contextlib
from copy import deepcopy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT / 'stage4_structured.py'
sys.path.insert(0, str(TESTS))
from check_s4_01 import forbidden, inspect_source, require


def payload(mode='model', answer='离线假正文', uncertainty='假响应，尚未调用模型或检索资料'):
    return {'mode': mode, 'answer': answer, 'uncertainty': uncertainty,
            'source_status': 'not_retrieved', 'sources': []}


def response(raw=None, finish='stop'):
    if raw is None:
        raw = json.dumps(payload(), ensure_ascii=False)
    return SimpleNamespace(choices=[SimpleNamespace(
        finish_reason=finish, message=SimpleNamespace(content=raw))])


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = response() if result is None else result
        self.error = error
        self.calls = []
        self.close_count = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if self.error is not None:
            raise self.error
        return self.result

    def close(self):
        self.close_count += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='仅演示内存假客户端，不请求真实模型')
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
            require(SOURCE.is_file(), '继续使用阶段4入口stage4_structured.py')
            tree = inspect_source(SOURCE.read_text(encoding='utf-8'))
            app = ModuleType('stage4_structured')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with patch('builtins.open', side_effect=forbidden), \
                    patch('builtins.input', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(),
                    '导入只定义函数，不打印、创建客户端或请求模型')
            require(callable(getattr(app, 'ask_structured', None)),
                    '新增ask_structured(client, question: str) -> dict')
            cache['app'] = app
        return cache['app']

    def silent(action):
        output, errors = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=forbidden), \
                patch('builtins.input', side_effect=forbidden), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return action()
            finally:
                require(not output.getvalue() and not errors.getvalue(),
                        '函数只返回数据或抛异常，不打印、读输入或访问文件')

    def ask(client, question='离线问题'):
        return silent(lambda: module().ask_structured(client, question))

    def parse(raw, **kwargs):
        return silent(lambda: module().parse_answer_json(raw, **kwargs))

    def expect(action, kind, message):
        try:
            action()
        except Exception as error:
            require(isinstance(error, kind),
                    f'{message}；应为{kind.__name__}，实际{type(error).__name__}')
            if kind is ValueError:
                require(not isinstance(error, json.JSONDecodeError),
                        '响应包络或业务字段错误是普通ValueError，不伪装为JSON语法错误')
            return error
        raise AssertionError(message + '；当前被当作成功返回')

    def no_parse(result):
        app = module()
        client = FakeClient(result)
        with patch.object(app, 'parse_answer_json', side_effect=AssertionError('尚不应调用解析器')) as parse_mock:
            expect(lambda: ask(client), ValueError, '响应未完整有效时明确拒绝')
            require(parse_mock.call_count == 0, '先验证choices、结束原因和正文，再调用JSON解析器')
        require(len(client.calls) == 1 and client.close_count == 0,
                '仅调用一次，不自行关闭由调用方提供的客户端')

    def normal():
        for answer in ('  中文正文  ', '  中文\n"引号"与反斜线\\  '):
            value = payload(answer=answer, uncertainty=' \t离线说明\n ')
            client = FakeClient(response(json.dumps(value, ensure_ascii=False)))
            result = ask(client)
            expected = payload(answer=answer.strip(), uncertainty='离线说明')
            require(result == expected, '返回已校验model回答dict，两个文本清理两端，内部原文保留')

    def request_parameters():
        client = FakeClient()
        ask(client, '  参数检查  ')
        require(len(client.calls) == 1, '一次提问恰好一次create，不重试或额外调用')
        request = client.calls[0]
        require(request == module().build_structured_request('  参数检查  '),
                '沿用构造函数的完整六字段请求，不丢JSON Mode或预算')
        require(request['model'] == 'kimi-k3' and request['stream'] is False and
                request['response_format'] == {'type': 'json_object'} and
                request['max_completion_tokens'] == 4096 and request['reasoning_effort'] == 'low',
                '既定模型、模式、非流式和预算保持')

    def invalid_question():
        for question, kind in [(None, TypeError), (False, TypeError), ([], TypeError),
                               ('', ValueError), (' \t\n', ValueError)]:
            client = FakeClient()
            expect(lambda: ask(client, question), kind, '先使用请求构造函数完成输入校验')
            require(client.calls == [] and client.close_count == 0, '无效问题零客户端请求')

    def envelopes():
        choice = response().choices[0]
        for result in (SimpleNamespace(), SimpleNamespace(choices=None),
                       SimpleNamespace(choices=()), SimpleNamespace(choices=(choice,)),
                       SimpleNamespace(choices=[]),
                       SimpleNamespace(choices=[choice, choice]), SimpleNamespace(choices=[None]),
                       SimpleNamespace(choices=[SimpleNamespace()]),
                       SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop')]),
                       SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=None)]),
                       SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace())])):
            no_parse(result)

    def finish_reasons():
        for reason in (None, '', 'length', 'tool_calls', 'content_filter', 'stop ', 0):
            no_parse(response(finish=reason))

    def invalid_content():
        for content in (None, '', ' \t\n', 7, False, [], {}):
            result = response()
            result.choices[0].message.content = content
            no_parse(result)

    def json_errors():
        raw_good = json.dumps(payload(), ensure_ascii=False)
        for raw in ('{', "{'answer': '单引号'}", '```json\n'+raw_good+'\n```', raw_good+'说明'):
            client = FakeClient(response(raw))
            expect(lambda: ask(client), json.JSONDecodeError,
                   '正文是原始JSON字符串，语法错误保留JSONDecodeError')
            require(len(client.calls) == 1, 'JSON错误不自动重问模型')

    def business_errors():
        changes = [('mode', 'mock'), ('mode', ' model '), ('source_status', 'retrieved'),
                   ('sources', ['未实际检索的假条目']), ('sources', {}),
                   ('answer', None), ('uncertainty', ' \t\n')]
        values = [[], {'answer': '缺字段'}, {**payload(), 'extra': True}]
        for key, value in changes:
            values.append({**payload(), key: value})
        for value in values:
            client = FakeClient(response(json.dumps(value, ensure_ascii=False)))
            expect(lambda: ask(client), ValueError, '不合model回答契约时拒绝，不能覆盖来源或模式')
            require(len(client.calls) == 1, '业务错误不重试，不用模拟回答掩盖')

    def explicit_mode():
        app = module()
        parameter = inspect.signature(app.parse_answer_json).parameters.get('expected_mode')
        require(parameter is not None and parameter.kind is inspect.Parameter.KEYWORD_ONLY and
                parameter.default == 'mock', '新增仅关键字参数expected_mode，默认mock保持旧调用兼容')
        for mode in ('mock', 'model'):
            raw = json.dumps(payload(mode))
            first, second = parse(raw, expected_mode=mode), parse(raw, expected_mode=mode)
            require(first == payload(mode) and first is not second and
                    first['sources'] is not second['sources'], '返回已验证原模式及独立dict/list')
            first['sources'].append('离线隔离标记')
            require(second['sources'] == [], '结果之间不共享sources')
            other = 'model' if mode == 'mock' else 'mock'
            expect(lambda: parse(raw, expected_mode=other), ValueError, '调用方预期模式与原字段必须一致')
        require(parse(json.dumps(payload('mock'))) == payload('mock'), '省略expected_mode仍接受mock')
        expect(lambda: parse(json.dumps(payload())), ValueError, '默认mock不能自行接受model')
        for mode in (None, False, [], 1):
            expect(lambda: parse('{', expected_mode=mode), TypeError, '先校验expected_mode类型')
        for mode in ('', 'retrieved', ' model ', 'MODEL'):
            expect(lambda: parse('{', expected_mode=mode), ValueError, '先拒绝未知expected_mode')
        expect(lambda: app.parse_answer_json(json.dumps(payload()), 'model'), TypeError,
               'expected_mode必须按名称传入，避免位置参数混淆')

    def delegation():
        app = module()
        question = '  透传问题  '
        request = app.build_structured_request(question)
        raw = ' \n' + json.dumps(payload(answer='  尚未清理的正文  '), ensure_ascii=False) + '\n '
        sentinel = {'解析器返回对象': '用于验证原样透传，不是业务成功样例'}
        client = FakeClient(response(raw))
        with patch.object(app, 'build_structured_request', return_value=request) as builder, \
                patch.object(app, 'parse_answer_json', return_value=sentinel) as parse_mock:
            result = ask(client, question)
            builder.assert_called_once_with(question)
            parse_mock.assert_called_once_with(raw, expected_mode='model')
        require(client.calls == [request], '将构造函数字典解包为create的关键字参数')
        require(result is sentinel, '直接返回解析器结果，不重新构造或JSON序列化')

    def sdk_error():
        error = RuntimeError('offline-sdk-error-marker')
        client = FakeClient(error=error)
        app = module()
        with patch.object(app, 'parse_answer_json', side_effect=AssertionError('失败请求不解析')) as parse_mock:
            caught = expect(lambda: ask(client), RuntimeError, 'SDK异常交给调用层处理')
            require(caught is error, '保留原异常对象，不换成成功或新异常')
            require(parse_mock.call_count == 0, 'SDK异常后不调用解析器')
        require(len(client.calls) == 1 and client.close_count == 0,
                '不自动重试，也不关闭由外层拥有的客户端')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s403b-regression-') as temporary:
            directory = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py'):
                require((PROJECT/name).is_file(), f'回归文件缺失：{name}')
                (directory/name).write_bytes((PROJECT/name).read_bytes())
            (directory/'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py',
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py'):
                (directory/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(directory/'test/check_s4_03a.py')],
                cwd=directory, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=160)
            require(result.returncode == 0 and '10/10 项通过' in result.stdout,
                    'S4-03A及此前回归不能退化：\n'+(result.stdout+result.stderr)[-2800:])

    def demo():
        print('离线假客户端演示：未读取Key，未请求真实模型。')
        print('以下mode=model是被测试的响应协议；正文来自内存假数据。')
        client = FakeClient(response(json.dumps(payload(answer='  一条离线假回答  '), ensure_ascii=False)))
        result = ask(client, '为什么地形会影响道路？')
        require(result == payload(answer='一条离线假回答'), '演示必须返回通过model契约校验的字典')
        require(len(client.calls) == 1, '演示只调用内存假客户端一次')
        print('假客户端调用次数：', len(client.calls))
        print('返回类型：', type(result).__name__)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print('未验证供应商真实接口、模型回答质量、usage或实际费用。')

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
            check('正常model回答解析并清理文本', normal)
            check('完整六字段请求只调用一次客户端', request_parameters)
            check('无效问题先拒绝，零客户端请求', invalid_question)
            check('choices或message无效时明确拒绝', envelopes)
            check('非stop结果先拒绝，不调用解析器', finish_reasons)
            check('空白或非字符串正文先拒绝', invalid_content)
            check('JSON语法错误原样保留，不修补或重问', json_errors)
            check('字段、模式与来源错误不覆盖洗白', business_errors)
            check('expected_mode显式选择、默认兼容与对象隔离', explicit_mode)
            check('复用构造器与解析器，参数及返回对象透传', delegation)
            check('SDK异常原样传播、不重试、不关闭外部客户端', sdk_error)
            check('S4-03A及此前回归（临时工程）', previous)
    require((hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None) == before,
            '检查期间入口变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8] if before else "未创建"}。')
    print('仅使用内存假客户端与临时旧课回归；未加载.env或真实Key、未请求模型、未读取会话。')
    print('通过仅证明本课离线调用与校验；真实接口、模型质量、usage和费用另行验证。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
