import os
import json
from openai import OpenAI

from config import get_api_key, get_base_url

client = OpenAI(
    api_key=get_api_key("kimi"),
    base_url=get_base_url("kimi"),
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气。",
            "parameters": {
                "type": "object",
                "required": ["city"],
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如北京",
                    }
                },
            },
        },
    }
]

stream = client.chat.completions.create(
    model="kimi-k3.1-pro",
    messages=[
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "杭州今天天气怎么样？"},
    ],
    tools=tools,
    stream=True, # <-- 开启流式输出
    stream_options={"include_usage": True}, # <-- 请求最后的 usage 数据块
)

usage = None
finish_reason = None
reasoning_content = "" # <-- 折叠后的推理内容（思考模型）
tool_calls = []        # <-- 重建后的 tool calls，每个 index 对应一条

for chunk in stream:
    chunk_usage = chunk.usage
    if chunk_usage is None and chunk.choices:
        chunk_usage = getattr(chunk.choices[0], "usage", None)
    if chunk_usage:
        usage = chunk_usage
    if not chunk.choices:
        continue

    choice = chunk.choices[0]
    delta = choice.delta
    # print(f'choice:{choice} delta: {delta}')
    if choice.finish_reason:
        finish_reason = choice.finish_reason

    # reasoning_content 先于 content 和 tool_calls 到达；SDK 类型未声明该字段，用 hasattr/getattr 读取
    if hasattr(delta, "reasoning_content"):
        reasoning_fragment = getattr(delta, "reasoning_content")
        if reasoning_fragment:
            reasoning_content += reasoning_fragment # <-- 追加，不要覆盖
            print(reasoning_fragment, end=" ")

    if delta.content:
        print(delta.content, end="")

    for tool_call in delta.tool_calls or []:
        index = tool_call.index # <-- 同一个 tool call 的片段共享相同的 index
        while len(tool_calls) <= index:
            tool_calls.append({"id": "", "type": "", "name": "", "arguments": ""})
        current = tool_calls[index]
        if tool_call.id: # <-- id、type、name 只在第一个片段出现
            current["id"] = tool_call.id
        if tool_call.type:
            current["type"] = tool_call.type
        if tool_call.function:
            if tool_call.function.name:
                current["name"] = tool_call.function.name
            if tool_call.function.arguments:
                current["arguments"] += tool_call.function.arguments # <-- 追加，不要覆盖

# finish_reason 为 "tool_calls" 时，执行工具并将 assistant 消息（含 tool_calls 和折叠后的
# reasoning_content，即 Preserved Thinking）与工具结果追加到 messages 后再次调用 API
if finish_reason == "tool_calls":
    for tool_call in tool_calls:
        arguments = json.loads(tool_call["arguments"]) # <-- 折叠完成后再解析 JSON
        print(f"\ntool_call: {tool_call['id']} {tool_call['name']}({arguments})")

if usage:
    print("\ntotal_tokens:", usage.total_tokens)