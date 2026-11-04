"""S4-07：已知失败转安全结果，保留响应统计；全程离线。"""

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
from types import ModuleType
from unittest.mock import patch

import httpx2
from openai import APIError, APIConnectionError, APIStatusError, APITimeoutError

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT/'stage4_tool_app.py'
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(PROJECT))
from check_s4_01 import forbidden, require
from check_s4_06c import FakeClient, tool_response, FIRST_USAGE, SECOND_USAGE
from check_s4_06b import BODY, QUESTION, incoming, response

PRIVATE = 'offline-private-error-marker'
MESSAGES = {'invalid_input':'问题必须是非空字符串。',
            'invalid_output':'模型返回的工具请求或回答不符合约定。',
            'api_error':'模型请求失败。', 'execution_error':'工具流程执行失败。'}
META = {'finish_reason','prompt_tokens','completion_tokens','total_tokens'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='展示成功及已知失败结果，统计均为假值')
    args = parser.parse_args()
    tracked = [SOURCE, PROJECT/'stage4_tool_flow.py', PROJECT/'stage4_tools.py']
    before = {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked if p.is_file()}
    cache,outcomes = {},[]

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
            require(SOURCE.is_file(), '新增stage4_tool_app.py，只实现run_tool_question')
            tree = ast.parse(SOURCE.read_text(),filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    require(all(a.name in {'copy','json'} for a in node.names), '边界不导入网络、配置或文件模块')
                if isinstance(node,ast.ImportFrom):
                    require(node.level==0 and node.module in {'copy','json','openai','stage4_tool_flow'}, '只导入标准库、SDK异常类型和当前流程')
                    if node.module=='openai':
                        require(all(a.name=='APIError' for a in node.names), '只导入APIError，不创建自己的SDK客户端')
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                    require(node.func.id not in {'open','input','__import__','eval','exec','compile','globals'}, '边界不访问文件、终端或动态执行文本')
            app=ModuleType('stage4_tool_app')
            app.__file__=str(SOURCE)
            output,errors=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):
                exec(compile(tree,str(SOURCE),'exec'),app.__dict__)
            require(not output.getvalue() and not errors.getvalue(),'导入不运行入口或打印')
            require(callable(getattr(app,'run_tool_question',None)),'实现run_tool_question(client, question) -> dict')
            cache['app']=app
        return cache['app']

    def invoke(client, question=QUESTION, calls=1):
        app=module()
        output,errors,incomplete=io.StringIO(),io.StringIO(),False
        with patch.object(app,'ask_with_tool',wraps=app.ask_with_tool) as pipeline, \
                contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):
            try:
                return app.run_tool_question(client,question)
            except NotImplementedError:
                incomplete=True
                raise
            finally:
                require(not output.getvalue() and not errors.getvalue(),'只返回结果，不打印原异常或其他内容')
                require(client.close_calls==0,'调用方拥有client，本函数不能关闭')
                if not incomplete:
                    require(pipeline.call_count==calls,f'完整流程应调用{calls}次，实际{pipeline.call_count}；不能重试')
                    if calls:
                        positional,keywords=pipeline.call_args
                        received_client=positional[0] if positional else keywords.get('client')
                        received_question=positional[1] if len(positional)>1 else keywords.get('question')
                        require(received_client is client,'透传同一client')
                        require(isinstance(received_question,str) and received_question.strip()==question.strip(),'保留有效问题，不换成固定问题')
                        print("keywords.get('on_metadata') ", keywords.get('on_metadata'))
                        require(callable(keywords.get('on_metadata')),'把内部统计收集函数传给on_metadata')

    def shape(result, *, answer=None, code=None, records=None):
        require(isinstance(result,dict) and set(result)=={'ok','answer','error','responses'},'外层恰好ok/answer/error/responses四字段dict')
        require(type(result['ok']) is bool and result['ok']==(code is None),'ok必须是对应成功／失败的bool')
        require(isinstance(result['responses'],list),'responses为列表，不能只保留最后一次统计')
        require(all(isinstance(item,dict) and set(item)==META for item in result['responses']),'每次统计只保留四字段，不能塞SDK响应或异常')
        require(result['responses']==([] if records is None else records),'保留失败前收到的全部统计，不能清空／补造或合并')
        if code is None:
            require(result['answer']==answer and result['error'] is None,'成功保留已校验答案，error为None')
        else:
            require(result['answer'] is None,'失败不能返回mock或旧答案冒充成功')
            require(result['error']=={'code':code,'message':MESSAGES[code]},'按异常类别返回固定错误码和文案，不回显原异常')
        text=json.dumps(result,ensure_ascii=False)
        require(PRIVATE not in text,'不能把原异常文本或原响应错误详情放进结果')
        require(json.loads(text)==result,'整个结果可序列化，不包含异常对象')

    def formats():
        app=module()
        require(app.ERROR_MESSAGES==MESSAGES,'保留已提供的四个稳定错误码和文案')
        shape(app.success_result(BODY,[]),answer=BODY)
        for code in MESSAGES:
            shape(app.failure_result(code,[]),code=code)
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            require(app.main()==0,'提供的格式示例正常结束')
        require('未执行问答流程' in output.getvalue(),'格式示例不能说已调用模型')

    def success():
        client=FakeClient()
        result=invoke(client)
        shape(result,answer=BODY,records=[{'finish_reason':'tool_calls',**FIRST_USAGE},{'finish_reason':'stop',**SECOND_USAGE}])
        require(len(client.requests)==2,'成功路径沿用C的两次请求')

    def missing():
        answer={**BODY,'answer':'虚构教学目录未收录该名称，不能据此判断现实中是否存在。'}
        client=FakeClient([tool_response(incoming('未收录地点')),response(content=json.dumps(answer,ensure_ascii=False))])
        result=invoke(client)
        shape(result,answer=answer,records=[{'finish_reason':'tool_calls',**FIRST_USAGE},{'finish_reason':'stop',**SECOND_USAGE}])
        require(json.loads(client.requests[1]['messages'][-1]['content'])['found'] is False,'合法未命中保留正常业务结果，不转execution_error')

    def invalid_input():
        for question in (None,5,False,[],{},'', ' \t\n','\u3000'):
            client=FakeClient()
            shape(invoke(client,question,calls=0),code='invalid_input')
            require(not client.requests,'无效输入不能调用流程或SDK')

    def invalid_first():
        unknown=incoming()
        unknown['tool_calls'][0]['function']['name']='delete_file'
        bad_json=incoming()
        bad_json['tool_calls'][0]['function']['arguments']='{'
        multiple=incoming()
        multiple['tool_calls']*=2
        for first in (tool_response(finish='stop'),tool_response(unknown),tool_response(bad_json),tool_response(multiple)):
            client=FakeClient([first])
            result=invoke(client)
            shape(result,code='invalid_output',records=[{'finish_reason':first.choices[0].finish_reason,**FIRST_USAGE}])
            require(len(client.requests)==1,'坏工具请求不补问模型、不追加请求')

    def invalid_final():
        for final in (response(content='{'),response(finish='length'),response(content=json.dumps({**BODY,'mode':'mock'}))):
            client=FakeClient([tool_response(),final])
            shape(invoke(client),code='invalid_output',records=[{'finish_reason':'tool_calls',**FIRST_USAGE},
                  {'finish_reason':final.choices[0].finish_reason,**SECOND_USAGE}])
            require(len(client.requests)==2,'续答失败只保留两次已有响应，不重试或回退mock')

    def api_errors():
        request=httpx2.Request('POST','https://offline.kimi.test/v1/chat/completions')
        status=httpx2.Response(503,request=request,json={'error':{'message':PRIVATE}})
        errors=[APIError(PRIVATE,request,body={'error':PRIVATE}),APIConnectionError(message=PRIVATE,request=request),
                APITimeoutError(request),APIStatusError(PRIVATE,response=status,body={'error':PRIVATE})]
        for error in errors:
            for first in (True,False):
                client=FakeClient([error] if first else [tool_response(),error])
                records=[] if first else [{'finish_reason':'tool_calls',**FIRST_USAGE}]
                shape(invoke(client),code='api_error',records=records)
                require(len(client.requests)==(1 if first else 2),'API失败不重试，未收到响应时不编造统计')

    def execution_errors():
        app=module()
        tools=sys.modules['stage4_tools']
        client=FakeClient([tool_response()])
        with patch.object(tools,'lookup_place',side_effect=RuntimeError(PRIVATE)) as lookup:
            shape(invoke(client),code='execution_error',records=[{'finish_reason':'tool_calls',**FIRST_USAGE}])
            require(lookup.call_count==1,'工具失败不能重新执行')
        require(len(client.requests)==1,'执行失败不请求续答')
        # RuntimeError只归为宽泛的流程执行失败，不能声称已精确定位到工具。
        with patch.object(app,'ask_with_tool',side_effect=RuntimeError(PRIVATE)):
            shape(invoke(FakeClient()),code='execution_error')

    def unexpected():
        app=module()
        for error in (TypeError(PRIVATE),AttributeError(PRIVATE),OSError(PRIVATE),KeyboardInterrupt(),SystemExit(7)):
            with patch.object(app,'ask_with_tool',side_effect=error):
                try:
                    invoke(FakeClient())
                except BaseException as caught:
                    require(caught is error,'未约定异常及退出／中断原样传播，不用Exception／BaseException统吞')
                else:
                    raise AssertionError('未约定错误不能伪装成业务失败结果')

    def metadata():
        for usage,expected in [(None,None),({'prompt_tokens':0,'completion_tokens':0,'total_tokens':0},0)]:
            client=FakeClient([tool_response(usage=usage),response(content='{')])
            shape(invoke(client),code='invalid_output',records=[{'finish_reason':'tool_calls','prompt_tokens':expected,
                  'completion_tokens':expected,'total_tokens':expected},{'finish_reason':'stop',**SECOND_USAGE}])

    def isolation():
        app=module()
        answer=deepcopy(BODY)
        original={'finish_reason':'stop',**SECOND_USAGE}
        callbacks=[]
        def fake_pipeline(client,question,*,on_metadata=None):
            callbacks.append(on_metadata)
            on_metadata(original)
            return answer
        with patch.object(app,'ask_with_tool',side_effect=fake_pipeline):
            first=invoke(FakeClient())
            shape(first,answer=BODY,records=[original])
            callbacks[0]({'finish_reason':'stop',**FIRST_USAGE})
            original['total_tokens']=999
            answer['sources'].append('外部改动')
            shape(first,answer=BODY,records=[{'finish_reason':'stop',**SECOND_USAGE}])
        one,two=invoke(FakeClient()),invoke(FakeClient())
        one['responses'][0]['total_tokens']=999
        one['answer']['sources'].append('调用方改动')
        require(two['answer']==BODY and two['responses'][0]['total_tokens']==17,'不同调用不共享答案或统计')
        with patch.object(app,'ask_with_tool',side_effect=ValueError(PRIVATE)):
            shape(invoke(FakeClient()),code='invalid_output')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s407-regression-') as temporary:
            target=Path(temporary)
            for name in ('model_demo_ask_turn.py','IncompleteStreamError.py','conversation.py','session_store.py','config.py',
                         '.gitignore','pyproject.toml','uv.lock','STAGE3_REVIEW.md','stage4_structured.py','stage4_live.py',
                         'stage4_tools.py','stage4_tool_flow.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py','check_s2_03.py','check_s3_01.py','check_s3_02.py','check_s3_03.py',
                         'check_s3_04.py','check_s3_05.py','check_s3_06.py','check_s3_07a.py','check_s3_07b.py',
                         'check_s3_08.py','check_stage_3.py','check_s4_01.py','check_s4_02.py','check_s4_03a.py',
                         'check_s4_03b.py','check_s4_03c.py','check_s4_03d.py','check_s4_04.py','check_s4_05.py',
                         'check_s4_06a.py','check_s4_06b.py','check_s4_06c.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result=subprocess.run([sys.executable,'-B',str(target/'test/check_s4_06c.py')],cwd=target,
                env={'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,timeout=330)
            require(result.returncode==0 and '13/13 项通过' in result.stdout,'C的13项与此前回归不能退步：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ,{},clear=True),patch('builtins.open',side_effect=forbidden), \
            patch('builtins.input',side_effect=forbidden),patch('socket.socket.connect',side_effect=forbidden), \
            patch('socket.socket.connect_ex',side_effect=forbidden),patch('socket.create_connection',side_effect=forbidden):
        if args.demo:
            try:
                cases=[('成功',FakeClient()),('首轮模型输出不符',FakeClient([tool_response(finish='stop')])),
                       ('续答JSON失败',FakeClient([tool_response(),response(content='{')]))]
                print('离线边界演示：全部SDK回答和用量为假值；本地查询虚构目录，真实模型请求0次。')
                for title,client in cases:
                    result=invoke(client)
                    shape(result,answer=BODY if title=='成功' else None,
                          code=None if title=='成功' else 'invalid_output',
                          records=([{'finish_reason':'tool_calls',**FIRST_USAGE},{'finish_reason':'stop',**SECOND_USAGE}]
                                   if title!='首轮模型输出不符' else [{'finish_reason':'stop',**FIRST_USAGE}]))
                    print(title+'：'+json.dumps(result,ensure_ascii=False))
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title,action in [('提供的四字段结果格式与离线示例',formats),('成功答案与两次统计',success),
                    ('合法未命中仍成功，不伪装执行异常',missing),('非法输入零流程／零请求',invalid_input),
                    ('坏首轮／工具请求转invalid_output且保留一次统计',invalid_first),
                    ('续答坏JSON／截断／模式不符保留两次统计',invalid_final),
                    ('SDK APIError及子类：失败阶段与固定文案',api_errors),('RuntimeError转流程错误，不重试',execution_errors),
                    ('未约定异常及中断退出继续传播',unexpected),('失败统计None/0保留、不清空',metadata),
                    ('结果快照与不同调用隔离',isolation),('C的13项与此前全链回归',previous)]:
                check(title,action)
    require({p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before}==before,'检查期间源码变化，请重跑')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；边界源码 {before.get(SOURCE, "")[:8]}。')
    print('仅假SDK响应／异常与虚构目录；未读取.env、真实Key、请求头或会话，未连接模型。')
    print('通过不代表模型质量或史实已核实；失败无usage不能推断免费。')
    return 0 if all(outcomes) else 1


if __name__=='__main__':
    raise SystemExit(main())
