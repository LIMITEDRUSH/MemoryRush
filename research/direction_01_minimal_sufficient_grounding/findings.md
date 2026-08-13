# Direction 01 Research Findings

## Research Question

在冻结原文、候选命题和可定位证据跨度给定时，怎样联合约束命题最小自足性与证据最小充分性，使 write-time persistent-memory admission 可被删除和语义扰动审计？

## Current Understanding

尚未形成方法有效性结论。本轮已用公开安全的合成句复现：当前 validator 会把引用真实 paragraph ID、但把 `may` 强化成 `always` 的 MemoryUnit 判为 valid。现有 qwen artifact 也包含被结构 validator 接受的 modality、attribution 与 scope strengthening。它们是 `DEBUGGING` 级基线证据，只证明现有结构检查存在语义盲点，不证明 proposed method 有效。

独立文献审计表明，命题最小自足、qualifier 保真、最小充分证据组、evidence deletion、语义扰动、write-time admission 和 false-write cascade 各自都有直接先例。宽口径 novelty 已被反驳；唯一仍可检验的是把这些约束组合成同一个、可审计的双侧 write-time certificate，并证明其在 coverage/compute/downstream 全部匹配时产生不可由单组件解释的交互收益。

## Key Results

- `run-debug-001`：现有 ID-only MemoryUnit validation 接受 modality strengthening；见 `CURRENT_RESULTS.md` 与回归测试。
- 环境基线：合规 Python 3.13.14 环境下，变更前 `15 passed`；稳定 framework checkpoint `114 passed`。
- provenance loader 已对重复段落坐标、未知字段和标签来源/裁决状态组合 fail closed；这是数据完整性修复，不是方法结果。
- qualifier coverage 已从类型级改为具体 slot 级；两个同类型实体不再被一个 `ENTITY` 标记错误覆盖。
- 两个 `PARTIAL` span 可通过显式 required support parts 联合支持一个不可误拆的跨句命题；这只是 provisional representation。
- 36-case catalog 已物化并冻结：20/13/3 ADMIT/REJECT/REVIEW，27 个 agent-authored/provisional、9 个 conditional programmatic relation certificates；SHA-256 为 `36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`，82,639 bytes。它不是 human gold，且尚无 benchmark 方法结果。
- benchmark oracle 现在必须与 support matrix 重算出的全部 inclusion-minimal sets 和同一三路 policy 一致；证书 integrity 是工程结果，不是效果结果。
- 仅内部自洽的 oracle 不是独立证书：loader 现只接受九个预注册 paired relations，并固定 canonical source/base-case digests。该机制阻止 self-consistent label forgery，但关系标签仍条件于 agent-authored provisional base 的语义正确性。
- C014（deontic `must -> may`）与 C034（新增 atom 的无支持）不能由表面 edit 机械决定，已在首次 benchmark 结果前降为 provisional；C006 与 C020 在 open-world 语义下是 `insufficient_evidence`，不是显式 `contradicted`。
- duplicate minimal-evidence-set 编码现在 fail closed；C022 的两个不同 singleton sets 合法，但重复同一 set（包括换序）非法。
- ID-only、exact-copy 与 static-oracle adapters 已实现。后者只作 plumbing upper bound；前两者均不是 strong semantic verifier。

## Patterns and Insights

- 当前方向的可证伪优势来自“写入前阻止 unsupported semantic strengthening”，而不是更强检索或更大模型。
- 任何风险改善都必须在匹配 coverage/计算和固定下游条件下解释，否则会退化为“拒绝更多所以错误更少”。
- exact quote 只证明字符串来自原文，不能自动证明候选命题的组合语义、作用域和模态忠实。
- 当前回归例说明 paragraph-ID validity 与 semantic support 是两个不同 estimand；后续 baseline 报告不得混称。
- 可替换 solver 的输出不能被 orchestration 盲信；当前边界会对选中 evidence 重新计算 sufficiency，避免伪造/bug result 污染 admission record。
- benchmark loader 与 runtime 必须调用同一个 claim-form decision override；独立两份逻辑曾令 evidence REJECT + form REVIEW 被错误抬升，现已用回归反例消除。
- `programmatic_oracle` 只能证明预注册派生关系保持其构造约束，不能把 provisional base 升格为客观真值；任何结果必须分层报告 27 个 provisional cases 与 9 个 conditional certificates。
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
