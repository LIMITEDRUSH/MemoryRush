# Direction 01 新颖性审计

审计截止：`2026-08-14`

审计对象：`Joint Minimal-Sufficient Grounding Admission`

审计结论：**宽 novelty = REJECTED；窄 delta = MIXED / NOT YET DEMONSTRATED**

## 1. 审计声明

本审计基于公开可核验的 ACL Anthology、TACL/Computational Linguistics、arXiv、OpenReview 与论文直接链接的 artifact。它是 closest-work 与 novelty-pressure 审计，不是声称穷尽所有数据库的系统综述。

所有论文实验数字均是**作者报告值，未在 MemoryRush 独立复现**。本审计没有运行论文代码、没有重做 benchmark，也没有把 LLM judge 分数、搜索摘要或本次文字综合当作客观真值。`PR / WS / PP` 的含义、原始检索式、逐篇分析与同名消歧见 `LITERATURE_LANDSCAPE.md`；机器可读书目见 `papers.jsonl`。

## 2. 被审计的主张

锁定研究对象是一个 write-time 决策：给定冻结原文 `D`、候选命题 `c` 和可定位 evidence spans `E`，只有同时满足以下条件时才允许写入持久记忆：

1. `c` 最小但自足；
2. entity、relation、object、time、scope、condition、quantifier、modality、negation 与 attribution 保真；
3. `E` 对完整命题联合充分；
4. `c` 在命题侧 inclusion-minimal；
5. `E` 在证据侧 inclusion-minimal；
6. evidence deletion 和定向语义扰动支持结论；
7. 输出结构化 `ADMIT / REVIEW / REJECT`；
8. 在冻结 downstream stack、匹配 admission coverage 与计算预算时，降低 false admission 及其下游 unsupported-answer propagation。

审计必须区分：

- **组成部分新颖性**：上述每个机制是否已有先例；
- **组合新颖性**：是否已有一篇论文把这些机制用于同一个 `(D,c,E)` write certificate；
- **经验新颖性**：这个组合是否在公平对照中产生不能由更强 verifier、更低 coverage、更短记忆或更高计算解释的收益。

## 3. 宽 novelty 否决

### 3.1 否决表

| 若拟声称的宽 novelty | Verdict | 直接反例 |
|---|---|---|
| 首个“命题最小但自足”方法 | `REJECTED` | Molecular Facts (`PR`) 明确定义 decontextuality 与 minimality；AIS、Claimify、DnDScore 进一步覆盖自足、coverage、消歧与去语境化。 |
| 首个 qualifier/context-aware factuality 方法 | `REJECTED` | Molecular Facts、DnDScore；TriQua (`PP`, 2026-08-05) 明确使用 base triple + hyperrelational qualifiers 并定位 qualifier errors。 |
| 首个 minimal sufficient evidence 方法 | `REJECTED` | Minimal Evidence Group (`WS`) 正式定义组内非冗余、整体充分的 evidence groups；User-Centric Evidence Ranking (`PR`) 定义 Minimal Sufficient Rank。 |
| 首个用 evidence deletion 判断 sufficiency | `REJECTED` | Atanasova et al. 2022 TACL (`PR`) 已做句子级和 constituent-level omission；Pair-ID (`PP`) 在固定 reader/retrieval 下做配对 evidence addition/deletion。 |
| 首个以语义 corruption 检查 grounded claim | `REJECTED` | MiniCheck 使用 structured factual errors；ConsistencyGate 使用 number、negation、proper-noun 与 contradiction corruption；FactEval 系统测试 17 类 perturbations。 |
| 首个 write-time memory gate | `REJECTED` | A-MAC (`WS`)、Selective Memory (`PP`) 和 ConsistencyGate (`PP`) 均明确在 write time 决定 admission。 |
| 首个 source-support memory admission | `REJECTED` | ConsistencyGate 在候选事实写入前直接判断 source-context support；A-MAC 也含 factual confidence。 |
| 首个 atomic claim-to-evidence contract | `REJECTED` | GAVEL (`PR`) 要求每个 atomic subclaim 绑定显式句子/表格单元并做 deterministic scrutiny；ProvenanceGuard 进行 claim-to-source routing。 |
| 首个 evidence-before-belief / typed provenance memory | `REJECTED` | TierMem (`WS`)、Eywa (`PP`)、MemIR (`PP`) 已分离 immutable/raw evidence、derived claims、retrieval cues 与 source provenance。 |
| 首个 `ADMIT / REVIEW / REJECT` 或 abstention 路径 | `REJECTED` | Attribute or Abstain、Claimify 的 ambiguity abstention、ProvenanceGuard allow/block、A-MAC/ConsistencyGate admission 均构成直接先例。 |
| 首个测试错误记忆向下游传播 | `REJECTED` | ConsistencyGate 明确提出 memory contamination cascade，并随交互轮次报告 contamination 与 QA F1。 |
| 首个 matched-coverage/matched-admission 对照 | `REJECTED` | ConsistencyGate 已使用与经验 admission rate 匹配的 Random；Pair-ID 固定 query、retrieval state 与 reader，并使用 matched sham。 |

