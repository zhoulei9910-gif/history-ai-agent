"""S2-02 离线检查：仅模拟结果，禁止读取 .env 或连接真实网络。"""

import contextlib
import hashlib
import io
import os
from pathlib import Path
import socket
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from openai.types.chat import ChatCompletionMessage

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))
dotenv_stub = ModuleType('dotenv')
dotenv_stub.load_dotenv = lambda *args, **kwargs: False


def block_network(*args, **kwargs):
    raise AssertionError('离线检查禁止连接真实网络')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    outcomes = []

    def check(name, action):
        try:
            action()
        except Exception as exc:
            outcomes.append(False)
            print(f'未通过｜{name}：{type(exc).__name__}: {exc}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{name}')

    source = project / 'model_demo_ask_turn.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    with patch.dict(sys.modules, {'dotenv': dotenv_stub}), \
            patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', block_network), \
            patch('socket.create_connection', block_network):
        import model_demo_ask_turn as app

        def render(content='离线回答正文', reason='stop', assistant_message=None, tokens=(10, 5, 15)):
            values = tokens if tokens is not None else (None, None, None)
            # 展示测试使用命名参数；旧位置参数兼容性由 S3-02 独立断言检查。
            answer = app.ModelAnswer(
                content=content, finish_reason=reason,
                assistant_message=assistant_message,
                prompt_tokens=values[0], completion_tokens=values[1], total_tokens=values[2],
            )
            output = io.StringIO()
            # S3-02 的 CLI 使用 ask_turn；保持原展示检查，真实接线由新课脚本验证。
            entry = 'ask_turn' if callable(getattr(app, 'ask_turn', None)) else 'ask_once'
            with patch('builtins.input', side_effect=['离线问题', 'quit']), \
                    patch.object(app, entry, return_value=answer), \
                    contextlib.redirect_stdout(output):
                app.main()
            return output.getvalue()

        def check_dataclass():
            answer = app.ModelAnswer('离线回答正文', 'stop')
            require((answer.prompt_tokens, answer.completion_tokens,
                     answer.total_tokens) == (None, None, None),
                    '三个统计字段应默认 None')
            repr(answer)

        def check_response_data():
            for content in (None, '', '   ', '部分回答'):
                response = SimpleNamespace(
                    choices=[SimpleNamespace(
                        message=ChatCompletionMessage(role='assistant', content=content),
                        finish_reason='length')],
                    usage=SimpleNamespace(prompt_tokens=10,
                                          completion_tokens=5,
                                          total_tokens=15),
                )
                client = SimpleNamespace(chat=SimpleNamespace(
                    completions=SimpleNamespace(create=Mock(return_value=response))))
                output = io.StringIO()
                with patch.object(app, 'get_api_key', return_value='offline-placeholder'), \
                        patch.object(app, 'OpenAI', return_value=client), \
                        contextlib.redirect_stdout(output):
                    answer = app.ask_once('离线问题')
                require(answer.content == (content or ''),
                        '正文应保留返回数据，提示文案放到 main')
                require(answer.finish_reason == 'length',
                        f'结束原因应保留原始 length，实际为 {answer.finish_reason!r}')
                require(output.getvalue() == '', 'ask_once 自身应返回数据，不输出展示内容')

        def check_normal():
            output = render()
            require('离线回答正文' in output and 'stop' in output,
                    '应显示正文和结束原因')
            require('模型生成' in output and '未检索来源' in output,
                    '应保留来源状态标签')
            require(output.count('用量') == 1 and 'total=15' in output,
                    '统计应显示一次')

        def check_request_settings():
            response = SimpleNamespace(
                choices=[SimpleNamespace(
                    message=ChatCompletionMessage(role='assistant', content='离线回答正文'),
                    finish_reason='stop')],
                usage=None,
            )
            create = Mock(return_value=response)
            client = SimpleNamespace(chat=SimpleNamespace(
                completions=SimpleNamespace(create=create)))
            factory = Mock(return_value=client)
            with patch.object(app, 'get_api_key', return_value='offline-placeholder'), \
                    patch.object(app, 'OpenAI', factory), \
                    contextlib.redirect_stdout(io.StringIO()):
                app.ask_once('离线问题')
            require(factory.call_count == 1 and create.call_count == 1,
                    '单次调用应只创建一个客户端并请求一次')
            options = factory.call_args.kwargs
            params = create.call_args.kwargs
            problems = []
            if options.get('max_retries') != 0 or options.get('timeout') != 120:
                problems.append('客户端应保留 max_retries=0、timeout=120')
            if params.get('model') != 'kimi-k3' or params.get('stream') is not False:
                problems.append('应保留 kimi-k3 和 stream=False')
            if params.get('max_completion_tokens') != 4096 or 'max_tokens' in params:
                problems.append('恢复 max_completion_tokens=4096，移除旧 max_tokens')
            if params.get('reasoning_effort') != 'low':
                problems.append('恢复 reasoning_effort="low"')
            require(not problems, '；'.join(problems))

        def check_missing():
            output = render(tokens=None)
            require('离线回答正文' in output and 'stop' in output,
                    '缺少统计仍需显示正文与结束原因')
            require('未提供用量统计' in output and 'None' not in output
                    and output.count('用量') == 1,
                    '缺失说明与数字统计应二选一，不能再打印 None 数字行')

        def check_zero():
            output = render(tokens=(0, 0, 0))
            require('未提供用量统计' not in output,
                    '0 是已提供的数值，使用 is None 判断缺失')
            require('离线回答正文' in output and 'stop' in output
                    and 'total=0' in output and output.count('用量') == 1,
                    '应显示正文、零用量和结束原因')

        def check_empty(content):
            output = render(content=content)
            require('回答为空' in output or '未返回有效回答' in output,
                    '应先 strip 再判断，给出空回答提示')
            require('stop' in output and 'total=15' in output,
                    '空回答仍需显示结束原因与用量')

        def check_truncated(content='部分回答', tokens=(10, 5, 15)):
            output = render(content=content, reason='length', tokens=tokens)
            require('length' in output and '截断' in output,
                    '保留原始结束原因，并在 main 额外显示中文截断提示')
            if not content.strip():
                require('回答为空' in output or '未返回有效回答' in output,
                        '空回答也要提示')
            if tokens is None:
                require('未提供用量统计' in output and 'None' not in output,
                        '缺失统计时不要打印 None 数字行')

        check('数据类构造', check_dataclass)
        check('调用层保留原始正文与结束原因', check_response_data)
        check('正常回答', check_normal)
        check('缺少用量', check_missing)
        check('用量为零', check_zero)
        check('空字符串回答', lambda: check_empty(''))
        check('纯空白回答', lambda: check_empty('   '))
        check('截断回答', check_truncated)
        check('空回答且截断、缺少用量', lambda: check_truncated('', None))
        check('已约定的调用参数', check_request_settings)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before,
            '检查期间源文件发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('这是离线功能检查，没有读取 .env 或发起模型请求。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
