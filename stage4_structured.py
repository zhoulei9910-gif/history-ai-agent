"""阶段4独立学习入口：S4-01离线结构化数据，不调用模型。"""

import json


def make_mock_answer(answer: str, uncertainty: str) -> dict:
    """S4-01由学员实现：校验两个文本参数，返回约定的模拟回答字典。

    字段、输入规则与验收命令见LEARNING_PLAN.md的S4-01。
    只构造数据，不打印、不请求模型、不读写文件。
    """
    raise NotImplementedError("请完成S4-01的make_mock_answer")


def main() -> None:
    result = make_mock_answer(
        "这是一条结构化输出的离线示例。",
        "未调用模型或检索资料，示例不代表经核实的史实。",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
