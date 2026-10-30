"""S3-06：用真实 SDK 分片类型离线检查 consume_stream；不创建模型请求。"""

import argparse
import contextlib
from copy import deepcopy
import hashlib
import inspect
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

from openai.types.chat import ChatCompletionChunk

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from check_s3_02 import block_network, require


def chunk(content=None, *, role=None, reason=None, usage=None,
          reasoning=None, no_choices=False):
    delta = {'content': content}
    if role is not None:
        delta['role'] = role
    if reasoning is not None:
        delta['reasoning_content'] = reasoning
    return ChatCompletionChunk(
        id='offline-stream', object='chat.completion.chunk', created=0, model='kimi-k3',
        choices=[] if no_choices else [
            {'index': 0, 'delta': delta, 'finish_reason': reason}],
        usage=None if usage is None else dict(zip(
            ('prompt_tokens', 'completion_tokens', 'total_tokens'), usage)),
    )


def stats(answer):
    return answer.prompt_tokens, answer.completion_tokens, answer.total_tokens


def demonstrate(app):
    """用同一组假分片演示回调发生在完整结果返回之前。"""
    print('【离线模拟】不读取真实 Key，不调用模型；下列用量是假值。')

    def show_piece(fragment):
        print(f'回调收到片段：{fragment!r}')

    events = iter([
        chunk('第一片'),
        chunk('第二片'),
        chunk(reason='stop'),
        chunk(no_choices=True, usage=(4, 2, 6)),
    ])
    print('调用 consume_stream 之前')
    answer = app.consume_stream(events, on_text=show_piece)
    print('consume_stream 已 return，现在拿到完整 ModelAnswer')
    print(f'完整正文：{answer.content!r}')
    print(f'结束原因：{answer.finish_reason!r}；模拟用量：{stats(answer)}')


