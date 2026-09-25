"""Model configuration UI; only non-secret configuration is stored in SQLite."""

import json
import os

import streamlit as st

from memoryrush.api import APIConfig, OpenAICompatibleProvider
from memoryrush.providers import DeterministicPreviewProvider, LlamaCppProvider, OllamaProvider

PROVIDERS = {
    "llama.cpp": "本地 · llama.cpp",
    "ollama": "本地 · Ollama",
    "api": "外部 API",
    "preview": "离线预览",
}
PRESETS = {
    "OpenAI": ("https://api.openai.com/v1", "OPENAI_API_KEY", "max_completion_tokens"),
    "DeepSeek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY", "max_tokens"),
    "阿里云百炼 / Qwen": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_API_KEY",
        "max_tokens",
    ),
    "自定义兼容接口": ("", "MEMORYRUSH_API_KEY", "max_tokens"),
}


def provider_settings(bank):
    name = bank.setting("provider") or os.environ.get("MEMORYRUSH_PROVIDER", "llama.cpp")
    model = bank.setting(f"model_{name}") or bank.setting("model") or "qwen3:8b"
    endpoint = bank.setting(f"endpoint_{name}") or (
        "http://127.0.0.1:8384/v1/chat/completions"
        if name == "llama.cpp"
        else "http://127.0.0.1:11434/api/generate"
    )
    if name == "api":
        saved = json.loads(bank.setting("api_config") or "{}")
        model, endpoint = saved.get("model", "未配置模型"), saved.get("endpoint", "")
    return name, model, endpoint, int(bank.setting("memory_budget") or "5")


def get_provider(bank):
    name, model, endpoint, _ = provider_settings(bank)
    if name == "api":
        config = APIConfig(**json.loads(bank.setting("api_config") or "{}"))
        # A session key is bound to the exact approved endpoint, never a provider label.
        key = st.session_state.get("api_credentials", {}).get(config.endpoint, "")
        if not key:
            key = os.environ.get(config.key_env, "")
        return OpenAICompatibleProvider(config, key, approved_endpoint=bank.setting("api_approved"))
    if name == "preview":
        return DeterministicPreviewProvider()
    if name not in {"llama.cpp", "ollama"}:
        raise ValueError("未知模型接口，请重新选择。")
    return (LlamaCppProvider if name == "llama.cpp" else OllamaProvider)(model, endpoint)


@st.dialog("设置", width="large")
def settings_dialog(bank):
    current, model, endpoint, budget = provider_settings(bank)
    st.caption("应用与历史保存在本机。模型可以在本地运行，也可以使用你选择的 API。")
    name = st.selectbox(
        "模型接口",
        list(PROVIDERS),
        format_func=PROVIDERS.get,
        index=list(PROVIDERS).index(current) if current in PROVIDERS else 0,
    )
    saved = json.loads(bank.setting("api_config") or "{}")
    preset = bank.setting("api_preset") or "OpenAI"
    if name == "api":
        preset = st.selectbox("API 服务", list(PRESETS), index=list(PRESETS).index(preset))
        defaults = PRESETS[preset]
        if preset != (bank.setting("api_preset") or "OpenAI"):
            saved = {}
        endpoint, model = saved.get("endpoint", defaults[0]), saved.get("model", "")
    elif name != current:
        model = bank.setting(f"model_{name}") or "qwen3:8b"
        endpoint = bank.setting(f"endpoint_{name}") or (
            "http://127.0.0.1:8384/v1/chat/completions"
            if name == "llama.cpp"
            else "http://127.0.0.1:11434/api/generate"
        )
    with st.form(f"model_settings_{name}_{preset}"):
        if name != "preview":
            model = st.text_input("模型 ID", value=model, placeholder="填写服务商控制台中的模型 ID")
            endpoint = st.text_input(
                "API Base URL / 完整地址" if name == "api" else "本机模型地址", value=endpoint
            )
        if name == "api":
            api_key = st.text_input(
                "API Key（仅本次浏览器会话）",
                type="password",
                help="不写入数据库或配置文件。留空可沿用当前会话对此地址的密钥，或读取下方环境变量。",
            )
            st.caption(
                "不要把密钥发到聊天里。重开浏览器可能需要重新输入；也可自行设置下方环境变量。"
            )
            with st.expander("兼容性与密钥选项"):
                key_env = st.text_input("密钥环境变量名称", value=saved.get("key_env", defaults[1]))
                modes = ["json_object", "json_schema", "prompt"]
                mode = st.selectbox(
                    "JSON 输出模式",
                    modes,
                    index=modes.index(saved.get("response_mode", "json_object")),
                )
                params = ["max_tokens", "max_completion_tokens"]
                token_parameter = st.selectbox(
                    "输出长度参数",
                    params,
                    index=params.index(saved.get("token_parameter", defaults[2])),
                )
                output_tokens = st.number_input(
                    "每次请求输出额度（含推理 tokens）",
                    1024,
                    32768,
                    int(saved.get("output_tokens", 8192)),
                    step=1024,
                )
                st.caption(
                    "默认 JSON 模式；不支持时手动选 prompt。结构校验始终保留，不静默降级或自动重试。"
                )
            st.warning(
                "发送范围：文章正文/引文、阅读兴趣、参与评分的旧记忆；提问时所选范围内所有启用记忆会分批评相关性，并发送问题与最近最多 3 轮对话。可能产生多次 API 调用和费用。"
            )
            approved = st.checkbox("我允许把上述内容发送到填写的 API 地址，并了解可能产生费用。")
        with st.expander("阅读与记忆偏好"):
            budget = st.slider("每篇自动保留数量", 1, 20, budget)
            profile = st.text_area(
                "我的阅读兴趣 / 当前目标", value=bank.setting("profile"), max_chars=500
            )
            st.caption("只影响新记忆的评分，不自动重写已有分数。")
        if st.form_submit_button("保存并使用", type="primary"):
            try:
                if name == "api":
                    config = APIConfig(
                        endpoint, model, key_env, mode, token_parameter, int(output_tokens)
                    )
                    if not approved:
                        raise ValueError("请先确认 API 的发送范围；尚未切换模型。")
                    key = api_key.strip() or st.session_state.get("api_credentials", {}).get(
                        config.endpoint, ""
                    )
                    if key:
                        OpenAICompatibleProvider(config, key, approved_endpoint=config.endpoint)
                    bank.setting("api_config", json.dumps(config.public_dict()))
                    bank.setting("api_approved", config.endpoint)
                    bank.setting("api_preset", preset)
                    if api_key.strip():
                        st.session_state.setdefault("api_credentials", {})[config.endpoint] = key
                elif name != "preview":
                    (LlamaCppProvider if name == "llama.cpp" else OllamaProvider)(model, endpoint)
                    bank.setting(f"model_{name}", model)
                    bank.setting(f"endpoint_{name}", endpoint)
                bank.setting("provider", name)
                bank.setting("memory_budget", str(budget))
                bank.setting("profile", profile)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("本机数据与记忆规则"):
        st.code(str(bank.path), language=None)
        st.text(
            "基础分 → 时间衰减 → 问题相关性 → 带引文的回答。实际引用并校验通过才强化，24 小时最多一次。评分/衰减是工程默认值，尚未做效果校准。"
        )
        st.caption("默认数据不在 OneDrive，数据库未加密。外部 API 的保留政策由你选择的服务商决定。")
    if st.button("清除本次会话中的 API 密钥"):
        st.session_state.pop("api_credentials", None)
        # Removing this dialog's widgets on a full rerun also discards password-field state.
        st.rerun()
