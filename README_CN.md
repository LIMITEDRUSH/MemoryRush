# MemoryRush

在本机运行的个人 LLM（大语言模型）阅读助手。阅读 TXT / Markdown 文章，提取有原文依据的 Memory Point（记忆点），并在后续对话中自动召回。它是个人工具，不是商业化平台。

[English](README.md) · [完整使用与评分、衰减、召回说明](docs/READING_ASSISTANT_CN.md)

## 已实现

- Codex 式对话入口：历史侧栏、文章附件、按需展开的记忆检查。
- 提取后单独调用模型评分，保留逐维理由与原始记录；校验证据、结构和范围，再按价值与重复程度决定保留。
- SQLite 本地持久记忆：时间衰减、半衰期、固定、可恢复停用，以及仅对实际引用的记忆进行强化。
- 后续对话由模型评估问题相关性，结合当前强度自动召回，并附上原文引文。
- 本地 llama.cpp、Ollama，以及显式启用的 OpenAI 兼容 HTTPS Chat Completions API。
- 无模型也可使用明确标注的离线预览；预览候选不冒充模型评分，不进入自动召回。

## 快速开始

需要 Python 3.10–3.13，建议 3.12。在仓库根目录运行：

```powershell
python -m venv .venv-reading
.\.venv-reading\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/check_setup.py
python -m streamlit run app/streamlit_app.py --server.port 8502
```

macOS/Linux 改用 `source .venv-reading/bin/activate` 激活环境。打开 <http://127.0.0.1:8502>，在「设置」选择接口并填写实际模型名。仓库不附带或自动下载模型权重。

- **Ollama**：自行启动 Ollama 并安装本地模型，例如 `ollama pull qwen3:8b`；在设置中选择 Ollama，填写相同模型 ID。
- **llama.cpp**：自行启动带 GGUF 权重的本机服务，填写回环地址的 Chat Completions 接口及模型别名。
- **外部 API**：选择预设或自定义 HTTPS 地址，填写模型 ID、临时会话密钥或密钥环境变量名；明确确认发送范围和费用后才能启用。
- **离线预览**：只检查阅读流程与界面，不需要推理服务；自动记忆对话需要真实模型。

Windows 可选启动脚本：`./scripts/start_local.ps1 -ApiOnly` 只启动页面，`-Ollama` 使用已运行的 Ollama。llama.cpp 模式需传入 `-LlamaServer`、`-ModelPath`，或设置 `MEMORYRUSH_LLAMA_SERVER`、`MEMORYRUSH_MODEL_PATH`。脚本自动创建环境需安装 `uv`；上面的手动安装不需要。

## 模型如何打分

模型分别评估重要性、新颖性、个人相关性、未来用途、启发性、旧记忆关联、证据支持和持久性，并逐项说明理由。程序把前七项与用户显式标注按固定权重合成基础分，持久性用于确定半衰期。高分不能绕过原文引用检查。

```text
文章 → 提取候选 → 模型评分 → 证据/保留检查 → 本地记忆库
问题 → 模型相关性评分 + 衰减后的强度 → 选中证据 → 回答
```

强度根据实际间隔时间计算，刷新页面不会反复衰减。回答真正引用且检查通过的记忆，24 小时内最多强化一次。在「记忆库」展开条目可查看分数、理由、原始评分、原文证据和当前强度。详细权重与公式见[机制说明](docs/READING_ASSISTANT_CN.md)。

## 命令行与测试

```powershell
python -m memoryrush.cli process data/sample_docs/reading_memory_example.txt --provider preview
python -m memoryrush.cli process data/sample_docs/reading_memory_example.txt --provider ollama --model qwen3:8b
python -m memoryrush.cli memories
python -m pytest -q
```

`scripts/smoke_local.py` 是可选的真实本地 llama.cpp 集成检查，使用合成文章和独立验证数据库，不属于离线测试。

## 隐私与边界

Windows 默认数据目录为 `%LOCALAPPDATA%/MemoryRush`，其他系统为 `~/.local/share/MemoryRush`。可通过 `MEMORYRUSH_DATA_DIR` 修改，请避开云同步目录。数据库未加密。API 密钥不写入数据库或处理导出；`.env.example` 仅说明可选设置，应用不会自动加载 `.env`。

API 模式可能发送文章、兴趣、候选记忆、问题和近期对话；单次操作可包含多次收费请求，不会从本地失败自动切换云端。外部接口已通过模拟端到端检查，尚未用第三方真实付费密钥验收；本地 Qwen 已用合成输入完成过真实集成检查。

评分、权重和衰减是可检查的工程规则，不是客观真值概率，也没有证明人类记忆效果提升。引用存在不保证答案的语义完全正确。目前分批扫描启用记忆，大库可能较慢；尚不支持 PDF/OCR、网页抓取、Anthropic 原生 Messages、Responses-only 接口或逐 token 流式输出。

公开仓库只保留安全样例，不上传密钥、私人文章、聊天记录、数据库、模型权重、验证原始轨迹或环境目录。`docs/`、`tasks/` 内旧研究与概念文档保留为历史设计资料，不表示相关实验已实现或验证。
