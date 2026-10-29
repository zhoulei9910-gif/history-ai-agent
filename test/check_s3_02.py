"""S3-02：真实 SDK + 内存 HTTP 假响应，检查多轮接线；不读取 Key 或调用模型。"""

import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import httpx2
from openai import OpenAI as SDKOpenAI, APIError

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def block_network(*args, **kwargs):
    raise AssertionError('离线检查禁止连接真实网络')


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_event(content='【模拟响应】已设为南京。', reason='stop', usage=(10, 5, 15)):
    message = {
        'role': 'assistant', 'content': content,
        'reasoning_content': 'offline-protocol-only',
    }
    body = {
        'id': 'offline-completion', 'object': 'chat.completion', 'created': 0,
        'model': 'kimi-k3',
        'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
    }
    if usage is not None:
        body['usage'] = dict(zip(
            ('prompt_tokens', 'completion_tokens', 'total_tokens'), usage))
    return body


@contextlib.contextmanager
def fake_io(app, events):
    requests = []
    factories = []
    clients = []

    def handler(request):
        requests.append(json.loads(request.content))
        index = len(requests) - 1
        require(index < len(events), '请求超过用例预算，检查自动重试或循环')
        event = events[index]
        if event == 'timeout':
            raise httpx2.ReadTimeout('offline-sensitive-marker', request=request)
        if isinstance(event, int):
            return httpx2.Response(event, json={
                'error': {'message': 'offline-sensitive-marker', 'type': 'offline_error'}
            })
        return httpx2.Response(200, json=event)

    def factory(*args, **kwargs):
        require(not args, '客户端配置请继续使用已有关键字参数')
        factories.append({key: value for key, value in kwargs.items() if key != 'api_key'})
        require(kwargs.get('max_retries') == 0, '保留 max_retries=0，避免重复付费尝试')
        require(kwargs.get('timeout') == 120, '保留客户端 timeout=120')
        require(str(kwargs.get('base_url', '')).rstrip('/') == 'https://api.moonshot.cn/v1',
                '继续使用当前 Kimi base_url，不切换供应商')
        client = SDKOpenAI(**kwargs, http_client=httpx2.Client(
            transport=httpx2.MockTransport(handler)))
        clients.append(client)
        return client

    try:
        with patch.object(app, 'get_api_key', return_value='offline-fake-key'), \
                patch.object(app, 'OpenAI', side_effect=factory):
            yield SimpleNamespace(requests=requests, factories=factories)
    finally:
        for client in clients:
            client.close()


def quiet_call(function, *args):
    output = io.StringIO()
    with patch('builtins.input', side_effect=AssertionError('调用函数不能读取终端输入')), \
            contextlib.redirect_stdout(output):
        try:
            return function(*args)
        finally:
            require(not output.getvalue(), '调用层只返回数据，输出交给 main/display')


