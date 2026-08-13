# MemoryRush 项目上下文

## 用途

这是 MemoryRush 的持续项目记忆。Codex 只在任务涉及项目需求、架构、实现、进度或下一步开发时按需读取相关部分，不要求在每次回答前完整读取。

本文件记录已经明确确认的需求、技术方向、协作方式和当前状态。它不是完整聊天记录，也不记录尚未确认的讨论。

最后更新：2026-08-12

## 项目定位

MemoryRush 是一个个人、本地优先、研究导向的 AI/ML 工程项目，用于研究：能否把长文转换成少量、有原文证据、适合后续召回的 memory units，并通过可复现实验比较它们与摘要及普通 chunk retrieval 的效果。

项目当前不是 startup、SaaS、订阅服务、企业平台或商业产品。不要引入定价、增长、营销、企业权限或大规模部署需求。

## 用户协作要求

- 默认使用中文，并按初学者能够跟上的方式解释。
- 开发过程必须说明目标、原理、数据流、选择、替代方案、权衡、问题和验证结果。
- 在任何项目实施、文件修改、会改变状态的命令、模型运行、软件安装、commit 或 push 前，先列出行动清单并等待用户明确确认。
- 清单必须包含目标和范围、预计涉及的文件或命令、验证方式。确认只覆盖清单中列出的范围；范围实质扩大时，必须重新列清单并再次确认。
- 解释、答疑和制定清单所需的最小只读检查不需要确认。
- 清单发出后，用户回复“确认”“开始”或“继续”可视为批准该清单。
- commit 或 push 必须明确列入已获批准的清单；否则不执行。
- 回答进度时必须区分：计划完成、本地实现、验证通过、已 commit、已 push。
- 简单或无关回答不读取完整项目上下文；项目任务只加载当前需要的部分，以控制 token 使用。

## 当前 Source Of Truth

按优先级使用：

1. 用户最新的明确要求。
2. 本文件。
3. `docs/RESEARCH_SPEC_CN.md`：研究需求和架构。
4. `docs/RESEARCH_PLAN_CN.md`：开发和研究顺序。
5. `tasks/plan_CN.md` 与 `tasks/todo_CN.md`：进度和验收项。
6. `docs/MemoryPoint_*`：最初构想和历史路线，只作为背景，不覆盖当前规格。

## 当前实现状态

- Phase 0：研究定位、规格和计划已完成。
- Phase 1：TXT/Markdown 解析、稳定段落表示已在本地实现。
- Phase 2：结构化输出 contracts、证据引用检查、fake-provider pipeline 已在本地实现。
- Phase 3：Ollama provider、第一版 Prompt、fake artifact 和 `qwen3:8b` 真实 artifact 已在本地完成。
- Phase 4 及以后：benchmark、evaluation、review UI、持久记忆库、retrieval、动态强化与衰减尚未实现。

当前本地实现改动尚未 commit/push。GitHub 上不能被视为已经包含这些代码。

当前验证状态：`compileall` 通过；fake provider 和 `qwen3:8b` 都能生成 valid artifact；Ollama JSON smoke test 通过，模型在 RTX 3070 Ti Laptop GPU 上以 100% GPU 运行。当前虚拟环境缺少 `pytest`，所以正式 pytest 测试套件尚未运行。

## 当前文章处理链路

```text
TXT/Markdown
-> SourceDocument + stable SourceParagraph IDs
-> versioned extraction prompt
-> fake provider or local Ollama LLM
-> structured candidate output
-> deterministic schema/evidence validation
-> local JSON artifact
```

当前产出的 `summary`、`core_ideas`、`memory_units` 和 `recall_questions` 都是候选结果。`recall_questions` 是复习题，不是历史记忆检索机制。

## AI 职责边界

### 本地生成式 LLM

负责：

- 理解文章并提出候选 core ideas 和 memory units。
- 生成证据引用候选和 recall questions。
- 后续在已经检索出的少量记忆和原文证据上判断 support/conflict/extension。
- 后续根据检索结果和证据组织最终回答。

不负责：

- 解析和保存文件。
- 决定候选是否自动成为正式长期记忆。
- 把自己生成的 confidence 或 salience 当成客观真值。
- 扫描整个记忆库完成检索。
- 控制召回日志、强化、衰减或删除。

真实本地模型的当前首选是 Ollama 上的 `qwen3:8b`。资源不足时可以考虑 `qwen3:4b`，资源充足时再比较更大模型。代码当前默认模型仍可能是 `qwen2.5:7b-instruct`，需要在真实运行阶段统一。

