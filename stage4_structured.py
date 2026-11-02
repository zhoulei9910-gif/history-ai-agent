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


def parse_answer_json(raw: str) -> dict:
    """S4-02：解析JSON并校验回答契约，返回规范化dict。

    语法错误保留JSONDecodeError；业务结构错误（缺字段、类型错、
    空白、伪造来源等）统一抛ValueError。只在原始值上校验，不覆盖洗白。
    """
    # 1) raw 必须是 str，其余类型一律 TypeError
    if not isinstance(raw, str):
        raise TypeError("raw 必须是 str")

    # 2) 解析 JSON：语法错误保留 json.JSONDecodeError，不捕获
    data = json.loads(raw)

    # 3) 顶层必须是对象（dict）
    if not isinstance(data, dict):
        raise ValueError("顶层必须是 JSON 对象")

    # 4) 恰好五个字段，缺字段或多余字段都拒绝
    if set(data.keys()) != {"mode", "answer", "uncertainty", "source_status", "sources"}:
        raise ValueError("字段必须恰好为 mode/answer/uncertainty/source_status/sources")

    # 5) 四个文本字段都必须是 str
    for key in ("mode", "answer", "uncertainty", "source_status"):
        if not isinstance(data[key], str):
            raise ValueError(f"{key} 必须是 str")

    # 6) answer / uncertainty 清理首尾空白后必须非空
    answer = data["answer"].strip()
    uncertainty = data["uncertainty"].strip()
    if not answer or not uncertainty:
        raise ValueError("answer 和 uncertainty 不能为空")

    # 7) sources 先验 list 类型，再验必须为空（不能 `not sources` 判断）
    sources = data["sources"]
    if not isinstance(sources, list):
        raise ValueError("sources 必须是 list")
    if sources:
        raise ValueError("sources 必须为空列表")

    # 8) mode / source_status 精确匹配，不 strip、不洗白
    if data["mode"] != "mock" or data["source_status"] != "not_retrieved":
        raise ValueError("mode 必须为 mock，source_status 必须为 not_retrieved")

    # 9) 返回规范化后的新 dict：answer/uncertainty 已 strip，sources 是新空列表
    return {
        "mode": "mock",
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



def ask_structured(client, question: str) -> dict:
    """S4-03B：使用传入客户端请求一次，校验响应后返回回答dict。

    配合parse_answer_json的显式expected_mode扩展；具体规则见学习计划。
    本课用假客户端离线检查，不在此创建客户端、打印或处理重试。
    """
    raise NotImplementedError("请完成S4-03B的ask_structured及解析器模式扩展")


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
