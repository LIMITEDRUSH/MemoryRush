# Direction 01 文献地图：Joint Minimal-Sufficient Grounding Admission

审计截止：`2026-08-14`

审计性质：公开原始来源的 closest-work 与 concurrent-work 审计

研究问题：给定冻结原文 `D`、候选命题 `c` 与 evidence spans `E`，联合约束命题最小但自足、qualifier 保真、证据集合最小但对完整命题充分；以 evidence deletion 和实体、数字、时间、否定、条件、modality 等语义扰动形成 write-time `ADMIT / REVIEW / REJECT` 判据，并在固定下游条件、匹配 admission coverage 时测试 false admission 的传播。

## 1. 证据状态与阅读方式

- `PR`：可由期刊或正式 conference proceedings 核验的同行评审论文，包括 ACL/EMNLP/NAACL/EACL 主会、Findings 与 TACL/Computational Linguistics。
- `WS`：可由官方 workshop proceedings 或 OpenReview workshop 页面核验的论文；其证据权重低于主会/期刊长文。
- `PP`：截至审计日只核验到 arXiv 预印本，没有把它写成已同行评审结论。
- 文中所有实验数字均是**作者报告值，未在本仓库独立复现**。本文件不把作者报告、LLM judge 分数或本次检索综合当作客观真值。
- “本轮未发现完整覆盖”只说明截至审计日、在下述来源和检索式中没有定位到该组合，不证明不存在遗漏论文。
- 详细、逐行可解析的书目信息和原始 URL 见同目录 `papers.jsonl`。

## 2. 来源、时间窗与实际检索式

### 2.1 原始来源

- ACL Anthology 与论文 PDF：ACL、EMNLP、NAACL、EACL、Findings、TACL。
- MIT Press/DOI：Computational Linguistics 与 TACL 的正式 DOI 元数据。
- arXiv abstract/HTML/PDF：用于核验提交日期、作者、版本与预印本声明。
- OpenReview：用于核验 ICLR 2026 MemAgents workshop 的发表状态。
- 论文直接给出的 GitHub 或 artifact URL；没有从二手聚合页推断代码地址。

本地 `papers/` 与 `literature/` 没有可供此次审计使用的 PDF。近五年工作均被纳入候选池，重点复核 `2025-08-14` 以后，以及 `2026-02-14` 以后的 concurrent work。

### 2.2 实际检索式

```text
site:aclanthology.org attribution evidence minimal sufficient claim atomicity LLM grounded generation
site:arxiv.org "minimal evidence" claim attribution language model
site:arxiv.org "atomic decomposition" factuality attribution evidence
site:arxiv.org "write-time" memory admission evidence provenance LLM
site:aclanthology.org claim decomposition factuality atomic context evidence support 2025
site:aclanthology.org citation attribution completeness evidence sufficiency 2025
site:aclanthology.org evidence deletion perturbation entailment claim verification 2024
site:aclanthology.org long-term memory provenance grounded claims agent 2026
site:arxiv.org 2026 claim evidence semantic perturbation entity number time negation modality factuality verification
site:aclanthology.org/2026 qualifier factuality claim evidence modality negation
site:arxiv.org "evidence deletion" claim verification LLM
site:aclanthology.org counterfactual perturbation attribution evidence claim support
site:aclanthology.org evidence sufficiency perturbation fact verification deletion minimal 2026
site:arxiv.org/abs 2026 "minimal sufficient evidence" claim verification
```

此外，对 AIS、Molecular Facts、AttributionBench、Attribute or Abstain、Minimal Evidence Group、FactLens、ProvenanceGuard、Rethinking Atomic Decomposition、Eywa、MemIR、GAVEL、TriQua 做了逐条精确标题与同名消歧检索。

## 3. 研究版图

