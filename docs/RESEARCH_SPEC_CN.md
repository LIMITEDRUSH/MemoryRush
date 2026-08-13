# MemoryRush 研究规格

英文版：[RESEARCH_SPEC.md](RESEARCH_SPEC.md)

## 基本假设

1. MemoryRush 是个人研究型 AI/ML 工程项目。
2. 第一位真实用户是项目作者本人，阅读技术文章、论文、笔记和教育材料。
3. 项目目标是验证一个阅读记忆与检索想法。
4. 优先本地运行，因为阅读材料可能涉及隐私，也因为可复现性很重要。
5. 一个小而可测的研究原型，比一个功能很宽但无法评估的应用更有价值。
6. 初始 benchmark 可以小，但必须明确、可重复，并诚实记录限制。

## 目标

MemoryRush 研究的是：AI 系统能否把长文阅读转化为持久、可证据追溯、适合后续召回的 memory units，并且比普通摘要或普通 chunk retrieval 更有用。

核心研究问题：

```text
由 salience 选择并结合用户反馈的 source-grounded memory units，
能否在长期阅读召回任务上优于 summary-only 和 chunk-based retrieval baseline？
```

项目应产出：

- 本地研究原型。
- 明确的 memory-unit schema。
- 小规模标注 benchmark。
- baseline 对比。
- evaluation 结果。
- 技术报告或项目 write-up。

## MemoryRush 是什么

MemoryRush 是本地阅读记忆研究系统。给定一篇文章，它应解析原文，识别候选的“值得记住的想法”，把每个 memory unit 绑定到原文证据，生成复习问题，并保存 review decision 以便后续评价。

它不是：

- 文档聊天机器人。
- 通用摘要器。
- 笔记软件复刻。
- flashcard 生成器。
- 向量检索 demo。

它的核心主张是：阅读记忆应该是选择性的、有证据的、可评价的。

## 研究问题

### RQ1: Salience

MemoryRush 能否选择出人类认为值得记住的文章段落或想法？

早期指标：在小规模人工标注 benchmark 上计算 Precision@K 和 NDCG@K。

### RQ2: Source Grounding

每个生成的 memory unit 能否追溯到支持它的原文段落？

早期指标：evidence coverage、invalid evidence-reference rate、unsupported memory-unit rate。

### RQ3: Review Usefulness

生成的 memory units 和 recall questions 是否有用到值得用户接受或轻微编辑？

早期指标：accept/edit/reject rate、usefulness rating、duplicate/noise rate。

### RQ4: Retrieval Benefit

后续提问时，memory units 是否比 raw chunks 或 summaries 提供更好的召回质量？

后续指标：Precision@K、NDCG@K、citation correctness、human preference。

### 延后问题：Dynamic Memory

reinforcement 和 decay 是否能让长期 retrieval ranking 优于静态 memory storage？

这是原始想法的重要部分，但应放在第一条 memory-unit extraction 和 evaluation 闭环跑通之后。

## 范围

### 第一条研究 slice

第一条 slice 应处理一篇 TXT 或 Markdown 文章，并产出可 review 的结构化结果：

- 标准化文章 metadata。
- 有序 source paragraphs。
- 简短 summary。
- 3-7 个候选 core ideas。
- memory units。
- evidence references。
- recall questions。
- validation report。

早期可以先手动 review 输出。完整 UI 有用，但第一阶段应先证明 pipeline 和 schema。

### 第一个可验证原型必须包含

- TXT 和 Markdown ingestion。
- 稳定 paragraph IDs。
- 结构化 memory-unit schema。
- deterministic fake-provider tests。
- 本地 LLM provider 路径，优先 Ollama。
- 本地输出存储，早期可用 JSONL 或 SQLite。
- 10-20 篇文章的 benchmark，包含人工标注 salient passages 或 expected memory units。
- evaluation 脚本，覆盖 schema validity、evidence coverage、salience ranking、duplicate rate。

### 原型有用之后再做

- PDF、DOCX、URL ingestion。
- 多文档召回。
- embedding search 和 vector indexes。
- reinforcement 和 decay。
- highlight-driven personalization。
- memories 之间的 graph relations。
- custom model training。
- polished Streamlit workflow。

这些不是被否定，而是排在第一条可验证 extraction/evaluation 闭环之后。


## 技术栈

### 选择

- 语言：Python `>=3.10,<3.14`
- 数据契约：Pydantic，用于结构化 AI 输出验证。
- CLI/scripts：Python scripts 和 `memoryrush.cli`。
- 本地 UI：Streamlit，在 pipeline 稳定之后。
- 本地 LLM：Ollama first。
- 存储：早期 generated artifacts 用 JSONL；review state 需要查询后再用 SQLite。
- ML/evaluation：scikit-learn、pandas、numpy。
- 后续 embeddings：sentence-transformers。
- 后续 vector search：FAISS，仅在 retrieval experiments 开始后引入。
- 测试：pytest。

