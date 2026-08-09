# MemoryRush

MemoryRush 是一个本地研究原型，用于从长文阅读材料中提取带原文证据的记忆点。

项目关注一个具体问题：读完一篇文章后，系统能否找出少数值得保留的想法，为每个想法绑定原文证据，并评估这些记忆点是否有助于后续复习和召回？

英文 README：[README.md](README.md)

## 当前范围

第一版刻意保持小范围：

- 将 TXT 和 Markdown 文章解析为稳定段落；
- 生成结构化摘要、核心观点、memory units、证据链接和 recall questions；
- 验证生成的 memory units 是否能追溯到原文段落；
- 构建小规模标注 benchmark；
- 和 summary-only、chunk-based retrieval 等简单 baseline 对比。

这个仓库当前不是 SaaS 产品、笔记平台、浏览器插件，也不是商业阅读应用。

## 文档

| 文档 | 英文 | 中文 |
|---|---|---|
| 研究规格 | [docs/RESEARCH_SPEC.md](docs/RESEARCH_SPEC.md) | [docs/RESEARCH_SPEC_CN.md](docs/RESEARCH_SPEC_CN.md) |
| 研究计划 | [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md) | [docs/RESEARCH_PLAN_CN.md](docs/RESEARCH_PLAN_CN.md) |
| 实施计划 | [tasks/plan.md](tasks/plan.md) | [tasks/plan_CN.md](tasks/plan_CN.md) |
| 任务清单 | [tasks/todo.md](tasks/todo.md) | [tasks/todo_CN.md](tasks/todo_CN.md) |

原始构想记录保留在 `docs/MemoryPoint_*` 文件中。

## 快速开始

推荐 Python 版本：`3.10` 到 `3.12`。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/check_setup.py
python -m memoryrush.cli samples
streamlit run app/streamlit_app.py
```

后续 extraction 实验可选本地模型：

```powershell
ollama pull qwen2.5:7b-instruct
```

## 项目方向

计划中的 pipeline：

```text
article
-> stable source paragraphs
-> structured memory candidates
-> evidence validation
-> reviewable artifacts
-> benchmark evaluation
-> baseline comparison
```

第一项实现任务是确认 source-document 和 paragraph contracts，因为后续 memory unit、citation、annotation 和 evaluation 都依赖稳定的原文引用。

## 隐私

不要提交私人文档、个人阅读日志、API keys、本地模型缓存或生成的个人 memory database。公开示例应使用安全 sample documents 或 synthetic data。
