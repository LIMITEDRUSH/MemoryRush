# MemoryRush 研究计划

英文版：[RESEARCH_PLAN.md](RESEARCH_PLAN.md)

## 概览

项目应按研究原型推进，而不是按宽泛应用推进。最短的有效路径是：

```text
article -> stable paragraphs -> structured memory units -> validation -> small benchmark -> baseline comparison
```

所有功能都应服务 `docs/RESEARCH_SPEC.md` 中的研究问题。

## 依赖图

```text
Research specification
  -> domain and schema contracts
    -> ingestion with stable paragraph IDs
      -> fake-provider pipeline validation
        -> local LLM extraction
          -> artifact storage
            -> small benchmark
              -> evaluation metrics
                -> baseline comparisons
                  -> UI/review workflow
                    -> retrieval and dynamic memory experiments
```

必须按这个顺序推进，因为 MemoryRush 的关键是 evidence-linked outputs。如果 schema 和 validation 不稳，后面的 UI、retrieval 和 model training 都会放大噪声。

## 主要决策

| 决策 | 选择 | 原因 |
|---|---|---|
| 项目定位 | 个人研究原型 | 核心价值是验证 memory-unit extraction 和 recall，不是运营应用。 |
| 第一界面 | CLI/script first，Streamlit later | 最高风险是 memory-unit quality 和 evidence validity。 |
| 第一输入 | TXT/Markdown | 避免 parser noise 干扰研究问题。 |
| 第一 AI 方法 | 本地 LLM prompted extraction | 能快速测试 representation，同时保持 local-first。 |
| 第一 evaluation | 10-20 篇标注文章 | 手工可完成，也足以暴露 failure modes。 |
| 存储顺序 | JSONL artifacts first，SQLite later | 早期更需要可检查 run outputs，不急着做查询功能。 |
| retrieval 顺序 | extraction 评价后再做 vector search | chunk retrieval 是 baseline，不是第一独特贡献。 |

## Phase 0: 重新定位和规划

**目标：** 用研究型 specification 和 task sequence 替代产品型计划。

交付物：

- `docs/RESEARCH_SPEC.md`
- `docs/RESEARCH_SPEC_CN.md`
- `docs/RESEARCH_PLAN.md`
- `docs/RESEARCH_PLAN_CN.md`
- `tasks/plan.md`
- `tasks/plan_CN.md`
- `tasks/todo.md`
- `tasks/todo_CN.md`

验收：

- 研究问题明确。
- 当前计划中移除商业/产品假设。
- 第一项 implementation task 小且可测试。
- deferred features 清楚列出。

验证：

```powershell
rg -n "pricing|subscription|monetization|customer growth|marketing|enterprise" docs tasks README.md README_CN.md
```

这些词只应出现在明确的 non-goals 中。

## Phase 1: Evidence-Preserving Article Representation

**目标：** 让 source text 稳定到足以被后续 AI 输出引用。

任务：

- 确认或调整 `SourceDocument` 和 `SourceParagraph` contracts。
- 解析 TXT 和 Markdown。
- 生成稳定 document ID 和 paragraph IDs。
- 保留 title、source path、document type、paragraph order。
- 添加 parser tests。

验收：

- sample TXT/Markdown 文件能解析为有序 paragraphs。
- unsupported file types 有清楚错误。
- 同一 source content 的 paragraph IDs 稳定。
- parsed output 可以序列化。

验证：

```powershell
python scripts/parse_docs.py data/sample_docs
python -m pytest tests/test_text_parser.py
```

## Phase 2: Structured Memory Output Contracts

**目标：** 在使用 live model 前，先定义生成结果必须长什么样。

任务：

- 定义 Pydantic models：summary、core ideas、evidence spans、memory units、recall questions、processing runs。
- 要求每个 memory unit 引用 paragraph IDs。
- 验证 confidence 和 salience score 范围。
- 添加 invalid-output tests。

验收：

- valid fake outputs 通过 validation。
- missing evidence 失败。
- unknown paragraph IDs 失败。
- duplicate 或 empty memory units 被标记。

验证：

```powershell
python -m pytest tests/pipeline
python -m compileall memoryrush scripts app tests
```

## Phase 3: Fake-Provider End-To-End Pipeline

**目标：** 在没有模型波动的情况下证明 pipeline shape。

任务：

- 创建 provider interface。
- 创建 deterministic fake provider。
- 串起 parse -> prompt context -> provider -> validation -> artifact output。
- 写一个 focused end-to-end test。

验收：

- 一个 sample article 能通过 fake provider 生成 validated artifact。
- 测试不依赖 network 或 Ollama。
- validation issues 清楚可检查。

验证：

```powershell
python -m pytest tests/pipeline
```

