"""S4-06B：把一次工具结果回传模型续答；默认入口只预览，不读取Key。"""

import argparse
from copy import deepcopy
import json

from stage4_structured import build_structured_request, extract_response_metadata, parse_answer_json
from stage4_tools import execute_tool_request

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
    """S4-06B由学员实现：执行工具，追加完整协议，再请求一次续答。

    输入assistant_message是上一响应的完整dict；本课由假SDK消息提供。
    复用build_followup_request／execute_tool_request／parse_final_response。
    保留元数据回调的失败统计；不创建或关闭外部client、不重试、不循环。
    消息顺序、无调用与异常边界见学习计划。
    """
    raise NotImplementedError("请完成S4-06B的ask_after_tool")


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
    raise SystemExit(main())
