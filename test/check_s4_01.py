"""S4-01：离线检查结构化回答契约；不加载Key、不请求模型或读取会话。"""

import ast
import contextlib
import hashlib
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
PROJECT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT / 'stage4_structured.py'
FIELDS = {'mode', 'answer', 'uncertainty', 'source_status', 'sources'}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def forbidden(*args, **kwargs):
    raise AssertionError('本课只处理传入文本和JSON，不读取输入／文件或连接网络')


def inspect_source(text):
    tree = ast.parse(text, filename=str(SOURCE))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            require(all(alias.name == 'json' for alias in node.names),
                    'S4-01只需json标准库；模型／旧入口接入留后续课程')
        elif isinstance(node, ast.ImportFrom):
            require(node.level == 0 and node.module == 'json',
                    'S4-01只需json标准库，不导入配置、SDK或旧业务入口')
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            require(node.func.id not in {'open', 'input', '__import__', 'eval', 'exec', 'compile'},
                    '本课不执行文件／终端输入或动态代码')
    return tree


def main():
    outcomes = []
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None
    cache = {}

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
        if 'app' not in cache:
            require(SOURCE.is_file(), '新增阶段4独立入口stage4_structured.py，不修改阶段3入口')
            text = SOURCE.read_text(encoding='utf-8')
            tree = inspect_source(text)
            app = ModuleType('stage4_structured')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with patch('builtins.open', side_effect=forbidden), \
                    patch('builtins.input', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(),
                    '导入只定义函数，不能直接打印、运行main或请求模型')
            require(callable(getattr(app, 'make_mock_answer', None)),
                    '定义make_mock_answer(answer: str, uncertainty: str) -> dict')
            cache.update(app=app, text=text)
        return cache['app']

    def call(answer, uncertainty):
        app = module()
        output, errors = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=forbidden), \
                patch('builtins.input', side_effect=forbidden), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.make_mock_answer(answer=answer, uncertainty=uncertainty)
            finally:
                require(not output.getvalue() and not errors.getvalue(),
                        '构造函数只返回dict，打印由main负责')

    def shape(value):
        require(isinstance(value, dict), '返回Python dict，JSON字符串留给main序列化')
        require(set(value) == FIELDS, '固定五个字段：mode、answer、uncertainty、source_status、sources')
        require(type(value['answer']) is str and type(value['uncertainty']) is str,
                'answer和uncertainty是文本字段')
        require(isinstance(value['sources'], list), 'sources使用列表，没有来源时是[]')

    def contract():
        value = call('离线正文', '尚未调用模型或检索资料')
        shape(value)
        require(value['answer'] == '离线正文' and
                value['uncertainty'] == '尚未调用模型或检索资料',
                '正文和不确定性使用调用方传入值，不写死示例内容')

    def text_values():
        for answer, uncertainty in [('  示例一  ', '\t未检索\n'),
                                    ('  中文\n"引号"与反斜线\\  ', '  仅为数据\n结构演示  ')]:
            value = call(answer, uncertainty)
            shape(value)
            require(value['answer'] == answer.strip() and
                    value['uncertainty'] == uncertainty.strip(),
                    '只清理首尾空白；内部中文、换行、引号和反斜线保留')
            require(json.loads(json.dumps(value, ensure_ascii=False)) == value,
                    '结果可完成JSON往返，不自行手拼转义字符')

    def empty_values():
        for answer, uncertainty in [('', '说明'), ('  \t\n', '说明'),
                                    ('正文', ''), ('正文', ' \t\n')]:
            try:
                call(answer, uncertainty)
            except ValueError:
                continue
            raise AssertionError('任一字段strip后为空时抛ValueError，不返回空白正文或说明')

    def invalid_types():
        for answer, uncertainty in [(None, '说明'), (17, '说明'), ([], '说明'),
                                    ('正文', None), ('正文', False), ('正文', {}),
                                    ('', None), (None, '')]:
            try:
                call(answer, uncertainty)
            except TypeError:
                continue
            raise AssertionError('先检查两个参数均为str；错误类型抛TypeError，注解不会自动校验')

    def source_state():
        for answer in ('示例正文', '这句话提到引用，但未提供任何检索结果'):
            value = call(answer, '离线模拟，未经来源核实')
            shape(value)
            require(value['mode'] == 'mock', 'mode固定mock，明确当前没有调用真实模型')
            require(value['source_status'] == 'not_retrieved' and value['sources'] == [],
                    '没有检索时source_status为not_retrieved，sources必须是空列表')

    def isolation():
        first = call('甲', '说明甲')
        second = call('乙', '说明乙')
        shape(first)
        shape(second)
        require(first is not second and first['sources'] is not second['sources'],
                '每次新建dict和sources列表，不共享可变对象')
        first['answer'] = '被外部修改'
        first['sources'].append('offline-source-marker')
        third = call('丙', '说明丙')
        require(second['answer'] == '乙' and second['sources'] == [] and
                third['answer'] == '丙' and third['sources'] == [],
                '调用方修改一个结果不影响其他或后续结果')

    def cli():
        app = module()
        # 当前模块只允许json；再次执行前在子进程隔离环境和文件／网络访问。
        wrapper = '''import builtins, json, socket
from unittest.mock import patch
def forbidden(*args, **kwargs):
    raise AssertionError('离线CLI禁止文件输入或网络连接')
code = compile(TEXT, 'stage4_structured.py', 'exec')
with patch('builtins.open', side_effect=forbidden), patch('builtins.input', side_effect=forbidden), patch('socket.socket.connect', side_effect=forbidden), patch('socket.socket.connect_ex', side_effect=forbidden), patch('socket.create_connection', side_effect=forbidden):
    exec(code, {'__name__': '__main__', '__file__': 'stage4_structured.py'})
'''.replace('TEXT', repr(cache['text']))
        result = subprocess.run([sys.executable, '-B', '-c', wrapper],
            cwd=PROJECT, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
            capture_output=True, text=True, timeout=15)
        require(result.returncode == 0, '直接运行新入口应成功；当前错误：' + result.stderr[-1000:])
        require(not result.stderr, '正常CLI不向stderr输出错误')
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise AssertionError('stdout只打印一份完整JSON，不混入提示词、Python dict或额外说明') from None
        shape(value)
        require(value['answer'].strip() and value['uncertainty'].strip(), 'CLI示例两个文本均非空')
        require(value['mode'] == 'mock' and value['source_status'] == 'not_retrieved' and
                value['sources'] == [], 'CLI如实标注离线模拟及未检索来源')
        require(any('\u4e00' <= character <= '\u9fff' for character in result.stdout),
                '使用ensure_ascii=False保留可读中文')
        require(callable(getattr(app, 'main', None)), '用main组织运行，并保留入口保护')
        sentinel = {'mode': 'mock', 'answer': '被调用函数返回的正文', 'uncertainty': '离线说明',
                    'source_status': 'not_retrieved', 'sources': []}
        output = io.StringIO()
        with patch.object(app, 'make_mock_answer', return_value=sentinel) as factory, \
                contextlib.redirect_stdout(output):
            app.main()
        require(factory.call_count == 1 and json.loads(output.getvalue()) == sentinel,
                'main复用构造函数一次，再序列化返回结果，不另写一份硬编码对象')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s401-regression-') as temporary:
            directory = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml',
                         'uv.lock', 'STAGE3_REVIEW.md'):
                require((PROJECT / name).is_file(), f'上一阶段验收所需文件缺失：{name}')
                (directory / name).write_bytes((PROJECT / name).read_bytes())
            (directory / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py',
                         'check_s3_02.py', 'check_s3_03.py', 'check_s3_04.py',
                         'check_s3_05.py', 'check_s3_06.py', 'check_s3_07a.py',
                         'check_s3_07b.py', 'check_s3_08.py', 'check_stage_3.py'):
                (directory / 'test' / name).write_bytes((PROJECT / 'test' / name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(directory / 'test/check_stage_3.py')],
                cwd=directory, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=100)
            require(result.returncode == 0 and '3/3 项通过' in result.stdout,
                    '阶段3程序及已完成报告不能回退：\n' + (result.stdout + result.stderr)[-2600:])

    with patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        check('结构化对象的五字段契约', contract)
        check('清理首尾并保留中文、换行及JSON转义', text_values)
        check('空白参数拒绝为ValueError', empty_values)
        check('错误类型先拒绝为TypeError', invalid_types)
        check('模拟模式与未检索来源状态一致', source_state)
        check('每次返回独立字典和来源列表', isolation)
        check('独立CLI输出完整JSON并复用构造函数', cli)
        check('S3-09及此前回归（临时工程）', previous)

    require((hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None) == before,
            '检查期间新入口变化，请重新运行')
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8] if before else "未创建"}。')
    print('仅标准库、内存数据与临时回归副本；未加载.env或真实Key、未请求模型、未读取会话。')
    print('本课只验证离线契约，不证明真实模型结构化输出能力、回答质量或事实来源。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
