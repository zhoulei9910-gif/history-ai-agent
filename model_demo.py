# 单次真实模型调用示例：使用 OpenAI SDK 调用 Kimi（Moonshot）
from openai import OpenAI, APIError

from config import get_api_key, get_base_url


def main() -> None:
    # 1. 读取并校验 API Key：缺失或全空白时 get_api_key() 会抛 ValueError
    try:
        api_key = get_api_key("kimi")
    except ValueError as e:
        print("配置缺失：", e)
        return

    # 2. 读取一次问题；空白输入直接结束，不发网络请求
    question = input("请输入地理或历史问题：").strip()
    if not question:
        print("问题不能为空，请输入地理或历史问题。")
        return

    # 3. 创建客户端：120 秒超时、不自动重试
    client = OpenAI(
        api_key=api_key,
        base_url=get_base_url("kimi"),
        timeout=120.0,
        max_retries=0,
    )

    # 4. 发起一次非流式调用：最多 1024 tokens
    try:
        response = client.chat.completions.create(
            model="kimi-k3",
            messages=[
                {"role": "system", "content": "You are a helpful history assistant"},
                {"role": "user", "content": question},
            ],
            stream=False,
            max_completion_tokens=4096,
            reasoning_effort = "low",
            timeout=120.0,
        )
    except APIError as e:
        # 鉴权失败、超时等 SDK 异常：只报告错误类别，不伪装成功
        print(f"模型调用失败（{type(e).__name__}）")
        return

    # 5. 读取并打印结果：来源标记、回答、用量、结束原因
    choice = response.choices[0]
    content = choice.message.content or ""
    usage = response.usage

    print("response: %r" %response)
    print("choice: %r" %choice)
    print("模型生成｜未检索来源")
    if not content or content.strip() == "":
        print("未返回有效回答")
    if usage:
        print(
            f"用量：prompt={usage.prompt_tokens} "
            f"completion={usage.completion_tokens} "
            f"total={usage.total_tokens}"
        )
    else:
        print("未提供用量统计")
    print("content:", content)

    print(f"finish_reason：{choice.finish_reason}")
    if choice.finish_reason == "length":
        print("提示：回答被截断（达到 max_tokens 上限）。")

if __name__ == "__main__":
    main()
