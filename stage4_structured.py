"""阶段4独立学习入口：S4-01离线结构化数据，不调用模型。"""

import json


def make_mock_answer(answer: str, uncertainty: str) -> dict:
    """S4-01由学员实现：校验两个文本参数，返回约定的模拟回答字典。

    字段、输入规则与验收命令见LEARNING_PLAN.md的S4-01。
    只构造数据，不打印、不请求模型、不读写文件。
    """
    # 1) 先类型：两个参数都必须是 str
    if not isinstance(answer, str) or not isinstance(uncertainty, str):
        raise TypeError("answer 和 uncertainty 必须是 str")

    # 2) 再空白：strip 后为空才拒绝
    answer = answer.strip()
    uncertainty = uncertainty.strip()
    if not answer or not uncertainty:
        raise ValueError("answer 和 uncertainty 不能为空")

    # 3) 固定五字段
    return {
        "mode": "mock",
        "answer": answer,
        "uncertainty": uncertainty,
        "source_status": "not_retrieved",
        "sources": [],
    }


def parse_answer_json(raw: str, *, expected_mode: str = "mock") -> dict:
    """解析JSON并校验回答契约，返回规范化dict。

    expected_mode 为仅关键字参数，默认 mock 保持旧调用兼容；
    校验时要求原始 mode 与 expected_mode 完全一致，不覆盖洗白。
    语法错误保留 JSONDecodeError，业务结构错误统一抛 ValueError。
    """
    # 1) raw 必须是 str
    if not isinstance(raw, str):
        raise TypeError("raw 必须是 str")

    # 2) expected_mode 先验类型，再验取值（不 strip、精确匹配）
    if not isinstance(expected_mode, str):
        raise TypeError("expected_mode 必须是 str")
    if expected_mode not in ("mock", "model"):
        raise ValueError("expected_mode 只能是 mock 或 model")

    # 3) 解析 JSON：语法错误保留 json.JSONDecodeError，不捕获
    data = json.loads(raw)

    # 4) 顶层必须是对象（dict）
    if not isinstance(data, dict):
        raise ValueError("顶层必须是 JSON 对象")

    # 5) 恰好五个字段，缺字段或多余字段都拒绝
    if set(data.keys()) != {"mode", "answer", "uncertainty", "source_status", "sources"}:
        raise ValueError("字段必须恰好为 mode/answer/uncertainty/source_status/sources")

    # 6) 四个文本字段都必须是 str
    for key in ("mode", "answer", "uncertainty", "source_status"):
        if not isinstance(data[key], str):
            raise ValueError(f"{key} 必须是 str")

    # 7) answer / uncertainty 清理首尾空白后必须非空
    answer = data["answer"].strip()
    uncertainty = data["uncertainty"].strip()
    if not answer or not uncertainty:
        raise ValueError("answer 和 uncertainty 不能为空")

    # 8) sources 先验 list 类型，再验必须为空（不能 `not sources` 判断）
    sources = data["sources"]
    if not isinstance(sources, list):
        raise ValueError("sources 必须是 list")
    if sources:
        raise ValueError("sources 必须为空列表")

    # 9) mode 必须与 expected_mode 精确一致，source_status 固定 not_retrieved
    if data["mode"] != expected_mode:
        raise ValueError(f"mode 必须为 {expected_mode}")
    if data["source_status"] != "not_retrieved":
        raise ValueError("source_status 必须为 not_retrieved")

    # 10) 返回规范化后的新 dict（保留原始 mode，不硬编码）
    return {
        "mode": data["mode"],
        "answer": answer,
        "uncertainty": uncertainty,
        "source_status": "not_retrieved",
        "sources": [],
    }


def build_structured_request(question: str) -> dict:
    """S4-03A：仅构造Kimi JSON Mode请求参数，不发送请求。

    输入、六个请求字段及提示词要求见LEARNING_PLAN.md。
    返回内存dict；不打印、不加载配置、不调用SDK或解析回答。
    """
    if not isinstance(question, str):
        raise TypeError("question 必须是 str")

    question = question.strip()
    if not question:
        raise ValueError("question 不能为空")

    system_prompt = """你是一名中文历史地理问答助手。每次回答只输出一个 JSON 对象，不要输出代码围栏（如 ```json），不要输出任何解释文字或前后缀，JSON 之外不能有任何内容。

输出对象恰好包含以下五个字段，字段名和值严格如下：

{
    "mode": "model",
    "answer": "非空字符串",
    "uncertainty": "非空字符串",
    "source_status": "not_retrieved",
    "sources": []
}

要求：
- mode 固定为 "model"。
- answer 为非空字符串，用中文回答用户的历史地理问题。
- uncertainty 为非空字符串，说明回答的不确定程度；用户基于虚构前提提问时明确说明，不编造真实年份或来源。
- source_status 固定为 "not_retrieved"，表示尚未检索资料。
- sources 固定为空列表 []，不虚构来源。
"""
    return {
        "model": "kimi-k3",
        "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": question
        }

        ],
        "response_format": {"type": "json_object"},
        "stream": False,
        "max_completion_tokens": 4096,
        "reasoning_effort": "low",
    }



def extract_response_metadata(response) -> dict:
    """S4-03C：只读提取结束原因及用量；缺失为None，零值保留。

    四字段、缺失与回调接线规则见LEARNING_PLAN.md；不判断回答成功。
    本函数由学员实现，不请求模型或计算费用。
    """
    choices = getattr(response, "choices", None)
    if isinstance(choices, list) and len(choices) == 1:
        finish_reason = getattr(choices[0], "finish_reason", None)
    else:
        finish_reason = None

    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    usage = getattr(response, "usage", None)
    if usage is not None :
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

    return {
        "finish_reason": finish_reason,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }

    # raise NotImplementedError("请完成S4-03C元数据提取与on_metadata回调接线")


def ask_structured(client, question: str, *, on_metadata=None) -> dict:
    """使用传入客户端请求一次，校验响应包络后返回已校验的回答dict。

    本课用假客户端离线检查，不在此创建客户端、打印或处理重试；
    SDK 异常原样向上传播，不自行关闭由调用方提供的客户端。
    """
    # 1) 构造请求（内部完成 question 的类型/空白校验）
    request = build_structured_request(question)

    if on_metadata is not None and not callable(on_metadata):
        raise TypeError("on_metadata 必须是可调用对象或 None")

    # 2) 请求一次：SDK 异常原样向上传播，不捕获、不重试
    response = client.chat.completions.create(**request)

    if on_metadata is not None:
        metadata = extract_response_metadata(response)
        on_metadata(metadata)

    # 3) 校验响应包络，逐层用 getattr，缺失或结构错误统一 ValueError
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("响应 choices 必须恰好一个")
    choice = choices[0]
    if choice is None:
        raise ValueError("choice 不能为空")

    finish_reason = getattr(choice, "finish_reason", None)
    if finish_reason != "stop":
        raise ValueError("finish_reason 必须为 stop")

    message = getattr(choice, "message", None)
    if message is None:
        raise ValueError("message 不能为空")
    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content 必须是非空白字符串")

    # 4) 交给解析器，显式期望 model 模式
    return parse_answer_json(content, expected_mode="model")


def main() -> None:
    result = make_mock_answer(
        "这是一条结构化输出的离线示例。",
        "未调用模型或检索资料，示例不代表经核实的史实。",
    )

    result_str = json.dumps(result)
    parse_answer_json(result_str)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
