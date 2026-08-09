# MemoryPoint 实施清单

这份清单按实际开发顺序排列。原则是每一阶段都产出一个能运行的小闭环，先做本地 baseline RAG，再逐步加 memory point、highlight、dynamic memory、evaluation。

## 架构顺序

后续实现按下面的边界推进：

```text
UI / CLI
  -> application use cases
    -> domain models
    -> pipeline stages
      -> provider interfaces
    -> persistence repositories
    -> evaluation services
```

核心规则：

- UI 和 CLI 只做入口，不直接拥有业务逻辑。
- domain 不依赖 Streamlit、SQLite、FAISS、Ollama 或文件 IO。
- AI pipeline 每个阶段都要有明确输入和输出。
- prompts 后续要放到独立目录并版本化。
- evaluation 要作为正式模块，不要等最后才补。
- 当前最先迁移的是 domain boundary，然后再做 chunking。

## Phase 0: 环境和仓库准备

目标：项目能被别人 clone 后跑起来。

任务：

- 建 Python 项目结构。
- 建 `requirements.txt` 或 `pyproject.toml`。
- 建 `.env.example`。
- 建 `data/sample_docs/`。
- 建 README quickstart。
- 安装基础依赖。
- 安装 Ollama，并拉取本地模型。

推荐命令：

```powershell
pip install streamlit sentence-transformers faiss-cpu scikit-learn pandas numpy pydantic
ollama pull qwen2.5:7b-instruct
```

验收标准：能运行一个空的 CLI 或 Streamlit 页面。

## Phase 1: 文档读取

目标：先只支持 TXT / Markdown。

任务：

- 定义 `Document` 数据结构。
- 定义 `Paragraph` 数据结构。
- 实现 TXT parser。
- 实现 Markdown parser。
- 给每个 paragraph 保存 `document_id`、`paragraph_id`、`source_path`、`position`、`text`。
- 准备 3-5 篇 sample docs。
- 写解析脚本。

推荐命令：

```powershell
python scripts/parse_docs.py data/sample_docs
```

验收标准：输入文件夹，输出结构化 JSON。

## Phase 2: Chunking

目标：把 paragraph 变成可检索 chunks。

任务：

- 定义 `Chunk` 数据结构。
- 实现按 token 或字符长度合并 paragraph。
- 保留 source metadata。
- 给 chunk 保存 `chunk_id`、`document_id`、`paragraph_ids`、`text`、`source_path`、`start_position`、`end_position`。
- 输出 `data/processed/chunks.jsonl`。

验收标准：每个 chunk 都能追溯回原文 paragraph。

## Phase 3: 本地 Embedding + FAISS 检索

目标：先做最小 retrieval baseline。

任务：

- 用 `sentence-transformers` 加载 embedding model。
- 第一版使用 `BAAI/bge-small-en-v1.5`。
- 为 chunks 生成 embeddings。
- 建 FAISS index。
- 保存 `data/index/faiss.index`。
- 保存 `data/index/chunk_metadata.json`。
- 写搜索脚本。

推荐命令：

```powershell
python scripts/search.py "What is this article about?"
```

验收标准：输入 query，返回 top-k chunks 和 source。

## Phase 4: Baseline RAG Answer

目标：让本地 LLM 基于检索结果回答。

任务：

- 写 Ollama client。
- 检索 top-k chunks。
- 拼接 prompt。
- 要求回答必须包含 source。
- 写 `ask.py`。

推荐命令：

```powershell
python scripts/ask.py "What are the key ideas?"
```

验收标准：能基于本地文档回答，并引用 chunk/source。

## Phase 5: 文章总结

目标：每篇文章能生成 summary。

任务：

- 读取 document paragraphs。
- 对长文分段总结。
- 再做 final summary。
- 保存 `document_id`、`summary_paragraphs`、`source_paragraph_ids`、`created_at`。
- 第一版用本地 Ollama 模型。

验收标准：每篇 sample doc 有结构化 summary。

## Phase 6: Memory Point 提取

目标：从文章中生成候选 memory points。

任务：

- 定义 `MemoryPoint` 数据结构。
- 字段包括 `memory_id`、`document_id`、`content`、`evidence`、`source_paragraph_ids`、`tags`、`memory_type`、`base_score`、`created_at`。
- 用 LLM 从 summary + source 提取 3-8 个候选点。
- 要求每个 memory point 必须带 evidence。
- 保存到 JSONL 或 SQLite。

验收标准：每篇文章能生成可追溯证据的 memory points。

## Phase 7: SQLite Memory Bank

目标：长期记忆能保存和查询。

任务：

