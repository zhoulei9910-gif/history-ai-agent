# 定义回答问题的主函数，接收一个字符串参数 question
import os
from warnings import catch_warnings

from config import get_api_key


def answer_question(question: str) -> str:
    # 函数的类型标注说明：参数 question 是字符串，返回值也是字符串

    # 文档字符串，说明本函数的作用：返回一段离线模拟文本，用于验证问答流程是否跑通
    """返回离线模拟文本，用于验证问答流程。"""

    # 返回一个格式化字符串（f-string）：把用户输入的问题嵌入到提示语里，
    # 前面标注【模拟响应｜无来源、未核实】，表示这只是一个占位回答，还没有接入真实 AI/检索
    return f"【模拟响应｜无来源、未核实】收到问题：{question}"


# 定义程序入口函数 main，不接收参数，也不返回值
def main() -> None:
    # 类型标注：返回值为 None，表示这个函数只做事、不返回数据

    # 用 input() 从命令行读取用户输入，并立即调用 .strip() 去掉首尾空白字符
    # 提示文字是“请输入地理或历史问题：”，输入结果存到变量 question 里
    global api_key
    try:
        api_key = get_api_key()
    except Exception as e:
        print("error:", e)

    while (True):
        question = input("请输入地理或历史问题：").strip()

        # 判断输入是否为空字符串（用户直接回车或只输入了空格）
        if not question or question.isspace():
            # 如果为空，打印错误提示，告诉用户问题不能为空
            print("问题不能为空，请输入地理或历史问题。")
            # 直接 return 结束 main 函数，不再继续往下执行
            return
        elif question == "退出" or question == "exit" or question == "quit":
            print("再见...")
            return

        # 调用上面的 answer_question 函数，把用户输入传进去，得到模拟回答
        answer = answer_question(question)

        # 把得到的回答打印到命令行显示给用户
        print(answer)


# 判断当前文件是否作为主程序直接运行（而不是被其他文件 import 导入）
if __name__ == "__main__":
    # 如果是直接运行，就调用 main 函数启动整个程序
    main()
