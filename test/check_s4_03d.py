"""S4-03D：真实SDK＋内存HTTP检查，隔离Key和网络；不执行付费模型调用。"""

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
from unittest.mock import Mock, patch

import httpx2
import openai
from openai import OpenAI as SDKOpenAI

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
sys.path.insert(0, str(TESTS))
from check_s4_01 import forbidden, inspect_source, require
from check_s4_03b import payload

ENTRY = PROJECT / 'stage4_live.py'
CORE = PROJECT / 'stage4_structured.py'
FAKE_KEY = 'offline-stage4-key-marker'
FAKE_URL = 'https://offline.kimi.test/v1'
PRIVATE = 'offline-private-error-marker'
META_FIELDS = {'finish_reason', 'prompt_tokens', 'completion_tokens', 'total_tokens'}


def packet(raw=None, finish='stop', usage='normal'):
    if raw is None:
        raw = json.dumps(payload(answer='离线SDK假正文'), ensure_ascii=False)
    return {'id': 'offline-completion', 'object': 'chat.completion', 'created': 0,
            'model': 'kimi-k3', 'choices': [{'index': 0, 'finish_reason': finish,
            'message': {'role': 'assistant', 'content': raw}}],
            'usage': {'prompt_tokens': 8, 'completion_tokens': 3, 'total_tokens': 11}
                     if usage == 'normal' else usage}


