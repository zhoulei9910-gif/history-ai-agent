"""S4-03C：离线检查响应元数据提取与失败前通知；假用量不代表真实费用。"""

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
from check_s4_03b import FakeClient, payload, response

FIELDS = {'finish_reason', 'prompt_tokens', 'completion_tokens', 'total_tokens'}


def with_usage(raw=None, finish='stop', **counts):
    result = response(raw, finish)
    result.usage = SimpleNamespace(**({'prompt_tokens': 8, 'completion_tokens': 3,
                                      'total_tokens': 11} if not counts else counts))
    return result


def expected(finish='stop', prompt=8, completion=3, total=11):
    return {'finish_reason': finish, 'prompt_tokens': prompt,
            'completion_tokens': completion, 'total_tokens': total}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='演示成功和JSON失败仍保留假用量；不请求模型')
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
            require(not output.getvalue() and not errors.getvalue(), '导入只定义函数，不打印、加载配置或请求模型')
            require(callable(getattr(app, 'extract_response_metadata', None)),
                    '新增extract_response_metadata(response) -> dict')
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
                require(not output.getvalue() and not errors.getvalue(), '提取器与调用端只返回或抛错，不打印、输入或访问文件')

    def extract(result):
        return silent(lambda: module().extract_response_metadata(result))

    def ask(client, question='离线问题', **kwargs):
        return silent(lambda: module().ask_structured(client, question, **kwargs))

    def expect(action, kind, message):
        try:
            action()
        except Exception as error:
            require(isinstance(error, kind), f'{message}；应为{kind.__name__}，实际{type(error).__name__}')
            if kind is ValueError:
                require(not isinstance(error, json.JSONDecodeError), '响应包络／业务错误仍是普通ValueError')
            return error
        raise AssertionError(message + '；错误被当作成功返回')

    def shape(metadata):
        require(isinstance(metadata, dict) and set(metadata) == FIELDS,
                '元数据为恰好四字段的新dict，不包含原始响应、正文或额外费用字段')

    def normal_metadata():
        result = with_usage()
        before_result = deepcopy(result)
        metadata = extract(result)
        shape(metadata)
        require(metadata == expected(), '如实保留响应结束原因及三个计数')
        require(result == before_result, '提取器不修改原响应')

    def missing_usage():
        for result in (response(), SimpleNamespace(choices=response().choices, usage=None)):
            require(extract(result) == expected(prompt=None, completion=None, total=None),
                    'usage缺失或None时三个统计均为None')
        result = with_usage(prompt_tokens=8)
        require(extract(result) == expected(completion=None, total=None),
                '部分字段缺失只填对应None，不推算total_tokens')
        result.usage = SimpleNamespace(prompt_tokens=None, completion_tokens=3, total_tokens=None)
        require(extract(result) == expected(prompt=None, total=None), '已提供的None保持缺失语义')

    def zero_usage():
        for values in ((0, 0, 0), (8, 0, 8), (0, 3, 3)):
            result = with_usage(prompt_tokens=values[0], completion_tokens=values[1], total_tokens=values[2])
            require(extract(result) == expected(prompt=values[0], completion=values[1], total=values[2]),
                    '0是已提供数值，不能用or None把它改成缺失')

    def finish_reason():
        for finish in ('stop', 'length', 'unknown', '', ' stop ', None):
            require(extract(with_usage(finish=finish)) == expected(finish),
                    '结束原因保持原值，不strip、翻译或写死stop')
        choice = response().choices[0]
        for choices in (None, [], (), (choice,), [choice, choice], [None], [SimpleNamespace()]):
            result = with_usage()
            result.choices = choices
            require(extract(result) == expected(None), '无单项list或缺结束原因时为None，但仍保留usage')
        result = with_usage()
        del result.choices
        require(extract(result) == expected(None), 'choices属性缺失时仍保留usage')

    def callback_order():
        app = module()
        parameter = inspect.signature(app.ask_structured).parameters.get('on_metadata')
        require(parameter is not None and parameter.kind is inspect.Parameter.KEYWORD_ONLY and
                parameter.default is None, '增加仅关键字参数on_metadata=None，保持旧调用兼容')
        client, events, seen = FakeClient(with_usage()), [], []
        original = client.chat.completions.create
        def create(**kwargs):
            events.append('request')
            return original(**kwargs)
        def notify(metadata):
            events.append('metadata')
            seen.append(metadata)
            return {'这个回调返回值': '应被忽略'}
        sentinel = {'解析器对象': '透传检查'}
        def parse(*args, **kwargs):
            events.append('parse')
            return sentinel
        client.chat.completions.create = create
        with patch.object(app, 'parse_answer_json', side_effect=parse) as parse_mock, \
                patch.object(app, 'extract_response_metadata', wraps=app.extract_response_metadata) as extractor:
            answer = ask(client, on_metadata=notify)
            extractor.assert_called_once_with(client.result)
            parse_mock.assert_called_once_with(client.result.choices[0].message.content, expected_mode='model')
        require(events == ['request', 'metadata', 'parse'] and seen == [expected()],
                'create返回后、正文解析前通知一次，不等成功后才记录')
        require(answer is sentinel and len(client.calls) == 1, '忽略回调返回值，保留原解析结果且不重问')

    def invalid_callback():
        for callback in (False, 0, '', [], {}):
            client = FakeClient(with_usage())
            expect(lambda: ask(client, on_metadata=callback), TypeError, '非None且不可调用的观察器请求前拒绝')
            require(client.calls == [] and client.close_count == 0, '无效回调零请求，不关闭外部客户端')
        for question, kind in ((None, TypeError), (' \t\n', ValueError)):
            client, seen = FakeClient(with_usage()), []
            expect(lambda: ask(client, question, on_metadata=seen.append), kind, '输入错误仍在请求前拒绝')
            require(client.calls == [] and seen == [], '无效问题不请求也不通知元数据')

    def default_skip():
        app = module()
        with patch.object(app, 'extract_response_metadata', side_effect=AssertionError('默认应完全跳过提取器')):
            for explicit in (False, True):
                client = FakeClient(with_usage())
                answer = ask(client, **({'on_metadata': None} if explicit else {}))
                require(answer == payload() and len(client.calls) == 1, '默认None保持原B行为与返回值')

    def failed_answers():
        cases = [(with_usage(finish='length'), ValueError), (with_usage(raw=' '), ValueError),
                 (with_usage(raw='{'), json.JSONDecodeError),
                 (with_usage(raw=json.dumps({**payload(), 'sources': ['并未检索的假来源']})), ValueError)]
        for choices in ([], (response().choices[0],), [None], [SimpleNamespace(finish_reason='stop')]):
            result = with_usage()
            result.choices = choices
            cases.append((result, ValueError))
        for result, kind in cases:
            seen, client = [], FakeClient(result)
            metadata = extract(result)
            expect(lambda: ask(client, on_metadata=seen.append), kind, '无效回答保留既有异常')
            require(seen == [metadata] and len(client.calls) == 1,
                    '回答包络／正文／JSON／业务失败前仍通知已返回统计，不能为补统计重问')
        client, seen = FakeClient(response()), []
        client.result.choices[0].message.content = '{'
        expect(lambda: ask(client, on_metadata=seen.append), json.JSONDecodeError, '缺usage也仍传播原JSON错误')
        require(seen == [expected(prompt=None, completion=None, total=None)], '缺统计时仍通知缺失状态，不伪造0')

    def sdk_failure():
        error, seen = RuntimeError('offline-sdk-error'), []
        client = FakeClient(error=error)
        app = module()
        with patch.object(app, 'extract_response_metadata', side_effect=AssertionError('没有响应不提取')):
            caught = expect(lambda: ask(client, on_metadata=seen.append), RuntimeError, 'SDK失败原样传播')
        require(caught is error and not seen and len(client.calls) == 1 and client.close_count == 0,
                '无响应不通知、不重试、不自行关闭客户端')

    def callback_failure():
        app, error, seen = module(), RuntimeError('offline-observer-error'), []
        client = FakeClient(with_usage())
        def notify(metadata):
            seen.append(metadata)
            raise error
        with patch.object(app, 'parse_answer_json', side_effect=AssertionError('观察器异常后不继续解析')) as parse_mock:
            caught = expect(lambda: ask(client, on_metadata=notify), RuntimeError, '观察器异常原样传播')
            require(parse_mock.call_count == 0, '本课不吞掉观察器异常后继续业务')
        require(caught is error and seen == [expected()] and len(client.calls) == 1 and client.close_count == 0,
                '回调错误不重试，也不关闭外部客户端')

    def isolation():
        result = with_usage()
        first, second = extract(result), extract(result)
        require(first is not second and first == second, '每次返回新的元数据dict')
        first['total_tokens'] = 999
        require(second == expected() and result.usage.total_tokens == 11, '修改提取结果不改原响应或其他结果')
        before_result, seen = deepcopy(result), []
        def notify(metadata):
            seen.append(metadata)
            metadata.clear()
            metadata['answer'] = '观察器试图改正文'
        client = FakeClient(result)
        answer = ask(client, on_metadata=notify)
        require(answer == payload() and result == before_result and len(seen) == 1,
                '回调只能修改独立元数据，不污染响应或回答')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s403c-regression-') as temporary:
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
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py', 'check_s4_03b.py'):
                (directory/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(directory/'test/check_s4_03b.py')],
                cwd=directory, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=180)
            require(result.returncode == 0 and '12/12 项通过' in result.stdout,
                    'S4-03B补强检查及此前回归不能退化：\n'+(result.stdout+result.stderr)[-2800:])

    def demo():
        print('离线假客户端演示：未读取Key，未请求模型；以下用量是假值，不代表真实费用。')
        for raw in (json.dumps(payload(), ensure_ascii=False), '{'):
            client, seen = FakeClient(with_usage(raw=raw)), []
            try:
                answer = ask(client, on_metadata=seen.append)
            except json.JSONDecodeError:
                print('JSON失败：JSONDecodeError；仍收到假元数据：', seen)
            else:
                print('正常假回答：', answer['answer'], '；假元数据：', seen)
            require(seen == [expected()] and len(client.calls) == 1, '两种情况都应先收到假统计且各只调用一次')
        print('演示未验证真实接口、模型质量或实际费用。')

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
            check('正常响应提取四字段，不改原响应', normal_metadata)
            check('缺失与部分usage保留None，不推算', missing_usage)
            check('零统计保留0，不改成None', zero_usage)
            check('结束原值与无效choices的元数据边界', finish_reason)
            check('回调接口、单次提取与先通知后解析', callback_order)
            check('无效回调与无效问题均零请求', invalid_callback)
            check('默认None跳过提取，旧返回值兼容', default_skip)
            check('回答校验失败前仍保留已返回统计', failed_answers)
            check('SDK失败无响应，不提取或通知', sdk_failure)
            check('回调异常原样传播、不重试或继续解析', callback_failure)
            check('元数据与回答及原响应相互隔离', isolation)
            check('S4-03B补强及此前回归（临时工程）', previous)
    require((hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None) == before,
            '检查期间入口变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8] if before else "未创建"}。')
    print('只用内存假响应与临时旧课副本；未读取.env或Key、会话，未请求真实模型。')
    print('假用量不代表实际费用；只验证元数据传递和失败边界，不证明模型质量。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