| 子问题 | 已有最直接工作 | 已经覆盖的核心机制 | 本方向仍需证明的差异 |
|---|---|---|---|
| 命题最小且自足 | AIS (`PR`), Molecular Facts (`PR`), Claimify (`PR`), DnDScore (`PR`) | source-relative full support；decontextuality；minimality；coverage；歧义时 abstain | 把这些条件变成 write-time admission certificate，并与证据侧最小性联合，而不是分别评价 |
| qualifier/context 保真 | Molecular Facts (`PR`), DnDScore (`PR`), TriQua (`PP`) | 语境补全与 atomicity 张力；base triple + hyperrelational qualifiers；qualifier error localization | 用冻结 `D` 上的定向语义反事实验证 qualifier 必须保留，且证明其降低 false admission |
| 证据充分性 | Fact Checking with Insufficient Evidence (`PR`), AttributionBench (`PR`), GAVEL (`PR`) | insufficient-evidence prediction；完整支持；每个 atomic subclaim 绑定显式 evidence unit | 对**完整命题**建立 span-level、可审计、三路 admission，而非只给验证分数 |
| 证据集合最小性 | Minimal Evidence Group (`WS`), User-Centric Evidence Ranking (`PR`) | Set-Cover-like MEG；minimal sufficient rank；互补证据和冗余控制 | 与命题侧 inclusion-minimal、自足和 qualifier constraints 联合求解 |
| evidence deletion | Atanasova et al. 2022 (`PR`), Pair-ID (`PP`) | 句子/constituent omission；固定 reader/retrieval 的证据增删干预与 sham controls | 从离线诊断升级为 write-time certificate，并覆盖每个已选 span 的必要性 |
| 语义扰动与鲁棒性 | MiniCheck (`PR`), FactEval (`PR`), ConsistencyGate (`PP`) | structured factual errors；17 类输入扰动；number/negation/proper-noun corruption | 预注册 entity/number/time/negation/condition/modality 轴，并验证扰动只改变目标语义 |
| write-time admission | A-MAC (`WS`), Selective Memory (`PP`), ConsistencyGate (`PP`) | 多因子 admission；salience/reliability gate；source-context support gate | 证明联合 certificate 超过同算力 holistic/consistency gate，而非因拒绝更多候选获胜 |
| false-admission propagation | ConsistencyGate (`PP`) | contamination cascade；WriteAll 与 admission-rate-matched Random | 在真实、非 pre-seeded 下游里固定 retriever/reader/storage 并匹配 coverage 测传播 |
| provenance 与 typed memory | TierMem (`WS`), Eywa (`PP`), MemIR (`PP`), ProvenanceGuard (`PP`) | immutable evidence；raw evidence/claim/cue 分型；claim-to-source routing；allow/block | 形式化 claim-condition × evidence-span 支持矩阵和双侧最小反事实证书 |
| 强 holistic 替代解释 | AlignScore (`PR`), MiniCheck (`PR`), Rethinking Atomic Decomposition (`PP`) | detail-matched holistic judge 可匹配或优于 atomic judge；廉价强 checker | 必须做相同输入、rubric、计算与 coverage 的 holistic 对照，不能默认 decomposition 有益 |

## 4. Closest works 深核

### 4.1 直接威胁宽 novelty 的工作

#### ConsistencyGate: Preventing Memory Contamination in LLM Agents via Self-Consistency Admission Control (`PP`)