### 为什么这样选

Python 最适合文本处理、本地 LLM、ML baseline、evaluation 和快速研究迭代。Streamlit 适合作为本地研究 UI，但不应成为核心逻辑层。Pydantic 有必要，因为 MemoryRush 依赖结构化 AI 输出验证。SQLite 适合 review decisions 和 evaluation examples 需要持久查询时使用。FAISS 和 embedding model 暂缓，因为第一阶段未解决的问题不是检索速度，而是 memory units 是否值得生成。

## 架构决策

使用本地 modular monolith：

```text
CLI / Streamlit
  -> application workflows
    -> domain models
    -> ingestion
    -> memory extraction pipeline
      -> prompts
      -> provider interfaces
    -> validation
    -> local storage
    -> evaluation
```

### 备选方案比较

| 方案 | 优点 | 对 MemoryRush 的问题 | 决策 |
|---|---|---|---|
| 只用 Notebook | 最快画出研究草图 | 难测试、难版本化、难复现 | 只用于探索，不做核心 pipeline |
| 模块化 Python package | 可测试、可复用、适合研究 | 比 notebook 多一点结构成本 | 采用 |
| 单独 backend + frontend | 后期边界更清楚 | 在研究验证前增加 API 和部署负担 | 延后 |
| 先做完整 RAG stack | 熟悉、容易展示 | 会推迟最独特的 memory-unit 问题 | extraction baseline 后再做 |
| 先训练自定义模型 | ML 味更强 | schema 和标签没稳定前训练没有意义 | benchmark 存在后再做 |

## Domain Model

初始实体：

| Entity | 作用 |
|---|---|
| `SourceDocument` | 一篇输入文章及其 metadata。 |
| `SourceParagraph` | 有序段落，包含稳定 ID 和 source position。 |
| `ProcessingRun` | 使用某个 prompt/model/config 处理文档的一次运行。 |
| `CoreIdea` | 从原文选择出的候选核心想法。 |
| `EvidenceSpan` | source paragraph ID 和支持性 quote。 |
| `MemoryUnit` | 面向后续召回的持久记忆表述。 |
| `RecallQuestion` | 关联到 memory unit 的问题和 expected answer。 |
| `ValidationIssue` | 输出被拒绝或需要 review 的结构化原因。 |
| `ReviewDecision` | 人工 accept/edit/reject 决策。 |
| `EvaluationExample` | 用于 salience 和 evidence 检查的标注样本。 |

延后实体：

- `MemoryState`：reinforcement 和 decay。
- `Highlight`：显式用户反馈。
- `MemoryRelation`：support/conflict/extension。
- `EmbeddingChunk`：retrieval baselines。

## Pipeline Contract

第一条可验证 pipeline：

```text
Input file/text
-> parse into SourceDocument + SourceParagraph[]
-> build prompt context
-> generate structured candidate output
-> validate schema and evidence links
-> write run artifact
-> compare against labels when available
```

最小结构化输出：

```json
{
  "summary": "Concise source-grounded article summary.",
  "core_ideas": [
    {
      "idea": "A specific idea worth remembering.",
      "why_it_matters": "Reason this idea may be useful later.",
      "evidence": {
        "paragraph_id": "p_003",
        "quote": "Exact or near-exact supporting source text."
      },
      "salience_score": 0.82
    }
  ],
  "memory_units": [
    {
      "content": "A durable memory statement.",
      "memory_type": "conceptual_insight",
      "evidence_paragraph_ids": ["p_003"],
      "tags": ["RAG", "retrieval"],
      "confidence": 0.78
    }
  ],
  "recall_questions": [
    {
      "question": "What is the remembered claim?",
      "expected_answer": "The answer supported by the memory unit.",
      "memory_unit_index": 0
    }
  ]
}
```

validation 必须拒绝或标记：

- 没有 evidence paragraph IDs 的 memory units。
- evidence paragraph IDs 不存在于 source document。
- 空的或重复的 memory units。
- unsupported quotes。
- malformed model output。

## AI/ML 方法

### Stage 1: Prompted Extraction Baseline

先用本地 LLM 做 extraction，因为它可以快速测试 memory-unit representation。prompt 必须要求结构化 JSON 和 evidence references。

### Stage 2: Heuristic And Summary Baselines

尽早加入简单 baseline：

- summary-only memory。
- first/last paragraph heuristic。
- keyword 或 TF-IDF salience heuristic。

这样可以避免在没有对比的情况下高估 LLM pipeline。

### Stage 3: Small Labeled Benchmark

