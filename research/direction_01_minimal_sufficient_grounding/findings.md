# Direction 01 Research Findings

## Research Question

在冻结原文、候选命题和可定位证据跨度给定时，怎样联合约束命题最小自足性与证据最小充分性，使 write-time persistent-memory admission 可被删除和语义扰动审计？

## Current Understanding

尚未形成方法有效性结论。本轮已用公开安全的合成句复现：当前 validator 会把引用真实 paragraph ID、但把 `may` 强化成 `always` 的 MemoryUnit 判为 valid。现有 qwen artifact 也包含被结构 validator 接受的 modality、attribution 与 scope strengthening。它们是 `DEBUGGING` 级基线证据，只证明现有结构检查存在语义盲点，不证明 proposed method 有效。

独立文献审计表明，命题最小自足、qualifier 保真、最小充分证据组、evidence deletion、语义扰动、write-time admission 和 false-write cascade 各自都有直接先例。宽口径 novelty 已被反驳；唯一仍可检验的是把这些约束组合成同一个、可审计的双侧 write-time certificate，并证明其在 coverage/compute/downstream 全部匹配时产生不可由单组件解释的交互收益。

## Key Results

- `run-debug-001`：现有 ID-only MemoryUnit validation 接受 modality strengthening；见 `CURRENT_RESULTS.md` 与回归测试。
- 环境基线：合规 Python 3.13.14 环境下，变更前 `15 passed`；当前 framework checkpoint `62 passed`。
- provenance loader 已对重复段落坐标、未知字段和标签来源/裁决状态组合 fail closed；这是数据完整性修复，不是方法结果。
- qualifier coverage 已从类型级改为具体 slot 级；两个同类型实体不再被一个 `ENTITY` 标记错误覆盖。
- 两个 `PARTIAL` span 可通过显式 required support parts 联合支持一个不可误拆的跨句命题；这只是 provisional representation。

## Patterns and Insights

- 当前方向的可证伪优势来自“写入前阻止 unsupported semantic strengthening”，而不是更强检索或更大模型。
- 任何风险改善都必须在匹配 coverage/计算和固定下游条件下解释，否则会退化为“拒绝更多所以错误更少”。
- exact quote 只证明字符串来自原文，不能自动证明候选命题的组合语义、作用域和模态忠实。
- 当前回归例说明 paragraph-ID validity 与 semantic support 是两个不同 estimand；后续 baseline 报告不得混称。
- 可替换 solver 的输出不能被 orchestration 盲信；当前边界会对选中 evidence 重新计算 sufficiency，避免伪造/bug result 污染 admission record。
- 文献中的最接近威胁是 ConsistencyGate、A-MAC、GAVEL、MEG、TriQua、Molecular Facts/Claimify 与 Evidence Sufficiency；后续实验必须以 interaction ablation 证明不是组件堆叠。

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

`MIXED`（工程可行性与现有 validator 盲点有直接证据；宽 novelty 被 closest work 否定；窄 joint-certificate claim 尚无 confirmatory 效果证据）。
