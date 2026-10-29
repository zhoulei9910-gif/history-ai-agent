"""会话的 JSON 保存与加载：只依赖标准库，不 import config/openai，也不读输入、不打印。"""

import json
from pathlib import Path


def _validate_history(history: list[dict]) -> None:
    """校验会话结构，无效时抛 ValueError。

    有效结构：非空 list，奇数长度，第 0 条为 system，之后 user/assistant
    交替且各自 content 都是非空白字符串；额外的协议字段（如 reasoning_content）保留不管。
    """
    if not isinstance(history, list) or not history:
        raise ValueError("会话历史必须是非空列表")
    if len(history) % 2 == 0:
        raise ValueError("会话历史必须以 system 开头，且 user/assistant 成对出现")

    for index, message in enumerate(history):
        if not isinstance(message, dict):
            raise ValueError(f"第 {index} 条消息必须是字典")
        expected_role = "system" if index == 0 else ("user" if index % 2 == 1 else "assistant")
        if message.get("role") != expected_role:
            raise ValueError(f"第 {index} 条消息 role 应为 {expected_role}")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"第 {index} 条消息 content 必须是非空白字符串")


def save_history(path: Path, history: list[dict]) -> None:
    """先校验，再以 UTF-8、ensure_ascii=False 把完整消息列表写为 JSON；失败不碰已有文件。"""
    _validate_history(history)
    path.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")


def load_history(path: Path) -> list[dict]:
    """读取并解析 JSON，校验会话结构后返回完整消息列表。

    缺文件传播 FileNotFoundError；路径为目录传播 OSError；坏 JSON 或结构错误抛 ValueError。
    """
    history = json.loads(path.read_text(encoding="utf-8"))
    _validate_history(history)
    return history
