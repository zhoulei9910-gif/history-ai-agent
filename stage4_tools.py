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
    """S4-05：读取一次工具请求，只解析不执行工具。

    无结构化调用（tool_calls 缺失/None/空列表）返回 None；
    单次 lookup_place 调用返回 tool_call_id/tool_name/arguments 三个字段。
    全部字段用 .get 取值，缺失/类型错统一 ValueError，不泄漏 KeyError；
    arguments 原本是 JSON 字符串，语法错误保留 JSONDecodeError。
    不修改原消息、不打印、不查询目录。
    """
    # 1) 顶层必须是 dict
    if not isinstance(assistant_message, dict):
        raise TypeError("assistant_message 必须是 dict")

    # 2) role 必须精确为 assistant（` assistant `、user、tool 都拒绝）
    if assistant_message.get("role") != "assistant":
        raise ValueError("role 必须为 assistant")

    # 3) tool_calls 缺失/None/空列表 → 无调用，返回 None
    tool_calls = assistant_message.get("tool_calls")
    if tool_calls is None:
        return None
    if not isinstance(tool_calls, list):
        raise ValueError("tool_calls 必须是 list")
    if len(tool_calls) == 0:
        return None
    if len(tool_calls) != 1:
        raise ValueError("tool_calls 必须恰好一个")

    # 4) 单个 tool_call 必须是 dict
    tool_call = tool_calls[0]
    if not isinstance(tool_call, dict):
        raise ValueError("tool_call 必须是 dict")

    # 5) id 原样保留（不 strip），只校验非空白 str
    call_id = tool_call.get("id")
    if not isinstance(call_id, str) or not call_id.strip():
        raise ValueError("tool_call id 必须是非空白字符串")

    # 6) type 必须精确为 function
    if tool_call.get("type") != "function":
        raise ValueError("tool_call type 必须为 function")

    # 7) function 必须是 dict，且只允许 lookup_place 工具
    function = tool_call.get("function")
    if not isinstance(function, dict):
        raise ValueError("tool_call function 必须是 dict")
    if function.get("name") != "lookup_place":
        raise ValueError("只允许 lookup_place 工具")

    # 8) arguments 必须是 JSON 字符串；语法错误保留 JSONDecodeError
    raw_arguments = function.get("arguments")
    if not isinstance(raw_arguments, str):
        raise ValueError("arguments 必须是 JSON 字符串")
    arguments = json.loads(raw_arguments)

    # 9) 解析后必须是恰好一个非空白 name 的 dict
    if not isinstance(arguments, dict):
        raise ValueError("arguments 必须是 JSON 对象")
    if set(arguments.keys()) != {"name"}:
        raise ValueError("arguments 只能包含 name 字段")
    name = arguments["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name 必须是非空白字符串")

    # 10) 返回独立三字段 dict：id 原样、name 清理首尾
    return {
        "tool_call_id": call_id,
        "tool_name": "lookup_place",
        "arguments": {"name": name.strip()},
    }


def execute_tool_request(assistant_message: dict) -> dict | None:
    """S4-06A由学员实现：解析后执行一次本地工具，构造回传消息。

    复用parse_tool_request；无调用返回None，有调用执行lookup_place一次。
    返回role/tool_call_id/name/content；content是完整工具结果的JSON字符串。
    不调用模型、不改原消息、不打印；解析或工具异常原样传播，不重试。
    """
    raise NotImplementedError("请完成S4-06A的execute_tool_request")


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
