"""S4-04：确定性地名查询工具。条目均为虚构教学数据，不是历史资料。"""

import argparse
from copy import deepcopy
import json

# 导师提供的固定目录；描述只是练习设定，不对应真实地名或史实。
PLACE_FIXTURES = [
    {
        "name": "青岚城",
        "aliases": ["青岚"],
        "description": "教学用虚构山城，不对应真实地点。",
    },
    {
        "name": "赤川镇",
        "aliases": ["赤川"],
        "description": "教学用虚构河谷城镇，不对应真实地点。",
    },
]


def lookup_place(name: str) -> dict:
    """S4-04由学员实现：清理名称，精确匹配目录，返回独立工具结果。

    四字段query/found/place/source_status及输入、未命中规则见学习计划。
    不调用模型，不打印、读文件、模糊匹配或补造未知条目。
    """
    raise NotImplementedError("请完成S4-04的lookup_place")


def main(argv=None) -> int:
    """导师提供的离线入口，只展示一次工具结果。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="目录名称或别名，仅精确匹配")
    args = parser.parse_args(argv)
    try:
        result = lookup_place(args.name)
    except (TypeError, ValueError):
        print("地名必须是非空字符串。")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
