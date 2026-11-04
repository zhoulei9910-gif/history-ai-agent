"""阶段5独立入口：S5-01先加载资料，关键词检索留给下一课。"""

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
    raise NotImplementedError("S5-01：请实现load_documents")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", nargs="?", type=Path,
        default=Path(__file__).with_name("knowledge_sources.json"),
        help="本地UTF-8资料JSON；默认读取本入口旁的knowledge_sources.json",
    )
    args = parser.parse_args()
    try:
        documents = load_documents(args.path)
    except (OSError, ValueError, NotImplementedError) as error:
        print(f"资料加载失败：{error}", file=sys.stderr)
        return 1
    print(json.dumps(documents, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
