"""S4-06B：假SDK响应验证工具结果续答，不读取Key或请求模型。"""

import argparse
import ast
import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT/'stage4_tool_flow.py'
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(PROJECT))
from check_s4_01 import forbidden, require
from check_s4_05 import sample
from openai.types.chat import ChatCompletion, ChatCompletionMessage

QUESTION = '请介绍教学目录中的青岚。'
BODY = {'mode': 'model', 'answer': '教学目录将青岚城设定为虚构山城。',
        'uncertainty': '这是离线样例中的虚构设定，不是已核实史实。',
        'source_status': 'not_retrieved', 'sources': []}
DEFAULT_USAGE = {'prompt_tokens': 9, 'completion_tokens': 4, 'total_tokens': 13}
UNSET = object()


def incoming(name=' 青岚 ', call_id='call_lookup_1'):
    message = sample(name, call_id)
    message['reasoning_content'] = '假SDK保留字段，仅用于完整消息检查。'
    return ChatCompletionMessage(**message).to_dict()


def response(*, content=UNSET, finish='stop', usage=UNSET, calls=None):
    message = {'role': 'assistant', 'content': json.dumps(BODY, ensure_ascii=False) if content is UNSET else content}
    if calls is not None:
        message['tool_calls'] = calls
    return ChatCompletion(id='offline-followup', object='chat.completion', created=0,
        model='kimi-k3', choices=[{'index': 0, 'finish_reason': finish, 'message': message}],
        usage=DEFAULT_USAGE if usage is UNSET else usage)


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = response() if result is None else result
        self.error, self.requests, self.raw_requests, self.close_calls = error, [], [], 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.raw_requests.append(request)
        self.requests.append(deepcopy(request))
        require(len(self.requests) == 1, '续答最多一次请求，不自动重试或循环')
        if self.error is not None:
            raise self.error
        return self.result

    def close(self):
        self.close_calls += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='展示完整请求上下文和假续答，不联网')
    args = parser.parse_args()
    tracked = [SOURCE, PROJECT/'stage4_tools.py', PROJECT/'stage4_structured.py']
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked if p.is_file()}
    cache, outcomes = {}, []

    def check(title, action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f'未通过｜{title}：{type(error).__name__}: {error}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{title}')

    def module():
        if 'app' not in cache:
            require(SOURCE.is_file(), '新增stage4_tool_flow.py，保留原工具／问答入口')
            tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(a.name in {'argparse', 'copy', 'json'} for a in node.names),
                            '本课使用外部client，不导入SDK／配置／网络或文件模块')
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in {'argparse', 'copy', 'json', 'stage4_tools', 'stage4_structured'},
                            '只复用本阶段已验收模块，不导入旧入口或配置')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile', 'globals'},
                            '编排不读文件、终端或动态执行工具名')
            app = ModuleType('stage4_tool_flow')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(), '导入不能执行入口或打印')
            require(callable(getattr(app, 'ask_after_tool', None)), '实现ask_after_tool')
            cache['app'] = app
        return cache['app']

    def invoke(client, message, *, question=QUESTION, callback=None, execute_count=1, lookup_count=1):
        app = module()
        tools = sys.modules['stage4_tools']
        snapshot, catalog = deepcopy(message), deepcopy(tools.PLACE_FIXTURES)
        original_response = client.result.to_dict()
        original_execute, original_lookup = app.execute_tool_request, tools.lookup_place
        output, errors = io.StringIO(), io.StringIO()
        incomplete = False
        with patch.object(app, 'execute_tool_request', wraps=original_execute) as execution, \
                patch.object(tools, 'lookup_place', wraps=original_lookup) as lookup, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.ask_after_tool(client, question, message, on_metadata=callback)
            except NotImplementedError:
                incomplete = True
                raise
            finally:
                require(message == snapshot and tools.PLACE_FIXTURES == catalog, '不改原assistant／reasoning字段或工具目录')
                require(client.result.to_dict() == original_response, '不修改SDK响应对象或用量来伪装成功')
                require(not output.getvalue() and not errors.getvalue(), '编排只返回或抛异常，不打印')
                require(client.close_calls == 0, '外部client由调用方管理，本函数不能关闭')
                if not incomplete:
                    require(execution.call_count == execute_count, f'execute_tool_request应调用{execute_count}次，实际{execution.call_count}')
                    require(lookup.call_count == lookup_count, f'lookup_place应执行{lookup_count}次，实际{lookup.call_count}')
                    if execute_count:
                        require(execution.call_args.args == (message,) and not execution.call_args.kwargs or
                                execution.call_args.kwargs == {'assistant_message': message} and not execution.call_args.args,
                                '把完整assistant交给已验收执行器')

    def preview():
        app = module()
        output = io.StringIO()
        with patch.object(app, 'ask_after_tool', side_effect=forbidden), contextlib.redirect_stdout(output):
            code = app.main([QUESTION])
        require(code == 0 and '未发送请求' in output.getvalue(), '默认入口只预览，无Key和模型调用')
        require('"tool_choice": "none"' in output.getvalue(), '提供的续答请求禁止新工具调用')

    def cli_process():
        module()  # 先检查允许的导入；子进程只运行已提供的离线预览入口。
        for question, expected_code in ((QUESTION, 0), ('   ', 1)):
            result = subprocess.run([sys.executable, '-B', str(SOURCE), question], cwd=PROJECT,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=15)
            require(result.returncode == expected_code,
                    f'CLI输入{question!r}应退出{expected_code}，实际{result.returncode}；'
                    'main返回值需要传给SystemExit，不能在__main__里被丢弃')
            require(not result.stderr and result.stdout.strip(), '离线CLI有清楚输出，无异常堆栈')
            if expected_code == 0:
                require('未发送请求' in result.stdout, '默认入口只做基础预览')
            else:
                require('问题必须是非空字符串' in result.stdout, '空白问题提示并以非零状态结束')

    def normal():
        client = FakeClient()
        records = []
        require(invoke(client, incoming(), callback=records.append) == BODY, '返回已校验五字段dict，不返回SDK对象或工具结果')
        require(len(client.requests) == 1, '只请求一次续答；输入工具调用已由上一步产生')
        require(records == [{'finish_reason': 'stop', **DEFAULT_USAGE}], '成功响应也通知四字段元数据一次')

    def context():
        client, message = FakeClient(), incoming(call_id=' call_exact\t')
        invoke(client, message)
        messages = client.requests[0]['messages']
        require([m['role'] for m in messages] == ['system', 'user', 'assistant', 'tool'],
                '保留原问题，随后先完整assistant再tool，不能只发工具结果')
        require(messages[1]['content'] == QUESTION and messages[2] == message, '保留原问题和完整assistant协议／reasoning字段')
        raw_message = client.raw_requests[0]['messages'][2]
        require(raw_message is not message and raw_message['tool_calls'] is not message['tool_calls'],
                '请求中的assistant使用深拷贝，隔离外部SDK消息和嵌套字段')
        tool = messages[3]
        require(set(tool) == {'role', 'tool_call_id', 'name', 'content'} and tool['tool_call_id'] == message['tool_calls'][0]['id'],
                'tool消息保留四字段，与同一assistant的调用ID关联')
        result = json.loads(tool['content'])
        require(result['query'] == '青岚' and result['found'] is True and result['source_status'] == 'fixture',
                '回传实际工具结果，fixture不改成真实史料')

    def budget():
        app, client = module(), FakeClient()
        invoke(client, incoming(), question='  '+QUESTION+'  ')
        request = client.requests[0]
        require(set(request) == {'model', 'messages', 'response_format', 'stream', 'max_completion_tokens',
                                'reasoning_effort', 'tools', 'tool_choice'}, '复用已提供的八字段续答请求')
        require(request['model'] == 'kimi-k3' and request['stream'] is False and request['tool_choice'] == 'none',
                '保持现有模型／非流式，续答只生成答案')
        require(request['max_completion_tokens'] == 4096 and request['reasoning_effort'] == 'low' and
                request['response_format'] == {'type': 'json_object'}, '保持原预算和JSON Mode，不引入旧max_tokens')
        require(request['tools'] == [app.LOOKUP_TOOL] and request['messages'][1]['content'] == QUESTION,
                '工具定义和清理后的原问题保留')
        require('虚构' in request['messages'][0]['content'], '提示词说明fixture不是真实史料')

    def not_found():
        client = FakeClient()
        invoke(client, incoming('未收录地点'))
        tool = json.loads(client.requests[0]['messages'][-1]['content'])
        require(tool == {'query': '未收录地点', 'found': False, 'place': None, 'source_status': 'fixture'},
                '合法未命中照常回传，让续答说明边界，不伪造命中')

    def invalid_input():
        cases = [(None, None, TypeError), (7, None, TypeError), (' \t', None, ValueError),
                 (QUESTION, '不是回调', TypeError)]
        for question, callback, kind in cases:
            client = FakeClient()
            try:
                invoke(client, incoming(), question=question, callback=callback, execute_count=0, lookup_count=0)
            except Exception as error:
                require(isinstance(error, kind), f'输入应抛{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('输入错误应在执行工具／请求前失败')
            require(not client.requests, '输入错误不能请求模型')

    def invalid_call():
        malformed = incoming()
        malformed['tool_calls'][0]['function']['arguments'] = '{'
        unknown = incoming()
        unknown['tool_calls'][0]['function']['name'] = 'delete_file'
        multiple = incoming()
        multiple['tool_calls'] *= 2
        for message, kind in [({'role': 'assistant'}, ValueError), (None, TypeError),
                              (malformed, json.JSONDecodeError), (unknown, ValueError), (multiple, ValueError)]:
            client = FakeClient()
            try:
                invoke(client, message, lookup_count=0)
            except Exception as error:
                require(isinstance(error, kind), f'无有效工具请求应抛{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('本函数需要已有工具调用；无调用不能请求续答')
            require(not client.requests, '工具请求校验失败不应发送续答请求')

    def bad_response():
        fixtures = [(response(finish='length'), ValueError), (response(content=' '), ValueError),
                    (response(content='{'), json.JSONDecodeError),
                    (response(content=json.dumps({**BODY, 'mode': 'mock'})), ValueError),
                    (response(finish='tool_calls', content=None, calls=sample()['tool_calls']), ValueError)]
        for result, kind in fixtures:
            client, records = FakeClient(result), []
            try:
                invoke(client, incoming(), callback=records.append)
            except Exception as error:
                require(isinstance(error, kind), f'续答失败应抛{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('截断／坏正文／新工具调用必须拒绝，不返回工具结果冒充回答')
            require(len(client.requests) == 1 and len(records) == 1, '收到响应先通知统计；失败不重试或再次执行工具')
            require(records[0]['finish_reason'] == result.choices[0].finish_reason and records[0]['total_tokens'] == 13,
                    '失败也保留原finish_reason与用量')

    def metadata():
        app = module()
        for usage, expected in [(None, None), ({'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}, 0)]:
            client, records = FakeClient(response(usage=usage)), []
            invoke(client, incoming(), callback=records.append)
            require(records == [{'finish_reason': 'stop', 'prompt_tokens': expected,
                                 'completion_tokens': expected, 'total_tokens': expected}], '缺失None，0保留，不推算统计')
        with patch.object(app, 'extract_response_metadata', side_effect=forbidden):
            require(invoke(FakeClient(), incoming()) == BODY, '无回调时完全跳过统计提取')
        error = RuntimeError('离线回调失败')
        def failing_callback(value):
            raise error
        with patch.object(app, 'parse_final_response', side_effect=forbidden) as parsing:
            try:
                invoke(FakeClient(), incoming(), callback=failing_callback)
            except Exception as caught:
                require(caught is error, '回调失败原样传播，不继续解析或重试')
            else:
                raise AssertionError('回调错误必须传播')
            require(parsing.call_count == 0, '先通知统计，再校验回答')

    def failures():
        app = module()
        error = RuntimeError('离线工具执行失败')
        client = FakeClient()
        with patch.object(app, 'execute_tool_request', side_effect=error):
            try:
                invoke(client, incoming(), lookup_count=0)
            except Exception as caught:
                require(caught is error, '工具异常原样传播，不请求模型或伪造结果')
            else:
                raise AssertionError('工具错误必须传播')
        require(not client.requests, '工具失败不应请求模型')
        error = RuntimeError('离线SDK异常')
        client, records = FakeClient(error=error), []
        try:
            invoke(client, incoming(), callback=records.append)
        except Exception as caught:
            require(caught is error, 'SDK异常原样传播，不吞掉／重试／回退mock')
        else:
            raise AssertionError('SDK错误必须传播')
        require(len(client.requests) == 1 and records == [], '无SDK响应就无元数据，不假填0或再次请求')

    def isolation():
        app = module()
        tool = deepcopy(app.LOOKUP_TOOL)
        first, second = FakeClient(), FakeClient()
        a = invoke(first, incoming('青岚'))
        b = invoke(second, incoming('赤川'), question='请介绍教学目录中的赤川。')
        a['sources'].append('调用方修改')
        require(b == BODY and app.LOOKUP_TOOL == tool, '结果／工具schema互不污染')
        require(first.requests[0]['messages'][1]['content'] == QUESTION and
                second.requests[0]['messages'][1]['content'] == '请介绍教学目录中的赤川。', '不同问题请求隔离')
        require(len(first.requests[0]['messages']) == len(second.requests[0]['messages']) == 4,
                '每次请求保留system/user/assistant/tool四条完整消息')
        require(first.requests[0]['messages'][3] != second.requests[0]['messages'][3], '每次执行工具，不复用上一轮结果')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s406b-regression-') as temporary:
            target = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py', 'stage4_live.py', 'stage4_tools.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py',
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py', 'check_s4_03b.py',
                         'check_s4_03c.py', 'check_s4_03d.py', 'check_s4_04.py', 'check_s4_05.py', 'check_s4_06a.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(target/'test/check_s4_06a.py')], cwd=target,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=280)
            require(result.returncode == 0 and '10/10 项通过' in result.stdout,
                    'S4-06A及旧课不能回退：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ, {}, clear=True), patch('builtins.open', side_effect=forbidden), \
            patch('builtins.input', side_effect=forbidden), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                client, records, message = FakeClient(), [], incoming()
                print('离线续答演示：工具调用与SDK回答均为假数据；只执行本地虚构目录，不连接模型。')
                answer = invoke(client, message, callback=records.append)
                require(len(client.requests) == 1 and answer == BODY, '完成一次续答并返回已校验答案')
                for item in client.requests[0]['messages']:
                    shown = {'role': item['role'], 'content': '（已提供的系统提示词）'} if item['role'] == 'system' else item
                    print(json.dumps(shown, ensure_ascii=False))
                print('假SDK续答：'+json.dumps(answer, ensure_ascii=False))
                print('模拟元数据：'+json.dumps(records, ensure_ascii=False))
                print('SDK接口调用1次（假client）；lookup_place执行1次；真实模型请求0次。')
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title, action in [('安全导入与默认基础预览', preview), ('真实CLI进程：有效0／空白1', cli_process),
                    ('一次续答返回已校验五字段答案', normal),
                    ('完整assistant在tool之前，保留推理字段与调用ID', context),
                    ('原请求预算、工具schema、JSON Mode及tool_choice none', budget),
                    ('未命中照常回传fixture结果', not_found), ('问题／回调错误先于工具与请求', invalid_input),
                    ('缺失或非法工具调用不请求模型', invalid_call), ('坏续答保留统计，拒绝新工具且不循环', bad_response),
                    ('元数据None/0、可选回调及通知先后', metadata), ('工具／SDK异常传播与外部client所有权', failures),
                    ('请求、结果与原工具schema隔离', isolation), ('S4-06A及此前全链回归（临时工程）', previous)]:
                check(title, action)
    require({p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before} == before, '检查期间源码变化，请重新运行')
    if args.demo:
        return 0
    digest = before.get(SOURCE, '')[:8]
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；续答源码 {digest or "未创建"}。')
    print('仅假client、真实SDK DTO及本地虚构工具；未读.env／Key或真实会话，未请求模型。')
    print('不证明真实模型已提出工具调用或完成续答；演示model字段与token数都是协议假值。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