def main():
    outcomes = []
    sources = [project / 'model_demo_ask_turn.py', project / 'conversation.py']
    before = {source: fingerprint(source) for source in sources}
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
            patch('socket.create_connection', block_network):
        import model_demo_ask_turn as app
        import conversation

        def api(name):
            function = getattr(app, name, None)
            require(callable(function), f'请在 model_demo_ask_turn.py 实现 {name}')
            return function

        def fresh():
            return conversation.create_history(app.SYSTEM_PROMPT)

        def turn(history, question):
            return quiet_call(api('ask_turn'), history, question)

        def assert_raw(answer, raw):
            value = getattr(answer, 'assistant_message', None)
            require(isinstance(value, dict), 'ModelAnswer.assistant_message 应保存完整消息字典')
            require(all(key in value and value[key] == item for key, item in raw.items()),
                    '保留原始正文及 reasoning_content 等字段；使用 message.to_dict()')

        def check_dto():
            answer = app.ModelAnswer('离线回答', 'stop')
            require(hasattr(answer, 'assistant_message') and answer.assistant_message is None,
                    '给 ModelAnswer 新增 assistant_message: dict | None = None')
            legacy = app.ModelAnswer('离线回答', 'stop', 10, 5, 15)
            require((legacy.prompt_tokens, legacy.completion_tokens, legacy.total_tokens,
                     legacy.assistant_message) == (10, 5, 15, None),
                    '保留旧五参数构造：第三至五位仍为 prompt/completion/total；'
                    '把新增 assistant_message 字段放在原三个 token 字段之后')

        def check_shared_request():
            function = api('ask_messages')
            messages = [{'role': 'system', 'content': app.SYSTEM_PROMPT},
                        {'role': 'user', 'content': '离线问题'}]
            saved = deepcopy(messages)
            event = fake_event(content='  【模拟响应】原始正文\n')
            with fake_io(app, [event]) as trace:
                answer = quiet_call(function, messages)
            require(len(trace.requests) == 1, '单次请求只调用一次 SDK')
            params = trace.requests[0]
            require(params.get('messages') == saved and messages == saved,
                    'ask_messages 原样发送传入消息，不重建单轮消息、不改调用方数据')
            require(params.get('model') == 'kimi-k3' and params.get('stream') is False
                    and params.get('max_completion_tokens') == 4096
                    and params.get('reasoning_effort') == 'low' and 'max_tokens' not in params,
                    '保留 kimi-k3、非流式、4096/low 及现有预算')
            require(answer.content == '  【模拟响应】原始正文\n'
                    and answer.finish_reason == 'stop'
                    and (answer.prompt_tokens, answer.completion_tokens, answer.total_tokens)
                    == (10, 5, 15), '保留原始正文、结束原因及用量')
            assert_raw(answer, event['choices'][0]['message'])

        def check_once_wrapper():
            api('ask_messages')
            answer = app.ModelAnswer('离线回答', 'stop')
            messages = [{'role': 'system', 'content': '离线接线规则'},
                        {'role': 'user', 'content': '离线接线问题'}]
            with patch.object(app, 'build_messages', return_value=messages) as build, \
                    patch.object(app, 'ask_messages', return_value=answer) as request, \
                    patch.object(app, 'OpenAI', side_effect=AssertionError('单轮包装不重复建客户端')):
                result = quiet_call(app.ask_once, '  离线接线问题  ')
            require(build.call_count == 1 and request.call_count == 1 and result is answer,
                    'ask_once 校验后复用 build_messages 和 ask_messages')
            supplied = request.call_args
            value = supplied.args[0] if supplied.args else supplied.kwargs.get('messages')
            require(value == messages, '把单轮消息交给 ask_messages，保留旧接口')

        def check_two_turns():
            api('ask_turn')
            history = fresh()
            first = fake_event()
            second = fake_event('【模拟响应】南京。', usage=None)
            with fake_io(app, [first, second]) as trace:
                answer = turn(history, '  研究对象设为南京。  ')
                require(len(history) == 3, '第一轮成功后提交 user/assistant')
                assert_raw(answer, first['choices'][0]['message'])
                saved = deepcopy(history)
                followup = turn(history, '刚才的研究对象是哪座城市？')
            require(len(trace.requests) == 2 and len(history) == 5,
                    '两轮各一次请求，已提交历史共五条消息')
            require(trace.requests[1]['messages'] == saved + [
                {'role': 'user', 'content': '刚才的研究对象是哪座城市？'}],
                    '第二轮必须带上完整历史及第一答协议字段')
            require(followup.total_tokens is None, '缺少 usage 时保留 None，不影响成功提交')

        def check_blank():
            function = api('ask_turn')
            history = fresh()
            saved = deepcopy(history)
            with patch.object(app, 'get_api_key', side_effect=AssertionError('空白应在读配置前拒绝')), \
                    patch.object(app, 'OpenAI', side_effect=AssertionError('空白不能创建客户端')):
                for entry, arguments in [(app.ask_once, (' \t\n',)),
                                         (function, (history, ' \t\n'))]:
                    try:
                        quiet_call(entry, *arguments)
                    except ValueError:
                        continue
                    raise AssertionError('空白问题应抛 ValueError')
            require(history == saved, '空白问题不修改历史')

        def check_missing_key():
            api('ask_turn')
            history = fresh()
            saved = deepcopy(history)
            with patch.object(app, 'get_api_key', side_effect=ValueError('离线缺配置')), \
                    patch.object(app, 'OpenAI', side_effect=AssertionError('缺配置不能创建客户端')):
                try:
                    turn(history, '离线问题')
                except ValueError:
                    pass
                else:
                    raise AssertionError('配置异常应交给调用方处理')
            require(history == saved, '缺配置时不能提前提交 user')

        def check_failures():
            api('ask_turn')
            for event in (401, 503, 'timeout'):
                history = fresh()
                saved = deepcopy(history)
                with fake_io(app, [event]) as trace:
                    try:
                        turn(history, '本轮会失败')
                    except APIError:
                        pass
                    else:
                        raise AssertionError('SDK 异常应传播给 main，不伪造成功返回')
                require(len(trace.requests) == 1 and history == saved,
                        '401/503/读取超时只尝试一次，历史保持原状')

        def check_incomplete():
            api('ask_turn')
            for content, reason in [(None, 'stop'), ('', 'stop'), ('  ', 'stop'),
                                    ('部分回答', 'length'), ('其他结束', 'content_filter')]:
                history = fresh()
                saved = deepcopy(history)
                with fake_io(app, [fake_event(content, reason)]) as trace:
                    answer = turn(history, '离线问题')
                require(history == saved and len(trace.requests) == 1,
                        '只有 stop 且正文非空白才提交；空回答、截断及其他状态不提交')
                require(answer.content == (content or '') and answer.finish_reason == reason
                        and answer.total_tokens == 15,
                        '未提交的结果仍返回正文、结束原因和用量供展示')

        def run_cli(inputs, events):
            output = io.StringIO()
            with fake_io(app, events) as trace, \
                    patch('builtins.input', side_effect=inputs), \
                    contextlib.redirect_stdout(output):
                app.main()
            return trace, output.getvalue()

        def check_cli_normal():
            first = fake_event()
            trace, output = run_cli(
                ['研究对象设为南京。', '刚才的研究对象是哪座城市？', 'quit'],
                [first, fake_event('【模拟响应】南京。')])
            require(len(trace.requests) == 2, '两题及退出命令只产生两次模型请求')
            require([item['role'] for item in trace.requests[1]['messages']]
                    == ['system', 'user', 'assistant', 'user'],
                    'main 循环外创建一次历史，循环内使用 ask_turn')
            raw = first['choices'][0]['message']
            require(all(trace.requests[1]['messages'][2].get(key) == value
                        for key, value in raw.items()), 'CLI 第二轮保留完整 assistant')
            require(output.count('模型生成') == 2 and output.count('未检索来源') == 2
                    and output.count('结束原因: stop') == 2 and output.count('用量:') == 2,
                    '每轮继续展示来源标签、原始结束原因及一次用量')
            require('offline-protocol-only' not in output, '协议字段用于回传，不直接展示原始对象')

        def check_cli_failure():
            trace, output = run_cli(
                ['   ', '失败的问题', '成功的问题', 'quit'], [503, fake_event()])
            require(len(trace.requests) == 2, '空白/退出不请求，503 不自动重试')
            require(trace.requests[1]['messages'] == [
                {'role': 'system', 'content': app.SYSTEM_PROMPT},
                {'role': 'user', 'content': '成功的问题'}],
                    'CLI 失败后继续循环，但不能把失败的问题带入下一次上下文')
            require('模型调用失败' in output and '模型生成' in output,
                    '显示安全错误类别后继续处理下一题')
            require('offline-sensitive-marker' not in output and 'offline-fake-key' not in output,
                    '不输出原始 APIError、Key 或请求对象')

        def check_cli_incomplete():
            trace, output = run_cli(
                ['空回答问题', '截断问题', '最后的问题', 'quit'],
                [fake_event(''), fake_event('部分回答', 'length'), fake_event()])
            require(len(trace.requests) == 3 and trace.requests[2]['messages'] == [
                {'role': 'system', 'content': app.SYSTEM_PROMPT},
                {'role': 'user', 'content': '最后的问题'}],
                    '空回答/截断不进入历史，但 CLI 可以继续下一题')
            require(('回答为空' in output or '未返回有效回答' in output)
                    and '截断' in output and output.count('用量:') == 3
                    and output.count('结束原因:') == 3,
                    '未提交的结果仍展示提示、用量与结束原因，不能提前 continue 跳过')

        def check_previous():
            result = subprocess.run(
                [sys.executable, str(tests / 'check_s3_01.py')],
                cwd=project, capture_output=True, encoding='utf-8',
                errors='replace', timeout=30,
            )
            require(result.returncode == 0,
                    '旧功能回归未通过，请运行 check_s3_01.py：\n'
                    + (result.stdout + result.stderr)[-2200:])

        check('结果对象兼容新增完整消息', check_dto)
        check('共用请求函数与完整消息序列化', check_shared_request)
        check('单轮接口复用请求函数', check_once_wrapper)
        check('连续两轮携带完整历史', check_two_turns)
        check('空白输入零配置零请求', check_blank)
        check('缺少配置不提交历史', check_missing_key)
        check('401/503/超时不提交且不重试', check_failures)
        check('空回答/截断/其他结束不提交', check_incomplete)
        check('CLI 多轮、退出与来源展示', check_cli_normal)
        check('CLI 失败后继续且历史干净', check_cli_failure)
        check('CLI 未提交结果仍保留展示', check_cli_incomplete)
        check('S3-01 及此前回归', check_previous)

    require(all(fingerprint(source) == value for source, value in before.items()),
            '检查期间业务源码变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过。')
    print('真实 SDK + 内存假响应；未加载 .env、未读真实 Key、未请求模型。')
    print('真实两轮问答质量和实际 usage 需学员另行记录。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
