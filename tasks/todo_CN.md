# MemoryRush 研究任务清单

英文版：[todo.md](todo.md)

## Task 0: Research Reframing

**说明：** 用研究型 specification 和有序 execution plan 替代之前的产品型 MVP plan。

**验收标准：**
- [x] `docs/RESEARCH_SPEC.md` 存在。
- [x] `docs/RESEARCH_PLAN.md` 存在。
- [x] `tasks/plan.md` 和 `tasks/todo.md` 反映研究顺序。

**验证：**
- [ ] 人工确认新方向。

**依赖：** 无

**可能修改文件：**
- `docs/RESEARCH_SPEC.md`
- `docs/RESEARCH_PLAN.md`
- `tasks/plan.md`
- `tasks/todo.md`

**预计范围：** Small：仅文档

## Task 1: Finalize Source Document Contracts

**说明：** 定义 evidence-grounded memory extraction 所需的最小 source document 和 paragraph 字段。

**验收标准：**
- [ ] Document contract 包含 ID、title、source path 或 source label、document type、paragraphs。
- [ ] Paragraph contract 包含 stable ID、text、position、source reference。
- [ ] contract 命名和 research spec 一致，或记录兼容原因。

**验证：**
- [ ] 现有 parser tests 通过。
- [ ] 对照 `docs/RESEARCH_SPEC.md` 手动 review。

**依赖：** Task 0

**可能修改文件：**
- `memoryrush/domain/`
- `tests/`

**预计范围：** Small：1-2 files

## Task 2: Verify TXT/Markdown Parsing

**说明：** 确保 TXT 和 Markdown 输入能产生适合 evidence references 的稳定有序 paragraphs。

**验收标准：**
- [ ] 支持 `.txt`、`.md`、`.markdown`。
- [ ] unsupported suffixes 有清楚失败信息。
- [ ] unchanged content 的 paragraph IDs 稳定。
- [ ] Markdown H1 title extraction 有测试覆盖。

**验证：**
- [ ] `python scripts/parse_docs.py data/sample_docs`
- [ ] `python -m pytest tests/test_text_parser.py`

**依赖：** Task 1

**可能修改文件：**
- `memoryrush/ingestion/`
- `scripts/parse_docs.py`
- `tests/test_text_parser.py`

**预计范围：** Small to Medium：2-3 files

## Task 3: Define Structured Memory Output Contracts

**说明：** 创建 summary、core ideas、evidence spans、memory units、recall questions、processing runs 的 typed contracts。

**验收标准：**
- [ ] 每个 memory unit 至少要求一个 evidence paragraph ID。
- [ ] confidence 和 salience scores 有范围限制。
- [ ] recall questions 链接到 memory unit。
- [ ] processing run metadata 可以记录 prompt version 和 model name。

**验证：**
- [ ] contract unit tests 能实例化 valid examples。
- [ ] invalid examples validation 失败。

**依赖：** Task 2

**可能修改文件：**
- `memoryrush/pipeline/`
- `tests/pipeline/`

**预计范围：** Medium：3-5 files

## Task 4: Add Evidence Validation

**说明：** 验证 generated evidence references 是否指向真实 source paragraphs，并检查空/重复输出。

**验收标准：**
- [ ] unknown paragraph IDs 被报告为 validation issues。
- [ ] empty memory units 被拒绝。
- [ ] duplicate memory units 被标记。
- [ ] validation output 可被 tests 和 scripts 检查。

**验证：**
- [ ] `python -m pytest tests/pipeline`

**依赖：** Task 3

**可能修改文件：**
- `memoryrush/pipeline/`
- `tests/pipeline/`

**预计范围：** Medium：2-4 files

## Task 5: Build Fake-Provider Pipeline Test

**说明：** 用 deterministic fake provider 串起 parsing、provider output、validation 和 artifact generation。

**验收标准：**
- [ ] 一个 sample article 可以不依赖 live model 跑完 pipeline。
- [ ] valid fake output 生成 valid artifact。
- [ ] invalid fake output 生成 validation issues。

**验证：**
- [ ] `python -m pytest tests/pipeline`
- [ ] `python -m compileall memoryrush scripts app tests`

**依赖：** Task 4

**可能修改文件：**
- `memoryrush/pipeline/`
- `memoryrush/providers/`
- `tests/pipeline/`

**预计范围：** Medium：3-5 files

## Task 6: Add Local LLM Provider Interface

**说明：** 添加 provider interface 和 Ollama adapter，避免 provider details 进入 domain 或 UI。

**验收标准：**
- [ ] Provider interface 接收 prompt/context，返回 structured text 或 JSON。
- [ ] Ollama adapter 对 missing service/model 给出清楚错误。
- [ ] 测试可使用 fake provider，不 import Ollama-specific code。

**验证：**
- [ ] Provider unit tests。
- [ ] 模型安装后进行 manual Ollama smoke test。

**依赖：** Task 5

**可能修改文件：**
- `memoryrush/providers/`
- `tests/providers/`

**预计范围：** Medium：3-5 files

## Task 7: Create Versioned Memory Extraction Prompt

**说明：** 编写第一版 article-to-memory extraction prompt，并把它放在 UI 之外。

**验收标准：**
- [ ] Prompt 要求 summary、core ideas、memory units、evidence IDs、recall questions。
- [ ] prompt version 和 processing results 一起保存。
- [ ] Prompt 明确要求 evidence paragraph IDs 来自 source context。

**验证：**
- [ ] Manual prompt review。
- [ ] fake-provider 或 prompt-rendering test。

**依赖：** Task 6

**可能修改文件：**
- `memoryrush/prompts/`
- `memoryrush/pipeline/`
- `tests/pipeline/`

**预计范围：** Small to Medium：2-3 files

## Task 8: Save First Local Model Run Artifact

