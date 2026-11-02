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
    raise NotImplementedError("请完成S4-03A的build_structured_request")


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
