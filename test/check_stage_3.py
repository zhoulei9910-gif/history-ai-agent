"""S3-09：汇总离线回归与阶段报告格式；不自动判定模型质量或学员理解。"""

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parent.parent
REPORT = PROJECT / 'STAGE3_REVIEW.md'
SNAPSHOT_FILES = (
    'model_demo_ask_turn.py', 'IncompleteStreamError.py', 'conversation.py',
    'session_store.py', 'config.py', 'pyproject.toml', 'uv.lock',
)
SCENARIOS = {
    '多轮追问': ('test/check_s3_02.py',),
    '窗口裁剪': ('test/check_s3_03.py',),
    '保存恢复': ('test/check_s3_04.py', 'test/check_s3_05.py'),
    '流式中断': ('test/check_s3_08.py',),
}


def snapshot():
    digest = hashlib.sha256()
    for name in SNAPSHOT_FILES:
        digest.update(name.encode())
        digest.update(b'\0')
        digest.update((PROJECT / name).read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()[:8]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_report():
    require(REPORT.is_file(), '请创建 STAGE3_REVIEW.md，按学习计划填写阶段评估')
    return REPORT.read_text(encoding='utf-8')


def section(text, title):
    match = re.search(r'^##\s+' + re.escape(title) + r'\s*$', text, re.M)
    require(match is not None, f'报告需有二级标题：## {title}')
    content = text[match.end():]
    next_heading = re.search(r'^##\s+', content, re.M)
    return content[:next_heading.start()] if next_heading else content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--program-only', action='store_true', help='只复跑程序，不检查阶段报告')
    args = parser.parse_args()
    before = snapshot()
    print(f'版本指纹：{before}（业务模块与依赖文件，不读取.env）', flush=True)
    results = []

    def check(title, action):
        try:
            action()
        except Exception as error:
            results.append(False)
            print(f'未通过｜{title}：{type(error).__name__}: {error}')
        else:
            results.append(True)
            print(f'通过  ｜{title}')

    def program():
        result = subprocess.run(
            [sys.executable, str(PROJECT / 'test/check_s3_08.py')],
            cwd=PROJECT,
            env={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
            capture_output=True, text=True, timeout=90,
        )
        require(result.returncode == 0,
                'S3-08及此前回归未通过：\n' + (result.stdout + result.stderr)[-3200:])
        require('12/12 项通过' in result.stdout, '应保留S3-08完整12项及其旧回归')
        print('      S3-08：12/12，退出码0；其中包含此前课程回归。')

    def report_version():
        text = section(read_report(), '自动检查')
        require(re.search(r'版本指纹\s*[:：]\s*`?' + re.escape(before) + r'`?\b', text),
                f'在“自动检查”填写本次版本指纹：{before}；业务或依赖变更后应重新评估')
        require('test/check_stage_3.py' in text, '记录实际运行命令 test/check_stage_3.py')
        require(re.search(r'程序检查\s*[:：]\s*12/12', text) and
                re.search(r'退出码\s*[:：]?\s*0', text),
                '按实际输出记录“程序检查：12/12，退出码0”；不是模型质量得分')

    def report_evidence():
        report = read_report()
        text = section(report, '验证范围')
        rows = {}
        for line in text.splitlines():
            if line.lstrip().startswith('|'):
                cells = [cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]
                if cells and cells[0] in SCENARIOS:
                    require(cells[0] not in rows, f'{cells[0]}不要重复记录')
                    rows[cells[0]] = cells
        for name, evidence in SCENARIOS.items():
            require(name in rows, f'验证范围表缺少“{name}”')
            cells = rows[name]
            require(len(cells) == 4, f'{name}需要四列：场景、离线证据、能确认、不能确认')
            require(any(path in cells[1] for path in evidence),
                    f'{name}需引用相关检查脚本：' + ' 或 '.join(evidence))
            for cell in cells[2:]:
                require(len(cell) >= 8 and not any(marker in cell for marker in
                        ('TODO', '待填写', '待补充', '...', '……')),
                        f'{name}的结论与局限请用自己的话填写，不能只留占位')
        real = section(report, '真实验证')
        for label, value in (('本课新增真实调用', '0'), ('真实模型效果', '待验证'), ('实际费用', '未知')):
            require(re.search(re.escape(label) + r'\s*[:：]\s*' + re.escape(value), real),
                    f'本课不新增真实调用，请据证据记录“{label}：{value}”')
        require('E12' in real and 'E13' in real, '引用EVAL_CASES.md中的E12/E13，说明当前证据缺口')
        understanding = section(report, '我的理解').strip()
        require(len(understanding) >= 30 and not any(marker in understanding for marker in
                ('TODO', '待填写', '待补充', '...', '……')),
                '用自己的话说明：为什么程序检查通过仍不能证明真实多轮回答质量')

    check('阶段程序回归：复用S3-08及此前检查', program)
    if not args.program_only:
        check('报告记录运行命令、程序结果及当前版本', report_version)
        check('报告有证据矩阵、真实验证状态及个人解释', report_evidence)
    require(snapshot() == before, '检查期间业务或依赖变化，请重新运行并更新报告版本')
    print(f'\n{sum(results)}/{len(results)} 项通过。')
    print('仅离线检查；无真实模型请求。报告检查只验证结构和版本，解释与质量结论仍需导师审阅。')
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
