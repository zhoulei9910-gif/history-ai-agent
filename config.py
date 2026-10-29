import os

from dotenv import load_dotenv

# 加载项目根目录的 .env 文件（若存在），把其中的变量合并进 os.environ。
# .env 已被 .gitignore 排除，不会进入版本控制；密钥只存在于本地。
load_dotenv()

# 供应商注册表：供应商名 -> 读取 key 的环境变量名 + 接口地址（base_url）。
PROVIDERS = {
    "deepseek": {"key_env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
    "glm":      {"key_env": "GLM_API_KEY",       "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    "openai":   {"key_env": "OPENAI_API_KEY",    "base_url": "https://api.openai.com/v1"},
    "kimi":     {"key_env": "KIMI_API_KEY",      "base_url": "https://api.moonshot.cn/v1"},
    "google":   {"key_env": "GOOGLE_API_KEY",    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai"},
}

# 项目当前默认使用的供应商。
DEFAULT_PROVIDER = "deepseek"

# 兼容旧配置：早期项目用统一的 MODEL_API_KEY 表示 DeepSeek 的 key。
# 当 DEEPSEEK_API_KEY 未配置时，回退读取 MODEL_API_KEY。
_LEGACY_KEY_ENV = "MODEL_API_KEY"


def _read_key(provider: str) -> str:
    """读取某供应商的 key（去首尾空白）；未配置时返回空字符串。"""
    key_env = PROVIDERS[provider]["key_env"]
    key = os.environ.get(key_env, "").strip()
    # 默认供应商的 key 支持旧变量名回退，保证早期评估用例（MODEL_API_KEY）仍可用
    if not key and provider == DEFAULT_PROVIDER:
        key = os.environ.get(_LEGACY_KEY_ENV, "").strip()
    return key


def get_api_key(provider: str = DEFAULT_PROVIDER) -> str:
    """读取并校验指定供应商的 API Key；缺失或全空白时抛 ValueError。"""
    print("provider: %r" % provider)
    if provider not in PROVIDERS:
        raise ValueError(f"未知的供应商：{provider}")
    key = _read_key(provider)
    if not key:
        raise ValueError(
            f"请配置 {PROVIDERS[provider]['key_env']}"
            f"（供应商：{provider}），可写在项目根目录的 .env 里"
        )
    return key


def get_base_url(provider: str = DEFAULT_PROVIDER) -> str:
    """读取指定供应商的接口地址。"""
    if provider not in PROVIDERS:
        raise ValueError(f"未知的供应商：{provider}")
    return PROVIDERS[provider]["base_url"]


def main() -> None:
    # 配置自检：逐个供应商报告是否已配置，只显示状态、不打印 Key 本身。
    for name in PROVIDERS:
        status = "已配置" if _read_key(name) else "未配置"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
