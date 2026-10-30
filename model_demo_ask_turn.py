from collections.abc import Callable, Iterable
from pathlib import Path
from platform import system

from openai import OpenAI, APIError
from dataclasses import dataclass

from openai.types.chat import ChatCompletionChunk

from IncompleteStreamError import IncompleteStreamError
from config import get_api_key, get_base_url
from conversation import check_param, build_turn_messages, create_history, commit_turn, SYSTEM_PROMPT
from session_store import load_history, save_history


MAX_HISTORY_ROUNDS = 2
SESSION_PATH = Path(__file__).resolve().parent / "data" / "session.json"
SOURCE_LABEL = "模型生成｜未检索来源"

# 每轮请求最多携带的完整历史轮次（一条 user + 一条 assistant 算一轮）

@dataclass
class ModelAnswer:
    """一次模型回答的结构化结果：正文、结束原因、可选用量与完整 assistant 消息。"""

    content: str
    finish_reason: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    assistant_message: dict | None = None


def build_messages(question: str) -> list[dict[str, str]]:
    """把单次问题组装成 [system, user] 两条消息；空白问题抛 ValueError。"""

    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]


def ask_messages(messages: list[dict]) -> ModelAnswer:
    """非流式调用一次模型，返回结构化结果；只提取数据，不打印、不提交历史。"""

    client = OpenAI(
        api_key=get_api_key("kimi"),
        base_url=get_base_url("kimi"),
        timeout=120,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model="kimi-k3",
        messages=messages,
        max_completion_tokens=4096,
        timeout=120.0,
        reasoning_effort="low",
        stream=False,
    )

    choice = response.choices[0]
    content = choice.message.content or ""
    finish_reason = choice.finish_reason or ""
    usage = response.usage

    # usage 可能为 None，先安全取值
    prompt_tokens = usage.prompt_tokens if usage else None
    completion_tokens = usage.completion_tokens if usage else None
    total_tokens = usage.total_tokens if usage else None

    assistant_message = choice.message.to_dict()

    return ModelAnswer(
        content = content,
        finish_reason = finish_reason,
        assistant_message = assistant_message,
        prompt_tokens = prompt_tokens,
        completion_tokens = completion_tokens,
        total_tokens = total_tokens,
    )


def ask_stream_messages(
    messages: list[dict],
    on_text: Callable[[str], None] | None = None,
) -> ModelAnswer:
    """流式调用一次模型：逐片把正文交给 on_text 回调，最后返回完整结果。"""

    with OpenAI(
        api_key=get_api_key("kimi"),
        base_url=get_base_url("kimi"),
        timeout=120,
        max_retries=0,
    ) as client:
        with client.chat.completions.create(
            model="kimi-k3",
            messages=messages,
            max_completion_tokens=4096,
            timeout=120.0,
            reasoning_effort="low",
            stream=True,
            stream_options={"include_usage": True}
        ) as stream:
            return consume_stream(stream, on_text)

def ask_turn(history: list[dict], question: str, stream = False, on_text: Callable[[str], None] | None = None ) -> ModelAnswer:
    """处理一轮问答：按 stream 选择调用方式；stop 且正文非空白才提交历史，finish_reason 为空抛 IncompleteStreamError。"""

    check_param(question, "question")
    message = build_turn_messages(history, question, MAX_HISTORY_ROUNDS)

    if stream:
        answer = ask_stream_messages(message, on_text)

    else:
        answer = ask_messages(message)

    finish_reason = getattr(answer, "finish_reason", "").strip()
    content = answer.content.strip()
    if finish_reason == "stop" and content:
        commit_turn(history, question, assistant_message = answer.assistant_message)
    elif stream and finish_reason == "":
        raise IncompleteStreamError("回答未能完成，不写入历史")
    return answer


def ask_once(question: str) -> ModelAnswer:
    """调用一次模型并返回结构化结果：只提取数据，不打印、不翻译。"""
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    answer = ask_messages(build_messages(question))
    return answer

def display(answer: ModelAnswer, streamed = False) -> None:
    """把结构化结果打印到终端：处理空回答、缺失/零用量、截断提示。"""
    if not streamed:
        # 来源标签
        print(SOURCE_LABEL)

    # 正文：先 strip 再判断，空白等同空
    content = (answer.content or "").strip()
    if content:
        if not streamed:
            print(content)
    else:
        print("回答为空")

    # 用量：缺失用 is None 判断（0 是已提供的有效值）
    if answer.total_tokens is None:
        print("未提供用量统计")
    else:
        print(
            f"用量: prompt={answer.prompt_tokens} "
            f"completion={answer.completion_tokens} "
            f"total={answer.total_tokens}"
        )

    # 结束原因：保留原始值；length 时额外给中文截断提示
    print(f"结束原因: {answer.finish_reason}")
    if answer.finish_reason == "length":
        print("提示：回答被截断")