## Phase 4: Local LLM Extraction Prototype

**目标：** 用本地模型生成第一批真实候选 memory units。

任务：

- 在 provider interface 后面加入 Ollama adapter。
- 创建 `article_memory_v1` prompt。
- 保存 prompt version、model name 和 run metadata。
- 处理一篇 sample article。
- 检查并记录 failure modes。

验收：

- 一篇 sample article 生成 summary、memory units、evidence IDs 和 recall questions。
- malformed model output 被拒绝或记录。
- 不需要私人数据。

验证：

```powershell
ollama pull qwen2.5:7b-instruct
python scripts/process_article.py data/sample_docs/reading_memory_example.txt
```

## Phase 5: Small Benchmark And Annotation Format

**目标：** 建立第一版 measurement target。

任务：

- 定义 annotation JSONL schema。
- 选择 10-20 篇安全文章。
- 标注 high-salience passages。
- 记录 expected memory-unit ideas 和 evidence paragraph IDs。
- 写 benchmark loader。

验收：

- 每个 benchmark example 都有 source document 和 labels。
- labels 尽量区分 high、medium、low salience。
- benchmark 文件不包含不该提交的私人或版权材料。

验证：

```powershell
python scripts/validate_annotations.py data/annotations
```

## Phase 6: Evaluation Metrics

**目标：** 把人工观察变成可复现数字。

任务：

- 计算 schema pass rate。
- 计算 evidence-link validity。
- 计算 salience 的 Precision@K 和 NDCG@K。
- 计算 duplicate memory-unit rate。
- 计算 recall-question answerability proxy 或人工 review sheet。

验收：

- evaluation 能一条命令运行。
- metrics 写入结果文件。
- limitations 和结果一起记录。

验证：

```powershell
python scripts/evaluate_memory_units.py data/annotations
```

## Phase 7: Baselines

**目标：** 和更简单的方法对比。

任务：

- 实现 summary-only baseline。
- 实现 first/last paragraph 或 section-position heuristic。
- 实现 TF-IDF salience baseline。
- 将 LLM memory extraction 和 baselines 对比。

验收：

- 每个 baseline 输出同一 comparable format。
- results table 至少包含 MemoryRush 和两个 simple baselines。
- 没有 result files 就不声称提升。

验证：

```powershell
python scripts/run_baselines.py data/annotations
python scripts/evaluate_memory_units.py data/annotations
```

## Phase 8: Local Review UI

**目标：** 在 pipeline 和 evaluation 可信后再加入交互。

任务：

- 添加单文章 Streamlit 页面。
- 显示 source paragraphs、memory units、evidence、recall questions。
- 支持手动 accept/edit/reject。
- 持久化 review decisions。

验收：

- UI 不拥有 pipeline logic。
- accept/reject decisions 被保存。
- review 时 evidence 始终可见。

验证：

```powershell
streamlit run app/streamlit_app.py
```

## Phase 9: Retrieval And Dynamic Memory Experiments

**目标：** 在有足够基础后回到原始长期记忆想法。

任务：

- 添加 chunk retrieval baseline。
- 添加 memory-unit retrieval。
- 比较 chunks、summaries、memory units。
- 如果有 review data，再加入 highlight signal。
- 有 retrieval logs 后再做 reinforcement/decay。

验收：

- retrieval experiments 至少比较两种 representation。
- dynamic scoring 有 ablation。
- citation correctness 被测量。

验证：

```powershell
python scripts/evaluate_recall.py data/annotations
```

## Phase 10: Report And Repository Polish

**目标：** 让研究结果清楚可读。

任务：

- 写 concise technical report。
- 包含 method、data、metrics、results、error analysis、limitations。
- 用真实结果更新 README。
- screenshots 只在 UI 反映真实行为后加入。

验收：

- 项目 claims 和 measured results 一致。
- setup commands 可运行。
- 仓库不包含私人数据或 secrets。

验证：

```powershell
python scripts/check_setup.py
python -m pytest
```

## 周期估算

按个人集中开发估算：

| 目标 | 范围 | 估算 |
|---|---|---:|
| 第一条 validated extraction slice | Phase 1-4 | 1-2 周 |
| 小规模 evaluation prototype | Phase 1-6 | 3-5 周 |
| 较强研究项目 | Phase 1-8 | 6-9 周 |
| 完整研究版本 | Phase 1-10 | 10-14 周 |

最大不确定性不是写代码，而是 annotation quality 和 evaluation design。

## 第一项实现任务

从 `tasks/todo.md` 的 `Task 1` 开始：根据当前 parser 确认 source-document 和 paragraph contracts。

这是正确起点，因为后续 memory unit、evidence span、benchmark label 和 citation 都依赖稳定 paragraph identity。
