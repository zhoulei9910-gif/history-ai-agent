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
    """S4-02由学员实现：解析JSON，校验原始字段，再返回规范化回答。

    只处理传入字符串；不打印、不请求模型、不读写文件。
    语法错误保留JSONDecodeError，业务结构错误用ValueError。
    """
    raise NotImplementedError("请完成S4-02的parse_answer_json")


def main() -> None:
    result = make_mock_answer(
        "这是一条结构化输出的离线示例。",
        "未调用模型或检索资料，示例不代表经核实的史实。",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
