"""S3-07A：真实 SDK + 内存 SSE 假响应；检查流式调用层，不读取 Key 或连接网络。"""

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

import httpx2
from openai import APIError, OpenAI as SDKOpenAI, Stream

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from check_s3_02 import block_network, require
from check_s3_06 import chunk, stats


class Wire(httpx2.SyncByteStream):
    """只提供内存 SSE 字节；记录 HTTP 响应关闭及逐片消费顺序。"""

    def __init__(self, events, after_event=None):
        self.events = events
        self.after_event = after_event
        self.closed = False

    def __iter__(self):
        for index, event in enumerate(self.events):
            yield ('data: ' + json.dumps(event.to_dict(), ensure_ascii=False) + '\n\n').encode()
            if self.after_event is not None:
                self.after_event(index, event)
        yield b'data: [DONE]\n\n'

    def close(self):
        self.closed = True


@contextlib.contextmanager
def fake_stream_io(app, events, *, after_event=None, status=200):
    requests, clients, wires = [], [], []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        require(len(requests) == 1, '一次函数调用只发一次请求，不重试或额外请求统计')
        require(body.get('stream') is True, '新函数请求需显式 stream=True')
        require(body.get('stream_options', {}).get('include_usage') is True,
                '用 stream_options={"include_usage": True} 请求最终用量')
        require(body.get('model') == 'kimi-k3' and
                body.get('max_completion_tokens') == 4096 and
                body.get('reasoning_effort') == 'low' and 'max_tokens' not in body,
                '沿用 kimi-k3、4096/low，不使用旧 max_tokens 字段')
        timeouts = request.extensions.get('timeout', {})
        require(timeouts and all(value == 120 for value in timeouts.values()),
                '保留流式请求的有效 timeout=120 秒')
        if status != 200:
            return httpx2.Response(status, json={
                'error': {'message': 'offline-sensitive-marker', 'type': 'offline_error'}})
        wire = Wire(events, after_event)
        wires.append(wire)
        return httpx2.Response(200, headers={'content-type': 'text/event-stream'}, stream=wire)

    def factory(*args, **kwargs):
        require(not args, 'OpenAI 客户端参数使用现有关键字形式')
        require(kwargs.get('timeout') == 120 and kwargs.get('max_retries') == 0,
                '客户端继续 timeout=120、max_retries=0')
        require(str(kwargs.get('base_url', '')).rstrip('/') == 'https://api.moonshot.cn/v1',
                '继续使用当前 Kimi base_url')
        client = SDKOpenAI(**kwargs, http_client=httpx2.Client(
            transport=httpx2.MockTransport(handler)))
        clients.append(client)
        return client

    try:
        with patch.object(app, 'get_api_key', return_value='offline-fake-key'), \
                patch.object(app, 'OpenAI', side_effect=factory):
            yield SimpleNamespace(requests=requests, clients=clients, wires=wires)
    finally:
        # 仅为失败测试清理；关闭断言必须放在调用后、退出此上下文之前。
        for client in clients:
            client.close()