### 3.2 宽 novelty 为什么不能靠改名恢复

把已有概念改写成 `joint admission`、`support matrix`、`certificate` 或 `memory integrity` 不会自动建立新颖性。审稿人会把当前骨架拆成以下已知模块：

```text
Molecular/Claimify/TriQua claim representation
+ MEG evidence selection
+ GAVEL evidence contract
+ TACL-2022 evidence deletion
+ MiniCheck/FactEval semantic perturbation
+ A-MAC/ConsistencyGate write admission
+ ConsistencyGate downstream contamination evaluation
```

因此，论文不能把模块清单当作 novelty proof。新颖性必须来自一个可精确定义、可被强组合基线推翻、并经交互消融证明不可约的窄机制。

## 4. Closest-work 对照矩阵

符号：`✓` 明确覆盖；`~` 部分或相邻覆盖；`—` 未覆盖。该矩阵是本次原始来源审计后的归纳，不是作者自称。

| Work | claim 最小/自足 | qualifier 保真 | evidence 最小/充分 | deletion/扰动 | write admission | 下游传播 | 与本方向最关键差异 |
|---|---:|---:|---:|---:|---:|---:|---|
| AIS (`PR`) | `~ / ✓` | `~` | `~ / ✓` | — | — | — | source-level attribution，无双侧最小性 |
| Molecular Facts (`PR`) | `✓ / ✓` | `~` | — | — | — | — | 只解决 claim representation |
| TACL Insufficient Evidence (`PR`) | — | `~` | `— / ✓` | `✓` deletion | — | — | evidence sufficiency diagnosis，不是 memory gate |
| AttributionBench (`PR`) | — | `~` | `— / ✓` | — | — | — | attribution evaluator benchmark |
| Attribute or Abstain (`PR`) | `~` | — | `~ / ✓` | — | `~` selective response | — | long-document answer attribution，不是持久写入 |
| FactLens (`PR`) | `✓ / ~` | `~` | — | — | — | — | subclaim-quality benchmark |
| Claimify (`PR`) | `~ / ✓` | `~` | — | — | `~` abstain | — | claim extraction，不联合 evidence minimality |
| MEG (`WS`) | — | — | `✓ / ✓` | `~` | — | `~` claim generation | 固定 claim，没有 write admission |
| Evidence Ranking (`PR`) | — | — | `~ / ✓` | — | — | human verification | 排序前缀而非 write certificate |
| GAVEL (`PR`) | `~` | `~` | `~ / ✓` | `~` deterministic scrutiny | — | — | inference-time multi-agent fact checking |
| TriQua (`PP`) | `~ / ✓` | `✓` | — | `~` qualifier error checks | — | — | 无 MEG/deletion/write gate |
| TierMem (`WS`) | — | `~` | `— / ~` | — | `~` verified write-back | QA | query-time sufficiency routing |
| Eywa (`PP`) | `~` | `~` | `— / ~` | — | `~` typed validation | QA | 架构性 provenance，无双侧最小 certificate |
| MemIR (`PP`) | `~` | `~` | `— / ~` | — | `~` factual authorization | QA | typed IR，无 deletion/minimality gold |
| ProvenanceGuard (`PP`) | `~` | `~` | `— / ✓` | `~` source swaps | `~` allow/block | repair | answer-level source ownership，不是 memory write |
| A-MAC (`WS`) | — | `~` | — | — | `✓` | QA | 多因子 value gate，不做双侧反事实 |
| ConsistencyGate (`PP`) | `~` | `~` | `— / ✓` | `~` corruption | `✓` | `✓` | 最强直接威胁；缺 claim/evidence minimality |
| Pair-ID (`PP`) | — | — | `~ / ~` | `✓` paired interventions | — | response repair | 离线 RAG audit，不是 runtime policy |
| Rethinking Atomic Decomposition (`PP`) | `~` | `~` | — | `~` reference degradation | — | — | 强 holistic judge 可不弱于 atomic judge |

