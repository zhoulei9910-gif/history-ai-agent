"""S4-04：离线检查确定性地名工具；条目为虚构练习数据，不请求模型。"""

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

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
SOURCE = PROJECT / 'stage4_tools.py'
sys.path.insert(0, str(TESTS))
from check_s4_01 import forbidden, require

FIELDS = {'query', 'found', 'place', 'source_status'}


def expected(query, place=None):
    return {'query': query, 'found': place is not None,
            'place': deepcopy(place), 'source_status': 'fixture'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='离线展示别名命中及未命中，不请求模型')
    args = parser.parse_args()
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None
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
            require(SOURCE.is_file(), '新增阶段4工具模块stage4_tools.py，保留已有核心和调用入口')
            tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(alias.name in {'argparse', 'copy', 'json', 'typing'} for alias in node.names),
                            '本课只用标准库容器与复制，不导入模型、配置或网络模块')
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in {'argparse', 'copy', 'json', 'typing'},
                            '工具只查传入名称与固定目录，不导入配置／SDK／旧问答入口')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile'},
                            '查询函数不访问文件／终端或执行动态代码')
            app = ModuleType('stage4_tools')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(), '导入不能运行CLI或输出')
            require(callable(getattr(app, 'lookup_place', None)), '实现lookup_place(name: str) -> dict')
            require(isinstance(getattr(app, 'PLACE_FIXTURES', None), list) and len(app.PLACE_FIXTURES) == 2,
                    '保留已提供的两个虚构目录条目；不提前接真实检索')
            cache['app'] = app
        return cache['app']

    def call(name):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return module().lookup_place(name)
            finally:
                require(not output.getvalue() and not errors.getvalue(), '查询只返回dict或抛异常，打印由main负责')

    def shape(result, query):
        require(isinstance(result, dict) and set(result) == FIELDS, '结果恰好query/found/place/source_status四字段dict')
        require(result['query'] == query and isinstance(result['query'], str), 'query保留清理后的输入，不替换成标准名')
        require(type(result['found']) is bool, 'found必须为bool，不能用字符串或0/1代替')
        require(result['source_status'] == 'fixture', '固定标注fixture，不能伪装已检索或核实来源')
        require(json.loads(json.dumps(result, ensure_ascii=False)) == result, '工具结果可完成JSON往返')

    def canonical():
        app = module()
        for place in app.PLACE_FIXTURES:
            result = call(place['name'])
            place_name = place['name']
            shape(result, place['name'])
            require(result == expected(place['name'], place), '精确命中标准名，返回目录完整条目')

    def aliases():
        for place in module().PLACE_FIXTURES:
            for alias in place['aliases']:
                result = call(alias)
                shape(result, alias)
                require(result == expected(alias, place), '别名返回对应标准条目；query仍为本次别名')

    def whitespace():
        app = module()
        for raw, place in [(' \t青岚\n', app.PLACE_FIXTURES[0]), ('\u3000赤川镇\u3000', app.PLACE_FIXTURES[1])]:
            result = call(raw)
            shape(result, raw.strip())
            require(result == expected(raw.strip(), place), '保存strip结果，只清理首尾空白')
        raw = '  青 岚  '
        require(call(raw) == expected(raw.strip()), '不删除内部空白或私自做模糊归一化')

    def not_found():
        for name in ('未收录地点', '青', '青岚城附近', '赤川镇以外', '南京'):
            result = call(name)
            shape(result, name)
            require(result == expected(name), '未命中found=False、place=None，不猜测、不补造资料')

    def errors():
        for value, kind in [(None, TypeError), (False, TypeError), (7, TypeError),
                            ([], TypeError), ({}, TypeError), (b'place', TypeError),
                            ('', ValueError), (' \t\n', ValueError), ('\u3000', ValueError)]:
            try:
                call(value)
            except Exception as error:
                require(isinstance(error, kind), f'错误输入应为{kind.__name__}，实际{type(error).__name__}')
            else:
                raise AssertionError('非str先TypeError，空白str再ValueError，不能返回未命中掩盖无效参数')

    def provenance():
        for name in ('青岚城', '赤川', '未收录地点'):
            result = call(name)
            require(result['source_status'] == 'fixture', '命中或未命中均说明查询的是虚构练习目录')
            if result['place'] is not None:
                require('虚构' in result['place']['description'], '保留条目虚构说明，不写成史实或引用')

    def isolation():
        app = module()
        catalog = deepcopy(app.PLACE_FIXTURES)
        first, second = call('青岚'), call('青岚')
        require(first is not second and first['place'] is not second['place'] and
                first['place']['aliases'] is not second['place']['aliases'], '每次新建结果及嵌套条目／别名列表')
        first['query'] = '调用方改动'
        first['place']['description'] = '调用方改描述'
        first['place']['aliases'].append('调用方新别名')
        require(second == expected('青岚', catalog[0]) and call('青岚') == second,
                '调用方修改结果不影响其他或后续查询')
        require(app.PLACE_FIXTURES == catalog, '查询及外部修改不得污染固定目录，浅复制不够')

    def changed_catalog():
        app = module()
        place = {'name': '测试城', 'aliases': ['测试别名'], 'description': '仅用于离线检查的虚构条目'}
        with patch.object(app, 'PLACE_FIXTURES', [place]):
            require(call('测试别名') == expected('测试别名', place), '使用提供的目录查询，不能硬编码两条示例答案')
        with patch.object(app, 'PLACE_FIXTURES', []):
            require(call('青岚') == expected('青岚'), '目录没有条目时不能返回旧缓存或硬编码结果')

    def cli():
        app = module()
        for name in ('青岚', '未收录地点'):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = app.main([name])
            require(code == 0 and json.loads(output.getvalue()) == call(name), 'CLI输出一份完整中文JSON；未命中也是正常结果')
            require(any('\u4e00' <= c <= '\u9fff' for c in output.getvalue()), '保留可读中文')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = app.main(['  '])
        require(code == 1 and output.getvalue().strip(), '空白参数返回1并提示，不能作为未命中')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s404-regression-') as temporary:
            target = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py', 'stage4_live.py'):
                (target/name).write_bytes((PROJECT/name).read_bytes())
            (target/'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py',
                         'check_s4_01.py', 'check_s4_02.py', 'check_s4_03a.py', 'check_s4_03b.py',
                         'check_s4_03c.py', 'check_s4_03d.py'):
                (target/'test'/name).write_bytes((TESTS/name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(target/'test/check_s4_03d.py')], cwd=target,
                env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=220)
            require(result.returncode == 0 and '10/10 项通过' in result.stdout,
                    'S4-03D及旧课不能回退：\n'+(result.stdout+result.stderr)[-2200:])

    with patch.dict(os.environ, {}, clear=True), patch('builtins.open', side_effect=forbidden), \
            patch('builtins.input', side_effect=forbidden), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                print('离线虚构目录演示：不是模型回答，不是历史资料。')
                for name in (' 青岚 ', '未收录地点'):
                    result = call(name)
                    shape(result, name.strip())
                    print(json.dumps(result, ensure_ascii=False, indent=2))
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            for title, action in [('标准名称精确命中四字段结果', canonical),
                    ('别名映射与原查询保留', aliases), ('首尾清理，不做内部或模糊改写', whitespace),
                    ('未收录明确False/None，不补造资料', not_found), ('非str和空白参数异常分开', errors),
                    ('命中与未命中都标注fixture', provenance), ('结果、嵌套列表和原目录隔离', isolation),
                    ('目录替换与空目录，不硬编码答案', changed_catalog), ('CLI只展示JSON，未命中正常返回', cli),
                    ('S4-03D及此前回归（临时工程）', previous)]:
                check(title, action)
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before, '检查期间源文件变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；工具源码 {before[:8] if before else "未创建"}。')
    print('仅固定虚构数据与临时旧课回归；未读取.env／Key或真实会话，未请求模型。')
    print('通过不证明真实地名／历史事实已核实，也不表示模型已会调用工具。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
