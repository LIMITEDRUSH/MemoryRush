# Direction 01 Research Findings

## Research Question

在冻结原文、候选命题和可定位证据跨度给定时，怎样联合约束命题最小自足性与证据最小充分性，使 write-time persistent-memory admission 可被删除和语义扰动审计？

## Current Understanding

尚未形成实验结论。项目既有事实源明确承认：当前 validator 只验证结构、paragraph ID 存在性和部分 exact quote，不能证明每个 MemoryUnit 的完整语义受到证据支持。这是待复现的项目事实，不是方法有效性的证据。

## Key Results

无。`NO_EXPERIMENT_RUN_YET`。

## Patterns and Insights

- 当前方向的可证伪优势来自“写入前阻止 unsupported semantic strengthening”，而不是更强检索或更大模型。
- 任何风险改善都必须在匹配 coverage/计算和固定下游条件下解释，否则会退化为“拒绝更多所以错误更少”。
- exact quote 只证明字符串来自原文，不能自动证明候选命题的组合语义、作用域和模态忠实。

## Lessons and Constraints

- 本轮开始前工作树很脏，已用单独 checkpoint 精确保存并标注归属；后续 commit 只归属本轮新增内容。
- 中文文件需显式 UTF-8 读取，否则 PowerShell 默认展示可能乱码。
- 用户保留的 schema、minimality、verifier、solver、REVIEW、benchmark、model、annotation 与 metric 决策只能 provisional。

## Open Questions

- closest work 是否已经覆盖相同的目标、联合机制和固定下游 claim？
- inclusion-minimal 与 minimum-cardinality 在小规模 oracle 上产生多大差异？
- 强 holistic semantic judge 在 matched coverage 下是否已经足够？
- 原有 qwen3:8b artifact 中的 modality strengthening 能否被复现并由 deletion/perturbation audit 捕获？

## Evidence Status

`NOT_YET_TESTABLE`（截至初始化；协议、基线和运行尚未完成）。