## 5. 唯一仍可辩护的窄 delta

### 5.1 精确定义

截至 `2026-08-14`，本次检索没有定位到一篇可核验论文同时执行以下完整组合：

> 对同一个冻结三元组 `(D,c,E)`，同时颁发 claim-side 与 evidence-side 两个 inclusion-minimality certificate：`c` 必须在保持自足和所有 qualifiers 的前提下不可再删，`E` 必须在支持完整 `c` 的前提下逐 span 不可再删；然后以保持 base proposition 不变的 qualifier/entity/number/time/negation/condition/modality 定向反事实检验 decision sensitivity，把该双侧证书直接映射为 write-time `ADMIT / REVIEW / REJECT`，最后在 admission coverage、retriever、reader、memory budget 与计算预算匹配时测量真实 false-admission cascade。

这就是当前唯一可保留的 novelty delta。它必须被称为**窄的组合与评价协议候选**，不能表述成已被证明的新基础原理。

### 5.2 状态

- 概念组合状态：`MIXED`。
- 经验状态：`NOT YET DEMONSTRATED`。
- 证据等级：只有 literature gap hypothesis；尚无本方向的人标 benchmark、强组合基线、interaction ablation、真实 downstream cascade 或独立复现。
- 适合的暂定定位：严谨的 benchmark/evaluation protocol 或 auditable admission contract；目前不支持把它定位成已证实优于已有方法的通用 memory architecture。

### 5.3 推荐的保守论文表述

可以暂时写：

> “在截至 2026-08-14 的公开原始来源审计中，我们没有发现既有工作在 write time 对同一 `(D,c,E)` 联合验证 claim-side 与 evidence-side inclusion minimality，并把逐 span deletion 与 qualifier-preserving semantic counterfactuals 组成可审计的三路 admission certificate，随后在 coverage-matched、下游栈冻结的长期记忆实验中量化 false-admission propagation。该检索缺口是待实验验证的 provisional novelty hypothesis，而非不存在 prior art 的证明。”

不能写：

- “首次提出 write-time memory admission”；
- “首次用 evidence deletion 检验 sufficiency”；
- “首次定义 minimal sufficient evidence”；
- “首次同时考虑 atomicity 与 context”；
- “首次 qualifier-aware fact checking”；
- “首次发现 memory contamination cascade”；
- “首个 provenance-grounded memory”；
- “首个 coverage-matched admission evaluation”。

## 6. 让窄 delta 从假设变成证据所缺的实验

### 6.1 人工 gold 与标注协议

必须有人类标注并保留 disagreement：

- source entailment 与完整命题 support；
- claim inclusion-minimality；
- self-sufficiency/decontextualization；
- qualifier fidelity；
- 所有可接受的 minimal sufficient evidence groups，而非只标一套证据；
- `ADMIT / REVIEW / REJECT` 及原因；
- 每个 deletion/perturbation 是否只改变目标语义轴。

LLM-generated 或 LLM-judged labels 必须标 `provisional`，不能充当最终 gold。关键 subset 需要多标注者、盲审、agreement 与 adjudication。

### 6.2 反事实构造有效性

每类 entity、number、time、negation、condition、modality 扰动都需要：

1. 只改变预注册目标轴；
2. 保持语法自然和非目标语义；
3. 不引入长度、位置、罕见词或模板伪迹；
4. 配置 paraphrase/length/position sham controls；
5. 报告人工通过率、失败类型和被排除样例。

Pair-ID 的 paired intervention 与 sham control 是最低参照，而不是可选增强。

### 6.3 公平基线

至少需要：

- `WriteAll`；
- admission-rate-matched Random；
- ID-only 与 ID + exact quote；
- strong NLI / AlignScore / MiniCheck；
- detail-matched holistic LLM judge；
- A-MAC；
- ConsistencyGate `K=5` 与 LogProb；
- Molecular/Claimify/TriQua claim representation；
- MEG selector；
- GAVEL-style evidence contract；
- deletion-only、perturbation-only、extractive-copy；
- 各组件分数的简单加权或 ensemble。

