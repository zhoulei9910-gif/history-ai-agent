"""S3-07B：离线检查 CLI 流式接线；模拟 SSE，真实会话和 Key 不参与。"""

import ast
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
from openai import APIError

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from check_s3_02 import block_network, require
from check_s3_06 import chunk, stats
from check_s3_07a import fake_stream_io

LABEL = '模型生成｜未检索来源'


class Transcript(io.StringIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1
        super().flush()


def events(text='【离线正文甲】', reason='stop', usage=(9, 3, 12)):
    return [chunk(role='assistant'), chunk(reasoning='offline-protocol-only'),
            chunk(text), chunk(reason=reason), chunk(no_choices=True, usage=usage)]


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
            tempfile.TemporaryDirectory(prefix='geo-history-s307b-check-') as temporary:
        import session_store
        import model_demo_ask_turn as app

        directory = Path(temporary)

        def require_stream_option(function):
            parameter = inspect.signature(function).parameters.get('stream')
            require(parameter is not None and parameter.default is False,
                    f'{function.__name__} 新增 stream=False，保留旧默认行为')

        def seeded(rounds=0):
            history = [{'role': 'system', 'content': '文件中的离线规则'}]
            for number in range(1, rounds + 1):
                history.extend([
                    {'role': 'user', 'content': f'旧问题{number}'},
                    {'role': 'assistant', 'content': f'【旧回答{number}】',
                     'reasoning_content': f'offline-old-{number}'},
                ])
            return history

        def run_cli(path, inputs, plans, *, fail_first_save=False, before_request=None):
            require_stream_option(app.main)
            loads, saves, requests, output = [], [], [], Transcript()
            original_stream_call = app.ask_stream_messages
            next_plan = iter(plans)

            def read(candidate):
                require(path is not None and Path(candidate) == path,
                        '加载只使用传入临时路径，None 时不访问会话')
                loads.append(Path(candidate))
                return session_store.load_history(candidate)

            def write(candidate, history):
                require(path is not None and Path(candidate) == path,
                        '保存使用传入临时路径，不触碰项目会话')
                saves.append(deepcopy(history))
                if fail_first_save and len(saves) == 1:
                    raise PermissionError('offline-sensitive-marker')
                return session_store.save_history(candidate, history)

            def replay(messages, on_text=None):
                try:
                    plan = next(next_plan)
                except StopIteration:
                    raise AssertionError('模型请求超过本用例预算，检查重试／退出分支') from None
                if before_request is not None:
                    before_request(output, len(requests) + 1)
                with fake_stream_io(app, plan.get('events', []),
                                    status=plan.get('status', 200),
                                    after_event=plan.get('after')) as trace:
                    try:
                        return original_stream_call(messages, on_text)
                    finally:
                        requests.extend(deepcopy(trace.requests))

            with patch.object(app, 'load_history', side_effect=read), \
                    patch.object(app, 'save_history', side_effect=write), \
                    patch.object(app, 'ask_stream_messages', side_effect=replay), \
                    patch.object(app, 'ask_messages', side_effect=AssertionError('stream=True 选择流式调用')), \
                    contextlib.ExitStack() as stack:
                if path is None:
                    stack.enter_context(patch('pathlib.Path.mkdir',
                        side_effect=AssertionError('main(None) 不创建会话目录')))
                stack.enter_context(patch('builtins.input', side_effect=inputs))
                stack.enter_context(contextlib.redirect_stdout(output))
                result = app.main(path, stream=True)
            require(result is None, 'main 继续返回 None')
            return SimpleNamespace(loads=loads, saves=saves, requests=requests,
                                   output=output.getvalue(), transcript=output)

        def check_contract():
            require_stream_option(app.main)
            require_stream_option(app.ask_turn)
            callback = inspect.signature(app.ask_turn).parameters.get('on_text')
            require(callback is not None and callback.default is None,
                    'ask_turn 增加 on_text=None 并传给流式调用函数')
            streamed = inspect.signature(app.display).parameters.get('streamed')
            require(streamed is not None and streamed.default is False,
                    'display 增加 streamed=False，保留原展示默认值')

        def check_turn():
            require_stream_option(app.ask_turn)
            history = seeded()
            received = []

            def notify(text):
                require(len(history) == 1, '收到片段时还不能提交半轮历史')
                received.append(text)

            with fake_stream_io(app, events()) as trace, \
                    patch.object(app, 'ask_messages', side_effect=AssertionError('流式模式不能走旧调用')):
                answer = app.ask_turn(history, '  新问题  ', stream=True, on_text=notify)
                require(trace.requests[0]['messages'][-1]['content'] == '新问题', '问题沿用清理规则')
            require(answer.content == '【离线正文甲】' and received == [answer.content]
                    and len(history) == 3, '成功流只提交一次完整问答')
            require(history[-1] == answer.assistant_message and
                    history[-1].get('reasoning_content') == 'offline-protocol-only',
                    '提交完整 assistant，不只保存显示正文')

            history = seeded()
            answer = app.ModelAnswer('旧调用结果', 'stop', assistant_message={
                'role': 'assistant', 'content': '旧调用结果'})
            with patch.object(app, 'ask_messages', return_value=answer) as old, \
                    patch.object(app, 'ask_stream_messages', side_effect=AssertionError('保留旧默认')):
                result = app.ask_turn(history, '旧问题', stream=False,
                    on_text=lambda text: (_ for _ in ()).throw(AssertionError('非流式不调用回调')))
                require(result is answer and old.call_count == 1, 'stream=False 继续使用旧调用')

        def check_no_commit():
            require_stream_option(app.ask_turn)
            for text, reason in [('部分正文', 'length'), ('', 'stop'), ('   ', 'stop')]:
                history = seeded(1)
                original = deepcopy(history)
                with fake_stream_io(app, events(text, reason)):
                    answer = app.ask_turn(history, '新问题', stream=True)
                require(history == original and answer.content == text and stats(answer) == (9, 3, 12),
                        '截断／空白仍返回结果与元数据，但不提交历史')

        def check_display():
            parameter = inspect.signature(app.display).parameters.get('streamed')
            require(parameter is not None, 'display 增加 streamed 参数')
            for text, reason, usage in [('正文已显示', 'stop', (9, 3, 12)),
                                         ('', 'length', (None, None, None)),
                                         ('正文已显示', 'stop', (0, 0, 0))]:
                output = io.StringIO()
                answer = app.ModelAnswer(text, reason, *usage)
                with contextlib.redirect_stdout(output):
                    app.display(answer, streamed=True)
                result = output.getvalue()
                # print(f" LABEL:{LABEL not in result} result:{result} text:{text} ")
                require(LABEL not in result and (not text or text not in result),
                        'streamed=True 不重复输出来源标签或完整正文')
                require(result.count('结束原因:') == 1 and reason in result, '结束原因仍显示一次')
                require(('未提供用量统计' in result) if usage[-1] is None
                        else result.count('用量:') == 1, '统计仍显示一次，None/0 保持')
                if not text:
                    require('回答为空' in result and '截断' in result, '空答／length 提示保留')

        def check_live_cli():
            require_stream_option(app.main)
            problems = []

            def before_request(output, number):
                if output.getvalue().count(LABEL) != number:
                    problems.append('每次有效流式请求前打印一次来源标签，不能等第一片正文到达')

            fragments = ['【离线正文甲】', ' 【离线正文乙】']
            pieces = [chunk(role='assistant'), chunk(reasoning='offline-protocol-only'),
                      *[chunk(text) for text in fragments], chunk(reason='stop'),
                      chunk(no_choices=True, usage=(9, 3, 12))]
            seen, previous_flushes = [], [0]

            def after_event(index, event):
                if event.choices and event.choices[0].delta.content:
                    seen.append(event.choices[0].delta.content)
                    output = sys.stdout
                    current = output.getvalue()
                    require(LABEL in current and current.index(LABEL) < current.index(fragments[0]),
                            '第一次正文回调前先显示来源标签')
                    require(''.join(seen) in current, '每片到达即显示，不能只等最终 display')
                    require(output.flushes > previous_flushes[0], '每个正文片段显示后 flush')
                    previous_flushes[0] = output.flushes
                else:
                    previous_flushes[0] = sys.stdout.flushes

            trace = run_cli(None, ['问题', 'quit'], [{'events': pieces, 'after': after_event}],
                            before_request=before_request)
            result = trace.output
            require(result.count(''.join(fragments)) == 1 and result.count(LABEL) == 1,
                    '正文和来源各显示一次，不能流式后再打印全文')
            require(result.count('用量:') == 1 and result.count('结束原因:') == 1,
                    '消费结束再显示一份元数据')
            require('offline-protocol-only' not in result, '协议内容不显示到终端')
            require(''.join(fragments) + '\n' in result, '正文结束后补换行')
            require(not trace.loads and not trace.saves, 'main(None) 不启用文件存储')

            # 换行不能依赖“有 usage”分支中的字符串前缀；缺统计也是合法边界。
            body = '【无用量正文】'
            trace = run_cli(None, ['无用量问题', 'quit'],
                            [{'events': events(body, usage=None)}], before_request=before_request)
            if body + '\n' not in trace.output:
                problems.append('缺少 usage 时，正文结束仍须补换行，不能粘连“未提供用量统计”')
            require('未提供用量统计' in trace.output, '缺失用量提示保持')
            require(not problems, '；'.join(dict.fromkeys(problems)))

        def check_quit():
            path = directory / 'missing-parent' / 'session.json'
            trace = run_cli(path, ['  ', 'quit'], [])
            require(not trace.requests and not trace.saves and trace.loads == [path],
                    '空白／退出零请求零保存，启动仍只加载一次')
            require(LABEL not in trace.output and not path.parent.exists(),
                    '空白／退出不输出模型来源标签或提前建目录')

        def check_restore():
            path = directory / 'restored.json'
            old = seeded(4)
            path.write_text(json.dumps(old, ensure_ascii=False), encoding='utf-8')
            trace = run_cli(path, ['新问题', 'quit'], [{'events': events()}])
            require(len(trace.requests) == 1 and len(trace.requests[0]['messages']) == 6,
                    '恢复四轮后仍只发送最近两轮＋当前问题，共6条消息')
            saved = session_store.load_history(path)
            require(len(saved) == 11 and saved[:9] == old and len(trace.saves) == 1,
                    '成功后保存完整五轮，不裁剪存档或重复保存')
            require(saved[-1]['reasoning_content'] == 'offline-protocol-only', '存档保留完整协议字段')

        def check_errors():
            trace = run_cli(None, ['问题', 'quit'], [{'status': 503}])
            require(len(trace.requests) == 1 and '模型调用失败' in trace.output
                    and 'offline-sensitive-marker' not in trace.output, 'API 错误安全提示，继续且不重试')

            def interrupt(index, event):
                if event.choices and event.choices[0].delta.content:
                    raise APIError('offline-sensitive-marker',
                        request=httpx2.Request('POST', 'https://offline.invalid'), body=None)

            path = directory / 'interrupted.json'
            old = seeded(1)
            path.write_text(json.dumps(old, ensure_ascii=False), encoding='utf-8')
            trace = run_cli(path, ['中断问题', '恢复问题', 'quit'],
                [{'events': events(), 'after': interrupt}, {'events': events('恢复后的正文')}])
            require(len(trace.requests) == 2 and trace.requests[1]['messages'] ==
                    old + [{'role': 'user', 'content': '恢复问题'}],
                    '消费抛错后下一次请求不含中断问答，不能提交半轮内存')
            saved = session_store.load_history(path)
            require(len(trace.saves) == 1 and saved[:len(old)] == old and
                    len(saved) == len(old) + 2 and saved[-2]['content'] == '恢复问题',
                    '只有恢复后的成功问答保存，不以已显示片段当成功')
            require('【离线正文甲】\n' in trace.output and '模型调用失败' in trace.output,
                    '异常时也补换行，可用 try/finally 安排，防止提示粘在正文后')
            require('offline-sensitive-marker' not in trace.output, '不回显原始 APIError')

        def check_empty_length():
            for number, (text, reason) in enumerate([('', 'stop'), ('   ', 'stop'), ('部分正文', 'length')]):
                path = directory / f'uncommitted-{number}.json'
                trace = run_cli(path, ['问题', 'quit'], [{'events': events(text, reason)}])
                require(not trace.saves and not path.exists(), '空答／截断不保存未提交结果')
                require('结束原因:' in trace.output and '用量:' in trace.output,
                        '无效正文仍显示元数据')
                require('截断' in trace.output if reason == 'length' else '回答为空' in trace.output,
                        '空答／截断提示保留')
                require(trace.output.count(LABEL) == 1,
                        '空答也是一次有效模型请求，来源标签应在请求前出现一次')

        def check_save_failure():
            path = directory / 'recovery' / 'session.json'
            trace = run_cli(path, ['问题一', '问题二', 'quit'],
                [{'events': events('回答一')}, {'events': events('回答二')}], fail_first_save=True)
            require(len(trace.requests) == 2 and len(trace.requests[1]['messages']) == 4,
                    '保存失败后保留内存，下一轮携带前文，不重调上一轮模型')
            require(len(trace.saves) == 2 and len(session_store.load_history(path)) == 5,
                    '下一次成功保存包含之前未落盘问答')
            require('保存失败' in trace.output and '内存' in trace.output
                    and 'offline-sensitive-marker' not in trace.output, '保存失败提示及安全边界保持')

        def check_entry():
            tree = ast.parse(source.read_text())
            calls = []
            for node in tree.body:
                if isinstance(node, ast.If) and ast.unparse(node.test) in (
                        "__name__ == '__main__'", "'__main__' == __name__"):
                    calls.extend(child for child in ast.walk(node)
                                 if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                                 and child.func.id == 'main')
            require(any(any(keyword.arg == 'stream' and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is True for keyword in call.keywords)
                        for call in calls), '脚本入口显式 main(SESSION_PATH, stream=True)')

        def check_previous():
            regression = directory / 'regression-project'
            regression.mkdir()
            for name in ('model_demo_ask_turn.py', 'conversation.py', 'session_store.py',
                         'IncompleteStreamError.py', 'config.py', '.gitignore'):
                (regression / name).write_bytes((project / name).read_bytes())
            (regression / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py',
                         'check_s3_02.py', 'check_s3_03.py', 'check_s3_04.py',
                         'check_s3_05.py', 'check_s3_06.py', 'check_s3_07a.py'):
                (regression / 'test' / name).write_bytes((tests / name).read_bytes())
            result = subprocess.run([sys.executable, str(regression / 'test/check_s3_07a.py')],
                                    cwd=regression, capture_output=True, text=True, timeout=60)
            require(result.returncode == 0, 'S3-07A 及此前回归未通过：\n' +
                    (result.stdout + result.stderr)[-2600:])

        check('兼容原默认值的三个扩展接口', check_contract)
        check('ask_turn 选择调用方式并只提交完整成功结果', check_turn)
        check('截断／空答不提交且返回元数据', check_no_commit)
        check('已流式展示后只展示元数据及必要提示', check_display)
        check('CLI 实时刷新，正文／来源／统计不重复', check_live_cli)
        check('空白／退出零请求零保存', check_quit)
        check('恢复窗口与完整存档保持', check_restore)
        check('API／消费异常换行并保持历史', check_errors)
        check('空答／截断不落盘且仍有提示', check_empty_length)
        check('保存失败保留内存，下一轮补存', check_save_failure)
        check('脚本入口启用流式模式', check_entry)
        check('S3-07A 及此前回归（临时工程）', check_previous)

    require(hashlib.sha256(source.read_bytes()).hexdigest() == before, '检查期间源码变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8]}。')
    print('只使用内存 SSE 与临时会话；未加载 .env、未读取真实 Key、未请求真实模型。')
    print('本课不证明真实 SSE 传输完整性、模型质量或费用。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
