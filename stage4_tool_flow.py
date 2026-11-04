"""S4-06B：把一次工具结果回传模型续答；默认入口只预览，不读取Key。"""

import argparse
from copy import deepcopy
import json

from stage4_structured import build_structured_request, extract_response_metadata, parse_answer_json
from stage4_tools import execute_tool_request, lookup_place

# 导师提供的工具描述；它向API描述能力，不会执行Python函数。
LOOKUP_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_place",
        "description": "精确查询虚构教学地名目录；条目不是现实地理历史资料。",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "目录标准名或别名"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
}


def build_followup_request(question: str) -> dict:
    """导师提供：沿用已验收的结构化请求预算，准备续答基础参数。"""
    request = build_structured_request(question)
    request["messages"][0]["content"] += (
        "\nlookup_place只查询虚构教学目录，source_status=fixture不是真实史料来源。"
        "回答引用该目录时明确说明虚构设定；未收录不代表现实不存在。"
        "最终回答仍用五字段JSON，source_status=not_retrieved、sources=[]。"
    )
    request["tools"] = [deepcopy(LOOKUP_TOOL)]
    request["tool_choice"] = "none"
    # print("return request = %s" % json.dumps(request, ensure_ascii=False, indent=2) )
    return request


def parse_final_response(response) -> dict:
    """导师提供：沿用旧课包络与五字段校验，续答必须正常结束。"""
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("续答必须恰好一个choice")
    choice = choices[0]
    if getattr(choice, "finish_reason", None) != "stop":
        raise ValueError("续答必须stop结束，不继续执行工具")
    message = getattr(choice, "message", None)
    if getattr(message, "role", None) != "assistant":
        raise ValueError("续答必须是assistant消息")
    calls = getattr(message, "tool_calls", None)
    if calls is not None and (not isinstance(calls, list) or calls):
        raise ValueError("续答不应包含新工具调用")
    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("续答正文必须是非空白字符串")
    return parse_answer_json(content, expected_mode="model")


def ask_after_tool(client, question: str, assistant_message: dict, *, on_metadata=None) -> dict:
    """S4-06B：执行工具，追加完整协议，再请求一次续答。

    先校验 question 和 on_metadata；执行一次工具并把完整 assistant
    （深拷贝）与 tool 结果追加到请求后，请求一次续答并返回已校验答案。
    不创建/关闭外部 client、不重试、不循环；异常原样传播。
    """
    # 1) 构造续答基础请求（内部完成 question 的类型/空白校验）
    request = build_followup_request(question)
    # print(f" request: {request}")

    # 2) on_metadata 非 None 时必须是可调用对象（在工具执行和 SDK 请求之前）
    if on_metadata is not None and not callable(on_metadata):
        raise TypeError("on_metadata 必须是可调用对象或 None")

    # 3) 执行一次工具；无有效调用抛 ValueError，零 SDK 请求
    tool_message = execute_tool_request(assistant_message)

    if tool_message is None:
        raise ValueError("本续答函数需要已有工具调用")

    # 4) 追加完整 assistant（深拷贝）和 tool 结果，顺序 system → user → assistant → tool
    request["messages"].append(deepcopy(assistant_message))
    request["messages"].append(tool_message)

    # 5) 请求一次续答；SDK 异常原样传播，无响应不通知元数据
    response = client.chat.completions.create(**request)

    # 6) 收到响应后，先通知元数据，再校验回答
    if on_metadata is not None:
        on_metadata(extract_response_metadata(response))

    # 7) 返回已校验的五字段续答
    return parse_final_response(response)


def build_initial_tool_request(question: str) -> dict:
    """导师提供：首轮只提出工具请求，不要求输出最终答案JSON。"""
    request = build_followup_request(question)
    request.pop("response_format")
    request["tool_choice"] = "required"
    request["messages"][0]["content"] = (
        "你是中文地理历史助手。本流程查询虚构教学目录，不提供真实史料。"
        "本轮先根据用户问题提取要查询的地名，提出一次lookup_place调用。"
        "只允许一个调用；不要补造目录结果或把虚构条目当史实。"
        "后续步骤会执行工具并生成最终回答。"
    )
    return request


def read_tool_call_response(response) -> dict:
    """导师提供：校验首轮包络，保留完整SDK消息；参数由旧执行器校验。"""
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("首轮响应必须恰好一个choice")
    choice = choices[0]
    if getattr(choice, "finish_reason", None) != "tool_calls":
        raise ValueError("本固定流程首轮需要tool_calls，不接受直接答案")
    message = getattr(choice, "message", None)
    convert = getattr(message, "to_dict", None)
    if not callable(convert):
        raise ValueError("首轮message必须是可转dict的SDK消息")
    data = convert()
    if not isinstance(data, dict) or data.get("role") != "assistant":
        raise ValueError("首轮必须是assistant消息")
    calls = data.get("tool_calls")
    if not isinstance(calls, list) or not calls:
        raise ValueError("首轮需要非空tool_calls列表")
    return deepcopy(data)


def ask_with_tool(client, question: str, *, on_metadata=None) -> dict:
    """S4-06C：首轮让模型提出工具调用，再复用 ask_after_tool 执行并续答。

    固定两步流程：
    1) 首轮请求（tool_choice=required）让模型给出 lookup_place 调用；
    2) 提取完整 assistant 消息后，委托 ask_after_tool 执行工具并续答。

    首轮收到响应先通知元数据，再提取消息；on_metadata 沿两次调用透传。
    不在此直接执行工具、不循环；外部 client 不在此创建或关闭，异常原样传播。
    """
    # 1) 构造首轮请求（tool_choice=required），内部完成 question 校验
    request = build_initial_tool_request(question)

    # 2) on_metadata 非 None 时必须可调用（在两次 SDK 请求之前）
    if on_metadata is not None and not callable(on_metadata):
        raise TypeError("on_metadata 必须是可调用对象或 None")

    # 3) 首轮请求：SDK 异常原样传播，无响应不通知元数据
    response = client.chat.completions.create(**request)

    # 4) 收到首轮响应后，先通知一次元数据，再提取完整 assistant 消息
    if on_metadata is not None:
        on_metadata(extract_response_metadata(response))

    # 5) 把完整 assistant（含 tool_calls）交给 B 执行工具并续答，直接返回其结果
    assistant_message = read_tool_call_response(response)
    return ask_after_tool(client, question, assistant_message, on_metadata=on_metadata)


def main(argv=None) -> int:
    """导师提供：只预览基础参数，调用消息和工具结果由ask_after_tool追加。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="原始问题；此入口不请求模型")
    args = parser.parse_args(argv)
    try:
        request = build_followup_request(args.question)
    except (TypeError, ValueError):
        print("问题必须是非空字符串。")
        return 1
    print("续答基础参数预览｜尚未追加assistant/tool｜未读取Key、未发送请求")
    print(json.dumps(request, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    # main()
    raise SystemExit(main())