def main(demo_only=False):
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
            tempfile.TemporaryDirectory(prefix='geo-history-s306-check-') as temporary:
        import model_demo_ask_turn as app

        if demo_only:
            demonstrate(app)
            return 0

        def api():
            function = getattr(app, 'consume_stream', None)
            require(callable(function),
                    '请在 model_demo_ask_turn.py 实现 consume_stream(chunks, on_text=None)')
            return function

        def consume(chunks, *args):
            function = api()
            output = io.StringIO()
            forbidden = AssertionError('消费分片只返回结果/通知回调；不要请求模型、读写文件或提交历史')
            with contextlib.ExitStack() as stack:
                for name in ('OpenAI', 'get_api_key', 'get_base_url', 'ask_messages',
                             'ask_turn', 'save_history', 'load_history', 'commit_turn'):
                    stack.enter_context(patch.object(app, name, side_effect=forbidden))
                stack.enter_context(patch('builtins.input', side_effect=forbidden))
                stack.enter_context(patch('builtins.open', side_effect=forbidden))
                stack.enter_context(patch('pathlib.Path.open', side_effect=forbidden))
                stack.enter_context(contextlib.redirect_stdout(output))
                stack.enter_context(contextlib.redirect_stderr(output))
                try:
                    result = function(chunks, *args)
                finally:
                    require(not output.getvalue(),
                            'consume_stream 不直接打印；将非空正文片段交给 on_text')
            require(isinstance(result, app.ModelAnswer), '返回已有 ModelAnswer，不新增重复结果类型')
            return result

        def check_contract():
            parameter = inspect.signature(api()).parameters.get('on_text')
            require(parameter is not None and parameter.default is None,
                    'on_text 默认为 None，不传回调也能收集结果')
            answer = consume(iter(()))
            require(answer.content == '' and answer.finish_reason == '' and
                    stats(answer) == (None, None, None),
                    '空迭代器返回空正文/空结束原因/未知用量，不能伪造 stop')

        def check_content():
            events = [chunk('  南'), chunk('京'), chunk('\n'), chunk('河流🙂 '),
                      chunk(reason='stop')]
            original = deepcopy([event.to_dict() for event in events])
            answer = consume(iter(events))
            require(answer.content == '  南京\n河流🙂 ',
                    '按到达顺序追加原文，不能只保留最后一片或 strip 掉空白')
            require(original == [event.to_dict() for event in events], '不能改写传入 SDK 分片')

        def check_callback():
            received = []

            def single_pass():
                for text in ('南京', ' ', '【离线片段】'):
                    previous = len(received)
                    yield chunk(text)
                    require(received[previous:] == [text],
                            '收到正文立刻回调一次，再读取下一片；不要先 list(chunks)')
                yield chunk(reason='stop')

            answer = consume(single_pass(), received.append)
            require(received == ['南京', ' ', '【离线片段】'] and
                    answer.content == ''.join(received),
                    '回调参数是每个原始片段，不能是累计全文或拆成逐字通知')

        def check_empty_chunks():
            received = []
            answer = consume(iter([
                chunk(role='assistant'), chunk(''), chunk(no_choices=True),
                chunk('正文'), chunk(reason='stop'),
            ]), received.append)
            require(answer.content == '正文' and received == ['正文'] and
                    answer.finish_reason == 'stop',
                    '角色/空正文/空 choices 不产生正文回调，不应索引越界')

        def check_tail_usage():
            exhausted = []

            def events():
                yield chunk('回答')
                yield chunk(reason='stop')
                yield chunk(no_choices=True, usage=(12, 3, 15))
                exhausted.append(True)

            answer = consume(events())
            require(answer.finish_reason == 'stop' and stats(answer) == (12, 3, 15)
                    and exhausted == [True],
                    'finish_reason 后仍读到迭代器结束；最终 usage 分片 choices=[]')

        def check_missing_zero_usage():
            missing = consume(iter([chunk('回答', reason='stop')]))
            zero = consume(iter([chunk('回答', reason='stop'),
                                 chunk(no_choices=True, usage=(0, 0, 0))]))
            require(stats(missing) == (None, None, None) and stats(zero) == (0, 0, 0),
                    '未提供用量是 None；已提供的 0 不能改成 None 或自行估算')

        def check_finish_reason():
            for reason in ('stop', 'length', 'content_filter'):
                answer = consume(iter([chunk('部分正文', reason=reason), chunk()]))
                require(answer.finish_reason == reason, '保留原始结束原因，后续 None 不覆盖它')
            answer = consume(iter([chunk('仅正文，无结束标记')]))
            require(answer.finish_reason == '', '迭代器耗尽不等于模型 stop，缺标记返回空字符串')

        def check_reasoning():
            received = []
            answer = consume(iter([
                chunk(reasoning='offline-'),
                chunk('正文一', reasoning='protocol'), chunk('正文二', reason='stop'),
            ]), received.append)
            message = answer.assistant_message
            require(isinstance(message, dict) and message.get('role') == 'assistant' and
                    message.get('content') == '正文一正文二' and
                    message.get('reasoning_content') == 'offline-protocol',
                    '分别追加 content/reasoning_content，放入 assistant_message 供后续回传')
            require(received == ['正文一', '正文二'] and answer.content == '正文一正文二',
                    '协议字段不混入正文或 on_text；没有该扩展字段时也能运行')

        def check_metadata():
            answer = consume(iter([
                chunk(no_choices=True, usage=(1, 1, 2)), chunk(reason='length'),
                chunk(no_choices=True, usage=(8, 5, 13)), chunk(no_choices=True),
            ]))
            require(answer.content == '' and answer.finish_reason == 'length' and
                    stats(answer) == (8, 5, 13),
                    '空回答仍保留元数据；以最后非 None 的顶层 usage 为准')
            require(isinstance(answer.assistant_message, dict) and
                    answer.assistant_message.get('role') == 'assistant' and
                    answer.assistant_message.get('content') == '',
                    '即使无正文，也返回 role=assistant、content="" 的消息字典')

        def check_iterator_error():
            error = RuntimeError('offline-interrupted')
            received = []

            def interrupted():
                yield chunk('已收到的片段')
                raise error

            try:
                consume(interrupted(), received.append)
            except RuntimeError as actual:
                require(actual is error and received == ['已收到的片段'],
                        '异常原样传播，已触发的正文回调不代表整轮成功')
            else:
                raise AssertionError('迭代失败不能返回伪造的成功结果或吞掉异常')

        def check_callback_error():
            error = ValueError('offline-callback-failed')
            advanced = []

            def events():
                yield chunk('片段')
                advanced.append(True)
                yield chunk(reason='stop')

            def fail(text):
                raise error

            try:
                consume(events(), fail)
            except ValueError as actual:
                require(actual is error and not advanced,
                        '回调异常原样传播并停止消费，不能吞错继续')
            else:
                raise AssertionError('on_text 出错也应传播，不返回成功 ModelAnswer')

        def check_previous():
            regression = Path(temporary) / 'regression-project'
            regression.mkdir()
            names = ('conversation.py', 'session_store.py', 'model_demo_ask_turn.py',
                     'IncompleteStreamError.py', 'config.py', '.gitignore')
            for name in names:
                (regression / name).write_bytes((project / name).read_bytes())
            (regression / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py',
                         'check_s3_02.py', 'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py'):
                (regression / 'test' / name).write_bytes((tests / name).read_bytes())
            result = subprocess.run(
                [sys.executable, str(regression / 'test' / 'check_s3_05.py')],
                cwd=regression, capture_output=True, encoding='utf-8', errors='replace', timeout=45)
            require(result.returncode == 0, 'S3-05 及此前回归未通过：\n' +
                    (result.stdout + result.stderr)[-2200:])

        check('函数接口与空流默认结果', check_contract)
        check('原文顺序拼接，SDK 输入不被改写', check_content)
        check('单次迭代，正文到达即回调', check_callback)
        check('角色/空正文/空 choices 安全跳过', check_empty_chunks)
        check('结束原因之后继续接收最终 usage', check_tail_usage)
        check('缺失用量与有效零值', check_missing_zero_usage)
        check('保留结束原因，缺标记不伪造 stop', check_finish_reason)
        check('正文与 reasoning_content 分开保留', check_reasoning)
        check('无正文仍保留消息和最后已知用量', check_metadata)
        check('迭代中断原样传播，不伪造成功', check_iterator_error)
        check('回调失败传播并停止消费', check_callback_error)
        check('S3-05 及此前回归（临时工程）', check_previous)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before,
            '检查期间业务源码发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('仅消费离线 SDK 分片；未加载 .env、未读取真实 Key、未发送模型请求。')
    print('本课只检查单选文本流拼接，不证明真实传输完成、模型质量或工具调用能力。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='只演示正文回调与完整结果返回的顺序')
    args = parser.parse_args()
    raise SystemExit(main(demo_only=args.demo))