模型训练前先构建 10-20 篇文章的标注集，标注 high-salience passages 和 expected memory units。

### Stage 4: ML Ranking Baselines

benchmark 存在后再做：

- TF-IDF + Logistic Regression。
- Sentence-BERT + Logistic Regression。
- 如果标签足够，再做 Sentence-BERT + MLP。
- LLM scorer baseline。
- hybrid ranker，结合 salience、evidence quality 和后续 user feedback。

## Evaluation Strategy

### 早期评价

- schema pass rate。
- evidence reference validity。
- evidence quote support rate。
- duplicate memory-unit rate。
- memory unit count 是否在目标范围。
- manual accept/edit/reject rate。

### Benchmark Evaluation

- Precision@K。
- NDCG@K。
- label 足够完整时计算 Recall@K。
- citation correctness。
- unsupported memory-unit rate。
- recall-question answerability。

### 后续 Retrieval Evaluation

比较：

- chunk-based retrieval。
- summary-only retrieval。
- static memory units。
- 带 user feedback 的 memory units。
- 带 reinforcement/decay 的 memory units。

没有可复现脚本和结果文件前，不声称提升。

## 命令

项目成熟过程中预计保留这些命令：

```powershell
python scripts/check_setup.py
python -m memoryrush.cli health
python -m memoryrush.cli samples
python scripts/parse_docs.py data/sample_docs
python -m pytest
python -m compileall memoryrush scripts app tests
streamlit run app/streamlit_app.py
```

未来研究命令：

```powershell
python scripts/process_article.py data/sample_docs/reading_memory_example.txt
python scripts/evaluate_memory_units.py data/annotations
```

## 仓库结构

```text
memoryrush/
  domain/             纯实体和 validation-friendly models
  ingestion/          先支持 TXT/Markdown，后续扩展 parser
  pipeline/           extraction orchestration 和 structured contracts
  prompts/            versioned prompt templates
  providers/          LLM provider interfaces 和 Ollama adapter
  storage/            JSONL/SQLite persistence
  evaluation/         benchmark loading 和 metrics
  cli.py              thin command entry point
app/
  streamlit_app.py    本地研究 UI
scripts/
  check_setup.py
  parse_docs.py
  process_article.py
  evaluate_memory_units.py
tests/
  domain/
  ingestion/
  pipeline/
  evaluation/
docs/
  RESEARCH_SPEC.md
  RESEARCH_SPEC_CN.md
  RESEARCH_PLAN.md
  RESEARCH_PLAN_CN.md
data/
  sample_docs/
  annotations/
  processed/          ignored generated artifacts
```

## Code Style

核心代码应直接、清楚、可测试。domain 和 pipeline 代码应有类型，尽量 deterministic，并能用 fake provider 测试。

```python
class MemoryUnit(BaseModel):
    content: str
    memory_type: str
    evidence_paragraph_ids: list[str]
    tags: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
```

规则：

- Domain models 不 import Streamlit、Ollama、SQLite、FAISS。
- Provider adapters 不包含项目逻辑。
- Prompts 放在文件中并版本化。
- Scripts 调用 package 内可复用函数，不拥有核心行为。
- 先用 fake providers 测试，再做 live model check。

## 边界

Always:

- 保留 paragraph-level evidence links。
- 保存前验证结构化 AI 输出。
- generated artifacts 和 source data 分开。
- evaluation 可复现。
- 第一条 implementation slice 保持小。

Ask first:

- 添加 cloud dependency。
- 改 benchmark scope。
- 引入新的 major dependency。
- 替换 local-first 假设。
- 在第一条 slice 中扩展 TXT/Markdown 之外的 ingestion。

Never:

- 提交私人文档、阅读日志、API keys、model caches 或个人 memory database。
- 没有 evaluation script 和结果文件就声称性能提升。
- 在 memory extraction loop 验证前做宽泛 app features。
- 把 summary quality 当成项目成功的唯一标准。

## 下一里程碑成功标准

下一里程碑完成时应满足：

- 一篇 TXT/Markdown 文章能被解析成稳定段落。
- fake provider 能产出有效 structured memory output。
- invalid evidence links 会被测试捕获。
- 一个本地 LLM run 能对 sample article 产生可 review 输出。
- artifact 记录 prompt/model/config metadata。
- 10-20 篇文章 benchmark 格式已定义。

## Open Questions

1. 第一版 manual benchmark 做 10 篇还是 20 篇？
2. 早期 generated artifacts 用 JSONL，还是直接引入 SQLite？
3. 默认本地模型用 `qwen2.5:7b-instruct`，还是机器上可用的其他 Qwen/Llama 模型？
4. 项目名继续使用 MemoryRush、概念名使用 MemoryPoint，还是统一成一个名称？
