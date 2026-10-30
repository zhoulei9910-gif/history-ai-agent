"""S3-08：离线检查流式中断与提交边界，不证明原始 SSE [DONE]。"""

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
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import httpx2
from openai import APIError

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from check_s3_02 import block_network, require
from check_s3_06 import chunk, stats
from check_s3_07a import fake_stream_io

INCOMPLETE = '流式回答未完成，本轮未加入历史'
CANCELLED = '已取消，退出程序'


def events(text='【离线完整正文】', reason='stop', usage=(9, 3, 12)):
    result = [chunk(role='assistant'), chunk(text), chunk(reason=reason)]
    if usage is not None:
        result.append(chunk(no_choices=True, usage=usage))
    return result


def main():
    outcomes = []
    source = project / 'model_demo_ask_turn.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    dotenv_stub = ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False

    def check(name, action):
        try:
            action()
        except (Exception, KeyboardInterrupt) as exc:
            outcomes.append(False)
            print(f'未通过｜{name}：{type(exc).__name__}: {exc}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{name}')

    with patch.dict(sys.modules, {'dotenv': dotenv_stub}), \
            patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', block_network), \
            patch('socket.socket.connect_ex', block_network), \
            patch('socket.create_connection', block_network), \
            tempfile.TemporaryDirectory(prefix='geo-history-s308-check-') as temporary:
        import model_demo_ask_turn as app
        import session_store

        directory = Path(temporary)

        def error_type():
            result = getattr(app, 'IncompleteStreamError', None)
            require(isinstance(result, type) and issubclass(result, Exception),
                    '新增 IncompleteStreamError(Exception)，表达缺失结束原因')
            return result

        def seeded():
            return [{'role': 'system', 'content': '离线规则'},
                    {'role': 'user', 'content': '旧问题'},
                    {'role': 'assistant', 'content': '旧答案',
                     'reasoning_content': 'offline-old-protocol'}]

        def require_closed(trace, *, allow_no_wire=False):
            require(len(trace.requests) == 1, '每轮只请求一次，不自动重试或补统计')
            require(trace.clients and all(client.is_closed() for client in trace.clients),
                    '返回或异常传播前关闭客户端')
            require((allow_no_wire or trace.wires) and all(wire.closed for wire in trace.wires),
                    '返回或异常传播前关闭已创建的流响应')

        def ask(history, question='新问题', on_text=None):
            forbidden = AssertionError('ask_turn 不展示、不读写会话；提交由成功边界控制')
            output = io.StringIO()
            with patch.object(app, 'load_history', side_effect=forbidden), \
                    patch.object(app, 'save_history', side_effect=forbidden), \
                    patch.object(app, 'display', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                try:
                    return app.ask_turn(history, question, stream=True, on_text=on_text)
                finally:
                    require(not output.getvalue(), 'ask_turn 不直接输出；展示交由调用方')

        def run_cli(path, inputs, plans, *, before_request=None):
            loads, saves, requests, histories = [], [], [], []
            output = io.StringIO()
            original_stream = app.ask_stream_messages
            next_plan = iter(plans)

            def read(candidate):
                require(path is not None and Path(candidate) == path,
                        '加载只使用本次临时会话路径')
                loads.append(Path(candidate))
                history = session_store.load_history(candidate)
                histories.append(history)
                return history

            def write(candidate, history):
                require(path is not None and Path(candidate) == path,
                        '保存只使用本次临时会话路径')
                saves.append(deepcopy(history))
                return session_store.save_history(candidate, history)

            def replay(messages, on_text=None):
                try:
                    plan = next(next_plan)
                except StopIteration:
                    raise AssertionError('请求超过用例预算，检查错误分支重试／退出') from None
                if before_request is not None:
                    before_request(len(requests) + 1)
                with fake_stream_io(app, plan.get('events', []),
                                    after_event=plan.get('after')) as trace, \
                        contextlib.ExitStack() as request_stack:
                    if plan.get('cancel_request'):
                        def cancel_before_response(transport, request):
                            body = json.loads(request.content)
                            trace.requests.append(body)
                            require(body.get('stream') is True,
                                    '请求创建阶段取消仍只尝试本轮流式请求')
                            raise KeyboardInterrupt()

                        request_stack.enter_context(patch.object(
                            httpx2.MockTransport, 'handle_request', autospec=True,
                            side_effect=cancel_before_response))
                    try:
                        return original_stream(messages, on_text)
                    finally:
                        requests.extend(deepcopy(trace.requests))
                        # 在 fake_stream_io 的兜底清理之前判断，不能把测试清理当业务正确。
                        require_closed(trace, allow_no_wire=plan.get('cancel_request', False))
                        if plan.get('cancel_request'):
                            require(not trace.wires, '响应创建前取消没有已创建的流响应')

            with patch.object(app, 'load_history', side_effect=read), \
                    patch.object(app, 'save_history', side_effect=write), \
                    patch.object(app, 'ask_stream_messages', side_effect=replay), \
                    patch.object(app, 'ask_messages', side_effect=AssertionError('启用流式模式')), \
                    patch('builtins.input', side_effect=inputs) as mocked_input, \
                    contextlib.redirect_stdout(output), contextlib.ExitStack() as stack:
                if path is None:
                    stack.enter_context(patch('pathlib.Path.mkdir',
                        side_effect=AssertionError('None 模式不创建会话目录')))
                result = app.main(path, stream=True)
            require(result is None, 'main 继续返回 None')
            return SimpleNamespace(loads=loads, saves=saves, requests=requests,
                                   histories=histories, output=output.getvalue(),
                                   inputs=mocked_input.call_count)

        def check_contract():
            cls = error_type()
            error = cls('offline-sensitive-marker')
            require(isinstance(error, Exception), '项目异常可由明确的 except 分支捕获')

        def check_normal():
            history = seeded()
            old = deepcopy(history)
            received = []

            def notify(fragment):
                require(history == old, '片段展示期间不提前提交半轮')
                received.append(fragment)

            pieces = [chunk(reasoning='offline-protocol'), *events()]
            with fake_stream_io(app, pieces) as trace:
                with patch.object(app, 'commit_turn', wraps=app.commit_turn) as commit:
                    answer = ask(history, '  新问题  ', notify)
                require(commit.call_count == 1, '成功问答只提交一次')
                require_closed(trace)
            require(history[:len(old)] == old and len(history) == len(old) + 2,
                    '成功追加一对问答，旧历史不改写')
            require(history[-2]['content'] == '新问题' and
                    history[-1] == answer.assistant_message and
                    history[-1].get('reasoning_content') == 'offline-protocol',
                    '提交清理后的问题及完整 assistant 协议字段')
            require(received == ['【离线完整正文】'] and stats(answer) == (9, 3, 12),
                    '流式回调、正文和最终统计保留')

        def check_incomplete():
            cls = error_type()
            for data in ([], [chunk(role='assistant')], [chunk('【部分正文】')]):
                history = seeded()
                old = deepcopy(history)
                received = []
                with fake_stream_io(app, data) as trace:
                    try:
                        ask(history, on_text=received.append)
                    except cls:
                        pass
                    else:
                        raise AssertionError('空流／无结束原因不能正常返回，应抛项目异常')
                    require_closed(trace)
                require(history == old, '无结束原因时不提交，即使已通知过正文')
                require(received == (['【部分正文】'] if len(data) == 1 and
                        data[0].choices[0].delta.content else []), '已收到片段仍可通知展示')

        def check_consumer_and_nonstream():
            # S3-06 的低层如实收集契约保留：未结束的消费结果本身不是异常。
            answer = app.consume_stream(iter([chunk('部分正文')]))
            require(answer.content == '部分正文' and answer.finish_reason == '',
                    'consume_stream 保留原始缺结束原因契约；判断放 ask_turn 流式分支')
            history = seeded()
            old = deepcopy(history)
            expected = app.ModelAnswer('旧调用无结束原因', '', assistant_message={
                'role': 'assistant', 'content': '旧调用无结束原因'})
            with patch.object(app, 'ask_messages', return_value=expected) as original, \
                    patch.object(app, 'ask_stream_messages', side_effect=AssertionError('旧默认保持')):
                result = app.ask_turn(history, '旧模式问题')
            require(result is expected and original.call_count == 1 and history == old,
                    'stream=False 不套用新项目异常，仍保留旧不提交行为')

        def check_unaccepted():
            for text, reason in [('部分正文', 'length'), ('非空', 'content_filter'),
                                 ('非空', 'tool_calls'), ('', 'stop'), ('   ', 'stop')]:
                history = seeded()
                old = deepcopy(history)
                with fake_stream_io(app, events(text, reason)) as trace:
                    answer = ask(history)
                    require_closed(trace)
                require(history == old and answer.finish_reason == reason,
                        '截断、其他结束原因及空白正文不提交；保留结果供最终展示')
            # 供应商未知的非空原因是返回值，不得误当 stop 或“缺失原因”。
            history = seeded()
            old = deepcopy(history)
            expected = app.ModelAnswer('正文', 'vendor_unknown', assistant_message={
                'role': 'assistant', 'content': '正文'})
            with patch.object(app, 'ask_stream_messages', return_value=expected):
                require(ask(history) is expected and history == old,
                        '未知非空结束原因保持，不提交，也不伪造成功')

        def check_api_failure():
            for failure_at in (0, 1, 2):
                error = APIError('offline-sensitive-marker',
                                 request=httpx2.Request('POST', 'https://offline.invalid'), body=None)

                def interrupt(index, event):
                    if index == failure_at:
                        raise error

                history = seeded()
                old = deepcopy(history)
                with fake_stream_io(app, events(), after_event=interrupt) as trace:
                    try:
                        ask(history)
                    except APIError as actual:
                        require(actual is error, '原 API 异常保留，不包装成成功')
                    else:
                        raise AssertionError('消费异常需向上传播，包括 stop 后发生的异常')
                    require_closed(trace)
                require(history == old, '首片前／部分正文后／stop 后异常均不提交')

        def check_usage():
            for usage, expected in ((None, (None, None, None)), ((0, 0, 0), (0, 0, 0))):
                history = seeded()
                with fake_stream_io(app, events(usage=usage)) as trace:
                    answer = ask(history)
                    require_closed(trace)
                require(len(history) == 5 and stats(answer) == expected,
                        '缺统计不等于中断；有效0保留，正常stop可按当前策略提交')

        def check_cli_incomplete():
            path = directory / 'incomplete.json'
            old = seeded()
            path.write_text(json.dumps(old, ensure_ascii=False), encoding='utf-8')
            original = path.read_bytes()

            def before_request(number):
                if number == 2:
                    require(path.read_bytes() == original, '失败问答不能先覆盖会话文件')

            trace = run_cli(path, ['失败问题', '恢复问题', 'quit'],
                            [{'events': [chunk('【未完成正文】')]},
                             {'events': events('【恢复正文】')}], before_request=before_request)
            require(trace.output.count(INCOMPLETE) == 1 and
                    '【未完成正文】\n' + INCOMPLETE in trace.output,
                    '固定未完成提示一次，先补换行，再继续等待问题')
            require(len(trace.requests) == 2 and trace.requests[1]['messages'] ==
                    old + [{'role': 'user', 'content': '恢复问题'}],
                    '下一轮不包含失败问题或部分回答，不自动重试')
            saved = session_store.load_history(path)
            require(len(trace.saves) == 1 and saved == old + [
                {'role': 'user', 'content': '恢复问题'},
                {'role': 'assistant', 'content': '【恢复正文】'}],
                '只有恢复后的完整问答提交并保存一次')

        def check_cli_api_recover():
            def interrupt(index, event):
                if index == 1:
                    raise APIError('offline-sensitive-marker',
                        request=httpx2.Request('POST', 'https://offline.invalid'), body=None)

            trace = run_cli(None, ['错误问题', '恢复问题', 'quit'],
                            [{'events': events('【中断正文】'), 'after': interrupt},
                             {'events': events('【恢复正文】')}])
            require('【中断正文】\n' in trace.output and '模型调用失败' in trace.output and
                    'offline-sensitive-marker' not in trace.output,
                    'API失败有安全提示及换行，不回显原始错误')
            require(len(trace.requests) == 2 and len(trace.requests[1]['messages']) == 2 and
                    trace.requests[1]['messages'][-1]['content'] == '恢复问题',
                    'API失败后继续；失败问答不污染下一轮')
            require(not trace.loads and not trace.saves, 'None模式仍不访问会话')

        def check_cli_cancel():
            for failure_at in ('request', 0, 1, 2):
                path = directory / f'cancel-{failure_at}.json'
                old = seeded()
                path.write_text(json.dumps(old, ensure_ascii=False), encoding='utf-8')
                original = path.read_bytes()

                def interrupt(index, event):
                    if index == failure_at:
                        raise KeyboardInterrupt()

                try:
                    trace = run_cli(path, ['取消问题', '不应再次读取'],
                        [{'events': events('【取消前正文】'), 'after': interrupt,
                          'cancel_request': failure_at == 'request'}])
                except KeyboardInterrupt:
                    stage = '请求创建阶段' if failure_at == 'request' else '消费阶段'
                    raise AssertionError(f'{stage}取消应由 main 捕获并提示后返回') from None
                require(trace.inputs == 1 and len(trace.requests) == 1 and not trace.saves,
                        'Ctrl-C退出，不继续input、不重试、不保存')
                require(trace.histories == [old] and path.read_bytes() == original,
                        '取消保留原内存历史和原存档，包括stop后取消')
                require(trace.output.count(CANCELLED) == 1 and
                        trace.output.rstrip().endswith(CANCELLED), '取消使用固定提示并结束')
                if failure_at in (1, 2):
                    require('【取消前正文】\n' + CANCELLED in trace.output,
                            '已展示部分正文也须先换行再显示取消提示')

        def check_cli_empty_length():
            for number, (text, reason) in enumerate([('', 'stop'), ('  ', 'stop'),
                                                    ('部分正文', 'length')]):
                path = directory / f'uncommitted-{number}.json'
                trace = run_cli(path, ['问题', 'quit'], [{'events': events(text, reason)}])
                require(not trace.saves and not path.exists(), '空白或截断不创建未提交会话')
                require('回答为空' in trace.output if reason == 'stop' else '截断' in trace.output,
                        '沿用空答和截断提示，不误判为缺失结束原因')

        def check_previous():
            regression = directory / 'regression-project'
            regression.mkdir()
            for name in ('model_demo_ask_turn.py', 'conversation.py', 'session_store.py',
                         'IncompleteStreamError.py', 'config.py', '.gitignore'):
                (regression / name).write_bytes((project / name).read_bytes())
            (regression / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py',
                         'check_s3_02.py', 'check_s3_03.py', 'check_s3_04.py',
                         'check_s3_05.py', 'check_s3_06.py', 'check_s3_07a.py',
                         'check_s3_07b.py'):
                (regression / 'test' / name).write_bytes((tests / name).read_bytes())
            result = subprocess.run([sys.executable, str(regression / 'test/check_s3_07b.py')],
                                    cwd=regression, capture_output=True, text=True, timeout=80)
            require(result.returncode == 0, 'S3-07B及此前回归未通过：\n' +
                    (result.stdout + result.stderr)[-2400:])

        check('定义项目级不完整流异常', check_contract)
        check('完整stop按当前应用策略只提交一次', check_normal)
        check('空流／部分正文无结束原因抛错且不提交', check_incomplete)
        check('低层消费与旧非流式默认契约保持', check_consumer_and_nonstream)
        check('截断／其他结束原因／空白不提交', check_unaccepted)
        check('首片前／部分正文后／stop后API异常与资源释放', check_api_failure)
        check('缺用量及有效零值不被误判为中断', check_usage)
        check('未完成安全提示并继续，失败历史不污染下一轮', check_cli_incomplete)
        check('API中断后换行并继续，无重试和历史污染', check_cli_api_recover)
        check('Ctrl-C取消退出，不提交或保存，关闭资源', check_cli_cancel)
        check('空答／截断提示及不落盘规则保持', check_cli_empty_length)
        check('S3-07B及此前回归（临时工程）', check_previous)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before,
            '检查期间源码变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('仅使用内存SSE和临时会话，未加载.env、未读取真实Key、未请求真实模型。')
    print('stop+非空正文+消费未抛错只是本课应用接受策略，不证明原始[DONE]或传输完整性。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
