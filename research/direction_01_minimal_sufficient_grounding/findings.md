# Direction 01 Research Findings

## Research Question

在冻结原文、候选命题和可定位证据跨度给定时，怎样联合约束命题最小自足性与证据最小充分性，使 write-time persistent-memory admission 可被删除和语义扰动审计？

## Current Understanding

尚未形成方法有效性结论。本轮已用公开安全的合成句复现：当前 validator 会把引用真实 paragraph ID、但把 `may` 强化成 `always` 的 MemoryUnit 判为 valid。该结果是 `DEBUGGING` 级基线证据，只证明现有结构检查存在语义盲点，不证明 proposed method 有效。

## Key Results

- `run-debug-001`：现有 ID-only MemoryUnit validation 接受 modality strengthening；见 `CURRENT_RESULTS.md` 与回归测试。
- 环境基线：合规 Python 3.13.14 环境下，变更前 `15 passed`；首个 contracts 切片后 `20 passed`。

## Patterns and Insights

- 当前方向的可证伪优势来自“写入前阻止 unsupported semantic strengthening”，而不是更强检索或更大模型。
- 任何风险改善都必须在匹配 coverage/计算和固定下游条件下解释，否则会退化为“拒绝更多所以错误更少”。
- exact quote 只证明字符串来自原文，不能自动证明候选命题的组合语义、作用域和模态忠实。
- 当前回归例说明 paragraph-ID validity 与 semantic support 是两个不同 estimand；后续 baseline 报告不得混称。

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

`NOT_YET_TESTABLE`（协议与一个 DEBUGGING 基线已完成；joint solver/verifier 和 confirmatory run 尚未完成）。