- 建 SQLite schema。
- 表包括 `documents`、`paragraphs`、`chunks`、`memory_points`、`highlights`、`recall_events`。
- 把 documents、chunks、memory_points 写入数据库。
- 写 `list_memory_points()`。
- 写 `get_memory_by_id()`。
- 写 `search_memory_points()`。
- 写简单 CLI 查看 memory bank。

验收标准：关闭程序后，memory bank 仍然存在。

## Phase 8: Memory Scoring

目标：memory point 有初始分数。

任务：

- 先用规则分数，不急着训练模型。
- 字段包括 `importance`、`novelty`、`usefulness`、`evidence_strength`、`user_highlight_signal`、`base_score`。
- LLM 可以辅助给维度打分，但结果要结构化保存。

推荐公式：

```text
base_score =
0.25 * importance
+ 0.20 * usefulness
+ 0.20 * novelty
+ 0.20 * evidence_strength
+ 0.15 * user_highlight_signal
```

验收标准：memory bank 能按 score 排序。

## Phase 9: Streamlit 阅读界面

目标：开始有可演示 demo。

页面：

- `Upload / Paste`
- `Reading View`
- `Memory Bank`

任务：

- 上传 TXT / Markdown。
- 展示原文 paragraphs。
- 展示 summary。
- 展示 memory points。
- 显示 score 和 evidence。

验收标准：不用命令行也能跑完整流程。

## Phase 10: Highlight 反馈

目标：用户行为能影响 memory。

任务：

- 在 paragraph 旁加 highlight 按钮。
- 支持 `important`、`surprising`、`useful`、`disagree`、`remember_this`、`unclear`。
- 保存到 `highlights` 表。
- highlight 后更新相关 memory point 的 `user_highlight_signal` 和 `base_score`。
- Memory Bank 里显示来源 highlight。

验收标准：用户 highlight 会改变 memory score。

## Phase 11: Dynamic Memory

目标：实现强化和衰减。

任务：

- 给 memory point 加 `recall_count`、`last_recalled_at`、`current_strength`、`decay_rate`。
- 每次被检索或用于回答，写入 `recall_events`。
- 实现 current strength 更新。
- Memory Bank 显示 `current_strength`。

推荐公式：

```text
current_strength =
base_score * exp(-decay_rate * days_since_last_recall)
+ alpha * log(1 + recall_count)
+ gamma * user_feedback_score
```

验收标准：记忆会因为被召回而增强，长期不用会下降。

## Phase 12: Recall Chat

目标：对历史 memory 对话。

任务：

- Query 同时检索 chunks、memory_points、highlights。
- 按 hybrid score 排序。
- 回答时显示 source chunks、memory points used、highlights used。
- UI 加 `Recall Chat` tab。

验收标准：能问“我之前读过哪些内容和 RAG hallucination 有关？”

## Phase 13: 标注数据集

目标：开始把项目变成 ML 项目。

任务：

- 先做 20 篇，不要一开始做 100 篇。
- 每篇标注 high salience passages。
- 每篇标注 medium salience passages。
- 每篇标注 low salience passages。
- 标注 evidence span。
- 标注 memory point。
- 标注 tags。
- 保存为 JSONL。
- 写 annotation guideline。

验收标准：有一个可训练、可评估的小数据集。

## Phase 14: ML Baselines

目标：不要全靠 LLM。

任务：

- 训练 TF-IDF + Logistic Regression。
- 训练 Sentence-BERT + Logistic Regression。
- 训练 Sentence-BERT + MLP。
- 输出 salience score。
- 和 LLM scorer 对比。

验收标准：能跑出 Precision@K 和 NDCG@K。

## Phase 15: Evaluation

目标：做结果表。

对比系统：

- Standard RAG。
- Summary Memory。
- Static MemoryPoint。
- MemoryPoint without highlight。
- MemoryPoint without decay。
- Full MemoryPoint。

指标：

```text
Precision@5
Recall@5
NDCG@5
MRR
Citation correctness
Unsupported answer rate
```

验收标准：README 里能放真实结果表。

## Phase 16: Report + Polish

目标：变成可以展示的项目。

任务：

- 写 technical report。
- README 加 architecture。
- README 加 results。
- 加 screenshots。
- 录 demo video。
- 清理 sample data。
- 确认没有 API key 或私人文档。

验收标准：别人打开 GitHub，3 分钟内能看懂项目价值。

## 最先做的 7 天计划

Day 1：

- 项目结构。
- requirements。
- sample docs。

Day 2：

- TXT parser。
- Markdown parser。

Day 3：

- chunking。
- metadata。

Day 4：

- sentence-transformers embedding。

Day 5：

- FAISS search。

Day 6：

- Ollama `ask.py`。

Day 7：

- README quickstart。
- 确保 baseline RAG 跑通。

## 当前第一目标

```text
先做一个完全本地运行的 baseline RAG，然后再在它上面加 memory point layer。
```
