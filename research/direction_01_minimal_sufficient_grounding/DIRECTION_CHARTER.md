# Direction 01 Charter: Joint Minimal-Sufficient Grounding Admission

Status: `LOCKED_BY_USER`  
Started: `2026-08-14T02:43:37+08:00`

## LOCKED_CORE

本轮研究问题固定为：给定冻结原文 `D`、候选记忆命题 `c` 和可定位证据跨度集合 `E`，研究该命题—证据组合在什么条件下才有资格于 write time 进入持久记忆。

唯一主贡献固定为：**联合约束记忆命题与证据集合的 write-time admission，使命题最小但自足、证据集合最小但对完整命题充分。**

方向只研究 source-support integrity：不判断来源在现实世界中为真，不研究内容是否值得记住，不把 salience、个性化、反馈、强化、衰减、遗忘、retrieval、reranking 或回答生成改成主问题。初始对象是具有冻结文本快照和可定位 evidence span 的说明性长文。

Admission 必须表达：

1. 命题自足性；
2. 实体、关系、对象、时间、范围、条件、量词、模态、否定与 attribution 保真；
3. 联合证据充分性；
4. 命题侧最小性；
5. 证据侧最小性；
6. `ADMIT / REVIEW / REJECT`；
7. evidence deletion 与语义扰动审计。

锁定机制骨架：

```text
Candidate MemoryUnit
-> main proposition + atomic claims + qualifier slots
-> paragraph IDs narrowed to evidence spans
-> claim-condition × evidence-span support matrix
-> minimal jointly sufficient evidence set
-> evidence deletion audit
-> entity/number/time/negation/condition/modality perturbations
-> ADMIT / REVIEW / REJECT with structured reasons
```

允许验证、反驳、实现和改进该骨架，但不得替换成普通 NLI filter、GraphRAG、多 Agent 辩论、通用 RAG、模型扩容或另一研究方向。

## Locked Hypothesis and Controls

在固定 candidate generator、evidence window、storage budget、retriever 与 answer model，并匹配计算预算和 admission coverage 时，joint admission 相比当前 ID-only validator、ID + exact quote 与 strong NLI filtering，应降低 false admission，并减少固定下游条件下的 unsupported answers。必须报告 risk–coverage 或 matched coverage，不能靠拒绝更多候选获胜。

必须检验的竞争解释：更强 verifier/更多计算、较低 coverage、atomicization 破坏跨句语义、下游收益来自更短 memory、循环自证、仅适用单段事实，以及 strong holistic judge / MEG-style / extractive-copy 已足够。

## User-Reserved Decisions

以下只能做可配置 provisional 比较，不能由代理标记为最终决定：正式 atomic/qualifier schema；inclusion-minimal 或全局最小基数；最终 verifier、solver、REVIEW 政策、benchmark、模型家族、人工标注、主指标/阈值、venue，以及是否永久进入 MemoryRush 架构。统一记录在 `USER_DECISIONS_REQUIRED.md`，状态只能为 `PROPOSED`。

## Evidence Discipline

- 文献、引用、实验、人工标签、显著性和 venue 潜力不得虚构。
- LLM/代理标签一律标为 provisional/LLM-generated。
- Protocol commit 必须早于相应 result commit。
- Run 必须标为 `CONFIRMATORY`、`EXPLORATORY`、`DEBUGGING` 或 `INVALID_RUN`。
- 阴性结果与失败原始输出必须保留。
- 若中断，状态标记 `INTERRUPTED/INCOMPLETE`；不得虚报十小时或完成度。