def consume_stream(
    chunks: Iterable[ChatCompletionChunk],
    on_text: Callable[[str], None] | None = None,
) -> ModelAnswer:
    """逐片收集文本；通过回调通知正文，最后返回完整结果。

    本函数不请求模型、不打印、不提交历史。迭代或回调失败时，
    异常自然交给调用方处理，不返回看起来成功的部分结果。
    """
    content_pieces = []
    reasoning_pieces = []
    finish_reason = ""
    usage = None

    for chunk in chunks:
        # 最后的统计分片可能没有 choices，所以先收集顶层用量。
        if chunk.usage is not None:
            usage = chunk.usage
        if not chunk.choices:
            continue

        choice = chunk.choices[0]
        if choice.finish_reason is not None:
            finish_reason = choice.finish_reason
            # 此处不退出循环：后面仍可能有统计分片。

        delta = choice.delta
        if delta.content:
            fragment = delta.content
            content_pieces.append(fragment)  # 收集：用于最后的完整结果。
            if on_text is not None:
                on_text(fragment)  # 通知：调用方现在就能收到这个正文片段。

        # 协议字段单独保留，既不混入正文，也不通知正文回调。
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            reasoning_pieces.append(reasoning)

    content = "".join(content_pieces)
    assistant_message = {
        "role": "assistant",
        "content": content,
    }
    if reasoning_pieces:
        assistant_message["reasoning_content"] = "".join(reasoning_pieces)

    # 返回：整个流消费结束后，调用方才拿到完整 ModelAnswer。
    return ModelAnswer(
        content=content,
        finish_reason=finish_reason,
        prompt_tokens=usage.prompt_tokens if usage is not None else None,
        completion_tokens=usage.completion_tokens if usage is not None else None,
        total_tokens=usage.total_tokens if usage is not None else None,
        assistant_message=assistant_message,
    )


def _print_fragment(fragment: str) -> None:
    """流式正文回调：逐片打印并 flush；来源标签由调用方在请求前打印。"""
    if fragment:
        print(fragment, end="", flush=True)


def main(session_path: Path | None = None, stream = False ) -> None:
    """交互式 CLI 主循环：启动加载或新建历史，逐轮问答、展示，成功后按需保存。"""

    if not session_path:
        local_history = create_history(SYSTEM_PROMPT)
    else:
        try:
            local_history = load_history(session_path)
        except FileNotFoundError:
            local_history = create_history(SYSTEM_PROMPT)
        except OSError as e:
            print("加载失败", type(e).__name__)
            return
        except ValueError as e:
            print("加载失败", type(e).__name__)
            return

    history = local_history
    while True:
        question = input("请输入地理或历史问题：").strip()
        if not question:
            print("问题不能为空，请重新输入地理或历史问题。")
            continue
        if question in ("退出", "exit", "quit"):
            return

        try:
            before = len(history)
            if stream:
                print(SOURCE_LABEL, flush=True)  # 每次有效请求前打印来源标签
            try:
                answer = ask_turn(history, question, stream=stream,
                                  on_text=_print_fragment if stream else None)
            finally:
                if stream:
                    print()  # 正文结束后补换行，成功或异常都补
            display(answer, streamed=stream)

            # 回答成功，保存到本地
            if session_path is not None and len(history) > before:
                session_path.parent.mkdir(parents=True, exist_ok=True)
                save_history(session_path, history)
        except ValueError as e:
            print(f"前置检查失败（{type(e).__name__}）：{e}")
            continue
        except APIError as e:
            print(f"模型调用失败（{type(e).__name__}）")
            continue
        except OSError as e:
            print(f"保存失败，本轮回答仍在内存（{type(e).__name__}）")
            continue
        except IncompleteStreamError as e:
            print(f"流式回答未完成，本轮未加入历史（{type(e).__name__}）")
            continue
        except KeyboardInterrupt:
            print("已取消，退出程序")
            return


if __name__ == "__main__":
    # print(SESSION_PATH)
    main(SESSION_PATH, stream = True)