**说明：** 用 local model 处理一篇安全 sample article，并保存可检查 artifact。

**验收标准：**
- [ ] Artifact 包含 input document ID、prompt version、model name、raw output、parsed output、validation status。
- [ ] 不使用私人数据。
- [ ] 如果输出 invalid，记录 failure modes。

**验证：**
- [ ] `ollama pull qwen2.5:7b-instruct`
- [ ] `python scripts/process_article.py data/sample_docs/reading_memory_example.txt`

**依赖：** Task 7

**可能修改文件：**
- `scripts/process_article.py`
- `memoryrush/pipeline/`
- `data/processed/` ignored artifact output

**预计范围：** Medium：3-5 files

## Task 9: Define Annotation Schema

**说明：** 定义 benchmark labels 的 JSONL 格式，用于评价 salience 和 evidence grounding。

**验收标准：**
- [ ] Schema 包含 document ID、paragraph ID、salience label、expected memory idea、evidence reference。
- [ ] Schema 支持 high、medium、low salience labels。
- [ ] example annotation file 不包含私人数据。

**验证：**
- [ ] Annotation schema check script 或 focused test。

**依赖：** Task 5

**可能修改文件：**
- `docs/`
- `data/annotations/`
- `tests/evaluation/`

**预计范围：** Small to Medium：2-4 files

## Task 10: Create First Benchmark

**说明：** 构建 10-20 篇安全文章的小 benchmark，包含 salience labels 和 expected memory units。

**验收标准：**
- [ ] 每个 benchmark document 有 parsed source paragraphs。
- [ ] 每篇文档至少有几个 high-salience labels。
- [ ] labeling guidelines 已写。

**验证：**
- [ ] Benchmark loader 能读取每个 example。
- [ ] 手动检查 privacy/copyright risk。

**依赖：** Task 9

**可能修改文件：**
- `data/annotations/`
- `docs/`
- `memoryrush/evaluation/`

**预计范围：** Medium：data and docs

## Task 11: Add Evaluation Metrics

**说明：** 测量 schema validity、evidence validity、salience ranking quality、duplicate rate、recall-question answerability。

**验收标准：**
- [ ] Evaluation 一条命令可运行。
- [ ] Results 写入可检查文件。
- [ ] Metrics 和 limitations 已记录。

**验证：**
- [ ] `python scripts/evaluate_memory_units.py data/annotations`

**依赖：** Task 10

**可能修改文件：**
- `memoryrush/evaluation/`
- `scripts/evaluate_memory_units.py`
- `tests/evaluation/`

**预计范围：** Medium：3-5 files

## Task 12: Add Simple Baselines

**说明：** 在做任何效果声称前，与更简单的方法比较。

**验收标准：**
- [ ] summary-only baseline 存在。
- [ ] position 或 TF-IDF salience baseline 存在。
- [ ] results table 至少比较两个 baselines 和 MemoryRush。

**验证：**
- [ ] `python scripts/run_baselines.py data/annotations`
- [ ] `python scripts/evaluate_memory_units.py data/annotations`

**依赖：** Task 11

**可能修改文件：**
- `memoryrush/evaluation/`
- `scripts/run_baselines.py`
- `tests/evaluation/`

**预计范围：** Medium：3-5 files

## Task 13: Add Local Review UI

**说明：** pipeline 和 evaluation path 跑通后，再添加 Streamlit review interface。

**验收标准：**
- [ ] 用户可以查看 source paragraphs、memory units、evidence、recall questions。
- [ ] 用户可以 accept、edit、reject memory units。
- [ ] UI 调用 application/pipeline code，而不是拥有核心逻辑。

**验证：**
- [ ] `streamlit run app/streamlit_app.py`
- [ ] manual review flow check。

**依赖：** Task 8

**可能修改文件：**
- `app/`
- `memoryrush/application/`
- `memoryrush/storage/`

**预计范围：** Medium：3-5 files

## Task 14: Persist Review Decisions

**说明：** 保存 accept/edit/reject decisions，使其后续成为 evaluation 和 personalization signals。

**验收标准：**
- [ ] decisions survive process restart。
- [ ] edited memory units 保留 original evidence。
- [ ] accepted 和 rejected items 可区分。

**验证：**
- [ ] 使用 temporary files 或 temporary SQLite database 的 storage tests。

**依赖：** Task 13

**可能修改文件：**
- `memoryrush/storage/`
- `tests/storage/`

**预计范围：** Medium：3-5 files

## Task 15: Add Retrieval Comparisons

**说明：** 比较 raw chunks、summaries、memory units 的 recall quality。

**验收标准：**
- [ ] chunk-based retrieval baseline 存在。
- [ ] summary-only retrieval baseline 存在。
- [ ] memory-unit retrieval 可用同一组 queries 评价。

**验证：**
- [ ] `python scripts/evaluate_recall.py data/annotations`

**依赖：** Task 12

**可能修改文件：**
- `memoryrush/evaluation/`
- `memoryrush/retrieval/`
- `scripts/evaluate_recall.py`
- `tests/evaluation/`

**预计范围：** Medium：4-5 files

## Task 16: Add Dynamic Memory Experiment

**说明：** 有 recall events 后再添加 reinforcement 和 decay，并作为 ablation 评价。

**验收标准：**
- [ ] recall events 被记录。
- [ ] static 和 dynamic memory rankings 可以比较。
- [ ] dynamic scoring 不替代 source-grounded evaluation。

**验证：**
- [ ] dynamic-memory unit tests。
- [ ] retrieval ablation result file。

**依赖：** Task 15

**可能修改文件：**
- `memoryrush/domain/`
- `memoryrush/retrieval/`
- `memoryrush/evaluation/`
- `tests/`

**预计范围：** Medium：4-5 files
