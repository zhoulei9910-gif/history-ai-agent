"""S3-04：离线检查完整会话的 JSON 保存/加载；文件只写临时目录。"""

import contextlib
from copy import deepcopy
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
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
    raise AssertionError('离线检查禁止连接真实网络')


def quiet_call(function, *args):
    output = io.StringIO()
    with patch('builtins.input', side_effect=AssertionError('存储函数不能读取终端输入')), \
            contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            return function(*args)
        finally:
            require(not output.getvalue(), '存储函数只返回数据，终端输出交给调用方')


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def example_history(rounds=4):
    history = [{'role': 'system', 'content': '  离线地理历史规则：不编造来源。\n'}]
    for number in range(1, rounds + 1):
        history.extend([
            {'role': 'user', 'content': f'  问题{number}：研究南京。\n'},
            {'role': 'assistant', 'content': f'【模拟回答{number}】南京。',
             'reasoning_content': 'offline-protocol-only',
             '_offline_test': {'places': ['南京', 'Rome'], 'value': None, 'flag': True}},
        ])
    return history


def invalid_histories():
    system = {'role': 'system', 'content': '离线规则'}
    user = {'role': 'user', 'content': '离线问题'}
    assistant = {'role': 'assistant', 'content': '离线回答'}
    return [
        None, {}, [], [user],
        [{'role': 'system', 'content': ' \t\n'}],
        [{'role': 'system', 'content': 123}],
        [system, user], [system, assistant, user],
        [system, user, {'role': 'user', 'content': '角色错误'}],
        [system, user, {'role': 'assistant', 'content': ''}],
        [system, user, {'role': 'assistant', 'content': None}],
        [system, {'role': 'user', 'content': '  '}, assistant],
        [system, '不是消息字典', assistant],
        [system, user, assistant, system, assistant],
    ]


