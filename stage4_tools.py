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
    if name is None or not isinstance(name, str):
        raise TypeError("name 必须是字符串")

    name = name.strip()
    if not name:
        raise ValueError("name 不能为空白")

    found = False
    place_search = None
    for place in PLACE_FIXTURES:
        if place["name"] == name or name in place["aliases"]:
            found = True
            place_search = deepcopy(place)

    return {
        "query": name,
        "found": found,
        "place": place_search,
        "source_status": "fixture"
    }

    # raise NotImplementedError("请完成S4-04的lookup_place")


def parse_tool_request(assistant_message: dict) -> dict | None:
    """S4-05由学员实现：读取一次工具请求，不执行工具。

    输入是完整assistant消息的dict（SDK消息可先to_dict）。无调用返回None；
    单次lookup_place调用返回tool_call_id/tool_name/arguments三个字段。
    arguments原本是JSON字符串；校验、异常和ID保留规则见学习计划。
    不修改原消息、不打印、不查询目录。保留下面已验收的CLI。
    """
    raise NotImplementedError("请完成S4-05的parse_tool_request")


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