必须固定 candidate generator、evidence window、retriever、answer model、storage budget、token/latency budget；报告完整 risk-coverage curve，并在相同 admitted count、相同 correct-fact recall 上比较。

### 6.4 真实下游传播

ConsistencyGate 的 real-conversation probe facts 被 pre-seed，作者自己说明这使 QA 对 gate 决策不敏感。本方向必须避免该缺陷：

- admission 决策必须真实改变未来可检索的 memory state；
- false rejection 的信息损失不能被另一份正确事实副本遮蔽；
- 测试 implicit、cross-sentence、temporal、multi-hop、cross-session facts；
- 在相同下游 query、retrieval、reader 与 memory budget 下测 unsupported answers per original candidate；
- 报告随轨迹长度变化的 propagation/amplification，而不只报告终点均值。

### 6.5 交互消融

逐一移除：

1. claim minimality；
2. self-sufficiency；
3. qualifier fidelity；
4. MEG selection；
5. evidence deletion；
6. semantic perturbations；
7. `REVIEW` 路径。

还需检验 joint method 是否显著超过最强单组件、所有二组件组合和简单 ensemble。若收益可被其中一项完全解释，组合 novelty 就不成立。

### 6.6 反循环与泛化

- generator、verifier、answer model、final judge 至少跨 model family；
- 关键结果由 blinded human audit 复核；
- 多域冻结文档、对话与工具输出；
- 多 seed、paired bootstrap 或随机化检验、置信区间；
- 预注册 corruption taxonomy、threshold、exclusion、primary metric；
- 保留 negative、null、failed 和 invalid runs。

## 7. Reviewer 2 式判定规则

### 当前判定

```text
Broad novelty: REJECTED
Narrow conjunction gap: MIXED
Empirical novelty: NOT YET DEMONSTRATED
Closest direct threat: ConsistencyGate
Closest claim-side threats: Molecular Facts, Claimify, TriQua
Closest evidence-side threats: TACL-2022 sufficiency, MEG, Evidence Ranking, GAVEL
Closest causal-intervention threat: Pair-ID
Required falsifier: detail-matched holistic judge at matched coverage and compute
```

### 可升级为“supported narrow novelty”的最低条件

只有同时满足下列条件，状态才可从 `NOT YET DEMONSTRATED` 升级：

1. 人工 gold 表明 proposed certificate 测到的是双侧最小性与完整支持，而不是 prompt preference；
2. 在 matched coverage/compute 下优于 ConsistencyGate、strong holistic、MEG + GAVEL 组合；
3. joint method 超过组件和简单 ensemble，且 interaction effect 有不确定性区间支持；
4. 真实非 pre-seeded memory 轨迹中降低 unsupported answers，而不只是减少写入；
5. 结果跨至少两个数据域和两个 verifier family；
6. 负面结果、false rejection、review burden、成本和失败样例完整报告。

### 触发方向降级或转向 benchmark-only 的条件

- strong holistic judge 在相同 coverage/compute 下匹配或超过 joint method；
- MEG + exact-quote/GAVEL contract 已解释全部收益；
- qualifier perturbation 主要被表面伪迹驱动；
- claim decomposition 的错误超过其 admission 收益；
- 真实下游不出现传播，或 propagation 只在合成短 context 出现；
- false-rejection cost 抵消 false-admission reduction；
- joint method 的提升只来自更多模型调用或更低 admission coverage。

在这些情况下，最诚实的产出应是 benchmark、failure taxonomy 或 negative result，而不是维持一个已被证伪的系统优越性主张。

## 8. 最终审计意见

当前方向不是“没有 prior art 的新领域”。它处于 claim decomposition/decontextualization、evidence sufficiency/minimality、attribution/provenance 与 agent-memory admission 四条成熟研究线的交叉点。宽 novelty 已被可核验 prior/concurrent work 否决。

唯一仍值得实验的是**双侧 inclusion-minimal、qualifier-preserving、counterfactual write certificate**这一窄组合，以及它在严格 matched coverage 的真实 memory cascade 中是否带来不可约收益。现阶段该主张只能标记为：

> `MIXED / NOT YET DEMONSTRATED`

任何更强表述都超出当前证据。
