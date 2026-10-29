"""S3-01：离线检查对话历史，不调用模型；沿用 S2-03 回归检查。"""

import contextlib
from copy import deepcopy
import hashlib
import importlib
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType
from unittest.mock import patch

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def block_network(*args, **kwargs):
    raise AssertionError('本节离线检查禁止连接真实网络')


def block_input(*args, **kwargs):
    raise AssertionError('历史管理函数不读取终端输入')


def quiet_call(function, *args):
    output = io.StringIO()
    with patch('builtins.input', side_effect=block_input), \
            contextlib.redirect_stdout(output), \
            contextlib.redirect_stderr(output):
        try:
            return function(*args)
        finally:
            require(not output.getvalue(), '历史管理函数只处理数据，不打印；展示放在调用方')


def expect_value_error(function, *args):
    try:
        quiet_call(function, *args)
    except ValueError:
        return
    raise AssertionError('无效输入应抛出 ValueError')


def fake_assistant():
    # 所有内容均为离线假值。_offline_test 只检查嵌套复制，不是 SDK 参数。
    return {
        'role': 'assistant',
        'content': '  【模拟响应】本轮讨论南京。\n',
        'reasoning_content': '【离线协议字段占位】',
        '_offline_test': {'tags': ['仅用于检查']},
    }


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    outcomes = []
    paths = [project / 'conversation.py', project / 'model_demo_ask_turn.py']
    before = {path: fingerprint(path) for path in paths}
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
        lesson = None
        import_problem = None
        if (project / 'conversation.py').is_file():
            try:
                lesson = quiet_call(importlib.import_module, 'conversation')
            except Exception as exc:
                import_problem = f'{type(exc).__name__}: {exc}'

        def api(name):
            require(lesson is not None,
                    '请创建 conversation.py 并实现本节三个函数'
                    + (f'；导入失败：{import_problem}' if import_problem else ''))
            function = getattr(lesson, name, None)
            require(callable(function), f'请实现 conversation.py 中的 {name}')
            return function

        def fresh(prompt='离线地理历史助手规则'):
            return quiet_call(api('create_history'), prompt)

        def prepare(history, question):
            return quiet_call(api('build_turn_messages'), history, question)

        def commit(history, question, assistant):
            return quiet_call(api('commit_turn'), history, question, assistant)

        def check_initial():
            prompt = '  离线地理历史助手规则\n'
            history = fresh(prompt)
            require(history == [{'role': 'system', 'content': prompt}],
                    '新历史只含一条 system 消息；保留传入的提示词原文')

        def check_first():
            history = fresh()
            original = deepcopy(history)
            messages = prepare(history, '  我们讨论南京。\t')
            require(messages == original + [{'role': 'user', 'content': '我们讨论南京。'}],
                    '请求消息为历史加本轮 user；问题先 strip，不重复添加 system')
            require(history == original, '准备请求不能提前修改已提交历史')

        def check_blank():
            for prompt in ('', '  ', '\t\n'):
                expect_value_error(api('create_history'), prompt)
            history = fresh()
            original = deepcopy(history)
            for question in ('', '  ', '\t\n'):
                expect_value_error(api('build_turn_messages'), history, question)
                require(history == original, '拒绝空问题时历史保持原状')

        def check_commit():
            history = fresh()
            assistant = fake_assistant()
            saved = deepcopy(assistant)
            result = commit(history, '  我们讨论南京。\t', assistant)
            require(result is None, 'commit_turn 原地更新历史，返回 None')
            require(history == [
                {'role': 'system', 'content': '离线地理历史助手规则'},
                {'role': 'user', 'content': '我们讨论南京。'},
                saved,
            ], '成功提交追加 user、完整 assistant；正文及额外字段不重写或丢失')
            assistant['content'] = '外部修改'
            assistant['_offline_test']['tags'].append('外部修改')
            require(history[2] == saved, '提交时复制 assistant，外部修改不应改变历史')

        def check_followup():
            history = fresh()
            assistant = fake_assistant()
            commit(history, '我们讨论南京。', assistant)
            original = deepcopy(history)
            messages = prepare(history, '  刚才讨论的是哪座城市？  ')
            require(messages == original + [
                {'role': 'user', 'content': '刚才讨论的是哪座城市？'}
            ], '追问必须携带此前 user 和完整 assistant，按时间顺序排列')
            require(history == original, '未提交的新问题不能留在历史中')

        def check_snapshot():
            history = fresh()
            commit(history, '我们讨论南京。', fake_assistant())
            original = deepcopy(history)
            first = prepare(history, '追问甲')
            second = prepare(history, '追问乙')
            second_saved = deepcopy(second)
            first[0]['content'] = '改动请求中的 system'
            first[2]['_offline_test']['tags'].append('改动请求中的嵌套数据')
            first.append({'role': 'user', 'content': '额外内容'})
            require(history == original and second == second_saved,
                    '请求快照要隔离嵌套 dict/list；list(history) 或 history.copy() 只做浅拷贝')

        def check_rejected():
            history = fresh()
            commit(history, '已成功的问题', fake_assistant())
            original = deepcopy(history)
            for question in ('', '  ', '\t\n'):
                expect_value_error(api('commit_turn'), history, question, fake_assistant())
                require(history == original, '先校验问题，再修改历史')
            invalid_assistants = [
                {}, {'role': 'user', 'content': '角色错误'},
                {'role': 'assistant'}, {'role': 'assistant', 'content': None},
                {'role': 'assistant', 'content': ''},
                {'role': 'assistant', 'content': ' \t\n'},
                {'role': 'assistant', 'content': 123},
            ]
            for assistant in invalid_assistants:
                expect_value_error(api('commit_turn'), history, '失败的问题', assistant)
                require(history == original,
                        '本节只提交非空文本 assistant；校验失败不得留下半轮 user')

        def check_sessions():
            first = fresh('会话甲规则')
            second = fresh('会话乙规则')
            commit(first, '会话甲的问题', fake_assistant())
            require(second == [{'role': 'system', 'content': '会话乙规则'}],
                    '不同会话不能共享可变历史；不要使用全局历史或可变默认参数')
            require(prepare(second, '会话乙的问题') == [
                {'role': 'system', 'content': '会话乙规则'},
                {'role': 'user', 'content': '会话乙的问题'},
            ], '构造会话乙请求时不能混入会话甲的内容')

        def check_previous():
            result = subprocess.run(
                [sys.executable, str(tests / 'check_s2_03.py')],
                cwd=project, capture_output=True, encoding='utf-8',
                errors='replace', timeout=30,
            )
            require(result.returncode == 0,
                    '既有功能回归失败，请运行 check_s2_03.py：\n'
                    + (result.stdout + result.stderr)[-2200:])

        check('初始化 system 历史', check_initial)
        check('准备首轮请求不改历史', check_first)
        check('空提示词和空问题拒绝', check_blank)
        check('成功提交完整消息并复制', check_commit)
        check('第二轮请求携带前文', check_followup)
        check('请求快照隔离嵌套数据', check_snapshot)
        check('无效提交不污染历史', check_rejected)
        check('两个会话相互独立', check_sessions)
        check('S2-03 与上一课回归', check_previous)

    require(all(fingerprint(path) == value for path, value in before.items()),
            '检查期间业务源文件发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过。')
    print('检查未加载 .env 或发送模型请求；假消息不证明真实追问效果。')
    if all(outcomes):
        print('离线模拟通过：第二轮角色顺序 system → user → assistant → user。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
