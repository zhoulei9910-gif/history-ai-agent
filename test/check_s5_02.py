"""S5-02关键词检索离线检查；不读取.env／会话或调用模型。

多数用例是明确标注的临时资料；实际资料仅验证接线，检索质量另行评估。
"""

import ast
from copy import deepcopy
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
OMITTED = object()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def document(identifier, title, text):
    return {"id": identifier, "title": title, "text": text,
            "source_url": "https://example.org/temporary-reference/" + identifier}


def main():
    before = {path: path.read_bytes() for path in (SOURCE, COLLECTION)}
    stamp = hashlib.sha256(before[SOURCE]).hexdigest()[:8]
    outcomes, cached = [], {}
    rows = [document("canal", "运河交通", "水利交通交通"),
            document("field", "农田水利", "灌溉与生产"),
            document("trade", "港口", "交通与贸易"),
            document("art", "宗教艺术", "雕刻")]

    def forbidden(*args, **kwargs):
        raise AssertionError("检索只处理传入内存资料，不读写文件、输入、配置或访问网络")

    @contextlib.contextmanager
    def isolated():
        with patch.dict(os.environ, {}, clear=True), \
                patch("builtins.open", side_effect=forbidden), \
                patch("io.open", side_effect=forbidden), \
                patch("builtins.input", side_effect=forbidden), \
                patch("socket.socket.connect", side_effect=forbidden), \
                patch("socket.socket.connect_ex", side_effect=forbidden), \
                patch("socket.create_connection", side_effect=forbidden):
            yield

    def module():
        if "module" not in cached:
            allowed = {"argparse", "json", "pathlib", "sys", "urllib.parse"}
            for node in ast.walk(ast.parse(before[SOURCE])):
                if isinstance(node, ast.Import):
                    require(all(item.name in allowed for item in node.names), "本课使用已有标准库，不接SDK或配置")
                if isinstance(node, ast.ImportFrom):
                    require(node.level == 0 and node.module in allowed, "本课保留独立标准库入口")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    require(node.func.id not in {"__import__", "eval", "exec", "compile"}, "资料仅作为数据")
            spec = importlib.util.spec_from_file_location("stage5_search_lesson", SOURCE)
            candidate = importlib.util.module_from_spec(spec)
            output, errors = io.StringIO(), io.StringIO()
            with isolated(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                spec.loader.exec_module(candidate)
            require(not output.getvalue() and not errors.getvalue(), "导入时不运行CLI或打印")
            require(callable(getattr(candidate, "search_documents", None)), "保留search_documents")
            cached["module"] = candidate
        return cached["module"]

    def call(documents, query, top_k=OMITTED):
        function = module().search_documents
        output, errors = io.StringIO(), io.StringIO()
        with isolated(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = function(documents, query) if top_k is OMITTED else function(documents, query, top_k)
        require(not output.getvalue() and not errors.getvalue(), "检索函数只返回数据，展示交给CLI")
        return result

    def rejects(query, top_k=OMITTED, expected=ValueError):
        try:
            call([], query, top_k)
        except expected:
            return
        raise AssertionError(f"空资料集也应先校验参数，抛{expected.__name__}")

    def hits(result):
        require(isinstance(result, list), "返回list，无命中返回[]")
        for item in result:
            require(isinstance(item, dict) and set(item) == {"id", "title", "text", "source_url", "score"},
                    "每项保留原四字段并增加score")
            require(type(item["score"]) is int and item["score"] > 0, "score须为正整数")
        return [(item["id"], item["score"]) for item in result]

    def single():
        require(hits(call(deepcopy(rows), "水利")) == [("canal", 1), ("field", 1)],
                "标题或正文命中都算；同一词出现多次仍只得1分")

    def multiple():
        expected = [("canal", 2), ("field", 1), ("trade", 1)]
        require(hits(call(deepcopy(rows), " \n水利\t交通 水利  ")) == expected,
                "按空白分词并去重；命中任一词即可入选，分数是不同词数量")

    def casefold():
        data = [document("case", "RIVER", "Straße与交通")]
        require(hits(call(data, "river STRASSE")) == [("case", 2)], "查询与资料均用casefold，不只改查询")
        require(call(data, "RIVER！") == [], "本课不去标点或做同义词扩展，不偷换匹配规则")

    def order():
        data = [deepcopy(rows[2]), deepcopy(rows[1]), deepcopy(rows[0])]
        require(hits(call(data, "交通 水利", 10)) == [("canal", 2), ("trade", 1), ("field", 1)],
                "按分数降序；同分保持资料输入顺序，不按id重排")
        require(hits(call(data, "交通 水利", 1)) == [("canal", 2)], "排序后再限制top_k")

    def limits():
        data = [document(str(i), "水利", "临时测试资料") for i in range(5)]
        require(hits(call(data, "水利")) == [("0", 1), ("1", 1), ("2", 1)], "默认top_k=3")
        require(len(call(data, "水利", 9)) == 5, "top_k超过命中数时不填充假结果")
        for value in (True, False, None, "3", 1.5, []):
            rejects("水利", value, TypeError)
        for value in (0, -1):
            rejects("水利", value, ValueError)

    def inputs():
        for value in (None, False, 1, b"river", [], {}):
            rejects(value, expected=TypeError)
        for value in ("", " \n\t "):
            rejects(value)

    def empty():
        require(call([], "水利") == [], "空资料集返回[]")
        require(call(deepcopy(rows), "不存在的检索词") == [], "无命中不退回第一条、不猜答案")

    def scope():
        data = [document("secret-id", "青", "山")]
        data[0]["source_url"] = "https://example.org/secret-url"
        for query in ("secret-id", "secret-url", "青山"):
            require(call(data, query) == [], "只搜title/text，换行隔开，不搜id/URL或拼接出跨字段关键词")

    def isolation():
        data = deepcopy(rows)
        original = deepcopy(data)
        first = call(data, "交通 水利")
        require(data == original, "不能给原资料加score或重排输入")
        hits(first)
        originals = {item["id"]: item for item in original}
        for item in first:
            require({key: item[key] for key in originals[item["id"]]} == originals[item["id"]],
                    "完整保留标题、正文和来源，不生成或改写内容")
            require(all(item is not source for source in data), "命中项必须是新的dict")
        first[0]["title"] = "调用方修改"
        first[0]["score"] = 999
        first.append(document("extra", "额外", "额外"))
        require(data == original and hits(call(data, "交通 水利")) == [("canal", 2), ("field", 1), ("trade", 1)],
                "调用方修改返回值不能影响资料或后续检索")

    def cli():
        with tempfile.TemporaryDirectory(prefix="geo-history-s502-cli-") as temporary:
            target = Path(temporary)
            entry = target / SOURCE.name
            entry.write_bytes(before[SOURCE])
            (target / COLLECTION.name).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}

            def run(*args):
                return subprocess.run([sys.executable, "-B", str(entry), *args], cwd=target, env=env,
                                      capture_output=True, text=True, timeout=15)

            good = run("--query", "水利 交通", "--top-k", "2")
            require(good.returncode == 0 and not good.stderr and hits(json.loads(good.stdout)) == [("canal", 2), ("field", 1)],
                    "CLI查询返回限定数量的JSON结果，保留来源并退出0")
            miss = run("--query", "不存在的检索词")
            require(miss.returncode == 0 and json.loads(miss.stdout) == [], "CLI无命中是正常空结果，退出0")
            for args in (("--query", "  "), ("--query", "水利", "--top-k", "0")):
                failed = run(*args)
                require(failed.returncode == 1 and not failed.stdout and "资料检索失败" in failed.stderr,
                        "CLI空白查询／非正top_k明确失败，退出1")

    def regression():
        result = subprocess.run([sys.executable, "-B", str(PROJECT / "test/check_s5_01.py")], cwd=PROJECT,
                                env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
                                capture_output=True, text=True, timeout=420)
        require(result.returncode == 0 and "10/10 项通过" in result.stdout,
                "S5-01加载与此前已验收请求配置／程序整链必须保持：\n" + (result.stdout + result.stderr)[-1800:])

    def check(title, action):
        try:
            action()
        except Exception as error:
            outcomes.append(False)
            print(f"未通过｜{title}：{type(error).__name__}: {error}")
        else:
            outcomes.append(True)
            print(f"通过  ｜{title}")

    for title, action in [
        ("独立入口与导入无副作用", module), ("单词标题／正文命中", single),
        ("空白分词、去重与不同词计分", multiple), ("casefold及明确的匹配边界", casefold),
        ("分数降序与同分顺序", order), ("top_k默认、截取与非法值", limits),
        ("查询类型与空白拒绝", inputs), ("空资料／无命中不补假答案", empty),
        ("只检索标题正文且不跨字段拼词", scope), ("结果保留来源并与输入隔离", isolation),
        ("CLI查询、无命中及错误码", cli), ("S5-01的10项及此前整链回归", regression),
    ]:
        check(title, action)
    require({path: path.read_bytes() for path in before} == before, "检查过程中代码或资料变化，请重跑")
    print(f"\n{sum(outcomes)}/{len(outcomes)} 项通过；入口源码 {stamp}。")
    print("离线检查只证明约定的关键词程序行为；分数不表示答案正确率或来源可信度。")
    print("未读.env／真实Key或会话，未请求模型、抓网页或改写资料。")
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
