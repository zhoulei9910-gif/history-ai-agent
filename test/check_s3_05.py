"""S3-05：离线检查 CLI 恢复/保存会话，真实会话文件不参与测试。"""

import contextlib
from copy import deepcopy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from check_s3_02 import block_network, fake_event, fake_io, require


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def memory_preserved(output):
    """提示需说明内存仍保留，不能只出现“内存”字样甚至声称内存保存失败。"""
    contradicts = re.search(r'内存[^\n]{0,8}(?:保存|提交|写入)失败', output)
    positive = re.search(
        r'(?:仍|还|依然|保留|留在|未丢失)[^\n]{0,12}内存'
        r'|内存[^\n]{0,12}(?:仍|还|依然|保留|留存|存在|保存成功|提交成功|未丢失)', output)
    return bool(positive) and not contradicts


def main():
    outcomes = []
    names = ('model_demo_ask_turn.py', 'conversation.py', 'session_store.py', '.gitignore')
    before = {name: fingerprint(project / name) for name in names}
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
            tempfile.TemporaryDirectory(prefix='geo-history-s305-') as temporary:
        directory = Path(temporary)
        import conversation
        import session_store
        import model_demo_ask_turn as app

        def seeded(rounds):
            history = [{'role': 'system', 'content': '文件中的离线规则：不编造来源。'}]
            for number in range(1, rounds + 1):
                history.extend([
                    {'role': 'user', 'content': f'旧问题{number}'},
                    fake_event(f'【旧模拟回答{number}】')['choices'][0]['message'],
                ])
            return history

        def write_seed(path, rounds=1):
            history = seeded(rounds)
            path.write_text(json.dumps(history, ensure_ascii=False), encoding='utf-8')
            return history

        def call_cli(path, inputs, events, *, load_error=None, fail_first_save=False):
            if path is not None:
                try:
                    inspect.signature(app.main).bind(path)
                except TypeError:
                    raise AssertionError('扩展 main(session_path: Path | None = None)，默认 None 保留旧行为') from None
            loads, saves, order = [], [], []
            expected_path = path

            def read(path):
                require(expected_path is not None and Path(path) == expected_path,
                        '读取必须使用传入的临时 session_path；None 时不读写文件')
                loads.append(Path(path))
                order.append('load')
                if load_error is not None:
                    raise load_error
                return session_store.load_history(path)

            def write(path, history):
                require(expected_path is not None and Path(path) == expected_path,
                        '保存必须使用传入 session_path，不能写死项目路径')
                saves.append(deepcopy(history))
                order.append('save')
                if fail_first_save and len(saves) == 1:
                    raise PermissionError('offline-sensitive-marker')
                return session_store.save_history(path, history)

            answers = iter(inputs)

            def read_input(*args):
                order.append('input')
                return next(answers)

            output = io.StringIO()
            with fake_io(app, events) as transport, \
                    patch.object(app, 'load_history', side_effect=read, create=True), \
                    patch.object(app, 'save_history', side_effect=write, create=True), \
                    patch('builtins.input', side_effect=read_input), \
                    contextlib.redirect_stdout(output):
                result = app.main() if path is None else app.main(path)
            require(result is None, 'main 继续返回 None，状态通过提示说明')
            return SimpleNamespace(loads=loads, saves=saves, order=order,
                                   requests=transport.requests, output=output.getvalue())

        def check_contract():
            parameter = inspect.signature(app.main).parameters.get('session_path')
            require(parameter is not None and parameter.default is None,
                    'main 新增 session_path 参数，默认 None 禁用持久化以兼容旧调用')
            path = getattr(app, 'SESSION_PATH', None)
            require(isinstance(path, Path) and path == project / 'data' / 'session.json',
                    'SESSION_PATH 使用脚本目录锚定 data/session.json，避免依赖启动目录')
            lines = (project / '.gitignore').read_text().splitlines()
            require('/data/session.json' in [line.strip() for line in lines],
                    '.gitignore 追加 /data/session.json，不调整已跟踪的其他文件')

        def check_disabled():
            trace = call_cli(None, ['离线问题', 'quit'], [fake_event()])
            require(len(trace.requests) == 1 and not trace.loads and not trace.saves,
                    'main() 不启用持久化，保留旧交互；仍只请求一次')
            require('模型生成｜未检索来源' in trace.output, '原来源展示保留')

        def check_new_quit():
            path = directory / '尚未创建目录' / '会话.json'
            trace = call_cli(path, ['   ', 'quit'], [])
            require(trace.loads == [path] and not trace.saves and not trace.requests,
                    '启动仅加载一次；FileNotFoundError 新建内存会话，空白/退出不保存或请求')
            require(trace.order[:2] == ['load', 'input'] and not path.parent.exists(),
                    '先加载再交互；真正成功保存时才创建父目录')

        def check_first_save():
            path = directory / '新会话目录' / '会话.json'
            trace = call_cli(path, ['  当前问题  ', 'quit'], [fake_event('【新模拟回答】')])
            require(len(trace.requests) == 1 and len(trace.saves) == 1 and path.is_file(),
                    '第一轮成功后创建父目录并保存一次，退出不重复保存')
            stored = json.loads(path.read_text(encoding='utf-8'))
            require(stored == trace.saves[0] and len(stored) == 3
                    and stored[0] == {'role': 'system', 'content': app.SYSTEM_PROMPT}
                    and stored[1] == {'role': 'user', 'content': '当前问题'}
                    and stored[2].get('reasoning_content') == 'offline-protocol-only',
                    '保存已提交的完整历史，保留清理后的问题及完整 assistant')
            require('模型生成｜未检索来源' in trace.output and '结束原因: stop' in trace.output,
                    '保存功能不替代原回答、来源及用量展示')

        def check_restore():
            path = directory / '恢复四轮.json'
            original = write_seed(path, 4)
            trace = call_cli(path, ['接着讨论', 'quit'], [fake_event('【新模拟回答】')])
            require(trace.loads == [path] and len(trace.requests) == 1 and len(trace.saves) == 1,
                    '启动读取一次，成功保存一次；不在循环中反复加载')
            require(trace.requests[0]['messages'] == [original[0]] + original[5:] + [
                {'role': 'user', 'content': '接着讨论'}],
                    '恢复后第一问只发最近两轮，保留文件内原 system 及完整协议字段')
            stored = json.loads(path.read_text(encoding='utf-8'))
            require(stored[:9] == original and len(stored) == 11 and stored == trace.saves[0],
                    '保存完整五轮 11 条历史，不能保存两轮请求快照或重复 system')

        def check_bad_files():
            for index, text in enumerate(('{not JSON', '[]',
                    '[{"role":"system","content":"规则"},{"role":"user","content":"半轮"}]')):
                path = directory / f'坏文件{index}.json'
                path.write_text(text, encoding='utf-8')
                trace = call_cli(path, [], [])
                require(trace.loads == [path] and not trace.saves and not trace.requests
                        and trace.order == ['load'] and '加载失败' in trace.output,
                        '坏 JSON/结构错误提示加载失败并返回，不进入交互或重置为空会话')
                require(path.read_text(encoding='utf-8') == text, '加载失败保留原文件')

        def check_read_error():
            path = directory / '读取失败.json'
            write_seed(path)
            before_bytes = path.read_bytes()
            trace = call_cli(path, [], [], load_error=PermissionError('offline-sensitive-marker'))
            require(trace.order == ['load'] and not trace.requests and not trace.saves
                    and path.read_bytes() == before_bytes, '读取权限错误不当作新会话，保持文件')
            require('加载失败' in trace.output and 'PermissionError' in trace.output
                    and 'offline-sensitive-marker' not in trace.output,
                    '加载错误只显示清楚的类别，不输出原始异常全文')

        def check_no_save():
            path = directory / '未成功不保存.json'
            original = write_seed(path)
            before_bytes = path.read_bytes()
            trace = call_cli(path, ['失败问题', '空答问题', '截断问题', 'quit'],
                             [503, fake_event('  '), fake_event('部分回答', 'length')])
            require(len(trace.requests) == 3 and not trace.saves and path.read_bytes() == before_bytes,
                    'API 错误、空回答和截断均不保存，不自动重试模型')
            for request, question in zip(trace.requests, ['失败问题', '空答问题', '截断问题']):
                require(request['messages'] == original + [{'role': 'user', 'content': question}],
                        '未完成问答不进入后续上下文')
            require('模型调用失败' in trace.output and '截断' in trace.output,
                    '原错误类别和未完成结果展示保留')

        def check_save_failure():
            path = directory / '保存失败后继续.json'
            trace = call_cli(path, ['问题甲', '问题乙', 'quit'],
                             [fake_event('第一答'), fake_event('第二答')], fail_first_save=True)
            require(len(trace.requests) == 2 and len(trace.saves) == 2,
                    '保存失败不重复调用模型；下一次成功问答正常再保存')
            require(trace.requests[1]['messages'][1]['content'] == '问题甲'
                    and trace.requests[1]['messages'][2]['content'] == '第一答',
                    '保存失败仍保留已经成功生成的内存历史供追问')
            require(len(trace.saves[-1]) == 5 and
                    json.loads(path.read_text(encoding='utf-8')) == trace.saves[-1],
                    '下次保存完整内存历史，包含上次未落盘的成功问答')
            require(trace.output.count('保存失败') == 1 and memory_preserved(trace.output)
                    and 'PermissionError' in trace.output and '第一答' in trace.output
                    and '第二答' in trace.output and 'offline-sensitive-marker' not in trace.output,
                    '文件保存失败时明确提示“本轮回答仍在内存”，不能称“内存保存失败”；保留类别并继续')

        def check_mkdir_failure():
            path = directory / '无法创建父目录' / '会话.json'
            with patch('pathlib.Path.mkdir', side_effect=PermissionError('offline-sensitive-marker')):
                trace = call_cli(path, ['离线问题', 'quit'], [fake_event('本轮有效回答')])
            require(len(trace.requests) == 1 and not trace.saves and not path.exists(),
                    '父目录创建失败也纳入保存错误处理，不再写文件或重请求')
            require('保存失败' in trace.output and memory_preserved(trace.output)
                    and '本轮有效回答' in trace.output and 'offline-sensitive-marker' not in trace.output,
                    '目录创建失败时也明确提示回答仍在内存，不能称“内存保存失败”')

        def check_entry():
            calls = []

            def absent(path):
                calls.append(Path(path))
                raise FileNotFoundError('offline-absent')

            output = io.StringIO()
            with patch.object(session_store, 'load_history', side_effect=absent), \
                    patch.object(session_store, 'save_history', side_effect=AssertionError('退出不保存')), \
                    patch('config.get_api_key', side_effect=AssertionError('退出不读取 Key')), \
                    patch('pathlib.Path.mkdir', side_effect=AssertionError('退出不创建目录')), \
                    patch('builtins.input', return_value='quit'), contextlib.redirect_stdout(output):
                runpy.run_path(str(project / 'model_demo_ask_turn.py'), run_name='__main__')
            require(calls == [project / 'data' / 'session.json'],
                    '脚本入口使用 main(SESSION_PATH)，实际启动时启用持久化')

        def check_previous():
            regression = directory / 'regression-project'
            regression.mkdir()
            names = ('conversation.py', 'session_store.py', 'model_demo_ask_turn.py',
                     'IncompleteStreamError.py', 'config.py',
                     'check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                     'check_s3_03.py', 'check_s3_04.py')
            for name in names:
                relative = Path('test') / name if name.startswith('check_') else Path(name)
                destination = regression / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((project / relative).read_bytes())
            result = subprocess.run([sys.executable, str(regression / 'test' / 'check_s3_04.py')],
                                    cwd=regression, capture_output=True, encoding='utf-8',
                                    errors='replace', timeout=40)
            require(result.returncode == 0, 'S3-04 及此前回归未通过：\n' +
                    (result.stdout + result.stderr)[-2200:])

        check('可选路径、默认位置及会话文件忽略', check_contract)
        check('main() 保留原无持久化调用', check_disabled)
        check('缺文件新建，空白/退出零请求零保存', check_new_quit)
        check('首次成功后创建目录并保存完整历史', check_first_save)
        check('恢复完整历史，发送窗口并继续保存', check_restore)
        check('坏 JSON/坏结构停止且保留原文件', check_bad_files)
        check('读取权限错误类别与安全提示', check_read_error)
        check('API 错误/空答/截断不保存', check_no_save)
        check('保存失败保留回答与内存并继续', check_save_failure)
        check('目录创建失败纳入保存错误处理', check_mkdir_failure)
        check('真实脚本入口启用会话路径', check_entry)
        check('S3-04 及此前回归', check_previous)

    require(all(fingerprint(project / name) == digest for name, digest in before.items()),
            '检查期间业务源码或 .gitignore 发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过。')
    print('会话读写使用临时文件；未加载 .env、未读真实 Key、未调用模型。')
    print('只验收本课 CLI 接线；真实回答质量及文件写入原子性不由本脚本保证。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