当前 inference baseline 保持本地运行。Fine-tuning 明确延后到 benchmark、训练目标和重复失败模式已经建立之后；届时可以租用 GPU 集群执行 LoRA/QLoRA 等受控训练实验，不受当前笔记本显存限制。租用集群不改变日常使用和基准推理优先本地运行的方向。

### Embedding 和排序模型

负责把用户问题和已接受的 memory units 转为可比较的向量，执行第一阶段候选检索。后续可以加入 reranker，但不应在 extraction 质量尚未评价前扩大检索技术栈。

### 确定性代码

负责 contracts、证据引用检查、持久化、固定公式计算、召回事件记录、强化/衰减更新和实验指标。能由普通代码确定的行为，不交给生成式 LLM 随机决定。

### 用户

通过 Accept/Edit/Reject、Highlight、收藏、笔记和“是否有帮助”等反馈，决定候选记忆的个人价值，并为后续个性化和评价提供标签。

## 计划中的记忆调取链路

```text
用户问题
-> query embedding
-> 从已接受的 memory units 检索 Top-N
-> 使用 query relevance、salience、grounding、用户反馈和 memory strength 排序
-> 根据 document_id + paragraph_id 取回原文证据
-> 本地 LLM 只根据候选记忆和证据生成带引用回答
-> 记录真正用于回答或被用户确认的 recall events
-> 后续更新 memory strength
```

新文章触发旧记忆时，先用 embedding 从历史 memory units 中找候选，再让 LLM 在双方原文证据范围内判断支持、冲突、补充或延伸关系。

记忆只出现在候选列表中时不应自动强化。只有实际用于回答、被用户查看、收藏、编辑、主动搜索或确认有帮助等事件才适合产生强化，避免自我强化循环。

## 评分设计路线

当前 Prompt 中让 LLM 直接输出 `salience_score` 只是未校准的测试 baseline。当前 Prompt 没有完整评分 rubric，因此该分数不能作为最终依据。

后续分开记录：

- `intrinsic_salience`：文章内部的中心性、信息增益、可迁移性、具体性和非重复性。
- `grounding_score`：证据覆盖、直接性、引用正确性和忠实度。
- `personal_relevance`：Accept/Edit/Reject、Highlight、收藏和笔记等用户信号。
- `query_relevance`：每次查询产生的语义相关性和 reranker 相关性。
- `memory_strength`：经过验证的召回事件、时间衰减和用户反馈形成的动态状态。

下一版评分 Prompt 应让模型按有明确锚点的 rubric 分项判断并给出理由，由 Python 计算实验分数。文章内排名优先于跨文章比较绝对分数。模型看不到用户历史时，不得猜测 `personal_relevance`。

最终 retrieval rank 可以组合这些信号，但权重必须通过 baseline comparison、人工标注和 ablation 决定。旧计划里的固定权重是研究假设，不是已确认结论。

## 研究与开发顺序

1. 安装并运行测试依赖，建立正式回归测试基础。
2. 使用 `qwen3:8b` 完成并保存一次真实 Ollama extraction artifact。
3. 记录真实模型的格式、证据、重复、长文和评分失败模式。
4. 定义 annotation schema，并建立小型人工标注 benchmark。
5. 比较 LLM extraction、summary-only 和简单 heuristic baseline。
6. 提取质量可接受后，再实现 review state、稳定 `memory_id` 和持久存储。
7. 实现 raw chunks、summaries 和 memory units 使用同一查询集的 retrieval comparison。
8. 有真实 recall events 后，再实验 reinforcement 和 decay。
9. 只有 baseline 证明 Prompt 或轻量 ranker 无法解决明确问题时，才使用租用 GPU 集群实验 LoRA/QLoRA，并与未微调模型做可复现对比。

## 当前重要问题

- 第一份 `qwen3:8b` artifact 通过当前 validation，但这只证明格式、段落 ID 和 core-idea quote 检查通过，不证明所有 MemoryUnit 在语义上完全受证据支持。
- 当前虚拟环境缺少 `pytest`。
- MemoryUnit 只引用段落 ID，尚未充分验证其完整语义是否被原文支持。
- 长文章目前一次性进入 Prompt，尚未处理上下文窗口限制。
- `memory_unit_index` 只适合单次 artifact；持久化前必须引入稳定 `memory_id`。
- 尚无 SQLite memory store、embedding index、retrieval API 或 recall event log。
- 中文规格文件在某些终端默认编码下可能显示乱码，读取时应显式使用 UTF-8。

## 记录更新规则

当用户明确确认以下变化时，同步更新本文件和英文版：

- 项目范围或非目标变化。
- AI、评分、检索、存储或评价方案变化。
- 开发阶段顺序变化。
- 协作方式变化。
- 当前阶段或验证状态发生实质变化。

不要把探索性提问、未选择的备选方案或一次性命令写成已确认决策。
