"""S3-03：离线检查按完整轮次裁剪请求；真实模型请求数为 0。"""

import contextlib
from copy import deepcopy
import hashlib
import inspect
import io
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from unittest.mock import patch

sys.dont_write_bytecode = True
tests = Path(__file__).resolve().parent
project = tests.parent
sys.path.insert(0, str(project))

from openai import APIError
from check_s3_02 import block_network, fake_event, fake_io, quiet_call, require


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    outcomes = []
    sources = [project / 'conversation.py', project / 'model_demo_ask_turn.py']
    before = {path: fingerprint(path) for path in sources}
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
        import conversation
        import model_demo_ask_turn as app

        def history_with(rounds, nested=False):
            history = conversation.create_history(app.SYSTEM_PROMPT)
            for number in range(1, rounds + 1):
                raw = fake_event(f'【模拟回答{number}】')['choices'][0]['message']
                if nested:
                    # 只供纯函数检查，不发送给 SDK。
                    raw['_offline_test'] = {'tags': [number]}
                conversation.commit_turn(history, f'问题{number}', raw)
            return history

        def prepare(history, question='当前问题', limit=2):
            function = conversation.build_turn_messages
            try:
                inspect.signature(function).bind(history, question, max_rounds=limit)
            except TypeError:
                raise AssertionError('给 build_turn_messages 新增 max_rounds: int | None = None') from None
            return quiet_call(lambda: function(history, question, max_rounds=limit))

        def expected(history, question, limit):
            # 用逐轮遍历构造期望，避免照抄学员切片实现。
            pairs = list(zip(history[1::2], history[2::2]))
            kept = pairs if limit is None else [
                pair for index, pair in enumerate(pairs) if index >= len(pairs) - limit
            ]
            result = [deepcopy(history[0])]
            for question_message, assistant in kept:
                result.extend([deepcopy(question_message), deepcopy(assistant)])
            result.append({'role': 'user', 'content': question.strip()})
            return result

        def require_limit():
            require(getattr(app, 'MAX_HISTORY_ROUNDS', None) == 2,
                    '在 model_demo_ask_turn.py 定义 MAX_HISTORY_ROUNDS = 2')

        def check_legacy():
            history = history_with(4)
            saved = deepcopy(history)
            result = quiet_call(conversation.build_turn_messages, history, '  当前问题  ')
            require(result == expected(saved, '当前问题', None) and history == saved,
                    '省略参数时保留原两参数行为：全部历史＋清理后的当前问题，不改历史')

        def check_boundaries():
            for rounds, limit in [(0, 2), (1, 2), (2, 2), (4, None), (1, 20)]:
                history = history_with(rounds)
                saved = deepcopy(history)
                result = prepare(history, '  当前问题\t', limit)
                require(result == expected(saved, '当前问题', limit) and history == saved,
                        f'{rounds} 轮历史、上限 {limit}：保留已有完整轮次，不补空消息；None 不裁剪')

        def check_latest():
            history = history_with(4)
            result = prepare(history, limit=2)
            require(result == expected(history, '当前问题', 2),
                    '四轮历史限两轮：system、问题3、回答3、问题4、回答4、当前问题；完整保留协议字段')
            require([item['role'] for item in result] ==
                    ['system', 'user', 'assistant', 'user', 'assistant', 'user'],
                    '不能只保留最后 N 条消息，也不能截成半轮')

        def check_zero():
            history = history_with(3)
            saved = deepcopy(history)
            require(prepare(history, limit=0) == [saved[0], {'role': 'user', 'content': '当前问题'}],
                    'max_rounds=0 只发送 system＋当前问题；注意 [-0:] 等于 [0:]')
            require(history == saved, '上限 0 也不能清空已提交历史')

        def check_snapshot():
            history = history_with(4, nested=True)
            saved = deepcopy(history)
            first = prepare(history, limit=1)
            second = prepare(history, limit=1)
            second_saved = deepcopy(second)
            require(first == expected(saved, '当前问题', 1), '先选最近完整轮次，再返回独立快照')
            first[0]['content'] = '修改请求 system'
            first[1]['content'] = '修改请求 user'
            first[2]['_offline_test']['tags'].append('修改嵌套数据')
            first[2]['reasoning_content'] = '修改协议字段'
            require(history == saved and second == second_saved,
                    '切片只复制外层；返回的 system、消息字典及嵌套值也须与历史隔离')

        def check_negative():
            history = history_with(2)
            saved = deepcopy(history)
            for limit in (-1, -3):
                try:
                    prepare(history, limit=limit)
                except ValueError:
                    pass
                else:
                    raise AssertionError('负数 max_rounds 应抛 ValueError，不能悄悄当成切片下标')
                require(history == saved, '负数校验失败不修改历史')

        def check_blank():
            history = history_with(3)
            saved = deepcopy(history)
            for limit in (None, 0, 2):
                try:
                    prepare(history, ' \t\n', limit)
                except ValueError:
                    pass
                else:
                    raise AssertionError('任何上限下都拒绝空白问题')
            require(history == saved, '空白问题不影响完整历史')

        def check_wiring():
            require_limit()
            raw = fake_event()['choices'][0]['message']
            answer = app.ModelAnswer('【模拟响应】成功', 'stop', assistant_message=raw)
            for limit in (0, 1, 2):
                history = history_with(4)
                saved = deepcopy(history)
                with patch.object(app, 'MAX_HISTORY_ROUNDS', limit), \
                        patch.object(app, 'ask_messages', return_value=answer) as request:
                    result = quiet_call(app.ask_turn, history, '  接线问题  ')
                supplied = request.call_args
                messages = supplied.args[0] if supplied.args else supplied.kwargs.get('messages')
                require(request.call_count == 1 and result is answer and
                        messages == expected(saved, '接线问题', limit),
                        'ask_turn 把 MAX_HISTORY_ROUNDS 传给消息组装函数；不写死 2 或在请求之后裁剪')
                require(history == saved + [{'role': 'user', 'content': '接线问题'}, raw],
                        '成功只追加当前完整问答，已提交历史不按请求窗口裁剪')

        def check_sdk_rounds():
            require_limit()
            history = history_with(0)
            events = [fake_event(f'【模拟回答{number}】') for number in range(1, 6)]
            with fake_io(app, events) as trace:
                for number in range(1, 6):
                    saved = deepcopy(history)
                    quiet_call(app.ask_turn, history, f'问题{number}')
                    require(trace.requests[-1]['messages'] == expected(saved, f'问题{number}', 2),
                            f'第 {number} 次真实 SDK 序列化请求应只含最近两轮及当前问题')
            require(len(trace.requests) == 5 and len(history) == 11,
                    '五轮成功请求各执行一次，本地历史仍为 system＋五轮问答，共 11 条')
            require(len(trace.requests[-1]['messages']) == 6,
                    '第 5 次请求只有 6 条消息，完整 assistant 协议字段仍回传')

        def check_failures():
            require_limit()
            for event in [503, 'timeout', fake_event('部分回答', 'length'), fake_event('  ')]:
                history = history_with(4)
                saved = deepcopy(history)
                with fake_io(app, [event]) as trace:
                    try:
                        quiet_call(app.ask_turn, history, '失败或未完成的问题')
                    except APIError:
                        require(event in (503, 'timeout'), '只有 SDK 失败才传播 APIError')
                    else:
                        require(isinstance(event, dict), 'SDK 失败仍应传播给调用方')
                require(len(trace.requests) == 1 and trace.requests[0]['messages'] ==
                        expected(saved, '失败或未完成的问题', 2),
                        '失败请求也使用窗口，且不自动重试')
                require(history == saved, '裁剪后的失败请求不能删旧历史或加入未完成问答')

        def check_cli():
            require_limit()
            output = io.StringIO()
            inputs = [f'问题{number}' for number in range(1, 6)] + ['quit']
            events = [fake_event(f'【模拟回答{number}】') for number in range(1, 6)]
            with fake_io(app, events) as trace, \
                    patch('builtins.input', side_effect=inputs), \
                    contextlib.redirect_stdout(output):
                app.main()
            require(len(trace.requests) == 5 and
                    [len(item['messages']) for item in trace.requests] == [2, 4, 6, 6, 6],
                    'CLI 连续五轮实际发送的消息数应为 2、4、6、6、6；退出不请求')
            require(trace.requests[-1]['messages'] ==
                    expected(history_with(4), '问题5', 2), 'CLI 第五轮携带完整第 3、4 轮及当前问题')
            text = output.getvalue()
            require(text.count('模型生成｜未检索来源') == 5 and text.count('用量:') == 5
                    and text.count('结束原因: stop') == 5 and 'offline-protocol-only' not in text,
                    '裁剪后保留原来源、用量、结束原因展示，不输出协议字段')

        def check_previous():
            result = subprocess.run([sys.executable, str(tests / 'check_s3_02.py')],
                                    cwd=project, capture_output=True, encoding='utf-8',
                                    errors='replace', timeout=30)
            require(result.returncode == 0, 'S3-02 回归未通过：\n' +
                    (result.stdout + result.stderr)[-2200:])

        check('省略参数保留旧行为', check_legacy)
        check('无历史/不足/等于上限及 None', check_boundaries)
        check('只保留最近 N 轮完整消息', check_latest)
        check('零轮只发送 system 和当前问题', check_zero)
        check('裁剪快照隔离嵌套数据', check_snapshot)
        check('负数上限拒绝且不改历史', check_negative)
        check('不同上限均拒绝空白问题', check_blank)
        check('ask_turn 使用可调整窗口且保留完整历史', check_wiring)
        check('五轮 SDK 请求受限而历史继续增长', check_sdk_rounds)
        check('长历史失败/空答/截断保持原状', check_failures)
        check('CLI 连续五轮及原展示', check_cli)
        check('S3-02 及此前回归', check_previous)

    require(all(fingerprint(path) == value for path, value in before.items()),
            '检查期间业务源码发生变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过。')
    print('纯函数＋真实 SDK 内存假响应；未加载 .env、未读真实 Key、未请求模型。')
    print('仅检查请求窗口；轮数不等于 token 预算，不验证真实模型回答质量。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
