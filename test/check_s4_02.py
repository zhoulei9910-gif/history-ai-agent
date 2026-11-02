"""S4-02：离线检查JSON解析与回答契约；不加载Key、不请求模型。"""

import argparse
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
SOURCE = PROJECT / 'stage4_structured.py'
sys.path.insert(0, str(TESTS))

from check_s4_01 import FIELDS, forbidden, inspect_source, require


def valid(answer='离线正文', uncertainty='没有调用模型或检索资料'):
    return {'mode': 'mock', 'answer': answer, 'uncertainty': uncertainty,
            'source_status': 'not_retrieved', 'sources': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='只演示合法解析与非法来源拒绝，不替代完整验收')
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
            require(SOURCE.is_file(), '继续使用阶段4入口stage4_structured.py，不修改阶段3入口')
            tree = inspect_source(SOURCE.read_text(encoding='utf-8'))
            app = ModuleType('stage4_structured')
            app.__file__ = str(SOURCE)
            output, errors = io.StringIO(), io.StringIO()
            with patch('builtins.open', side_effect=forbidden), \
                    patch('builtins.input', side_effect=forbidden), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                exec(compile(tree, str(SOURCE), 'exec'), app.__dict__)
            require(not output.getvalue() and not errors.getvalue(),
                    '导入只定义函数，不能打印、运行main或请求模型')
            require(callable(getattr(app, 'parse_answer_json', None)),
                    '新增parse_answer_json(raw: str) -> dict；保留原构造函数和main')
            cache['app'] = app
        return cache['app']

    def call(raw):
        app = module()
        output, errors = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=forbidden), \
                patch('builtins.input', side_effect=forbidden), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                return app.parse_answer_json(raw)
            finally:
                require(not output.getvalue() and not errors.getvalue(),
                        '解析函数只返回dict或抛异常，不打印、读输入或访问文件')

    def expect_error(raw, expected_type, message):
        try:
            call(raw)
        except Exception as error:
            require(isinstance(error, expected_type),
                    f'{message}；应为{expected_type.__name__}，实际{type(error).__name__}')
            if expected_type is ValueError:
                require(not isinstance(error, json.JSONDecodeError),
                        '语法正确但契约无效时用ValueError，不能伪装为JSON语法错误')
            return
        raise AssertionError(message + '；当前错误数据被正常返回')

    def reject_payload(payload, message):
        expect_error(json.dumps(payload, ensure_ascii=False), ValueError, message)

    def shape(result):
        require(isinstance(result, dict), '返回解析并校验后的dict，不返回原JSON字符串')
        require(set(result) == FIELDS, '结果保留约定的五个字段，不漏字段或附加字段')
        require(result['mode'] == 'mock' and result['source_status'] == 'not_retrieved' and
                isinstance(result['sources'], list) and result['sources'] == [],
                '本课只接受mock／not_retrieved和空来源列表')
        require(isinstance(result['answer'], str) and result['answer'].strip() and
                isinstance(result['uncertainty'], str) and result['uncertainty'].strip(),
                '正文与说明均为非空白str')

    def normal():
        for payload in (valid(), valid('第二个正文', '仅为离线结构示例')):
            result = call(json.dumps(payload, ensure_ascii=False))
            shape(result)
            require(result == payload, '返回传入JSON的内容，不能写死演示答案')

    def raw_types():
        for raw in (None, 7, False, [], {}, b'{}', bytearray(b'{}')):
            expect_error(raw, TypeError, 'raw必须是str；bytes或现成dict也需明确拒绝')

    def syntax():
        good = json.dumps(valid(), ensure_ascii=False)
        for raw in ('', ' \t\n', '{', "{'answer': '单引号'}", good + '尾随说明',
                    '```json\n' + good + '\n```', good + good):
            expect_error(raw, json.JSONDecodeError,
                         '非法JSON保留json.JSONDecodeError，不用eval、默认对象或截取文本修补')

    def top_level():
        for payload in ([], [valid()], None, 0, 1.5, True, False, '正文字符串'):
            reject_payload(payload, '合法JSON的顶层仍必须是对象；不能泄漏索引或属性异常')

    def fields():
        for key in FIELDS:
            payload = valid()
            del payload[key]
            reject_payload(payload, f'缺少字段{key}应抛ValueError，不能get默认值或泄漏KeyError')
        for key in ('confidence', 'source', 'unexpected'):
            payload = valid()
            payload[key] = '离线额外字段'
            reject_payload(payload, f'出现未约定字段{key}应拒绝，不能丢弃后返回合法对象')

    def field_types():
        for key in ('answer', 'uncertainty', 'mode', 'source_status'):
            for value in (None, False, 0, [], {}):
                payload = valid()
                payload[key] = value
                reject_payload(payload, f'{key}必须是str，字段类型错误统一为ValueError')
        for key in ('answer', 'uncertainty'):
            for value in ('', ' \t\n'):
                payload = valid()
                payload[key] = value
                reject_payload(payload, f'{key}清理后为空需拒绝')
        for value in (None, '', {}, False, 0):
            payload = valid()
            payload['sources'] = value
            reject_payload(payload, 'sources先检查list类型，不能只用真假判断空值')

    def provenance():
        changes = [('mode', 'model'), ('mode', 'Mock'), ('mode', ' mock '),
                   ('source_status', 'retrieved'), ('source_status', 'unknown'),
                   ('source_status', 'not_retrieved '), ('sources', ['离线伪造来源']),
                   ('sources', [{'title': '并未检索的练习条目'}])]
        for key, value in changes:
            payload = valid()
            payload[key] = value
            reject_payload(payload, '先校验原始模式和来源；不能覆盖错误值后返回看似合法的数据')

    def text_and_whitespace():
        payload = valid('  中文\n"引号"与反斜线\\结尾  ', '\t尚未检索\n内部换行保留\n')
        reordered = dict(reversed(list(payload.items())))
        for value in (payload, reordered):
            raw = ' \r\n\t' + json.dumps(value, ensure_ascii=True) + '\n '
            result = call(raw)
            shape(result)
            expected = valid(payload['answer'].strip(), payload['uncertainty'].strip())
            require(result == expected, '接受JSON外围空白和不同键顺序，仅清理两个文本字段首尾')
            require(json.loads(json.dumps(result, ensure_ascii=False)) == result,
                    '中文、引号、内部换行及反斜线完成JSON往返后保持')

    def isolation():
        raw = json.dumps(valid(), ensure_ascii=False)
        first, second = call(raw), call(raw)
        shape(first)
        shape(second)
        require(first is not second and first['sources'] is not second['sources'],
                '每次返回独立dict和sources列表，不能复用缓存可变对象')
        first['answer'] = '被调用者修改'
        first['sources'].append('offline-source-marker')
        third = call(raw)
        require(second == valid() and third == valid(), '修改前一次结果不影响其他或后续结果')

    def previous():
        with tempfile.TemporaryDirectory(prefix='geo-history-s402-regression-') as temporary:
            directory = Path(temporary)
            for name in ('model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
                         'session_store.py', 'config.py', '.gitignore', 'pyproject.toml', 'uv.lock',
                         'STAGE3_REVIEW.md', 'stage4_structured.py'):
                require((PROJECT / name).is_file(), f'回归文件缺失：{name}')
                (directory / name).write_bytes((PROJECT / name).read_bytes())
            (directory / 'test').mkdir()
            for name in ('check_display.py', 'check_s2_03.py', 'check_s3_01.py', 'check_s3_02.py',
                         'check_s3_03.py', 'check_s3_04.py', 'check_s3_05.py', 'check_s3_06.py',
                         'check_s3_07a.py', 'check_s3_07b.py', 'check_s3_08.py',
                         'check_stage_3.py', 'check_s4_01.py'):
                (directory / 'test' / name).write_bytes((TESTS / name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(directory / 'test/check_s4_01.py')],
                cwd=directory, env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, text=True, timeout=120)
            require(result.returncode == 0 and '8/8 项通过' in result.stdout,
                    'S4-01及此前回归不能退化：\n' + (result.stdout + result.stderr)[-2800:])

    def demo():
        payload = valid('  一条离线示例  ', '  尚未调用模型或检索  ')
        raw = json.dumps(payload, ensure_ascii=False)
        print('输入JSON字符串：', raw)
        result = call(raw)
        shape(result)
        print('返回类型：', type(result).__name__)
        print('清理后正文：', result['answer'])
        forged = deepcopy(payload)
        forged['sources'] = ['没有实际检索的演示条目']
        expect_error(json.dumps(forged, ensure_ascii=False), ValueError,
                     '演示中的非法来源必须被拒绝')
        print('非法来源已拒绝：ValueError')
        print('演示未请求模型；完整验收仍需运行不带--demo的检查。')

    with patch.dict(os.environ, {}, clear=True), \
            patch('socket.socket.connect', side_effect=forbidden), \
            patch('socket.socket.connect_ex', side_effect=forbidden), \
            patch('socket.create_connection', side_effect=forbidden):
        if args.demo:
            try:
                demo()
            except Exception as error:
                print(f'演示未通过：{type(error).__name__}: {error}')
                return 1
        else:
            check('正常JSON解析为已校验的五字段dict', normal)
            check('raw非字符串抛TypeError', raw_types)
            check('非法JSON保留JSONDecodeError', syntax)
            check('合法但非对象的JSON拒绝为ValueError', top_level)
            check('缺字段及额外字段明确拒绝', fields)
            check('字段类型与空白统一业务校验', field_types)
            check('拒绝伪造模式和来源，不覆盖洗白', provenance)
            check('JSON空白、键顺序及内部文本保留', text_and_whitespace)
            check('每次返回独立字典与来源列表', isolation)
            check('S4-01及此前回归（临时工程）', previous)

    require((hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.is_file() else None) == before,
            '检查期间入口变化，请重新运行')
    if args.demo:
        return 0
    print(f'\n{sum(outcomes)}/{len(outcomes)} 项通过；源文件 {before[:8] if before else "未创建"}。')
    print('只使用内存JSON和临时回归副本；未加载.env或真实Key、未请求模型、未读取会话。')
    print('本课只验证离线解析与契约，不证明真实模型效果或事实来源。')
    return 0 if all(outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