- 原始来源：[arXiv:2607.22962](https://arxiv.org/abs/2607.22962)，Yan Zhang、Shibo Li，提交于 2026-07-25。
- 问题与机制：在候选事实写入长期记忆前，对 source context 做 `K` 次 soft support scoring；阈值以上才写入，并提供单次 LogProb 版本。
- 数据与指标：LoCoMo、LoCoMo-Contam、MSC-Contam、MemContam；报告 contamination、admission precision/recall、QA F1，并用 `p=0.6` 的 Random 匹配经验 admission rate。
- 作者报告：Qwen 设置下 LoCoMo-Contam contamination `50.0% -> 34.1%`、MSC `50.0% -> 36.7%`、MemContam `50.0% -> 1.2%`，MemContam QA F1 `0.474 -> 0.840`。这些数值未复现。
- 关键限制：真实 LoCoMo/MSC probe facts 被 pre-seed，作者明确说明真实集 QA 对 gate 决策不敏感；真正的 cascade 证据主要来自简短、清晰的合成 MemContam。LoCoMo 正确事实 recall 仅 `0.58`。verifier 与 writer 使用同一待评 backbone，benchmark/corruption 亦有 LLM 生成成分。
- 与本方向差异：没有 claim minimality、自足性、qualifier schema、MEG 或逐 span deletion；但它已经覆盖“write-time correctness admission + matched admission baseline + downstream contamination cascade”。

#### Fact Checking with Insufficient Evidence (`PR`)

- 原始来源：[TACL 2022](https://aclanthology.org/2022.tacl-1.43/)，DOI `10.1162/tacl_a_00486`。
- 机制：在句子和 constituent 层做 fluency-preserving omission；删除 PP、noun/adjective/adverb/number/date modifiers 与 subordinate clauses，训练 Evidence Sufficiency Prediction。
- 数据与指标：三个 fact-checking datasets 与人工标注的 SufficientFacts1。作者报告 missing adverbial modifier 检出准确率仅 `21%`，date modifier `63%`，Evidence Sufficiency F1 最高增加 `17.8`，最终 FC F1 最高增加 `2.6`；均未复现。
- 差异：不是 persistent-memory gate，也未覆盖完整的替换扰动矩阵；但“evidence deletion 检查 sufficiency”本身已有明确先例。

#### Molecular Facts (`PR`)

- 原始来源：[Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.215/)，DOI `10.18653/v1/2024.findings-emnlp.215`，arXiv:2406.20079。
- 机制：明确把 decontextuality 定义为可独立理解，把 minimality 定义为为实现自足而尽量少添加信息；提出 molecular facts 平衡两者。
- 限制与差异：没有 evidence-set optimization、write gate 或传播实验；但它几乎精确覆盖“claim minimal but self-contained”。

#### Minimal Evidence Group Identification for Claim Verification (`WS`)

- 原始来源：[TrustNLP 2025](https://aclanthology.org/2025.trustnlp-main.8/)，DOI `10.18653/v1/2025.trustnlp-main.8`，arXiv:2404.15588。
- 机制：正式定义每组内部非冗余、整体充分、且可能存在多组解的 minimal evidence groups；化为依赖 entailment estimates 的 Set-Cover-like 问题。
- 数据与指标：WiCE、SciFact；作者报告相对 LLM prompting 的绝对提升分别为 `18.4` 与 `34.8`，未复现。
- 差异：固定 claim，不约束 claim 本身最小/自足，也不做 memory admission。

#### GAVEL (`PR`)

- 原始来源：[Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1789/)，DOI `10.18653/v1/2026.findings-acl.1789`。
- 机制：Evidence Contract 要求 atomic subclaim 绑定明确句子或表格单元；Scrutinizer 做 schema、identifier、exact quote、duplicate/conflict 等确定性检查；Judge 选择覆盖全部 subclaims 的 sufficient evidence set。
- 数据与指标：FEVEROUS 与 HOVER open-book；作者报告 provenance-aware official scores 提升约四个百分点，未复现。
- 限制与差异：多 agent 推理成本高；不求 evidence cardinality 最小，也无 claim-side minimality；是 inference-time fact checking，而非 persistent-memory admission。

#### TriQua (`PP`)

- 原始来源：[arXiv:2608.05228](https://arxiv.org/abs/2608.05228)，Jin Liu、Steffen Thoma、Achim Rettinger，提交于 2026-08-05。
- 机制：base triple 加 hyperrelational qualifiers，对 base 与 qualifier 分开验证和定位错误。
- 数据与指标：FActScore-Bio、LongFact、CLEARFACTS。作者报告 FActScore-Bio Pearson 约 `0.89-0.90`；qualifier misuse 主要由两个超大开放模型判断，误用率约 `1%-2%`，但 judge 间 kappa 只到中低水平。Qwen 设置的 CLEARFACTS overall F1 中 no-decomposition holistic 为 `86.22`，TriQua 为 `85.91`；均未复现。
- 限制与差异：极新的未同行评审预印本，主要依赖 LLM judge；没有 evidence-set minimality、deletion 或 write admission。它直接占据 qualifier-aware representation/fidelity。

#### Adaptive Memory Admission Control for LLM Agents (`WS`)

- 原始来源：[arXiv:2603.04549](https://arxiv.org/abs/2603.04549)；[ICLR 2026 MemAgents OpenReview](https://openreview.net/pdf?id=mmdqUrEY24)。
- 机制：future utility、factual confidence、semantic novelty、temporal recency、content type prior 五因子 admission。
- 数据与指标：LoCoMo；作者报告 F1 `0.583`、延迟下降 `31%`，未复现。
- 差异：不做双侧最小性或反事实证书，但“结构化 write-time admission”和其中的 factual confidence 不是空白。

#### What Would Fix This RAG Failure? (`PP`)

- 原始来源：[arXiv:2608.08944](https://arxiv.org/abs/2608.08944)，Wenzhang Du，提交于 2026-08-09。
- 机制：Pair-ID 固定 query、retrieval state 和 reader，交叉执行 support addition 与 verified-nonsupport deletion，并以 length/position matched sham 控制非语义效应。
- 数据与指标：从 19,981 个 query 构成完整 funnel，对预先哈希选出的 failures 运行配对干预；作者报告 support addition/deletion response rates、置信区间、AUROC、Brier 与跨 reader agreement，均未复现。
- 差异：是 response-level 离线 RAG failure audit，不是 memory write policy；但它显著抬高了本方向对“固定下游条件”和“语义干预 sham control”的要求。

### 4.2 Claim representation 与 attribution

#### AIS / Measuring Attribution in Natural Language Generation Models (`PR`)

- 原始来源：[Computational Linguistics 2023](https://aclanthology.org/2023.cl-4.2/)，DOI `10.1162/coli_a_00486`。
- AIS 是 `Attributable to Identified Sources` 评价框架，不是独立论文题名。框架先判断输出是否可理解，再问“According to source P, s”是否成立，要求输出全部信息受 source 支持。
- 差异：source 通常整体给定；不求 span-level MEG，也不做 memory admission。

#### AttributionBench (`PR`)

- 原始来源：[Findings ACL 2024](https://aclanthology.org/2024.findings-acl.886/)，DOI `10.18653/v1/2024.findings-acl.886`。
- 机制与数据：聚合 attribution datasets，统一测试 claim 是否被 citations 完整支持；论文另审查 300 多个错误。
- 作者报告：fine-tuned GPT-3.5 约 `80% macro-F1`，未复现。
- 差异：binary support benchmark，不优化双侧最小性或持续写入。

#### Attribute or Abstain (`PR`)

- 原始来源：[EMNLP 2024](https://aclanthology.org/2024.emnlp-main.463/)，DOI `10.18653/v1/2024.emnlp-main.463`。
- 机制与数据：LAB 包含六个 long-document attribution tasks；比较 citation、额外 retrieval 与 selective prediction。
- 关键限制：复杂 response 上 evidence quality 不能稳定预测 response quality，说明单分数 gate 可能隐藏 missing evidence。
- 差异：没有 MEG/deletion；但 `abstain`/人工复核路径已有强先例。

#### FactLens (`PR`)

- 原始来源：[Findings ACL 2025](https://aclanthology.org/2025.findings-acl.929/)，DOI `10.18653/v1/2025.findings-acl.929`，arXiv:2411.05980。
- 机制：手工策展 subclaim ground truth，并评价 atomicity、context/semantic equivalence、coverage、fabrication、redundancy。
- 差异：benchmark 而非 write-time controller；不优化证据集合。

#### Claimify / Towards Effective Extraction and Evaluation of Factual Claims (`PR`)

- 原始来源：[ACL 2025](https://aclanthology.org/2025.acl-long.348/)，DOI `10.18653/v1/2025.acl-long.348`。
- 机制：element-level coverage、outcome-based decontextualization，遇到无法可靠消歧的句子时不抽取 claim。
- 差异：没有固定 evidence spans 与 memory gate；但 claim coverage、自足与 ambiguity-aware abstention 已有直接基线。

#### DnDScore (`PR`)

- 原始来源：[EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1205/)，DOI `10.18653/v1/2025.emnlp-main.1205`。
- 机制：系统研究 decomposition 与 decontextualization 的冲突，并提出 decontextualization-aware verification。
- 差异：未引入 MEG、deletion 或 persistent write；但已经证明 claim representation 必须和 verifier 联合评价。

### 4.3 Provenance-grounded agent memory

#### TierMem / From Lossy to Verified (`WS`)

- 原始来源：[arXiv:2602.17913](https://arxiv.org/abs/2602.17913)，并可在 ICLR 2026 MemAgents OpenReview 发表列表核验。
- 机制：summary index 与 immutable raw-log store；运行时 sufficiency router 在摘要不足时升级到 raw evidence，并把 verified findings 带 provenance 写回。
- 作者报告：LoCoMo accuracy `0.851`，raw-only `0.873`，input tokens 降 `54.1%`、latency 降 `60.7%`，未复现。
- 差异：sufficiency 是 query-time evidence allocation，不是 candidate correctness admission。

#### Eywa (`PP`)

- 原始来源：[arXiv:2605.30771](https://arxiv.org/abs/2605.30771)。
- 机制：evidence-before-belief、immutable source evidence、canonical facts、typed validation、确定性多路 retrieval。
- 作者报告：LoCoMo、LongMemEval-S、BEAM 上的多组性能值，未复现。
- 限制：单作者预印本；BEAM 缺少充分的独立人工验证、显著性与外部系统公平控制。
- 差异：架构上已有 frozen evidence、derived claims 和 source support，但没有双侧最小 certificate。

#### MemIR (`PP`)

- 原始来源：[arXiv:2605.25869](https://arxiv.org/abs/2605.25869)，正式题名为 *Mitigating Provenance-Role Collapse in Long-Term Agents via Typed Memory Representation*。
- 机制：把 raw evidence、retrieval cues、truth-bearing claims 分型，仅 supported claim atoms 获得事实授权。
- 差异：没有 claim/evidence minimality gold、deletion 或三路 write decision；但 supported atom 与 evidence-role separation 已不是空白。

#### ProvenanceGuard (`PP`)

- 原始来源：[arXiv:2606.18037](https://arxiv.org/abs/2606.18037)。
- 机制：atomic claims 路由至 source-specific evidence，用 NLI/token alignment 检查 support 和 source ownership，返回 allow/block，并可 repair/reverify。
- 数据与指标：281 个 medical MCP traces；论文称 2,325 个 LLM-assisted labels，其中 361 个 held-out labels 经人工核验；作者报告 block F1 `0.802`、source accuracy `0.858`，更难数据的 source-plus-relation accuracy `0.229`，均未复现。
- 差异：是 answer-level source-aware verifier，不是 persistent-memory write certificate。

### 4.4 必须纳入的强替代基线

- **AlignScore (`PR`)**：[ACL 2023](https://aclanthology.org/2023.acl-long.634/)，DOI `10.18653/v1/2023.acl-long.634`。统一 holistic alignment function，是“无需分解即可完成 support checking”的强基线。
- **MiniCheck (`PR`)**：[EMNLP 2024](https://aclanthology.org/2024.emnlp-main.499/)，DOI `10.18653/v1/2024.emnlp-main.499`。770M checker 通过 structured synthetic errors 学习跨句 support；作者称可达 GPT-4 级准确率且成本低约 400 倍，未复现。
- **Rethinking Atomic Decomposition (`PP`)**：[arXiv:2603.28005](https://arxiv.org/abs/2603.28005)。在同输入、近似同 rubric 和冻结 prompts 下，holistic judge 在 ASQA/QAMPARI 匹配或优于 self-decomposing atomic judge，仅 TruthfulQA 有小 atomic 优势。它要求本方向使用 detail-matched holistic baseline。
- **A Closer Look at Claim Decomposition (`PR`)**：[\*SEM 2024](https://aclanthology.org/2024.starsem-1.13/)，DOI `10.18653/v1/2024.starsem-1.13`。证明 FActScore 对 decomposition method 敏感，不能把 decomposition error 归因给被评模型。
- **Decomposition Dilemmas (`PR`)**：[NAACL 2025](https://aclanthology.org/2025.naacl-long.320/)，DOI `10.18653/v1/2025.naacl-long.320`。显示 decomposition 的准确收益与新引入噪声存在权衡。

## 5. 用户历史线索核验

| 线索 | Verdict | 精确校正 |
|---|---|---|
| AIS | 有效，但不是独立论文标题 | 正式文献是 Rashkin et al. 2023 的 *Measuring Attribution in Natural Language Generation Models*；AIS 是框架缩写。 |
| Molecular Facts | 有效，`PR` | Gunjal & Durrett，Findings EMNLP 2024；直接定义 decontextuality + minimality。 |
| AttributionBench | 有效，`PR` | Li et al.，Findings ACL 2024；官方代码链接可核验。 |
| Attribute or Abstain | 有效，`PR` | Buchmann et al.，EMNLP 2024；LAB 是其 benchmark。 |
| Minimal Evidence Group | 有效，`WS` | 完整题名为 *Minimal Evidence Group Identification for Claim Verification*；MEG 是方法缩写。 |
| FactLens | 有效，`PR` | Mitra et al.，Findings ACL 2025；不要与拼作 `FacLens` 的其他工作混淆。 |
| ProvenanceGuard | 有效，但仅 `PP` | Alvarez et al.，arXiv:2606.18037；引用必须带完整题名和 ID，以避免同名 guard 混淆。 |
| Rethinking Atomic Decomposition | 有效，但仅 `PP` | Xinran Zhang，arXiv:2603.28005；核心是 prompt-controlled holistic 对照。 |
| Eywa | 有效，但仅 `PP` | Resham Joshi，arXiv:2605.30771；作者 artifact 可查，独立验证不足。 |
| MemIR | 有效，但属于方法名 | 正式题名为 *Mitigating Provenance-Role Collapse...*，arXiv:2605.25869。 |
| GAVEL | 有效，`PR` | 应引用 Xu et al. Findings ACL 2026 的 evidence-contract 论文；另有法律摘要和视觉领域同名工作。 |
| TriQua | 有效，但极新且仅 `PP` | arXiv:2608.05228，提交于 2026-08-05；是 qualifier fidelity 最直接 concurrent work。 |

## 6. 文献地图给实验设计的硬约束

1. 不能把 write-time gate、evidence deletion、MEG、claim minimal/self-contained、qualifier representation 或 contamination cascade 单独声明为新贡献。
2. 必须直接比较 ConsistencyGate、A-MAC、strong holistic checker、MEG selector、GAVEL-style contract、Molecular/Claimify/TriQua representation；只与 ID-only 或 exact-quote baseline 比较不足以建立 novelty。
3. 必须匹配 admission coverage、candidate generator、evidence window、retriever、answer model、storage budget 和计算预算；否则更低 false admission 可以由“拒绝更多”解释。
4. 必须使用真实会改变未来检索和回答的 write decisions；不能用 pre-seeding 把 false rejection 的下游代价隐藏掉。
5. 必须把人工 gold 与 LLM-generated/LLM-judged labels 分开；同一模型家族承担 generator、verifier、judge 时，需要跨家族或人工盲审排除循环自证。
6. 必须对语义扰动设置 meaning-preserving sham、单轴编辑检查、人工通过率和失败样例；否则模型可能利用格式或流畅度伪迹。

## 7. 当前边界

本文件建立的是可证伪的 related-work 边界，不是新颖性证书。宽 novelty 的否决、唯一剩余窄 delta、状态标签与证据缺口集中记录在 `NOVELTY_AUDIT.md`。书目数据集中记录在 `papers.jsonl`，避免 Markdown 中的简称、同名冲突或状态变化成为唯一来源。
