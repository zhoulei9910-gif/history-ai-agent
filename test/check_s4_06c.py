"""S4-06C：两次受控SDK调用的离线检查；本地虚构工具，不请求模型。"""

import argparse
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
from openai import OpenAI as SDKOpenAI
from openai.types.chat import ChatCompletion

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT/'stage4_tool_flow.py'
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(PROJECT))
from check_s4_01 import forbidden, require
from check_s4_06b import BODY, QUESTION, incoming, response

FIRST_USAGE = {'prompt_tokens': 13, 'completion_tokens': 4, 'total_tokens': 17}
SECOND_USAGE = {'prompt_tokens': 9, 'completion_tokens': 4, 'total_tokens': 13}
UNSET = object()


def tool_response(message=UNSET, *, finish='tool_calls', usage=UNSET):
    message = incoming() if message is UNSET else message
    return ChatCompletion(id='offline-tool-request', object='chat.completion', created=0, model='kimi-k3',
        choices=[{'index': 0, 'finish_reason': finish, 'message': message}],
        usage=FIRST_USAGE if usage is UNSET else usage)


class FakeClient:
    def __init__(self, results=None):
        self.results = [tool_response(), response()] if results is None else results
        self.requests, self.raw_requests, self.close_calls = [], [], 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.raw_requests.append(request)
        self.requests.append(deepcopy(request))
        require(len(self.requests) <= 2, '固定流程最多两次create，不循环或重试')
        index = len(self.requests)-1
        require(index < len(self.results), '失败后不能继续请求或多发一次请求')
        result = self.results[index]
        if isinstance(result, BaseException):
            raise result
        return result

    def close(self):
        self.close_calls += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='展示首轮假工具请求、实际本地查询和假续答')
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
            tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(a.name in {'argparse', 'copy', 'json'} for a in node.names), '编排使用传入client，不导入配置／SDK／网络')
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in {'argparse', 'copy', 'json', 'stage4_structured', 'stage4_tools'},
                            '只复用当前阶段，不导入配置或旧问答入口')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile', 'globals'},
                            '编排不读文件或终端、不动态执行模型文本')
            app = ModuleType('stage4_tool_flow')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(), '导入不能执行入口或打印')
            require(callable(getattr(app, 'ask_with_tool', None)), '实现ask_with_tool(client, question, *, on_metadata=None)')
            cache['app'] = app
        return cache['app']

    def invoke(client, *, question=QUESTION, callback=None, delegates=1, executions=1, lookups=1):
        app, tools = module(), sys.modules['stage4_tools']
        delegate_original = app.ask_after_tool
        execute_original, lookup_original = app.execute_tool_request, tools.lookup_place
        catalog, schema = deepcopy(tools.PLACE_FIXTURES), deepcopy(app.LOOKUP_TOOL)
        snapshots = [(r, r.to_dict()) for r in client.results if callable(getattr(r, 'to_dict', None))]
        output, errors, incomplete = io.StringIO(), io.StringIO(), False
        with patch.object(app, 'ask_after_tool', wraps=delegate_original) as continuation, \
                patch.object(app, 'execute_tool_request', wraps=execute_original) as execution, \
                patch.object(tools, 'lookup_place', wraps=lookup_original) as lookup, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.ask_with_tool(client, question, on_metadata=callback)
            except NotImplementedError:
                incomplete = True
                raise
            finally:
                require(not output.getvalue() and not errors.getvalue(), '编排只返回或抛异常，不打印')
                require(client.close_calls == 0, '外部client由调用方关闭')
                require(tools.PLACE_FIXTURES == catalog and app.LOOKUP_TOOL == schema, '不改目录或工具schema')
                require(all(r.to_dict() == raw for r,raw in snapshots), '不改SDK响应、完整消息或统计')
                if not incomplete:
                    require(continuation.call_count == delegates, f'ask_after_tool应复用{delegates}次，实际{continuation.call_count}')
                    require(execution.call_count == executions, f'执行器应调用{executions}次，实际{execution.call_count}；不要在C重复执行')
                    require(lookup.call_count == lookups, f'地名工具应执行{lookups}次，实际{lookup.call_count}')
                    if delegates:
                        bound = inspect.signature(delegate_original).bind(*continuation.call_args.args, **continuation.call_args.kwargs)
                        bound.apply_defaults()
                        require(bound.arguments['client'] is client and bound.arguments['question'] == question,
                                '复用同一client与原问题，不重建客户端或改写问题')
                        require(bound.arguments['on_metadata'] is callback, '同一元数据回调继续传给B')
                        require(bound.arguments['assistant_message'] == client.results[0].choices[0].message.to_dict(),
                                '传递首轮完整SDK消息，包括tool_calls和reasoning_content')

    def initial_request():
        app = module()
        request = app.build_initial_tool_request('  '+QUESTION+'  ')
        require(set(request) == {'model','messages','stream','max_completion_tokens','reasoning_effort','tools','tool_choice'},
                '首轮七字段，不带最终答案的response_format')
        require(request['model']=='kimi-k3' and request['tool_choice']=='required' and request['stream'] is False,
                '现有模型、非流式，首轮请求工具')
        require(request['max_completion_tokens']==4096 and request['reasoning_effort']=='low', '保留原请求预算')
        require(request['tools']==[app.LOOKUP_TOOL] and request['messages'][1]['content']==QUESTION, '工具描述与清理问题保留')
        request['tools'][0]['function']['name']='调用方修改'
        require(app.build_initial_tool_request(QUESTION)['tools']==[app.LOOKUP_TOOL], '每次构造独立schema')

    def response_helper():
        app, original = module(), tool_response()
        raw = app.read_tool_call_response(original)
        require(raw == original.choices[0].message.to_dict() and 'reasoning_content' in raw, '首轮DTO转完整dict，不只取content')
        raw['tool_calls'][0]['function']['name']='调用方修改'
        require(original.choices[0].message.tool_calls[0].function.name=='lookup_place', '消息快照不改SDK对象')

    def normal():
        client, records = FakeClient(), []
        require(invoke(client, callback=records.append)==BODY, '返回B已校验答案，不返回首轮调用请求')
        require(len(client.requests)==2, '正常路径两次SDK方法调用')
        require(records==[{'finish_reason':'tool_calls',**FIRST_USAGE},{'finish_reason':'stop',**SECOND_USAGE}],
                '两次响应各通知一次，顺序保留，不合并或覆盖统计')

    def messages():
        client=FakeClient()
        invoke(client)
        first,second=client.requests
        require(first['tool_choice']=='required' and 'response_format' not in first, '首轮提出调用，不强行解析最终答案JSON')
        require(second['tool_choice']=='none' and second['response_format']=={'type':'json_object'}, '续答禁止新工具，恢复五字段JSON Mode')
        require([m['role'] for m in first['messages']]==['system','user'], '首轮仅system/user，不提前编造调用或结果')
        require([m['role'] for m in second['messages']]==['system','user','assistant','tool'], '续答回填完整调用与结果')
        require(second['messages'][2]==client.results[0].choices[0].message.to_dict(), '使用SDK实际返回调用ID／参数／扩展字段')
        require(second['messages'][3]['tool_call_id']==second['messages'][2]['tool_calls'][0]['id'], '结果对应同一调用ID')
        require(len(client.raw_requests[0]['messages'])==2, '续答构造新请求，不能污染首轮容器')

    def missing():
        client=FakeClient([tool_response(incoming('未收录地点')),response()])
        invoke(client)
        result=json.loads(client.requests[1]['messages'][-1]['content'])
        require(result=={'query':'未收录地点','found':False,'place':None,'source_status':'fixture'}, '合法未命中照常回传，不猜测、不追加查询')

    def invalid_inputs():
        for question,callback,kind in [(None,None,TypeError),(5,None,TypeError),(' \t',None,ValueError),(QUESTION,'非回调',TypeError)]:
            client=FakeClient()
            try:
                invoke(client,question=question,callback=callback,delegates=0,executions=0,lookups=0)
            except Exception as error:
                require(isinstance(error,kind),f'应先抛{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('问题／回调错误必须在首次请求前失败')
            require(not client.requests,'非法输入不能请求模型')

    def bad_first():
        fixtures=[tool_response(finish='stop'),tool_response(finish='length'),
                  tool_response({'role':'assistant','content':None}),
                  SimpleNamespace(choices=[],usage=None),
                  SimpleNamespace(choices=[SimpleNamespace(finish_reason='tool_calls',message={})],usage=None)]
        for first in fixtures:
            client,records=FakeClient([first]),[]
            try:
                invoke(client,callback=records.append,delegates=0,executions=0,lookups=0)
            except Exception as error:
                require(isinstance(error,ValueError),f'首轮包络错误应ValueError，实际{type(error).__name__}')
            else:
                raise AssertionError('本固定工具路径首轮必须有有效工具调用，不能偷换为直接答案')
            require(len(client.requests)==1 and len(records)==1,'先保留首轮响应统计，拒绝后不委托／执行／续答')

    def invalid_tools():
        wrong_name=incoming()
        wrong_name['tool_calls'][0]['function']['name']='delete_file'
        wrong_json=incoming()
        wrong_json['tool_calls'][0]['function']['arguments']='{'
        multiple=incoming()
        multiple['tool_calls']*=2
        for message,kind in [(wrong_name,ValueError),(wrong_json,json.JSONDecodeError),(multiple,ValueError)]:
            client,records=FakeClient([tool_response(message)]),[]
            try:
                invoke(client,callback=records.append,lookups=0)
            except Exception as error:
                require(isinstance(error,kind),f'原执行器应拒绝为{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('未知工具／坏参数／多调用不能执行或请求续答')
            require(len(client.requests)==1 and len(records)==1,'保留首次统计，不修补参数或再问模型')

    def failures():
        for first_error in (True,False):
            error=RuntimeError('离线SDK失败')
            client=FakeClient([error] if first_error else [tool_response(),error])
            records=[]
            try:
                invoke(client,callback=records.append,delegates=0 if first_error else 1,
                       executions=0 if first_error else 1,lookups=0 if first_error else 1)
            except Exception as caught:
                require(caught is error,'SDK异常原样传播，不重试／回退或关闭外部client')
            else:
                raise AssertionError('SDK错误必须传播')
            require(len(client.requests)==(1 if first_error else 2) and len(records)==(0 if first_error else 1),
                    '无响应不补统计，后续失败保留已经收到的首轮统计')
        app,tools=module(),sys.modules['stage4_tools']
        error=RuntimeError('离线本地工具失败')
        client,records=FakeClient([tool_response()]),[]
        with patch.object(tools,'lookup_place',side_effect=error):
            try:
                invoke(client,callback=records.append)
            except Exception as caught:
                require(caught is error,'工具失败原样传播，不再次执行或请求续答')
            else:
                raise AssertionError('工具错误必须传播')
        require(len(client.requests)==1 and len(records)==1,'工具失败保留首轮统计且停止')

    def metadata():
        app=module()
        for usage,expected in [(None,None),({'prompt_tokens':0,'completion_tokens':0,'total_tokens':0},0)]:
            client,records=FakeClient([tool_response(usage=usage),response()]),[]
            invoke(client,callback=records.append)
            require(records[0]=={'finish_reason':'tool_calls','prompt_tokens':expected,'completion_tokens':expected,'total_tokens':expected},
                    '首轮None／0不混同，续答统计独立')
            require(records[1]=={'finish_reason':'stop',**SECOND_USAGE},'不能用第二次统计覆盖第一次')
        with patch.object(app,'extract_response_metadata',side_effect=forbidden):
            require(invoke(FakeClient())==BODY,'无回调时两轮都不提取元数据')
        error=RuntimeError('离线回调失败')
        def first_callback(value):
            raise error
        client=FakeClient([tool_response()])
        with patch.object(app,'read_tool_call_response',side_effect=forbidden) as parsing:
            try:
                invoke(client,callback=first_callback,delegates=0,executions=0,lookups=0)
            except Exception as caught:
                require(caught is error,'首轮回调异常直接传播')
            else:
                raise AssertionError('回调失败必须停止')
            require(parsing.call_count==0,'首轮先通知统计，再校验包络／消息')
        records=[]
        def second_callback(value):
            records.append(value)
            if len(records)==2:
                raise error
        client=FakeClient()
        try:
            invoke(client,callback=second_callback)
        except Exception as caught:
            require(caught is error,'透传回调，续答回调异常也原样停止')
        else:
            raise AssertionError('续答回调错误必须传播')
        require(len(client.requests)==2 and len(records)==2,'不重复请求或再次执行工具')

    def isolation():
        one,two=FakeClient(),FakeClient([tool_response(incoming('赤川')),response()])
        first=invoke(one)
        second=invoke(two,question='请查询教学目录中的赤川。')
        first['sources'].append('调用方修改')
        require(second==BODY,'答案容器不共享；假回答内容不表示模型已真实作答')
        require(one.requests[0]['messages'][1]['content']==QUESTION and
                two.requests[0]['messages'][1]['content']=='请查询教学目录中的赤川。','不同问题不串上下文')
        require(one.requests[1]['messages'][3]!=two.requests[1]['messages'][3],'工具结果来自各自首轮调用参数')

    def real_sdk():
        app,tools=module(),sys.modules['stage4_tools']
        packets=[tool_response().to_dict(),response().to_dict()]
        sent,records=[],[]
        def handler(request):
            sent.append(json.loads(request.content))
            require(len(sent)<=2,'真实SDK内存传输只允许两次，不重试')
            return httpx2.Response(200,json=packets[len(sent)-1])
        transport_client=httpx2.Client(transport=httpx2.MockTransport(handler),trust_env=False)
        with SDKOpenAI(api_key='offline-only-key',base_url='https://offline.kimi.test/v1',timeout=120.0,
                       max_retries=0,http_client=transport_client) as client, \
                patch.object(tools,'lookup_place',wraps=tools.lookup_place) as lookup:
            require(app.ask_with_tool(client,QUESTION,on_metadata=records.append)==BODY,'真实SDK解析首轮tool_calls与续答JSON')
            require(not transport_client.is_closed,'编排不能关闭外部SDK客户端')
            require(lookup.call_count==1,'真实SDK路径仍只执行一次本地工具')
        require(len(sent)==2 and sent[0]['tool_choice']=='required' and sent[1]['tool_choice']=='none','真实请求参数正确序列化')
        require(sent[1]['messages'][2]['tool_calls'][0]['id']==sent[1]['messages'][3]['tool_call_id'], 'SDK传输保留工具关联')
        require(len(records)==2,'两次SDK响应统计均通知；所有数值为假响应')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s406c-regression-') as temporary:
            target=Path(temporary)
            for name in ('model_demo_ask_turn.py','IncompleteStreamError.py','conversation.py','session_store.py',
                         'config.py','.gitignore','pyproject.toml','uv.lock','STAGE3_REVIEW.md',
                         'stage4_structured.py','stage4_live.py','stage4_tools.py','stage4_tool_flow.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py','check_s2_03.py','check_s3_01.py','check_s3_02.py','check_s3_03.py',
                         'check_s3_04.py','check_s3_05.py','check_s3_06.py','check_s3_07a.py','check_s3_07b.py',
                         'check_s3_08.py','check_stage_3.py','check_s4_01.py','check_s4_02.py','check_s4_03a.py',
                         'check_s4_03b.py','check_s4_03c.py','check_s4_03d.py','check_s4_04.py','check_s4_05.py','check_s4_06a.py','check_s4_06b.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result=subprocess.run([sys.executable,'-B',str(target/'test/check_s4_06b.py')],cwd=target,
                env={'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,timeout=300)
            require(result.returncode==0 and '13/13 项通过' in result.stdout,'S4-06B及旧课不能回退：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ,{},clear=True),patch('builtins.open',side_effect=forbidden), \
            patch('builtins.input',side_effect=forbidden),patch('socket.socket.connect',side_effect=forbidden), \
            patch('socket.socket.connect_ex',side_effect=forbidden),patch('socket.create_connection',side_effect=forbidden):
        if args.demo:
            try:
                client,records=FakeClient(),[]
                print('离线两步演示：首轮工具调用和续答均来自假SDK响应；本地目录是虚构fixture。')
                answer=invoke(client,callback=records.append)
                require(answer==BODY and len(client.requests)==2,'完成两次受控调用并返回已校验答案')
                for i,request in enumerate(client.requests,1):
                    print(f'第{i}次：tool_choice={request["tool_choice"]}，roles='+','.join(m['role'] for m in request['messages']))
                print('本地lookup_place执行1次；真实模型请求0次。')
                print('假续答：'+json.dumps(answer,ensure_ascii=False))
                print('两次模拟元数据：'+json.dumps(records,ensure_ascii=False))
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title,action in [('首轮请求七字段、required与独立schema',initial_request),
                    ('首轮SDK消息完整快照辅助',response_helper),('两次请求、复用B、一次工具与双响应统计',normal),
                    ('首轮与续答参数、消息顺序和ID关联',messages),('未知地名结果不补造、不追加查询',missing),
                    ('问题／回调校验先于首轮请求',invalid_inputs),('坏首轮响应先保留统计再停止',bad_first),
                    ('非法工具／参数／多调用不执行或续答',invalid_tools),('两轮SDK与本地工具异常原样停止',failures),
                    ('首轮None/0、可选回调与两次通知先后',metadata),('不同请求与答案容器隔离',isolation),
                    ('真实SDK＋两次内存HTTP序列化',real_sdk),('S4-06B的13项及此前回归',previous)]:
                check(title,action)
    require({p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before}==before,'检查期间源码变化，请重跑')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；编排源码 {before.get(SOURCE, "")[:8]}。')
    print('假响应、真实SDK内存传输及虚构目录；未读.env／真实Key、请求头或会话，未连接模型。')
    print('通过不证明Kimi真实生成了工具请求／回答；演示mode及token数均为协议假值。')
    return 0 if all(outcomes) else 1


if __name__=='__main__':
    raise SystemExit(main())
