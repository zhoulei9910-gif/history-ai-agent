"""阶段5独立入口：资料加载与关键词检索基线。"""

import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit


def is_https_source(value: str) -> bool:
    """导师提供的URL格式检查；不联网，也不证明页面内容正确。"""
    try:
        parts = urlsplit(value)
        return (
            parts.scheme == "https"
            and bool(parts.hostname)
            and parts.username is None
            and parts.password is None
            and not any(char.isspace() for char in value)
        )
    except ValueError:
        return False


def load_documents(path: Path) -> list[dict[str, str]]:
    """学员实现：UTF-8读取JSON，验证后返回清理过的资料列表。

    契约：
    - 顶层必须是list；空列表合法，返回[]。
    - 每项必须是dict，恰好包含id/title/text/source_url四字段。
    - 四字段均为str；保存strip结果，清理后不得为空。
    - 清理后的id不可重复；同一source_url可对应多条资料。
    - source_url须通过已提供的is_https_source。
    - 内容错误抛ValueError；文件错误保留OSError子类，不返回假成功。
    - 函数只读取传入文件并返回数据，不打印、不联网、不写文件。
    """
    records = []
    with path.open("r", encoding="utf-8") as fp:
        records = json.load(fp)
        if not isinstance(records, list):
            raise ValueError("顶层必须是 list")
        # print(records[1]["title"])

    seen_ids = set()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("记录必须是 dict 类型")
        if set(record.keys()) != {"id", "title", "text", "source_url"}:
            raise ValueError("必须包含id/title/text/source_url四字段四个字段")
        if not isinstance(record["id"], str) or not record["id"].strip():
            raise ValueError("id 必须为str 类型，且不为空")
        if not isinstance(record["title"], str) or not record["title"].strip():
            raise ValueError("title 必须为str 类型，且不为空")
        if not isinstance(record["text"], str) or not record["text"].strip():
            raise ValueError("text 必须为str 类型，且不为空")
        if not isinstance(record["source_url"], str) or not record["source_url"]:
            raise ValueError("source_url 必须为str 类型，且不为空")

        record["id"] = record["id"].strip()
        record["title"] = record["title"].strip()
        record["text"] = record["text"].strip()
        record["source_url"] = record["source_url"].strip()

        if not is_https_source(record["source_url"]):
            raise ValueError("source_url 不合法")

        if record["id"] in seen_ids:
            raise ValueError("id 不能重复")
        seen_ids.add(record["id"])

    return records
    # raise NotImplementedError("S5-01：请实现load_documents")


def search_documents(documents: list[dict[str, str]], query: str, top_k: int = 3) -> list[dict]:
    """S5-02由学员实现：按不同关键词的命中数量返回前top_k条资料。

    输入documents已经过load_documents校验，本函数不再加载文件。
    - query须为str，否则TypeError；清理后空白则ValueError。
    - top_k须为正整数；非int（包括bool）TypeError，0或负数ValueError。
      即使documents为空，也先验证上述参数。
    - query.casefold().split()按空白分词，并去除重复词。
      中文须显式用空格分开关键词，本课不做自然语言分词或同义词匹配。
    - 只在title和text中做大小写无关的子串匹配，两字段用换行分隔。
    - 每命中一个不同关键词得1分；同一词在正文重复不加分。
      命中任一词即可进入结果，得分0的资料排除。
    - 每项为原四字段加int类型score，返回新的dict，不修改输入。
    - 按score降序，分数相同保留输入先后顺序，最多返回top_k项。
    - 空资料集或无命中返回[]；不打印、不读写文件、不请求模型或补假答案。
    """
    raise NotImplementedError("S5-02：请实现search_documents")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", nargs="?", type=Path,
        default=Path(__file__).with_name("knowledge_sources.json"),
        help="本地UTF-8资料JSON；默认读取本入口旁的knowledge_sources.json",
    )
    parser.add_argument("--query", help="空格分隔的关键词；省略时仅加载资料")
    parser.add_argument("--top-k", type=int, default=3, help="检索最多返回条数，默认3")
    args = parser.parse_args()
    try:
        documents = load_documents(args.path)
    except (OSError, ValueError, NotImplementedError) as error:
        print(f"资料加载失败：{error}", file=sys.stderr)
        return 1
    if args.query is not None:
        try:
            documents = search_documents(documents, args.query, args.top_k)
        except (TypeError, ValueError, NotImplementedError) as error:
            print(f"资料检索失败：{error}", file=sys.stderr)
            return 1
    print(json.dumps(documents, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    # main()
    raise SystemExit(main())
