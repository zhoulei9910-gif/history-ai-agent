import json
from pathlib import Path
from platform import system

from openai import OpenAI, APIError
from dataclasses import dataclass

from config import get_api_key, get_base_url
from conversation import check_param, build_turn_messages, create_history, commit_turn, SYSTEM_PROMPT
from session_store import load_history, save_history


MAX_HISTORY_ROUNDS = 2
SESSION_PATH = Path(__file__).resolve().parent / "data" / "session.json"

# 每轮请求最多携带的完整历史轮次（一条 user + 一条 assistant 算一轮）

@dataclass
class ModelAnswer:
    content: str
    finish_reason: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    assistant_message: dict | None = None


def build_messages(question: str) -> list[dict[str, str]]:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]


def ask_messages(messages: list[dict]) -> ModelAnswer:
    client = OpenAI(
        api_key=get_api_key("kimi"),
        base_url=get_base_url("kimi"),
        timeout=120,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model="kimi-k3",
        messages=messages,
        stream=False,
        max_completion_tokens=4096,
        timeout=120.0,
        reasoning_effort="low"
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

def ask_turn(history: list[dict], question: str) -> ModelAnswer:
    check_param(question, "question")
    message = build_turn_messages(history, question, MAX_HISTORY_ROUNDS)
    answer = ask_messages(message)
    if answer.finish_reason == "stop" and answer.content.strip():
        commit_turn(history, question, assistant_message = answer.assistant_message)

    return answer


def ask_once(question: str) -> ModelAnswer:
    """调用一次模型并返回结构化结果：只提取数据，不打印、不翻译。"""
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    answer = ask_messages(build_messages(question))
    return answer

def display(answer: ModelAnswer) -> None:
    """把结构化结果打印到终端：处理空回答、缺失/零用量、截断提示。"""
    # 来源标签
    print("模型生成｜未检索来源")

    # 正文：先 strip 再判断，空白等同空
    content = (answer.content or "").strip()
    if content:
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


def main(session_path: Path | None = None) -> None:
    print(f"session_path: {not session_path }")
    if not session_path:
        print("session_path is none")
        local_history = create_history(SYSTEM_PROMPT)
    else:
        try:
            local_history = load_history(session_path)
        except FileNotFoundError:
            local_history = create_history(SYSTEM_PROMPT)
            # json.dump(local_history, open(session_path, "w"))
            print("session_path is not exist")
        except OSError as e:
            print("加载失败", type(e).__name__)
            return
        except ValueError as e:
            print("加载失败", {type(e).__name__})
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
            # answer = ask_once(question)
            before = len(history)
            answer = ask_turn(history, question)

            #展示回答结果
            display(answer)

            ## 回答成功，保存到本地
            if session_path is not None and len(history) > before:
                session_path.parent.mkdir(parents=True, exist_ok=True)
                save_history(session_path, history)
        except ValueError as e:
            print(f"前置检查失败 {type(e).__name__}")
            continue
        except APIError as e:
            print(f"模型调用失败（{type(e).__name__}）")
            continue
        except TypeError as e:
            print(f"data type error: {type(e).__name__}")
            continue
        except OSError as e:
            print(f"保存失败，本轮回答仍在内存 {type(e).__name__}")
            continue

if __name__ == "__main__":
    # print(SESSION_PATH)
    main(SESSION_PATH)
