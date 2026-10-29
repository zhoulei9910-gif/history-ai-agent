"""S2-03：离线检查提示词接线与消息结构；模型回答质量需人工评估。"""

import contextlib
import hashlib
import io
import os
from pathlib import Path
import re
import socket
import subprocess
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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def block_network(*args, **kwargs):
    raise AssertionError('离线检查禁止连接真实网络')


def builder_must_be_pure(*args, **kwargs):
    raise AssertionError('build_messages 只组装消息，应避免读取输入、配置或调用模型')


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

        def system_prompt():
            prompt = getattr(app, 'SYSTEM_PROMPT', None)
            require(isinstance(prompt, str) and bool(prompt.strip()),
                    '请在 model_demo_ask_turn.py 定义非空字符串 SYSTEM_PROMPT，规则内容由你编写')
            return prompt

        def builder():
            function = getattr(app, 'build_messages', None)
            require(callable(function),
                    '请新增 build_messages(question: str)，返回 system/user 两条消息')
            return function

        def check_prompt_placeholders():
            placeholders = sorted(set(re.findall(r'\{\{[^{}]*\}\}', system_prompt())))
            require(not placeholders,
                    '当前静态 SYSTEM_PROMPT 仍含未填变量：'
                    + '、'.join(placeholders[:8])
                    + '。本节没有模板渲染；移除未使用的变量声明，提示词只描述已实现能力。')

        def call_builder(question):
            function = builder()
            output = io.StringIO()
            with patch('builtins.input', side_effect=builder_must_be_pure), \
                    patch.object(app, 'OpenAI', side_effect=builder_must_be_pure), \
                    patch.object(app, 'get_api_key', side_effect=builder_must_be_pure), \
                    patch.object(app, 'get_base_url', side_effect=builder_must_be_pure), \
                    contextlib.redirect_stdout(output):
                try:
                    messages = function(question)
                except ValueError:
                    require(not output.getvalue(), '空输入应抛出 ValueError，由调用方展示提示')
                    raise
            require(not output.getvalue(), 'build_messages 返回数据，不打印消息')
            return messages

        def check_shape(question):
            messages = call_builder(question)
            require(isinstance(messages, list) and len(messages) == 2,
                    '返回 list，当前只包含 system、user 两条消息')
            require(all(isinstance(message, dict) for message in messages),
                    '每条消息使用 dict，包含 role 和 content')
            require(messages[0].get('role') == 'system'
                    and messages[0].get('content') == system_prompt(),
                    '第一条消息的 role=system，content=SYSTEM_PROMPT')
            require(messages[1].get('role') == 'user'
                    and messages[1].get('content') == question.strip(),
                    '第二条消息的 role=user，content 为去除首尾空白的问题')
            return messages

        def check_normal():
            check_shape('为什么河流会影响城市发展？')

        def check_blank():
            check_shape('  为什么河流会影响城市发展？ \t')
            for question in ('', '   ', '\t\n'):
                try:
                    call_builder(question)
                except ValueError:
                    continue
                raise AssertionError('空字符串或纯空白应抛出 ValueError')

        def check_independent():
            prompt = system_prompt()
            first = check_shape('问题甲')
            second = check_shape('问题乙')
            require(first[1]['content'] == '问题甲'
                    and second[1]['content'] == '问题乙',
                    '后一次调用不能改写前一次返回的消息')
            require(system_prompt() == prompt,
                    '用户问题应放 user 消息，不改写 SYSTEM_PROMPT')

        def check_wiring():
            builder()
            messages = [
                {'role': 'system', 'content': '离线接线检查规则'},
                {'role': 'user', 'content': '离线接线检查问题'},
            ]
            response = SimpleNamespace(
                choices=[SimpleNamespace(
                    message=ChatCompletionMessage(role='assistant', content='离线返回数据'),
                    finish_reason='stop')],
                usage=None,
            )
            create = Mock(return_value=response)
            client = SimpleNamespace(chat=SimpleNamespace(
                completions=SimpleNamespace(create=create)))
            with patch.object(app, 'build_messages', return_value=messages) as assemble, \
                    patch.object(app, 'get_api_key', return_value='offline-placeholder'), \
                    patch.object(app, 'OpenAI', return_value=client), \
                    contextlib.redirect_stdout(io.StringIO()):
                answer = app.ask_once('  离线接线检查问题  ')
            call = assemble.call_args
            supplied_question = (
                call.args[0] if call and call.args
                else call.kwargs.get('question') if call else None
            )
            require(assemble.call_count == 1
                    and supplied_question == '离线接线检查问题',
                    'ask_once 应调用一次 build_messages(question)，不要继续内联旧消息')
            require(create.call_count == 1
                    and create.call_args.kwargs.get('messages') == messages,
                    '将 build_messages 的返回值传给 SDK 的 messages 参数')
            require(answer.content == '离线返回数据'
                    and answer.finish_reason == 'stop',
                    '消息重构后保留原来的结果解析')

        def check_previous():
            result = subprocess.run(
                [sys.executable, str(tests / 'check_display.py')],
                cwd=project,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=20,
            )
            require(result.returncode == 0,
                    '上一课检查未通过，请运行 check_display.py 查看：\n'
                    + (result.stdout + result.stderr)[-1800:])

        check('SYSTEM_PROMPT 已定义', system_prompt)
        check('静态提示词没有未填模板变量', check_prompt_placeholders)
        check('消息角色与内容（纯函数）', check_normal)
        check('问题清理与空白拒绝', check_blank)
        check('不同问题的消息互不改写', check_independent)
        check('ask_once 使用消息组装函数', check_wiring)
        check('上一课 10 项回归', check_previous)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before,
            '检查期间源文件发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('检查未加载 .env 或发送模型请求。提示词内容与回答质量需另做人工评估。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