def main():
    outcomes = []
    source = project / 'model_demo_ask_turn.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    dotenv_stub = ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False

    def check(name, action):
        try:
            action()
        except Exception as exc:
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
            tempfile.TemporaryDirectory(prefix='geo-history-s307a-check-') as temporary:
        import model_demo_ask_turn as app

        def api():
            function = getattr(app, 'ask_stream_messages', None)
            require(callable(function),
                    '新增 ask_stream_messages(messages, on_text=None)，保留旧 ask_messages')
            return function

        def messages():
            return [{'role': 'system', 'content': '离线模拟规则'},
                    {'role': 'user', 'content': '离线问题'}]

        def normal_events(usage=(9, 3, 12)):
            return [chunk(role='assistant'), chunk('第一片'), chunk(' 第二片'),
                    chunk(reason='stop'), chunk(no_choices=True, usage=usage)]

        def call(data, *args):
            output = io.StringIO()
            forbidden = AssertionError('调用层只返回结果／转交回调，不展示、存储或提交历史')
            with patch('builtins.input', side_effect=forbidden), \
                    patch.object(app, 'display', side_effect=forbidden), \
                    patch.object(app, 'commit_turn', side_effect=forbidden), \
                    patch.object(app, 'save_history', side_effect=forbidden), \
                    patch.object(app, 'load_history', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                try:
                    result = api()(data, *args)
                finally:
                    require(not output.getvalue(), '调用层不直接 print；原样转交调用方回调')
            require(isinstance(result, app.ModelAnswer), '返回已有 ModelAnswer')
            return result

        def require_closed(trace):
            require(trace.clients and all(client.is_closed() for client in trace.clients),
                    '函数返回／抛错前关闭客户端，推荐 with OpenAI(...) as client')
            require(all(wire.closed for wire in trace.wires),
                    '消费流结束／抛错前关闭响应，推荐 with client.chat.completions.create(...) as stream')

        def check_contract():
            parameter = inspect.signature(api()).parameters.get('on_text')
            require(parameter is not None and parameter.default is None,
                    '新函数 on_text 默认 None，保留可选正文回调')

        def check_sdk():
            data = messages()
            original = deepcopy(data)
            with fake_stream_io(app, normal_events()) as trace:
                answer = call(data)
                require(len(trace.requests) == 1 and trace.requests[0]['messages'] == original,
                        '原样发送传入消息，只请求一次')
                require(answer.content == '第一片 第二片' and answer.finish_reason == 'stop'
                        and stats(answer) == (9, 3, 12), 'SDK 解析 SSE 后交给消费函数，返回完整元数据')
            require(data == original, '新函数不能改写调用方消息')

        def check_reuse():
            result = app.ModelAnswer('离线结果', 'stop', assistant_message={
                'role': 'assistant', 'content': '离线结果'})
            received, calls = [], []
            callback = received.append

            def consume(stream, on_text=None):
                require(isinstance(stream, Stream), '传入 SDK Stream，不提前 list 或重写消费逻辑')
                require(on_text is callback, '原样转交调用方 on_text，不替换成 display')
                calls.append(stream)
                return result

            with fake_stream_io(app, normal_events()) as trace, \
                    patch.object(app, 'consume_stream', side_effect=consume):
                answer = call(messages(), callback)
                require(answer is result and len(calls) == 1,
                        '复用 consume_stream 一次，并直接返回同一结果对象')
                require_closed(trace)

        def check_live_callback():
            received = []
            fragments = ['第一片', ' ', '第二片']
            events = [chunk(text) for text in fragments] + [
                chunk(reason='stop'), chunk(no_choices=True, usage=(9, 3, 12))]

            def after_event(index, event):
                if index < len(fragments):
                    require(received == fragments[:index + 1],
                            '每片正文解析后马上回调，不能等流结束后才通知')

            with fake_stream_io(app, events, after_event=after_event):
                answer = call(messages(), received.append)
                require(received == fragments and answer.content == ''.join(fragments),
                        '只通知正文原片段，不通知累计正文或元数据')

        def check_optional():
            with fake_stream_io(app, normal_events()):
                require(call(messages()).content == '第一片 第二片', '不传回调也能返回完整正文')

        def check_usage():
            for usage, expected in ((None, (None, None, None)), ((0, 0, 0), (0, 0, 0))):
                events = [chunk('正文', reason='stop')]
                if usage is not None:
                    events.append(chunk(no_choices=True, usage=usage))
                with fake_stream_io(app, events):
                    require(stats(call(messages())) == expected, '用量缺失与有效零值保持区别')

        def check_reasoning():
            received = []
            events = [chunk(reasoning='offline-'), chunk('正文', reasoning='protocol'),
                      chunk(reason='stop'), chunk(no_choices=True, usage=(9, 3, 12))]
            with fake_stream_io(app, events):
                answer = call(messages(), received.append)
                require(answer.assistant_message == {'role': 'assistant', 'content': '正文',
                        'reasoning_content': 'offline-protocol'} and received == ['正文'],
                        '真实 SDK 解析后仍保留协议扩展，正文回调不包含它')

        def check_close():
            with fake_stream_io(app, normal_events()) as trace:
                call(messages())
                require_closed(trace)

        def check_error_close():
            for source_of_error in ('consumer', 'callback'):
                error = ValueError('offline-failure')

                def fail(*args, **kwargs):
                    raise error

                with fake_stream_io(app, normal_events()) as trace, contextlib.ExitStack() as stack:
                    callback = fail if source_of_error == 'callback' else None
                    if source_of_error == 'consumer':
                        stack.enter_context(patch.object(app, 'consume_stream', side_effect=fail))
                    try:
                        call(messages(), callback)
                    except ValueError as actual:
                        require(actual is error, '消费／回调异常原样向上传播')
                    else:
                        raise AssertionError('异常不能吞掉、重试或伪造成功结果')
                    require(len(trace.requests) == 1, '失败也只请求一次')
                    require_closed(trace)

        def check_config():
            with fake_stream_io(app, normal_events()) as trace, \
                    patch.object(app, 'get_api_key', side_effect=ValueError('离线缺配置')):
                try:
                    call(messages())
                except ValueError:
                    pass
                else:
                    raise AssertionError('配置失败应传播，不继续创建请求')
                require(not trace.requests and not trace.clients,
                        '缺配置在创建客户端前停止，零请求')

        def check_http_error():
            for status in (401, 503):
                with fake_stream_io(app, [], status=status) as trace:
                    try:
                        call(messages())
                    except APIError as actual:
                        require(actual.status_code == status, '原 APIError 状态保留')
                    else:
                        raise AssertionError('HTTP 错误由调用方处理，不能返回成功结果')
                    require(len(trace.requests) == 1, '401/503 不自动重试')
                    require_closed(trace)

        def check_previous():
            regression = Path(temporary) / 'regression-project'
            regression.mkdir()
            for name in ('model_demo_ask_turn.py', 'conversation.py', 'session_store.py',
                         'IncompleteStreamError.py', 'config.py', '.gitignore'):
                (regression / name).write_bytes((project / name).read_bytes())
            (regression / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py',
                         'check_s3_02.py', 'check_s3_03.py', 'check_s3_04.py',
                         'check_s3_05.py', 'check_s3_06.py'):
                (regression / 'test' / name).write_bytes((tests / name).read_bytes())
            result = subprocess.run([sys.executable, str(regression / 'test/check_s3_06.py')],
                                    cwd=regression, capture_output=True, encoding='utf-8',
                                    errors='replace', timeout=50)
            require(result.returncode == 0, 'S3-06 及此前回归未通过：\n' +
                    (result.stdout + result.stderr)[-2400:])

        check('独立流式函数与可选回调接口', check_contract)
        check('SDK SSE 请求、模型预算及完整结果', check_sdk)
        check('复用消费函数并原样转交回调／返回值', check_reuse)
        check('真实 SDK 解析后逐片立即通知', check_live_callback)
        check('不提供回调仍返回完整结果', check_optional)
        check('缺失用量与有效零值', check_usage)
        check('reasoning_content 单独保留', check_reasoning)
        check('正常结束关闭客户端与响应', check_close)
        check('消费／回调异常传播并关闭资源', check_error_close)
        check('缺少配置零客户端零请求', check_config)
        check('401/503 原样传播且不重试', check_http_error)
        check('S3-06 及此前回归（临时工程）', check_previous)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before,
            '检查期间业务源码变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('仅内存 SSE 假响应；未加载 .env、未读取真实 Key、未发送模型网络请求。')
    print('本课只验收 SDK 调用层；CLI、真实流完整性、回答质量和费用另行验证。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
