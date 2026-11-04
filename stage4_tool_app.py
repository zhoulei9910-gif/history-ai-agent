"""S4-07：已知失败的应用边界；只使用调用方提供的客户端。"""

from copy import deepcopy
import json

from openai import APIError
from stage4_tool_flow import ask_with_tool

ERROR_MESSAGES = {
    "invalid_input": "问题必须是非空字符串。",
    "invalid_output": "模型返回的工具请求或回答不符合约定。",
    "api_error": "模型请求失败。",
    "execution_error": "工具流程执行失败。",
}


def success_result(answer: dict, responses: list) -> dict:
    """导师提供：成功结果保留答案及每次响应统计的独立快照。"""
    return {"ok": True, "answer": deepcopy(answer), "error": None,
            "responses": deepcopy(responses)}


def failure_result(code: str, responses: list) -> dict:
    """导师提供：只用固定错误文案，不保存异常对象或原异常文本。"""
    return {"ok": False, "answer": None,
            "error": {"code": code, "message": ERROR_MESSAGES[code]},
            "responses": deepcopy(responses)}


def run_tool_question(client, question: str) -> dict:
    """S4-07由学员实现：调用一次完整流程，转换已约定的失败并保留统计。

    内部创建responses列表，用其append接收ask_with_tool的on_metadata。
    非str／空白输入直接invalid_input，不调用流程；成功复用success_result。
    APIError／ValueError／RuntimeError分别映射api_error／invalid_output／
    execution_error，其余异常原样传播。无打印、重试、配置／文件访问或关闭client。
    """
    raise NotImplementedError("请完成S4-07的run_tool_question")


def main() -> int:
    """导师提供的离线格式示例；不是本课流程实现或模型响应。"""
    print("离线错误结果格式示例｜未执行问答流程、未读取Key或连接模型")
    print(json.dumps(failure_result("invalid_input", []), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