def main():
    outcomes = []
    paths = [project / name for name in
             ('session_store.py', 'conversation.py', 'model_demo_ask_turn.py')]
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

    with patch.dict(sys.modules, {'dotenv': dotenv_stub, 'config': None, 'openai': None}), \
            patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', block_network), \
            patch('socket.socket.connect_ex', block_network), \
            patch('socket.create_connection', block_network), \
            tempfile.TemporaryDirectory(prefix='geo-history-s304-') as temporary:
        directory = Path(temporary)
        lesson = None
        problem = None
        try:
            lesson = quiet_call(importlib.import_module, 'session_store')
        except Exception as exc:
            problem = f'{type(exc).__name__}: {exc}'

        def api(name):
            require(lesson is not None, '请创建只依赖标准库的 session_store.py；' + str(problem))
            function = getattr(lesson, name, None)
            require(callable(function), f'请实现 session_store.py 的 {name}')
            return function

        def save(path, history):
            return quiet_call(api('save_history'), path, history)

        def load(path):
            return quiet_call(api('load_history'), path)

        def expect_value_error(action):
            try:
                action()
            except ValueError:
                return
            raise AssertionError('无效 JSON 或会话结构应抛 ValueError，不能返回空历史或伪造成功')

        def check_save():
            history = example_history()
            saved = deepcopy(history)
            path = directory / '南京完整会话.json'
            require(save(path, history) is None, 'save_history 成功后返回 None')
            text = path.read_text(encoding='utf-8')
            require(json.loads(text) == saved and '南京' in text,
                    '文件顶层直接保存完整消息列表；UTF-8、ensure_ascii=False，中文可直接阅读')
            require(history == saved and len(json.loads(text)) == 9,
                    '四轮历史完整保存 9 条，不调用请求裁剪或修改传入历史')

        def check_load():
            path = directory / '外部 JSON.json'
            expected = example_history(2)
            path.write_text(json.dumps(expected, ensure_ascii=False), encoding='utf-8')
            before_bytes = path.read_bytes()
            result = load(path)
            require(result == expected and path.read_bytes() == before_bytes,
                    '读回完整消息列表，保留正文空白、system 原文和 assistant 额外字段；不改文件')

        def check_roundtrip():
            path = directory / '往返.json'
            original = example_history(2)
            saved = deepcopy(original)
            save(path, original)
            original[2]['_offline_test']['places'].append('外部变更')
            restored = load(path)
            require(restored == saved, '保存的是文件数据，不依赖原内存对象')
            restored[0]['content'] = '外部修改规则'
            restored[2]['_offline_test']['places'].append('外部修改嵌套值')
            require(load(path) == saved, '每次加载读回独立对象，不能共享被调用方改过的缓存')

        def check_empty_session():
            path = directory / '尚无问答.json'
            history = example_history(0)
            save(path, history)
            require(load(path) == history, '只有 system 的新会话也是有效会话；空列表不是')

        def check_overwrite():
            path = directory / '覆盖保存.json'
            save(path, example_history(4))
            second = example_history(1)
            save(path, second)
            require(json.loads(path.read_text(encoding='utf-8')) == second,
                    '再次保存替换完整文件，不追加第二份 JSON 或留下旧尾部')

        def check_malformed():
            path = directory / '语法损坏.json'
            for text in ('', '{not JSON', '[{"role":'):
                path.write_text(text, encoding='utf-8')
                expect_value_error(lambda: load(path))
                require(path.read_text(encoding='utf-8') == text, '加载失败不修改坏文件')

        def check_invalid_load():
            path = directory / '结构错误.json'
            for value in invalid_histories():
                text = json.dumps(value, ensure_ascii=False)
                path.write_text(text, encoding='utf-8')
                expect_value_error(lambda: load(path))
                require(path.read_text(encoding='utf-8') == text,
                        'JSON 语法正确不代表会话有效；校验失败不修改文件')

        def check_invalid_save():
            path = directory / '已有好会话.json'
            good = example_history(1)
            for value in invalid_histories():
                path.write_text(json.dumps(good, ensure_ascii=False), encoding='utf-8')
                before_bytes = path.read_bytes()
                saved = deepcopy(value)
                expect_value_error(lambda: save(path, value))
                require(path.read_bytes() == before_bytes and value == saved,
                        '保存前先校验；无效会话不能清空已有文件或改输入')

        def check_io_errors():
            try:
                load(directory / '不存在.json')
            except FileNotFoundError:
                pass
            else:
                raise AssertionError('缺文件应传播 FileNotFoundError，不静默创建空会话')
            for action in (lambda: load(directory), lambda: save(directory, example_history(1))):
                try:
                    action()
                except OSError:
                    pass
                else:
                    raise AssertionError('路径为目录时传播 OSError，不伪造读写成功')

        def check_fresh_process():
            path = directory / '重启恢复.json'
            history = example_history(3)
            save(path, history)
            code = '''import json, os, socket, sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
stub = ModuleType("dotenv")
stub.load_dotenv = lambda *args, **kwargs: False
def block(*args, **kwargs):
    raise AssertionError("离线子进程禁止连接网络")
with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {"dotenv": stub, "config": None, "openai": None}), patch("socket.socket.connect", block), patch("socket.socket.connect_ex", block), patch("socket.create_connection", block):
    import session_store
    print(json.dumps(session_store.load_history(Path(sys.argv[1])), ensure_ascii=False))
'''
            result = subprocess.run([sys.executable, '-c', code, str(path), str(project)],
                                    cwd=project, capture_output=True, encoding='utf-8',
                                    errors='replace', timeout=15)
            require(result.returncode == 0 and json.loads(result.stdout) == history,
                    '新 Python 进程应能仅凭文件恢复完整历史：' + result.stderr[-1000:])

        def check_window():
            import conversation
            path = directory / '恢复后裁剪.json'
            history = example_history(4)
            save(path, history)
            restored = load(path)
            messages = quiet_call(lambda: conversation.build_turn_messages(
                restored, '  接着讨论  ', max_rounds=2))
            require(restored == history and len(restored) == 9 and len(messages) == 6,
                    '保存/恢复完整历史，只有组装请求时才按两轮裁剪')
            require(messages == [history[0]] + history[5:9] + [
                {'role': 'user', 'content': '接着讨论'}],
                    '恢复后仍能回传最近完整 assistant 及额外字段')

        def check_previous():
            import conversation
            history = conversation.create_history('离线职责检查')
            message = {'role': 'assistant', 'content': '离线回答'}
            # 历史模块只处理内存；提前阻断 I/O，保护工程内已有会话。
            reason = 'commit_turn 只提交内存历史；请移除固定路径保存，文件读写由调用方安排'
            with patch('pathlib.Path.open', side_effect=AssertionError(reason)), \
                    patch('builtins.open', side_effect=AssertionError(reason)):
                quiet_call(conversation.commit_turn, history, '离线问题', message)

            # 回归运行在最小临时副本中，不复制 .env 或真实会话文件。
            regression = directory / 'regression-project'
            regression.mkdir()
            names = ('conversation.py', 'session_store.py', 'model_demo_ask_turn.py',
                     'config.py', 'check_display.py', 'check_s2_03.py',
                     'check_s3_01.py', 'check_s3_02.py', 'check_s3_03.py')
            for name in names:
                relative = Path('test') / name if name.startswith('check_') else Path(name)
                destination = regression / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((project / relative).read_bytes())
            result = subprocess.run([sys.executable, str(regression / 'test' / 'check_s3_03.py')],
                                    cwd=regression, capture_output=True, encoding='utf-8',
                                    errors='replace', timeout=30)
            require(result.returncode == 0, 'S3-03 及此前回归失败：\n' +
                    (result.stdout + result.stderr)[-2200:])

        check('完整历史保存为可读中文 JSON', check_save)
        check('加载外部 JSON 保留正文与协议字段', check_load)
        check('保存加载往返及对象隔离', check_roundtrip)
        check('只有 system 的新会话', check_empty_session)
        check('再次保存替换旧文件', check_overwrite)
        check('损坏 JSON 抛 ValueError', check_malformed)
        check('加载时校验会话结构', check_invalid_load)
        check('保存前校验且保留已有文件', check_invalid_save)
        check('文件缺失与路径错误传播', check_io_errors)
        check('新进程从文件恢复完整历史', check_fresh_process)
        check('恢复完整历史后再裁剪请求', check_window)
        check('S3-03 及此前回归', check_previous)

    require(all(fingerprint(path) == value for path, value in before.items()),
            '检查期间业务源码发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过。')
    print('读写仅使用临时会话文件；未加载 .env、未读真实 Key、未调用模型。')
    print('本课验证独立存储函数；CLI 自动恢复尚未接入，真实问答质量另行评估。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
