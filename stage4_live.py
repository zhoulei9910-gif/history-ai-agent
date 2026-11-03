"""S4-03D：单次结构化问答入口；只有显式--live才执行模型请求。"""

import argparse
import json

from stage4_structured import ask_structured, build_structured_request

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
    raise NotImplementedError("请完成S4-03D的run_live；先运行离线检查")


def main(argv=None) -> int:
    """导师提供的参数入口：默认预览，--live才调用run_live。"""
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
