"""S4-08：阶段4离线汇总与对比报告检查；不请求模型。"""

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode=True
TESTS=Path(__file__).resolve().parent
PROJECT=TESTS.parent
REPORT=PROJECT/'STAGE4_REVIEW.md'
CODE=['stage4_structured.py','stage4_tools.py','stage4_tool_flow.py','stage4_tool_app.py','test/check_stage_4.py']
sys.path.insert(0,str(TESTS))
sys.path.insert(0,str(PROJECT))
from check_s4_01 import forbidden,require
from check_s4_06c import FakeClient,tool_response
from check_s4_06b import BODY,QUESTION,incoming,response

EXPECTED=[['D1','direct','ok','ok','1','0','1','13'],
          ['T1','tool','ok','ok','2','1','2','30'],
          ['T2','tool','ok','ok','2','1','2','30'],
          ['T3','tool','invalid_output','invalid_output','2','1','2','未知']]


def fingerprint():
    digest=hashlib.sha256()
    for name in CODE:
        digest.update(name.encode()+b'\0'+(PROJECT/name).read_bytes()+b'\0')
    return digest.hexdigest()[:8]


def check_source_imports():
    allowed={'json','copy','argparse','openai','stage4_structured','stage4_tools','stage4_tool_flow'}
    for name in CODE[:4]:
        for node in ast.walk(ast.parse((PROJECT/name).read_text())):
            if isinstance(node,ast.Import):
                require(all(a.name in allowed for a in node.names),'离线对比不导入配置、文件或网络模块')
            if isinstance(node,ast.ImportFrom):
                require(node.level==0 and node.module in allowed,'离线对比只复用当前阶段')
                if node.module=='openai':
                    require(all(a.name=='APIError' for a in node.names),'业务模块不创建SDK客户端或读取Key')
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                require(node.func.id not in {'open','input','__import__','eval','exec','compile','globals'},'离线程序不读文件／终端或动态执行文本')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',help='打印四个离线场景及应填写的测量数据，不改报告')
    args=parser.parse_args()
    before={name:hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in CODE}
    before_report=hashlib.sha256(REPORT.read_bytes()).hexdigest() if REPORT.is_file() else None
    stamp=fingerprint()
    outcomes,cache=[],{}

    def check(title,action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f'未通过｜{title}：{type(error).__name__}: {error}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{title}')

    def scenarios():
        if 'rows' in cache:
            return cache['rows']
        check_source_imports()
        from stage4_structured import ask_structured
        from stage4_tool_app import run_tool_question
        import stage4_tools as tools
        rows=[]
        unknown={**BODY,'answer':'虚构教学目录未收录该名称，不能据此判定现实不存在。'}
        cases=[('D1','direct',QUESTION,FakeClient([response()])),
               ('T1','tool',QUESTION,FakeClient()),
               ('T2','tool','请查询未收录地点。',FakeClient([tool_response(incoming('未收录地点')),
                    response(content=json.dumps(unknown,ensure_ascii=False))])),
               ('T3','tool',QUESTION,FakeClient([tool_response(usage=None),response(content='{')]))]
        for case_id,path,question,client in cases:
            output,errors=io.StringIO(),io.StringIO()
            with patch.object(tools,'lookup_place',wraps=tools.lookup_place) as lookup, \
                    contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):
                if path=='direct':
                    records=[]
                    answer=ask_structured(client,question,on_metadata=records.append)
                    require(answer==BODY,'直接路径也必须经过答案契约校验')
                    state='ok'
                else:
                    result=run_tool_question(client,question)
                    records=result['responses']
                    state='ok' if result['ok'] else result['error']['code']
                require(not output.getvalue() and not errors.getvalue(),'业务函数不打印完整响应或调试内容')
                tool_calls=lookup.call_count
            totals=[item['total_tokens'] for item in records]
            total='未知' if not totals or any(type(value) is not int for value in totals) else str(sum(totals))
            rows.append([case_id,path,'invalid_output' if case_id=='T3' else 'ok',state,
                         str(len(client.requests)),str(tool_calls),str(len(records)),total])
            require(client.close_calls==0,'不关闭外部client')
        require(rows==EXPECTED,'四个受控场景的行为／次数／模拟统计不符合预期：请先修复程序，勿改报告掩盖')
        cache['rows']=rows
        return rows

    def program():
        with tempfile.TemporaryDirectory(prefix='geo-history-stage4-regression-') as temporary:
            target=Path(temporary)
            for name in ('model_demo_ask_turn.py','IncompleteStreamError.py','conversation.py','session_store.py','config.py',
                         '.gitignore','pyproject.toml','uv.lock','STAGE3_REVIEW.md','stage4_structured.py','stage4_live.py',
                         'stage4_tools.py','stage4_tool_flow.py','stage4_tool_app.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py','check_s2_03.py','check_s3_01.py','check_s3_02.py','check_s3_03.py',
                         'check_s3_04.py','check_s3_05.py','check_s3_06.py','check_s3_07a.py','check_s3_07b.py',
                         'check_s3_08.py','check_stage_3.py','check_s4_01.py','check_s4_02.py','check_s4_03a.py',
                         'check_s4_03b.py','check_s4_03c.py','check_s4_03d.py','check_s4_04.py','check_s4_05.py',
                         'check_s4_06a.py','check_s4_06b.py','check_s4_06c.py','check_s4_07.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result=subprocess.run([sys.executable,'-B',str(target/'test/check_s4_07.py')],cwd=target,
                env={'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,timeout=360)
            require(result.returncode==0 and '12/12 项通过' in result.stdout,'S4-07及此前程序检查须通过：\n'+(result.stdout+result.stderr)[-2200:])

    def report():
        require(REPORT.is_file(),'填写STAGE4_REVIEW.md，不修改业务或检查脚本')
        return REPORT.read_text()

    def table():
        text=report()
        match=re.search(r'^评估代码指纹：([0-9a-f]{8})\s*$',text,re.M)
        require(match is not None and match.group(1)==stamp,f'先运行--demo，将本次评估代码指纹{stamp}填入报告；它不是Git提交号')
        for line in ('验证方式：离线模拟','真实模型回答质量：待验证','实际费用：未知'):
            require(line in text,'保留离线证据范围，不能用模拟数据冒充真实质量或费用')
        rows=[]
        for line in text.splitlines():
            if not line.lstrip().startswith('|'):
                continue
            values=[part.strip() for part in line.strip().strip('|').split('|')]
            if values and values[0] in {'D1','T1','T2','T3'}:
                rows.append(values)
        measured=scenarios()
        require(len(rows)==4 and len({row[0] for row in rows})==4,'表格四个ID各一次，不新增或删掉失败例')
        require(sorted(rows)==sorted(measured),'按--demo填写实际状态、次数和模拟合计；T3完整合计应为未知，不是已知部分')

    def reflections():
        text=report()
        for title in ('对比结论','失败与统计','验证边界'):
            pattern=r'^### '+re.escape(title)+r'\s*$'
            match=re.search(pattern,text,re.M)
            require(match is not None,f'保留并填写“{title}”小节')
            rest=text[match.end():]
            end=re.search(r'^#{1,3} ',rest,re.M)
            paragraph=(rest[:end.start()] if end else rest).strip()
            require(len(paragraph)>=40 and not any(word in paragraph for word in ('待填写','TODO','请填写')),
                    f'用自己的话替换“{title}”占位，至少40字符；观点仍须导师人工审阅')

    with patch.dict(os.environ,{},clear=True),patch('builtins.open',side_effect=forbidden), \
            patch('builtins.input',side_effect=forbidden),patch('socket.socket.connect',side_effect=forbidden), \
            patch('socket.socket.connect_ex',side_effect=forbidden),patch('socket.create_connection',side_effect=forbidden):
        if args.demo:
            try:
                print('离线模拟对比｜全部回答与token数为假数据，不比较真实模型质量、延迟或实际费用。')
                print('评估代码指纹：'+stamp)
                print('| ID | 路径 | 预期业务状态 | 实际业务状态 | SDK调用 | 工具执行 | 响应条数 | 模拟total合计 |')
                print('| --- | --- | --- | --- | --- | --- | --- | --- |')
                for row in scenarios():
                    print('| '+' | '.join(row)+' |')
                print('四个程序场景均符合预期；T3业务失败不等于测试失败。真实模型请求0次。')
                print('统计不完整时合计未知；不能把部分用量当作完整成本。')
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title,action in [('S4-07的12项及此前整链程序检查',program),('四个离线对比场景与测量',scenarios),
                                 ('报告指纹、证据范围及测量表',table),('三段结论已填写（观点待人工复核）',reflections)]:
                check(title,action)
    require({name:hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in CODE}==before,'检查期间代码变化，请重跑')
    require((hashlib.sha256(REPORT.read_bytes()).hexdigest() if REPORT.is_file() else None)==before_report,'检查期间报告变化，请重跑')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；评估代码指纹 {stamp}。')
    print('仅离线程序与报告格式／数值检查；观点须导师人工审阅，真实模型质量仍待证据。')
    print('未读取.env／真实Key、请求头或会话；未修改报告或请求模型。')
    return 0 if all(outcomes) else 1


if __name__=='__main__':
    raise SystemExit(main())
