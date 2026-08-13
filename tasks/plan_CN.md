# 实施计划：MemoryRush 研究原型

英文版：[plan.md](plan.md)

## 概览

MemoryRush 应重新作为个人 AI/ML 研究原型推进。第一条有价值的 vertical slice 不是完整阅读应用，而是一个 evidence-preserving pipeline：输入一篇文章，输出经过验证、可追溯原文证据的 memory units，并能在小 benchmark 上评价。

## 架构决策

- 使用本地 modular Python package，因为项目需要可复现实验、测试和可检查输出。
- 先做 CLI/scripts，再做 UI，因为最高风险是 memory-unit quality 和 evidence validity。
- 先支持 TXT/Markdown，因为复杂 parsing noise 会干扰研究问题。
- live model 前先定义 Pydantic-style structured contracts，因为模型输出必须可验证。
- Ollama 前先做 fake-provider tests，因为可复现性很重要。
- 早期先用 JSONL run artifacts；review decisions 需要查询后再引入 SQLite。
- extraction 和 evaluation 跑通前，暂缓 vector retrieval、dynamic memory 和复杂 UI。

## 任务列表

### Phase 0: Research Reframing

- [x] Task 0: 用研究规格和研究计划替代产品型规划。

### Checkpoint: Planning

- [ ] 人工确认 `docs/RESEARCH_SPEC.md` 和 `docs/RESEARCH_PLAN.md` 符合当前方向。
- [ ] 研究规格被接受或修正前，不开始实现。

### Phase 1: Evidence-Preserving Source Representation

- [x] Task 1: 确认 source document 和 paragraph contracts。
- [x] Task 2: 根据 contracts 验证 TXT/Markdown parser 行为。

### Checkpoint: Source Representation

- [x] sample documents 能解析成稳定有序 paragraphs。
- [x] unsupported inputs 有清楚错误。
- [x] parsed output 能序列化并供后续 pipeline 使用。

说明：parser 行为已通过 compile checks、parser script output 和手工 assertions 验证。正式 `pytest` 命令需要等当前 Python 环境安装 `pytest` 后再跑。

### Phase 2: Structured Memory Pipeline

- [x] Task 3: 定义 structured memory output contracts。
- [x] Task 4: 添加 output validation rules。
- [x] Task 5: 构建 fake-provider end-to-end pipeline test。

### Checkpoint: Pipeline Shape

- [x] valid fake output 通过。
- [x] missing 或 invalid evidence 失败。
- [x] pipeline tests 不需要 live model。

说明：Phase 2 contracts 当前使用标准库 dataclasses，因为 active environment 没有安装 `pydantic`。行为已通过手工 assertions 和 compile checks 验证；正式 `pytest` 仍需等测试依赖安装后再跑。

### Phase 3: Local LLM Prototype

- [x] Task 6: 添加 local LLM provider interface 和 Ollama adapter。
- [x] Task 7: 创建第一版 versioned memory extraction prompt。
- [x] Task 8: 为一篇 sample article 保存 local model run artifact。

### Checkpoint: First Real Output

- [x] 使用 deterministic fake provider 时，一篇 sample article 能生成 summary、memory units、evidence 和 recall questions。
- [x] prompt version、model name、validation result 被记录。
- [x] 真实 local model run 的 failure modes 和限制已记录。

说明：`qwen3:8b` 已通过 Ollama 在 RTX 3070 Ti Laptop GPU 上完成真实运行，并生成 `data/processed/qwen3_8b_article_memory_artifact.json`。输出通过当前 schema/evidence validation。人工检查发现 salience 分数未校准、一个 tag 不准确，而且当前 validation 尚不能证明 MemoryUnit 的完整语义被证据支持。

### Phase 4: Benchmark And Evaluation

- [ ] Task 9: 定义 annotation schema。
- [ ] Task 10: 创建第一版 10-20 篇文章 benchmark。
- [ ] Task 11: 添加 evaluation metrics。
- [ ] Task 12: 添加 simple baselines。

### Checkpoint: Measured Prototype

- [ ] evaluation 能一条命令运行。
- [ ] results 对比 MemoryRush output 和 simple baselines。
- [ ] README/project report 只使用 measured claims。

### Phase 5: Review UI And Later Experiments

- [ ] Task 13: 添加 local review UI。
- [ ] Task 14: 持久化 review decisions。
- [ ] Task 15: 添加 retrieval comparisons。
- [ ] Task 16: 有 retrieval logging 后再添加 reinforcement/decay experiment。

### Checkpoint: Research Demo

- [ ] demo 反映已经评价过的 pipeline。
- [ ] retrieval 和 dynamic memory 有 ablations。
- [ ] report 包含 limitations 和 reproducible commands。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 生成的 memory units 变成普通摘要 | High | 要求 evidence links、小输出预算和 salience evaluation。 |
| LLM 输出难复现 | High | 使用 fake-provider tests，保存 prompt/model metadata，并评价 artifacts。 |
| 标注耗时太长 | Medium | 先做 10 篇，只有指标有用时再扩展。 |
| UI 分散研究重点 | Medium | 先做 CLI/evaluation，pipeline 证明后再做 Streamlit。 |
| retrieval stack 过早膨胀 | Medium | memory-unit quality 被测量后再引入 FAISS/vector work。 |

## Open Questions

- 第一版 benchmark 做 10 篇还是 20 篇？
- early run artifacts 只用 JSONL，还是 Phase 3 直接开始 SQLite？
- 哪个 local model 作为默认可复现实例？
- 文档中 MemoryRush 和 MemoryPoint 是否要统一命名，还是保持项目名/概念名区分？
