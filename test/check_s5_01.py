"""S5-01离线检查：资料加载、字段校验、CLI和阶段4回归。

只读声明的代码／报告／资料及临时用例，不读.env或实际会话，不请求模型。
资料的URL与文字是否相互支持，必须由导师另外人工核对。
"""

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT / "stage5_retrieval.py"
COLLECTION = PROJECT / "knowledge_sources.json"
BASE = {"id": "doc-a", "title": "临时测试标题", "text": "临时资料，不是史实。",
        "source_url": "https://example.org/reference/a"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    before = {path: path.read_bytes() for path in (SOURCE, COLLECTION)}
    stamp = hashlib.sha256(before[SOURCE]).hexdigest()[:8]
    outcomes = []
    cached = {}
    readable = {COLLECTION.resolve()}
    original_open = io.open

    def guarded_open(file, mode="r", *args, **kwargs):
        require(not isinstance(file, int) and Path(file).resolve() in readable,
                "加载器只能读取当前用例的资料文件，不能读取配置或会话")
        require(mode in {"r", "rt", "rb"}, "加载器不能写文件")
        return original_open(file, mode, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("本课不读取终端、环境配置或访问网络")

    @contextlib.contextmanager
    def isolated():
        with patch.dict(os.environ, {}, clear=True), \
                patch("builtins.open", side_effect=guarded_open), \
                patch("io.open", side_effect=guarded_open), \
                patch("builtins.input", side_effect=forbidden), \
                patch("socket.socket.connect", side_effect=forbidden), \
                patch("socket.socket.connect_ex", side_effect=forbidden), \
                patch("socket.create_connection", side_effect=forbidden):
            yield

    def module():
        if "module" not in cached:
            tree = ast.parse(before[SOURCE])
            allowed = {"argparse", "json", "pathlib", "sys", "urllib.parse"}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    require(all(item.name in allowed for item in node.names),
                            "本课只用提供的标准库，不导入配置、SDK或旧阶段入口")
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in allowed, "本课只用提供的标准库")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {"__import__", "eval", "exec", "compile"},
                            "资料作为数据读取，不动态执行")
            spec = importlib.util.spec_from_file_location("stage5_lesson", SOURCE)
            candidate = importlib.util.module_from_spec(spec)
            output, errors = io.StringIO(), io.StringIO()
            with isolated(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                spec.loader.exec_module(candidate)
            require(not output.getvalue() and not errors.getvalue(), "导入时不运行CLI或打印")
            require(callable(getattr(candidate, "load_documents", None)), "保留load_documents入口")
            cached["module"] = candidate
        return cached["module"]

    def call(path):
        candidate = module()
        output, errors = io.StringIO(), io.StringIO()
        with isolated(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = candidate.load_documents(path)
        require(not output.getvalue() and not errors.getvalue(), "load_documents只返回，不打印")
        return result

    def rejects(path, expected=ValueError):
        try:
            call(path)
        except expected:
            return
        raise AssertionError(f"应抛出{expected.__name__}，不能返回空列表或伪造成功")

    def check(title, action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f"未通过｜{title}：{type(error).__name__}: {error}")
        else:
            outcomes.append(True)
            print(f"通过  ｜{title}")

    with tempfile.TemporaryDirectory(prefix="geo-history-s501-check-") as temporary:
        directory = Path(temporary)
        counter = 0

        def fixture(value=None, *, text=None):
            nonlocal counter
            counter += 1
            path = directory / f"case-{counter}.json"
            path.write_text(text if text is not None else json.dumps(value, ensure_ascii=False), encoding="utf-8")
            readable.add(path.resolve())
            return path

        def valid():
            row = {key: f" \n{value}\t " for key, value in BASE.items()}
            second = {**BASE, "id": "doc-b", "text": "另一条中文资料。"}
            require(call(fixture([row, second])) == [BASE, second],
                    "返回清理后的中文资料；四字段都应保存strip结果，不硬编码示例")
            changed = {**BASE, "id": "other", "title": "新的标题", "source_url": "https://example.org/b?q=1#intro"}
            require(call(fixture([changed])) == [changed], "不同文件的内容不能串用或缓存成固定答案")

        def empty():
            require(call(fixture([])) == [], "空资料集合法，返回[]，不能补假资料")

        def structure():
            for value in ({"documents": [BASE]}, None, "text", [None], ["text"], [[]],
                          [{key: val for key, val in BASE.items() if key != "source_url"}],
                          [{**BASE, "extra": "unexpected"}]):
                rejects(fixture(value))

        def fields():
            for key in BASE:
                for value in (None, False, 7, [], {}, " \n\t "):
                    rejects(fixture([{**BASE, key: value}]))
            for url in ("http://example.org/a", "https://", "https://example.org/a b", "not-a-url"):
                rejects(fixture([{**BASE, "source_url": url}]))

        def duplicate():
            rejects(fixture([BASE, {**BASE, "id": " doc-a "}]))
            rows = [BASE, {**BASE, "id": "doc-b"}]
            require(call(fixture(rows)) == rows, "id应唯一；同一出处可以有多个独立条目")

        def failures():
            rejects(fixture(text="["), ValueError)
            missing = directory / "missing.json"
            readable.add(missing.resolve())
            rejects(missing, FileNotFoundError)
            readable.add(directory.resolve())
            rejects(directory, IsADirectoryError)

        def collection():
            raw = json.loads(before[COLLECTION])
            require(isinstance(raw, list) and len(raw) >= 2,
                    "当前资料集至少2条：保留导师示例，再自行增加1条真实来源的中文概述")
            loaded = call(COLLECTION)
            require(isinstance(loaded, list) and len(loaded) == len(raw), "实际资料不能被悄悄丢弃")
            require(all(len(row["text"]) >= 30 for row in loaded), "每条中文概述至少30字符；支持程度另做人工核对")

        def cli():
            target = directory / "cli"
            target.mkdir()
            entry = target / SOURCE.name
            entry.write_bytes(before[SOURCE])
            (target / COLLECTION.name).write_text(json.dumps([BASE], ensure_ascii=False), encoding="utf-8")
            env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
            good = subprocess.run([sys.executable, "-B", str(entry)], cwd=target, env=env,
                                  capture_output=True, text=True, timeout=15)
            require(good.returncode == 0 and not good.stderr and json.loads(good.stdout) == [BASE],
                    "默认CLI应输出一份JSON列表并退出0")
            bad = fixture(text="{")
            failed = subprocess.run([sys.executable, "-B", str(entry), str(bad)], cwd=target, env=env,
                                    capture_output=True, text=True, timeout=15)
            require(failed.returncode == 1 and not failed.stdout and "资料加载失败" in failed.stderr
                    and "Traceback" not in failed.stderr, "非法资料应明确提示并退出1，不输出假结果")

        def regression():
            result = subprocess.run([sys.executable, "-B", str(PROJECT / "test/check_stage_4.py")],
                                    cwd=PROJECT, env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
                                    capture_output=True, text=True, timeout=360)
            require(result.returncode == 0 and "4/4 项通过" in result.stdout,
                    "阶段4已验收的报告／请求参数／程序整链需保持：\n" + (result.stdout + result.stderr)[-1600:])

        for title, action in [
            ("独立标准库入口，导入无副作用", module),
            ("UTF-8中文、字段清理与不同文件", valid),
            ("空资料集不补假数据", empty),
            ("顶层与条目四字段结构", structure),
            ("字段类型、空白与来源URL", fields),
            ("清理后id唯一，允许同出处多条资料", duplicate),
            ("坏JSON及文件错误保持失败", failures),
            ("本地至少两条有来源的资料（内容待人工核对）", collection),
            ("CLI正常0／错误1", cli),
            ("阶段4汇总4/4及此前回归", regression),
        ]:
            check(title, action)

    require({path: path.read_bytes() for path in before} == before, "检查过程中源文件或资料变化，请重跑")
    print(f"\n{sum(outcomes)}/{len(outcomes)} 项通过；入口源码 {stamp}。")
    print("离线检查只验证程序与资料格式；来源支持程度、历史事实和学习理解由导师另外审阅。")
    print("未读.env／真实Key或会话，未请求模型、联网核验或改写资料。")
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
