"""S4-03D：单次结构化问答入口；只有显式--live才执行模型请求。"""

import argparse
import json

from openai import OpenAI, APIError
from stage4_structured import ask_structured, build_structured_request, extract_response_metadata

SOURCE_LABEL = "模型生成｜未检索来源"


def show_metadata(metadata: dict) -> None:
    """导师提供的展示辅助：保留None/0，不输出原始响应或计算费用。"""
    if metadata:
        print("响应元数据：" + json.dumps(metadata, ensure_ascii=False))
    else:
        print("未取得响应元数据，实际消耗未知。")


def run_live(question: str) -> int:
    """S4-03D由学员实现：读取Kimi配置，创建受控客户端并调用一次。

    本函数手动运行会付费，离线检查使用假配置及SDK内存HTTP传输。
    成功返回0；输入、配置、SDK或回答格式失败返回1；要求见学习计划。
    """
    # 1) 先校验问题：非 str 或 strip 后为空，在读取配置/创建客户端前返回 1
    if not question or not isinstance(question, str) or not question.strip():
        print("question必须为str，且不能为空")
        return 1

    captured = []  # 用列表承接 on_metadata 回调发来的元数据；captured.append 才是可调用对象
    # 2) 配置导入放函数内：只在真正要调模型时才 import config → 加载 .env
    from config import get_api_key
    from config import get_base_url
    try:
        # try 包住整个 with，缺 Key 的 ValueError 也能被接住
        with OpenAI(
            api_key=get_api_key("kimi"),
            base_url=get_base_url("kimi"),
            timeout=120,
            max_retries=0,
        ) as client:
            answer = ask_structured(client, question, on_metadata = captured.append)

            # 成功：打印来源标签和已校验的回答 JSON，返回 0
            print(SOURCE_LABEL)
            print(json.dumps(answer, ensure_ascii=False, indent=4))
            return 0
    except (TypeError, ValueError, APIError):
        # 输入/配置/SDK/回答格式失败：安全提示，返回 1
        print("调用模型失败")
        return 1
    finally:
        # 无论成功失败都展示元数据；SDK 失败无响应时 captured 为空 → 显示"未知"
        show_metadata(captured[0] if captured else {})


def main(argv=None) -> int:
    """提供的参数入口：默认预览，--live才调用run_live。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="本次地理或历史问题")
    parser.add_argument("--live", action="store_true", help="执行一次真实付费模型请求")
    args = parser.parse_args(argv)
    if not args.live:
        try:
            request = build_structured_request(args.question)
        except (TypeError, ValueError):
            print("问题必须是非空字符串。")
            return 1
        print("离线请求预览｜未读取Key、未发送请求")
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return 0
    try:
        return run_live(args.question)
    except KeyboardInterrupt:
        print("已取消。")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