def json_objects(output):
    values, index, decoder = [], 0, json.JSONDecoder()
    while index < len(output):
        if output[index] == '{':
            try:
                value, length = decoder.raw_decode(output[index:])
            except json.JSONDecodeError:
                pass
            else:
                values.append(value)
                index += length
                continue
        index += 1
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='使用假配置和内存HTTP演示，不读取Key或请求模型')
    args = parser.parse_args()
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (ENTRY, CORE) if path.is_file()}
    outcomes, cache = [], {}

    def check(label, action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f'未通过｜{label}：{type(error).__name__}: {error}')
        else:
            outcomes.append(True)
            print(f'通过  ｜{label}')

    def module():
        if cache:
            return cache['app'], cache['core']
        require(ENTRY.is_file(), '新增stage4_live.py入口，阶段4纯核心保持独立')
        core = ModuleType('stage4_structured')
        core.__file__ = str(CORE)
        exec(compile(inspect_source(CORE.read_text()), str(CORE), 'exec'), core.__dict__)
        tree = ast.parse(ENTRY.read_text(), filename=str(ENTRY))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        require(child.module not in ('config', 'dotenv'),
                                '配置导入放到run_live内，预览和导入不加载.env')
                    if isinstance(child, ast.Import):
                        require(all(alias.name not in ('config', 'dotenv') for alias in child.names),
                                '导入与默认预览不读取真实配置')
        app = ModuleType('stage4_live')
        app.__file__ = str(ENTRY)
        config = ModuleType('config')
        config.get_api_key = config.get_base_url = forbidden
        output = io.StringIO()
        with patch.dict(sys.modules, {'stage4_structured': core, 'config': config}), \
                patch.object(openai, 'OpenAI', side_effect=forbidden), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(compile(tree, str(ENTRY), 'exec'), app.__dict__)
        require(not output.getvalue(), '导入不能打印或启动CLI')
        require(callable(getattr(app, 'run_live', None)) and callable(getattr(app, 'main', None)),
                '保留run_live(question)->int和带入口保护的main')
        cache.update(app=app, core=core)
        return app, core

    def run(question='离线问题', result=None, *, status=200, missing_key=False,
            timeout=False, cli=False, preview=False):
        app, core = module()
        state = {'requests': [], 'clients': [], 'config': [], 'options': []}
        config = ModuleType('config')
        def key(provider=None):
            state['config'].append(('key', provider))
            if missing_key:
                raise ValueError(PRIVATE)
            return FAKE_KEY
        def base(provider=None):
            state['config'].append(('base', provider))
            return FAKE_URL
        config.get_api_key, config.get_base_url = key, base
        def handler(request):
            state['requests'].append(json.loads(request.content))
            if timeout:
                raise httpx2.ReadTimeout(PRIVATE, request=request)
            if status != 200:
                return httpx2.Response(status, json={'error': {'message': PRIVATE+' '+FAKE_KEY,
                                                             'type': 'offline_error'}})
            return httpx2.Response(200, json=packet() if result is None else result)
        def factory(**kwargs):
            state['options'].append(deepcopy(kwargs))
            require(kwargs.get('api_key') == FAKE_KEY and str(kwargs.get('base_url')) == FAKE_URL,
                    '显式使用Kimi配置，不硬编码或读取其他供应商的Key')
            require(kwargs.get('timeout') == 120 and kwargs.get('max_retries') == 0,
                    '客户端timeout=120、max_retries=0，避免隐式重试')
            client = SDKOpenAI(**kwargs, http_client=httpx2.Client(
                transport=httpx2.MockTransport(handler), trust_env=False))
            state['clients'].append(client)
            return client
        spy = Mock(wraps=core.ask_structured)
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {'config': config, 'stage4_structured': core}))
            stack.enter_context(patch.object(openai, 'OpenAI', side_effect=factory))
            if hasattr(app, 'OpenAI'):
                stack.enter_context(patch.object(app, 'OpenAI', side_effect=factory))
            stack.enter_context(patch.object(app, 'ask_structured', spy))
            stack.enter_context(patch.object(core, 'ask_structured', spy))
            stack.enter_context(contextlib.redirect_stdout(output))
            stack.enter_context(contextlib.redirect_stderr(errors))
            try:
                if preview:
                    code = app.main([question])
                elif cli:
                    code = app.main([question, '--live'])
                else:
                    code = app.run_live(question)
            finally:
                state['closed_on_return'] = all(client.is_closed() for client in state['clients'])
                for client in state['clients']:
                    if not client.is_closed():
                        client.close()
        text = output.getvalue()+errors.getvalue()
        require(FAKE_KEY not in text and PRIVATE not in text, '终端不能输出Key或原始SDK／配置异常')
        state['ask_count'] = spy.call_count
        return code, text, state

    def one_request(state):
        require(len(state['requests']) == 1 and len(state['clients']) == 1 and state['ask_count'] == 1,
                '一次显式调用只创建一个客户端、复用ask_structured一次、只发一条假HTTP请求')
        require(state['closed_on_return'], '成功和失败都关闭本函数创建的客户端，推荐with管理')
        require(('key', 'kimi') in state['config'] and ('base', 'kimi') in state['config'],
                '配置显式指定kimi，不能沿用默认DeepSeek')

    def metadata(output):
        values = [x for x in json_objects(output) if isinstance(x, dict) and set(x) == META_FIELDS]
        require(len(values) == 1, '响应元数据以一份JSON展示，包含结束原因和三个用量字段')
        return values[0]

    def preview():
        code, output, state = run('  离线预览问题  ', preview=True)
        require(code == 0 and not state['requests'] and not state['clients'] and not state['config'],
                '默认仅预览，不读取配置、创建客户端或发请求；真实调用必须--live')
        require('未发送请求' in output and json_objects(output) == [module()[1].build_structured_request('离线预览问题')],
                '预览明确离线并展示可序列化请求参数')

    def invalid_inputs():
        for question in (None, 9, False, [], '', ' \t\n'):
            code, output, state = run(question)
            require(code == 1 and output.strip() and not state['config'] and not state['clients'],
                    '无效问题返回1并给提示，在读取配置和创建客户端前结束')

    def missing_configuration():
        code, output, state = run(missing_key=True)
        require(code == 1 and output.strip() and not state['clients'] and not state['requests'],
                '缺少Key给安全提示并返回1，不创建客户端或请求')

    def normal():
        question = '  为什么河流影响城市发展？  '
        code, output, state = run(question, cli=True)
        require(code == 0, '成功返回0；用python文件--live接通run_live')
        one_request(state)
        require(state['requests'][0] == module()[1].build_structured_request(question),
                '真实SDK发送已验收的六字段JSON Mode请求，不改模型／预算')
        require(output.count('模型生成｜未检索来源') == 1 and
                payload(answer='离线SDK假正文') in json_objects(output),
                '如实标注一次来源并以可读中文JSON展示已校验回答')
        require(metadata(output) == {'finish_reason': 'stop', 'prompt_tokens': 8,
                'completion_tokens': 3, 'total_tokens': 11}, '打印来自响应回调的完整统计')

    def zero_statistics():
        code, output, state = run(result=packet(usage={'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}))
        require(code == 0 and metadata(output) == {'finish_reason': 'stop', 'prompt_tokens': 0,
                'completion_tokens': 0, 'total_tokens': 0}, '0计数仍显示0，不当作缺失')
        one_request(state)

    def missing_statistics():
        code, output, state = run(result=packet(usage=None))
        require(code == 0 and metadata(output) == {'finish_reason': 'stop', 'prompt_tokens': None,
                'completion_tokens': None, 'total_tokens': None}, '缺usage如实显示null，不补0或推算')
        one_request(state)

    def invalid_json():
        code, output, state = run(result=packet(raw='{'))
        require(code == 1, 'JSON解析失败返回1，而不是崩溃或伪造成功')
        one_request(state)
        require(metadata(output)['total_tokens'] == 11, 'JSON失败仍展示已返回用量，推荐finally展示')

    def rejected_answer():
        cases = [packet(finish='length'), packet(raw=' '),
                 packet(raw=json.dumps({**payload(), 'sources': ['没有检索的假来源']}))]
        for result in cases:
            code, output, state = run(result=result)
            require(code == 1, '截断、空答或来源校验失败不能返回成功')
            one_request(state)
            require(metadata(output)['total_tokens'] == 11, '业务拒绝也保留统计，不自动重复请求')

    def sdk_errors():
        for options in ({'status': 401}, {'status': 503}, {'timeout': True}):
            code, output, state = run(**options)
            require(code == 1 and output.strip(), 'SDK失败安全提示并返回1，不回显原异常')
            require('未知' in output or '未取得' in output, '无响应统计时明确未知，不把失败当作免费')
            one_request(state)
            require(not any(set(x) == META_FIELDS for x in json_objects(output)),
                    '未取得响应元数据时明确未知，不伪造零统计')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s403d-regression-') as temporary:
            target = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py',
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py', 'check_s4_03b.py', 'check_s4_03c.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(target/'test/check_s4_03c.py')], cwd=target,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=200)
            require(result.returncode == 0 and '12/12 项通过' in result.stdout,
                    'S4-03C及旧课不能回退：\n'+(result.stdout+result.stderr)[-2000:])

    with patch.dict(os.environ, {}, clear=True), patch('builtins.open', side_effect=forbidden), \
            patch('builtins.input', side_effect=forbidden), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                print('离线演示：真实SDK＋假配置＋内存HTTP，未读取Key、未请求模型，用量为假值。')
                code, output, state = run(cli=True)
                require(code == 0, '演示入口应成功')
                one_request(state)
                require(metadata(output)['total_tokens'] == 11, '演示保留假用量')
                print(output, end='')
                print('假HTTP请求次数：', len(state['requests']))
            except Exception as error:
                print('演示未通过：'+type(error).__name__)
                return 1
        else:
            for label, action in [('导入与默认预览无配置／SDK请求', preview),
                    ('无效问题在配置和客户端之前拒绝', invalid_inputs),
                    ('缺Key安全结束，零请求', missing_configuration),
                    ('真实SDK正常接线、预算、来源和元数据', normal),
                    ('零统计保留0', zero_statistics), ('缺usage如实保留null', missing_statistics),
                    ('JSON失败仍展示统计并关闭资源', invalid_json),
                    ('截断／空答／伪造来源拒绝且不重问', rejected_answer),
                    ('401／503／超时安全退出、零重试与关闭', sdk_errors),
                    ('S4-03C及此前回归（临时工程）', previous)]:
                check(label, action)
    require({str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (ENTRY, CORE)} == before,
            '检查期间源文件变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；入口 {before.get(str(ENTRY), "未创建")[:8]}。')
    print('仅真实SDK的内存假HTTP；未读取.env／Key或会话，未连接模型，无真实费用。')
    print('离线通过不代表Kimi真实响应／质量通过；真实评估另由学员手动最多两次。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
