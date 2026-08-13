# Direction 01 冻结 Synthetic Benchmark Case Catalog v0.1

目录状态：`FROZEN_SYNTHETIC_CANDIDATE_V0.1`

冻结日期：`2026-08-14`

适用协议：`PILOT_PROTOCOL.md`、`ANNOTATION_GUIDE.md`、`NOVELTY_AUDIT.md`

## 1. 边界、记号与真实性声明

本目录包含 36 个公开安全、项目自著的 synthetic cases。所有机构、人员、试验、日期、数量和事件均为虚构；没有使用私人资料、真实用户文本或受版权保护的外部段落。它是 benchmark 设计目录，不是已经物化的 JSONL，也不是 human gold。

- 自然撰写项由本次 AI/agent 写作产生，标为 `label_source=llm_generated`、`adjudication_status=provisional`；不能写成 `human` 或 `human_gold`。
- 受控变换项在目录中给出 base、单一预注册 operator 和精确改动，标为 `label_source=programmatic_oracle`、`adjudication_status=synthetic_oracle`。这里的“oracle”只表示标签由构造规则决定，不表示真实世界真值，也不表示已经有人类复核。
- 本目录没有运行模型、没有生成客观性能结论。后续若物化为可运行 artifact，必须计算 source snapshot SHA-256、paragraph offsets 和 span offsets，并逐字验证 span。
- `D` 是列出的冻结 source paragraphs；`E_pool` 是提供给所有方法的相同 evidence-span pool；`E*` 是 oracle 允许的 inclusion-minimal sufficient set。若存在多个 `E*`，全部列出。
- expected decision 同时给出 support label：`ADMIT/fully_supported`、`REJECT/{partially_supported|contradicted|insufficient_evidence}` 或 `REVIEW/ambiguous`。
- `base_case_id=null` 仅用于自然撰写项。受控 counterfactual 的 base 必须存在于本目录；同一 base block 的全部变体必须在 source-level split 中作为一个整体移动。

## 2. Operator allow-list

| Operator | 允许的目标变化 | 非目标部分约束 | 预期用途 |
|---|---|---|---|
| `NATURAL_AUTHORED` | 无机械变换 | 自然完整句；标签仍是 provisional | 自然正/负/歧义控制 |
| `ENTITY_REPLACE` | 只替换一个实体身份 | relation、object、时间、语法不变 | entity fidelity |
| `NUMBER_REPLACE` | 只替换一个数值 | 单位和其他语义不变 | number fidelity |
| `DATE_REPLACE` | 只替换日期 | 事件、实体和数量不变 | date/time fidelity |
| `NEGATION_FLIP` | 添加或删除命题否定 | 时段、实体和谓词不变 | negation fidelity |
| `MODALITY_STRENGTHEN` | `may` 等可能性提升为确定性 | condition、事件和上限不变 | modality fidelity |
| `MODALITY_WEAKEN` | `must` 等义务降为许可 | condition、事件不变 | modality fidelity |
| `CONDITION_DELETE` | 删除一个必要条件 | 主命题其他部分不变 | condition fidelity |
| `SCOPE_EXPAND_QUANTIFIER` | 把受限人群/范围扩到更大集合 | action、time 不变 | scope/quantifier fidelity |
| `ATTRIBUTION_TRANSFER` | 只改变话语归属者 | 被引内容与 modality 不变 | attribution fidelity |
| `EVIDENCE_DUPLICATE` | 复制 evidence unit | candidate 和原 evidence 不变 | redundancy negative control |
| `SELF_SUFFICIENCY_DELETE_ENTITY` | 删除实体并留下无外部先行词的代词/省略结构 | 谓词与时间不变 | claim self-sufficiency |
| `OVERCOMPOSE_UNSUPPORTED_ATOM` | 向已支持 candidate 添加一个无证据 atom | 原 atoms 不变 | over-composition |
| `MEANING_PRESERVING_PARAPHRASE` | 只改写表述 | 所有 atoms/qualifiers 保持 | positive sham |
| `CONDITION_PRESERVING_PARAPHRASE` | 改写但保留条件 | entity/action/scope 保持 | condition positive sham |

## 3. 冻结 case records

### MSG-C001 — 单 span、含 scope 与频率的自然正例

- **case_id**：`MSG-C001`；family：`F01 fully supported single-span`；tags：`single_span`, `scope`, `number`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Harbor Learning Lab replaces the blue intake filter every 30 days during routine operation.”
- **candidate**：“During routine operation, the Harbor Learning Lab replaces its blue intake filter every 30 days.”
- **atomic / qualifier / support-parts**：`A1=Harbor Learning Lab replaces blue intake filter`；`Qscope=during routine operation`；`Qfrequency=every 30 days`；`A1+Qscope+Qfrequency <- E1`。
- **evidence spans**：`E1=P1["The Harbor Learning Lab replaces the blue intake filter every 30 days during routine operation."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`；删除 `E1` 后没有任何支持。
- **rationale**：candidate 只是保持全部 arguments 与 qualifiers 的语序调整，单 span 足够且不可删。
- **rival explanation**：ID-only、exact quote 和强 semantic verifier 都可能答对；该项主要校验正例 recall，不单独支持 joint mechanism 优势。

### MSG-C002 — 单 span 自然 paraphrase 正例

- **case_id**：`MSG-C002`；family：`F01 fully supported single-span`；tags：`single_span`, `time_scope`, `paraphrase`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“On weekdays, the Maple Archive opens its quiet study room at 08:30.”
- **candidate**：“The Maple Archive's quiet study room opens at 08:30 on weekdays.”
- **atomic / qualifier / support-parts**：`A1=Maple Archive opens quiet study room`；`Qtime=08:30`；`Qscope=weekdays`；全部由 `E1` 支持。
- **evidence spans**：`E1=P1["On weekdays, the Maple Archive opens its quiet study room at 08:30."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：所有事实元素均保留，所有格与主动句变换不改变语义。
- **rival explanation**：词面较低重叠的 checker 可能误拒；若 joint method 胜出，可能只是 paraphrase robustness，而非双侧最小性。

### MSG-C003 — number 与 date 的跨段组合正例

- **case_id**：`MSG-C003`；family：`F02 jointly supported cross-span`；tags：`cross_span=yes`, `number`, `date`, `two_atom`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Willow trial enrolled 120 volunteers.”；`P2`：“Follow-up for the Willow trial ended on 18 September 2025.”
- **candidate**：“The Willow trial enrolled 120 volunteers and ended follow-up on 18 September 2025.”
- **atomic / qualifier / support-parts**：`A1=trial enrolled volunteers`, `Qnumber=120`, supported by `E1`；`A2=trial ended follow-up`, `Qdate=18 September 2025`, supported by `E2`。
- **evidence spans**：`E1=P1["The Willow trial enrolled 120 volunteers."]`；`E2=P2["Follow-up for the Willow trial ended on 18 September 2025."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1,E2}}`；删除任一 span 都只剩半个 candidate。
- **rationale**：两个明确 atoms 共享同一 trial entity，组合不引入额外关系；联合证据充分且 inclusion-minimal。
- **rival explanation**：holistic checker 也可能正确聚合两段；若它与 joint method 持平，本例不能证明 atomic support matrix 必需。

### MSG-C004 — condition threshold 与事件日志的跨段正例

- **case_id**：`MSG-C004`；family：`F02 jointly supported cross-span`；tags：`cross_span=yes`, `condition`, `date`, `number`, `compositional`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Cedar greenhouse controller closes the roof vent only when wind speed exceeds 40 kilometers per hour.”；`P2`：“On 14 May 2026, the sensor recorded 46 kilometers per hour at 14:10, and the controller log recorded a completed roof-vent closure at 14:11.”
- **candidate**：“On 14 May 2026, the Cedar greenhouse controller closed the roof vent after the recorded wind speed exceeded its 40-kilometer-per-hour threshold.”
- **atomic / qualifier / support-parts**：`A1=controller's closure threshold is wind >40`, `Qcondition=only when >40`, from `E1`；`A2=46 was recorded at 14:10 and closure completed at 14:11`, `Qdate=14 May 2026`, from `E2`；comparison `46>40` and timestamps support the relation。
- **evidence spans**：`E1=P1["closes the roof vent only when wind speed exceeds 40 kilometers per hour"]`；`E2=P2["On 14 May 2026, the sensor recorded 46 kilometers per hour at 14:10, and the controller log recorded a completed roof-vent closure at 14:11."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1,E2}}`。
- **rationale**：P1 提供阈值语义，P2 提供日期、读数和动作；“after”未扩张为未记录的因果保证。
- **rival explanation**：结果可能主要来自显式数值比较；应和不含 threshold reasoning 的跨段项分层报告。

### MSG-C005 — entity pair 的自然 base control

- **case_id**：`MSG-C005`；family：`F03 entity replacement`；tags：`paired_base`, `entity`, `single_span`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection.”
- **candidate**：“After each inspection, the North Workshop stores the calibrated torque wrench in cabinet 4.”
- **atomic / qualifier / support-parts**：`A1=North Workshop stores calibrated torque wrench in cabinet 4`；`Qtime=after each inspection`；全部由 `E1` 支持。
- **evidence spans**：`E1=P1["The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：作为 `MSG-C006` 和 `MSG-C031` 的 source-block control，保留实体与全部 qualifiers。
- **rival explanation**：本项与变体近重复；若 pair 被拆分到不同 split，会产生记忆泄漏而不是泛化证据。

### MSG-C006 — entity replacement counterfactual

- **case_id**：`MSG-C006`；family：`F03 entity replacement`；tags：`paired_counterfactual`, `entity`。
- **base_case_id / operator**：`MSG-C005 / ENTITY_REPLACE`；精确变换：candidate 中 `North Workshop -> South Workshop`，其余 token 不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection.”
- **candidate**：“After each inspection, the South Workshop stores the calibrated torque wrench in cabinet 4.”
- **atomic / qualifier / support-parts**：`A1=South Workshop stores calibrated torque wrench`；`Qlocation=cabinet 4`；`Qtime=after each inspection`；`E1` 支持 relation/object/location/time，但实体只支持 North，不支持 South。
- **evidence spans**：`E1=P1["The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection."]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`；base 的 `{E1}` 不能迁移为 South Workshop 的支持。
- **rationale**：唯一目标轴是 entity；证据明确把动作归给另一个实体。
- **rival explanation**：单词替换极易形成表面 cue；必须与同 block 的正例和 paraphrase sham 联合评估，且 operator 元数据不得进入模型输入。

### MSG-C007 — number/date pair 的自然 base control

- **case_id**：`MSG-C007`；family：`F04 number/date replacement`；tags：`paired_base`, `number`, `date`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Amber ferry drill began on 12 March 2026 with 48 participants.”
- **candidate**：“Forty-eight participants joined the Amber ferry drill when it began on 12 March 2026.”
- **atomic / qualifier / support-parts**：`A1=Amber ferry drill began`；`Qnumber=48 participants`；`Qdate=12 March 2026`；全部由 `E1` 支持。
- **evidence spans**：`E1=P1["The Amber ferry drill began on 12 March 2026 with 48 participants."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：自然语序变化保留 number 与 date，作为两个单轴 counterfactual 的共同 base。
- **rival explanation**：数字格式 `48` 与 `Forty-eight` 可能考察 normalization；应把 normalization failure 与 qualifier reasoning failure 分开。

### MSG-C008 — number replacement counterfactual

- **case_id**：`MSG-C008`；family：`F04 number/date replacement`；tags：`paired_counterfactual`, `number`。
- **base_case_id / operator**：`MSG-C007 / NUMBER_REPLACE`；精确语义变换：`Forty-eight -> Eighty-four`，日期与事件不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The Amber ferry drill began on 12 March 2026 with 48 participants.”
- **candidate**：“Eighty-four participants joined the Amber ferry drill when it began on 12 March 2026.”
- **atomic / qualifier / support-parts**：`A1=drill began`, `Qdate=12 March 2026` supported；`Qnumber=84` contradicted by `48` in `E1`。
- **evidence spans**：`E1=P1["began on 12 March 2026 with 48 participants"]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`。
- **rationale**：entity、event、date 与语法均保持，只有数量与冻结 source 冲突。
- **rival explanation**：字符串不等即可解决，未必需要 joint certificate；必须和更隐式的跨段 number case 分层。

### MSG-C009 — date replacement counterfactual

- **case_id**：`MSG-C009`；family：`F04 number/date replacement`；tags：`paired_counterfactual`, `date`。
- **base_case_id / operator**：`MSG-C007 / DATE_REPLACE`；精确变换：`12 March 2026 -> 21 March 2026`，数量与事件不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The Amber ferry drill began on 12 March 2026 with 48 participants.”
- **candidate**：“Forty-eight participants joined the Amber ferry drill when it began on 21 March 2026.”
- **atomic / qualifier / support-parts**：`A1=drill began`, `Qnumber=48` supported；`Qdate=21 March 2026` contradicted by `12 March 2026`。
- **evidence spans**：`E1=P1["The Amber ferry drill began on 12 March 2026 with 48 participants."]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`。
- **rationale**：只改变 date 轴；source 给出单一、明确的不同日期。
- **rival explanation**：数字 token 差异可能被 lexical mismatch 捕获；该项只证明基本 sensitivity，不证明对隐式时间范围的泛化。

### MSG-C010 — negation pair 的自然 base control

- **case_id**：`MSG-C010`；family：`F05 negation flip`；tags：`paired_base`, `negation`, `single_span`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“At no point during the overnight test did the rainwater pump operate.”
- **candidate**：“During the overnight test, the rainwater pump did not operate.”
- **atomic / qualifier / support-parts**：`A1=rainwater pump operated`；`Qnegation=true`；`Qscope=overnight test`；全部由 `E1` 支持。
- **evidence spans**：`E1=P1["At no point during the overnight test did the rainwater pump operate."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：保留显式否定和时段，是 `MSG-C011` 的正例控制。
- **rival explanation**：显式 `not` 是强 cue；不能据此推断系统能处理 lexical negation、double negation 或 scope negation。

### MSG-C011 — negation flip counterfactual

- **case_id**：`MSG-C011`；family：`F05 negation flip`；tags：`paired_counterfactual`, `negation`。
- **base_case_id / operator**：`MSG-C010 / NEGATION_FLIP`；精确变换：删除 candidate 中的 `not`，其余语义单元不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“At no point during the overnight test did the rainwater pump operate.”
- **candidate**：“During the overnight test, the rainwater pump operated.”
- **atomic / qualifier / support-parts**：`A1=rainwater pump operated`；`Qnegation=false` 与 source 的 `true` 冲突；`Qscope=overnight test` 保持。
- **evidence spans**：`E1=P1["At no point during the overnight test did the rainwater pump operate."]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`。
- **rationale**：明确的 polarity flip；不是“source 没说”，而是 source 直接否定 candidate。
- **rival explanation**：单词删除会改变长度和 `not` cue；需要 `MSG-C030` 这类长度/表述变化但语义不变的 positive sham，并禁止向方法暴露 operator。

### MSG-C012 — modality pair 的自然 base control

- **case_id**：`MSG-C012`；family：`F06 modality strengthening/weakening`；tags：`paired_base`, `modality`, `condition`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“During peak load, the new scheduler may reduce queue latency by up to 15 percent.”
- **candidate**：“During peak load, the new scheduler may reduce queue latency by up to 15 percent.”
- **atomic / qualifier / support-parts**：`A1=scheduler reduces queue latency`；`Qcondition=peak load`；`Qmodality=may`；`Qbound=up to 15%`；全部由 `E1` 支持。
- **evidence spans**：`E1=P1["During peak load, the new scheduler may reduce queue latency by up to 15 percent."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：作为 modality、condition 和 scope counterfactuals 的共同正例锚点。
- **rival explanation**：完全复制会偏袒 exact-quote baseline；因此该 block 只能诊断单轴 sensitivity，不能作为整体效能主证据。

### MSG-C013 — modality strengthening counterfactual

- **case_id**：`MSG-C013`；family：`F06 modality strengthening/weakening`；tags：`paired_counterfactual`, `modality`。
- **base_case_id / operator**：`MSG-C012 / MODALITY_STRENGTHEN`；精确变换：`may reduce -> reduces`，condition 与 upper bound 保留。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“During peak load, the new scheduler may reduce queue latency by up to 15 percent.”
- **candidate**：“During peak load, the new scheduler reduces queue latency by up to 15 percent.”
- **atomic / qualifier / support-parts**：`A1`、`Qcondition`、`Qbound` 匹配；`Qmodality=asserted actual` 强于 source 的 `may`。
- **evidence spans**：`E1=P1["During peak load, the new scheduler may reduce queue latency by up to 15 percent."]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none`；source 不反证一定发生，但不能授权确定性写入。
- **rationale**：保留 condition 后只测试 epistemic strengthening，避免把多个 qualifier 删除捆绑成一个负例。
- **rival explanation**：modal token mismatch 足以解决；若只是词表规则命中，不能外推到隐含 uncertainty。

### MSG-C014 — modality weakening counterfactual

- **case_id**：`MSG-C014`；family：`F06 modality strengthening/weakening`；tags：`paired_counterfactual`, `modality`, `deontic`。
- **base_case_id / operator**：`MSG-C015 / MODALITY_WEAKEN`；精确变换：`must -> may`。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“Before entering the clean room, visitors must wear sealed shoe covers.”
- **candidate**：“Before entering the clean room, visitors may wear sealed shoe covers.”
- **atomic / qualifier / support-parts**：`A1=visitors wear sealed shoe covers`；`Qcondition=before entering clean room`；`Qmodality=permission` 不保真于 source 的 obligation。
- **evidence spans**：`E1=P1["Before entering the clean room, visitors must wear sealed shoe covers."]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`。
- **rationale**：即便 weakening 看似更保守，它改变了规范性事实；记忆中不能把义务写成可选许可。
- **rival explanation**：某些 entailment 形式主义可能把 `must` 逻辑蕴含为 `may`；此项依赖“qualifier fidelity”而非单调逻辑，需在人工协议中明确。

### MSG-C015 — deontic modality 的自然 base control

- **case_id**：`MSG-C015`；family：`F06 modality strengthening/weakening`；tags：`paired_base`, `modality`, `condition`, `deontic`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“Before entering the clean room, visitors must wear sealed shoe covers.”
- **candidate**：“Visitors must wear sealed shoe covers before they enter the clean room.”
- **atomic / qualifier / support-parts**：`A1=visitors wear sealed shoe covers`；`Qcondition=before entering clean room`；`Qmodality=must`；`E1` 全支持。
- **evidence spans**：`E1=P1["Before entering the clean room, visitors must wear sealed shoe covers."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：语序变化但保持 obligation 与 condition，作为 `MSG-C014` 的 base。
- **rival explanation**：pair 内 lexical overlap 高；必须 source-block split，防止从 base 记住答案模式。

### MSG-C016 — condition deletion counterfactual

- **case_id**：`MSG-C016`；family：`F07 deleted condition/temporal scope/quantifier`；tags：`paired_counterfactual`, `condition`。
- **base_case_id / operator**：`MSG-C012 / CONDITION_DELETE`；精确变换：删除 `During peak load`，保留 `may` 与 `up to 15 percent`。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“During peak load, the new scheduler may reduce queue latency by up to 15 percent.”
- **candidate**：“The new scheduler may reduce queue latency by up to 15 percent.”
- **atomic / qualifier / support-parts**：`A1`、`Qmodality`、`Qbound` 匹配；material `Qcondition=peak load` 缺失，candidate 把适用域扩到未限定运行期。
- **evidence spans**：`E1=P1["During peak load, the new scheduler may reduce queue latency by up to 15 percent."]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none`。
- **rationale**：condition 被协议预先声明为 material；删除后不是自足的忠实摘要。
- **rival explanation**：某些应用把省略条件解释为不完整而非错误；若人类认为 materiality 不稳定，该类应改为 REVIEW 或从 confirmatory set 剔除，而不是事后保留有利标签。

### MSG-C017 — scope/quantifier 的自然 base control

- **case_id**：`MSG-C017`；family：`F07 deleted condition/temporal scope/quantifier`；tags：`paired_base`, `scope`, `quantifier`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“Only staff assigned to the night shift may unlock the west entrance after 22:00.”
- **candidate**：“After 22:00, only night-shift staff may unlock the west entrance.”
- **atomic / qualifier / support-parts**：`A1=staff may unlock west entrance`；`Qtime=after 22:00`；`Qscope=night-shift staff only`；`Qmodality=may`。
- **evidence spans**：`E1=P1["Only staff assigned to the night shift may unlock the west entrance after 22:00."]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：保留限定人群与时间，是 `MSG-C018` 的 positive control。
- **rival explanation**：显式 `only` 容易被规则捕捉；需要未来补充隐式 quantifier 自然样本。

### MSG-C018 — scope expansion counterfactual

- **case_id**：`MSG-C018`；family：`F07 deleted condition/temporal scope/quantifier`；tags：`paired_counterfactual`, `scope`, `quantifier`。
- **base_case_id / operator**：`MSG-C017 / SCOPE_EXPAND_QUANTIFIER`；精确语义变换：`only night-shift staff -> staff`，时间、动作和 modality 不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“Only staff assigned to the night shift may unlock the west entrance after 22:00.”
- **candidate**：“After 22:00, staff may unlock the west entrance.”
- **atomic / qualifier / support-parts**：`A1`、`Qtime`、`Qmodality` 匹配；`Qscope=all staff` 超出 source 的 restricted subset。
- **evidence spans**：`E1=P1["Only staff assigned to the night shift may unlock the west entrance after 22:00."]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none`。
- **rationale**：删除限定语后授权范围扩大，构成 material scope loss。
- **rival explanation**：长度变化与 `only` 删除可泄漏标签；应与长度变化但保持 scope 的自然 paraphrase 配对，并在 surface-only baseline 上报告。

### MSG-C019 — attribution pair 的自然 base control

- **case_id**：`MSG-C019`；family：`F08 attribution transfer`；tags：`paired_base`, `attribution`, `modality`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“In her inspection note, engineer Mira Sol described the western seal as likely to need replacement before winter.”
- **candidate**：“Engineer Mira Sol wrote that the western seal would likely need replacement before winter.”
- **atomic / qualifier / support-parts**：`A1=western seal likely needs replacement`；`Qtime=before winter`；`Qmodality=likely`；`Qattribution=Mira Sol's inspection note`。
- **evidence spans**：`E1=P1["engineer Mira Sol described the western seal as likely to need replacement before winter"]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：candidate 保留内容、概率与作者归属；不能去掉 “wrote/described” 后当作无条件事实。
- **rival explanation**：名字匹配即可解决一部分 attribution；后续真实人标集必须包含同名或多说话者干扰。

### MSG-C020 — attribution transfer counterfactual

- **case_id**：`MSG-C020`；family：`F08 attribution transfer`；tags：`paired_counterfactual`, `attribution`。
- **base_case_id / operator**：`MSG-C019 / ATTRIBUTION_TRANSFER`；精确变换：`Mira Sol -> Tomas Reed`，其余内容不变。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“In her inspection note, engineer Mira Sol described the western seal as likely to need replacement before winter.”
- **candidate**：“Engineer Tomas Reed wrote that the western seal would likely need replacement before winter.”
- **atomic / qualifier / support-parts**：content、time 与 modality 匹配；`Qattribution=Tomas Reed` 与 source 的 `Mira Sol` 冲突。
- **evidence spans**：`E1=P1["engineer Mira Sol described the western seal as likely to need replacement before winter"]`。
- **expected**：`REJECT / contradicted`。
- **minimal sets**：`E*=none`。
- **rationale**：source 确认了同一内容，但没有授权把它归给另一个人；正是 pooled support 会漏掉的 ownership error。
- **rival explanation**：entity mismatch 和 attribution mismatch 在本例重合；后续应以同一人多种角色的自然案例区分真正 source ownership 能力。

### MSG-C021 — topic-related non-supporting evidence

- **case_id**：`MSG-C021`；family：`F09 topic-related but non-supporting evidence`；tags：`natural_negative`, `topic_related`, `insufficient`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Quartz observatory installed a new humidity sensor beside the telescope dome.”；`P2`：“Its maintenance handbook explains how humidity can affect mirror coatings.”
- **candidate**：“The new humidity sensor automatically closes the Quartz observatory's telescope dome.”
- **atomic / qualifier / support-parts**：`A1=sensor automatically closes dome`；`Qmodality=automatic`；E1 只支持 installation/location，E2 只支持 topic relation；没有 control-action support。
- **evidence spans**：`E1=P1["installed a new humidity sensor beside the telescope dome"]`；`E2=P2["humidity can affect mirror coatings"]`。
- **expected**：`REJECT / insufficient_evidence`。
- **minimal sets**：`E*=none`。
- **rationale**：候选与 source 主题高度相关，但把邻近和动机拼成未记录的自动控制机制。
- **rival explanation**：strong holistic verifier 应能拒绝；若只有 joint method 成功，可能是 baseline 实现过弱。

### MSG-C022 — 重复 span 不应进入 minimal set

- **case_id**：`MSG-C022`；family：`F10 redundant evidence`；tags：`redundant=yes`, `duplicate`, `negative_control`。
- **base_case_id / operator**：`MSG-C001 / EVIDENCE_DUPLICATE`；精确变换：在 E_pool 中增加与 `E1` 文本相同但 ID 不同的 `E2`。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The Harbor Learning Lab replaces the blue intake filter every 30 days during routine operation.”；`P2`：“The Harbor Learning Lab replaces the blue intake filter every 30 days during routine operation.”
- **candidate**：“During routine operation, the Harbor Learning Lab replaces its blue intake filter every 30 days.”
- **atomic / qualifier / support-parts**：与 `MSG-C001` 相同；`E1` 或 `E2` 任一即可完整支持，二者一起非 inclusion-minimal。
- **evidence spans**：`E1=P1[full sentence]`；`E2=P2[identical full sentence]`。
- **expected**：`ADMIT / fully_supported`，但 solver 必须选择一个 span，而非 `{E1,E2}`。
- **minimal sets**：`E*={{E1},{E2}}`；minimum-cardinality 为 1；`{E1,E2}` 非最小。
- **rationale**：冗余不应把正确 candidate 变成 REJECT；它应改变 evidence selection/certificate。
- **rival explanation**：按字符串去重即可通过，不能证明语义最小性。

### MSG-C023 — 语义冗余的自然正例

- **case_id**：`MSG-C023`；family：`F10 redundant evidence`；tags：`redundant=yes`, `paraphrase_duplicate`, `natural_control`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Lark clinic's backup generator successfully completed its weekly self-test on Friday.”；`P2`：“Friday's weekly diagnostic for the Lark clinic backup generator finished successfully.”
- **candidate**：“The Lark clinic backup generator successfully completed its weekly self-test on Friday.”
- **atomic / qualifier / support-parts**：`A1=generator completed self-test successfully`；`Qfrequency=weekly`；`Qtime=Friday`；每个 span 单独支持完整 claim。
- **evidence spans**：`E1=P1[full sentence]`；`E2=P2[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1},{E2}}`；`{E1,E2}` 非 inclusion-minimal。
- **rationale**：测试语义级而非 exact-string 级冗余；两个合法最小解都应保留。
- **rival explanation**：P1 的 “completed” 未显式含 “successfully”，但日常语言可能暗示；若人工不同意，则 P1 单独不应进入 `E*`，需在冻结物化前 adjudicate。

### MSG-C024 — 直接矛盾 spans

- **case_id**：`MSG-C024`；family：`F11 contradictory spans`；tags：`contradictory=yes`, `date`, `review`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The first status bulletin says the River Gate inspection finished on 2 June 2026.”；`P2`：“A later status bulletin says the River Gate inspection finished on 3 June 2026, and it does not state that the earlier bulletin was corrected.”
- **candidate**：“The River Gate inspection finished on 3 June 2026.”
- **atomic / qualifier / support-parts**：`A1=inspection finished`；`Qdate=3 June 2026` supported by `E2` but contradicted by `E1`；source provides no authoritative correction rule。
- **evidence spans**：`E1=P1["finished on 2 June 2026"]`；`E2=P2["finished on 3 June 2026"]`。
- **expected**：`REVIEW / ambiguous`。
- **minimal sets**：local support set `{{E2}}`，但 global conflict set `{{E1,E2}}` 必须随 certificate 暴露；不能自动 ADMIT。
- **rationale**：later 不自动等于 corrected；两条冻结记录不兼容，需要来源权威或 adjudication。
- **rival explanation**：若 production policy 固定 last-write-wins，本例可能 ADMIT；当前协议未授权该规则，因此 REVIEW 是保守设计选择。

### MSG-C025 — 来源明确撤回后的矛盾 resolution control

- **case_id**：`MSG-C025`；family：`F11 contradictory spans`；tags：`contradictory=yes`, `cross_span=yes`, `correction`, `natural_control`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“An early notice listed the Solace Hall rehearsal at 18:00.”；`P2`：“The final notice explicitly cancels the 18:00 listing and reschedules the Solace Hall rehearsal to 19:30.”
- **candidate**：“The final scheduled time for the Solace Hall rehearsal is 19:30.”
- **atomic / qualifier / support-parts**：`A1=final rehearsal time is 19:30` from `E2`；`Qstatus=final`; `E1` supplies conflict history, `E2` explicitly resolves it。
- **evidence spans**：`E1=P1["listed ... at 18:00"]`；`E2=P2["explicitly cancels the 18:00 listing and reschedules ... to 19:30"]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E2}}`；E2 内部同时给出 cancellation 与新时间，E1 是冗余历史。
- **rationale**：与 `MSG-C024` 对照，证明系统不应见到任意冲突就一律 REVIEW；显式 correction 可以解析。
- **rival explanation**：`final`/`cancels` 是强 cue；后续需要不依赖单个关键词的版本权威规则。

### MSG-C026 — 代词归属真正歧义

- **case_id**：`MSG-C026`；family：`F12 genuinely ambiguous evidence`；tags：`ambiguous=yes`, `attribution`, `pronoun`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“Mara spoke with Lia after the sensor review. She said the calibration note was incomplete.”
- **candidate**：“Mara said that the calibration note was incomplete.”
- **atomic / qualifier / support-parts**：`A1=calibration note incomplete`；`Qattribution=Mara`；`E1` 支持内容，但 `She` 可合理指 Mara 或 Lio。
- **evidence spans**：`E1=P1["Mara spoke with Lia after the sensor review. She said the calibration note was incomplete."]`。
- **expected**：`REVIEW / ambiguous`。
- **minimal sets**：`E*=none` for unambiguous admission；`{E1}` 是歧义证据集而非充分证书。
- **rationale**：这是 responsible abstention，而不是硬判错误；需要代词消歧或外部来源。
- **rival explanation**：英语 recency/subject preferences 可能偏向某一 antecedent；人工判断是否“真正两读”必须在物化前独立复核。

### MSG-C027 — 临界数值的真正歧义

- **case_id**：`MSG-C027`；family：`F12 genuinely ambiguous evidence`；tags：`ambiguous=yes`, `number`, `scope`, `review`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The checklist says the auxiliary fan starts when temperature is above 30 degrees Celsius.”；`P2`：“The event log records exactly 30.0 degrees Celsius and a fan-start event at the same timestamp, but it does not identify whether the auxiliary or main fan started.”
- **candidate**：“At 30.0 degrees Celsius, the auxiliary fan started.”
- **atomic / qualifier / support-parts**：`A1=auxiliary fan started`；`Qtemperature=30.0`；P1 的 strict `above 30` 不授权阈值等号，P2 的 fan identity 未解析。
- **evidence spans**：`E1=P1["auxiliary fan starts when temperature is above 30 degrees Celsius"]`；`E2=P2["exactly 30.0 degrees Celsius and a fan-start event ... does not identify whether the auxiliary or main fan started"]`。
- **expected**：`REVIEW / ambiguous`。
- **minimal sets**：`E*=none`；`{E1,E2}` 仍无法唯一确定 fan identity。
- **rationale**：同 timestamp 的事件不足以跨越 strict-threshold 与 identity ambiguity。
- **rival explanation**：保守 verifier 可能 REJECT；三路决策是否能稳定区分 ambiguity 与 contradiction 是本例的主要价值。

### MSG-C028 — 不自足 fragment

- **case_id**：`MSG-C028`；family：`F13 claim fragment not self-sufficient`；tags：`self_sufficiency`, `fragment`, `natural_negative`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Aurora sampling cart reached Bay 6 at noon.”
- **candidate**：“It reached Bay 6 at noon.”
- **atomic / qualifier / support-parts**：`A1=?entity reached Bay 6`；`Qtime=noon`；candidate 的 `It` 在脱离 source 后没有可识别 antecedent。
- **evidence spans**：`E1=P1["The Aurora sampling cart reached Bay 6 at noon."]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none` for admissible self-sufficient claim；source 能恢复 entity，但 candidate 自身不满足 write contract。
- **rationale**：这是 claim-side failure，不是 evidence absence；持久写入的 proposition 必须能独立识别主体。
- **rival explanation**：若 memory schema 允许显式 entity ID 与文本分离，fragment 可能可解析；本目录假定 candidate text 是当前 write unit，未来 schema 改变需重审标签。

### MSG-C029 — over-composed claim 含一个 unsupported atom

- **case_id**：`MSG-C029`；family：`F14 over-composed claim with unsupported atom`；tags：`over_composed`, `cross_span=yes`, `natural_negative`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Pine courier delivered two sealed sample boxes to Lab C.”；`P2`：“The delivery log records arrival at 16:20.”
- **candidate**：“At 16:20, the Pine courier delivered two sealed sample boxes to Lab C, and both boxes passed contamination screening.”
- **atomic / qualifier / support-parts**：`A1=delivered two sealed sample boxes to Lab C`, `Qtime=16:20`, supported jointly by `E1+E2`；`A2=both boxes passed contamination screening` unsupported。
- **evidence spans**：`E1=P1[full sentence]`；`E2=P2["arrival at 16:20"]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none` for full candidate；`{E1,E2}` 仅是 supported-subclaim set for A1。
- **rationale**：一个被完整支持的长前缀不能掩盖末尾 unsupported atom；完整 proposition support 是 admission 单位。
- **rival explanation**：末尾位置可能成为 cue；应改变 unsupported atom 的位置并做位置平衡的扩展版本，当前单例不支持位置不变性。

### MSG-C030 — negation block 的 meaning-preserving sham

- **case_id**：`MSG-C030`；family：`F05 paired control`；tags：`programmatic_sham`, `negation_preserved`, `positive_control`。
- **base_case_id / operator**：`MSG-C010 / MEANING_PRESERVING_PARAPHRASE`；精确变换：`did not operate -> remained inactive`，保留 negative polarity 与 overnight scope。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“At no point during the overnight test did the rainwater pump operate.”
- **candidate**：“The rainwater pump remained inactive throughout the overnight test.”
- **atomic / qualifier / support-parts**：`A1=pump inactive/non-operating`；`Qnegation/equivalent_state=true`；`Qscope=overnight test`；`E1` 支持。
- **evidence spans**：`E1=P1[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：语义 polarity 不变但删除显式 `not`，用于识别只依赖否定词 presence 的标签循环。
- **rival explanation**：`remained inactive` 可能暗示全时段，而 source 的 `during` 未必等于 throughout；物化前需人工审核 temporal equivalence，失败则改成更保守 paraphrase。

### MSG-C031 — entity block 的 meaning-preserving sham

- **case_id**：`MSG-C031`；family：`F03 paired control`；tags：`programmatic_sham`, `entity_preserved`, `positive_control`。
- **base_case_id / operator**：`MSG-C005 / MEANING_PRESERVING_PARAPHRASE`；精确变换：主动句改为被动句，North Workshop 实体保持。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection.”
- **candidate**：“After every inspection, the calibrated torque wrench is placed in cabinet 4 by the North Workshop.”
- **atomic / qualifier / support-parts**：`A1=North Workshop stores/places wrench in cabinet 4`；`Qtime=after each/every inspection`；实体未改变。
- **evidence spans**：`E1=P1[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：检验系统是否把“表面改变”误当成 entity corruption；只有语义实体交换的 `MSG-C006` 应被拒。
- **rival explanation**：被动语态可能影响 verifier，而非 admission logic；错误应归入 verifier robustness。

### MSG-C032 — 保留 condition 的 positive sham

- **case_id**：`MSG-C032`；family：`F07 paired control`；tags：`programmatic_sham`, `condition_preserved`, `positive_control`。
- **base_case_id / operator**：`MSG-C012 / CONDITION_PRESERVING_PARAPHRASE`；精确变换：`During peak load -> When load is at its peak`，其他 qualifiers 保持。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“During peak load, the new scheduler may reduce queue latency by up to 15 percent.”
- **candidate**：“When load is at its peak, the new scheduler may reduce queue latency by as much as 15 percent.”
- **atomic / qualifier / support-parts**：`A1`；`Qcondition=peak load`；`Qmodality=may`；`Qbound=up to/as much as 15%`；全部支持。
- **evidence spans**：`E1=P1[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1}}`。
- **rationale**：与 `MSG-C016` 对照：短语被改写但 condition 没被删除，不能因 surface mismatch 拒绝。
- **rival explanation**：如果系统只通过 lexical overlap，可能把 sham 与 deletion 都判错；应同时报告 pair-level exact outcomes，而不只汇总 accuracy。

### MSG-C033 — 三段联合支持正例

- **case_id**：`MSG-C033`；family：`F02 jointly supported cross-span`；tags：`cross_span=yes`, `three_span`, `entity`, `number`, `date`, `attribution`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Delta Field Team collected 18 soil cores.”；`P2`：“The collection log dates that batch to 7 April 2026.”；`P3`：“Analyst Nia Verne recorded that all 18 cores were transferred to cold storage.”
- **candidate**：“Analyst Nia Verne recorded that the Delta Field Team's 18 soil cores, collected on 7 April 2026, were transferred to cold storage.”
- **atomic / qualifier / support-parts**：`A1=Delta Field Team collected 18 cores` from `E1`；`Qdate=7 April 2026` from `E2`；`A2=all 18 transferred to cold storage`, `Qattribution=Nia Verne` from `E3`。
- **evidence spans**：`E1=P1[full sentence]`；`E2=P2[full sentence]`；`E3=P3[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1,E2,E3}}`；逐 span deletion 分别丢失 collector/count、date、transfer/attribution。
- **rationale**：覆盖三段、共享 batch/count 链接与 attribution；不是简单相邻句复制。
- **rival explanation**：P2 的 “that batch” 需要指代链接；若 resolver 失败，可能是 coreference 而非 joint minimality 问题。

### MSG-C034 — attribution 与 condition 的跨段 over-composition

- **case_id**：`MSG-C034`；family：`F14 over-composed claim with unsupported atom`；tags：`cross_span=yes`, `attribution`, `condition`, `over_composed`。
- **base_case_id / operator**：`MSG-C035 / OVERCOMPOSE_UNSUPPORTED_ATOM`；精确变换：在 base candidate 后添加独立 atom `the automated controller initiated the response`。
- **provenance**：`generator_type=programmatic`; `label_source=programmatic_oracle`; `adjudication_status=synthetic_oracle`。
- **source paragraphs**：`P1`：“The safety guide says an alert should be sent if tank pressure exceeds 8 bar.”；`P2`：“Operator Jo Lin recorded a pressure of 8.6 bar at 11:05 and wrote that an alert was sent.”
- **candidate**：“Operator Jo Lin recorded that at 11:05 the tank pressure exceeded the 8-bar alert threshold and that an alert was sent; additionally, the automated controller initiated the response.”
- **atomic / qualifier / support-parts**：`A1=threshold is >8 bar` from `E1`；`A2=Jo recorded 8.6 at 11:05 and wrote alert sent` from `E2`；`A3=automated controller initiated the response` 无支持。
- **evidence spans**：`E1=P1["if tank pressure exceeds 8 bar"]`；`E2=P2[full sentence]`。
- **expected**：`REJECT / partially_supported`。
- **minimal sets**：`E*=none` for full candidate；`{E1,E2}` supports base only。
- **rationale**：自动控制器启动响应是新增的 material mechanism atom，不能由 alert 实际发生和 guide 条件推断。
- **rival explanation**：新增词位于句末；可能是位置 cue。未来扩展应把 unsupported atom 置于开头/中间并保持长度。

### MSG-C035 — attribution 与 condition 的跨段 base control

- **case_id**：`MSG-C035`；family：`F02 jointly supported cross-span`；tags：`cross_span=yes`, `paired_base`, `attribution`, `condition`, `number`, `time`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The safety guide says an alert should be sent if tank pressure exceeds 8 bar.”；`P2`：“Operator Jo Lin recorded a pressure of 8.6 bar at 11:05 and wrote that an alert was sent.”
- **candidate**：“Operator Jo Lin recorded that at 11:05 the tank pressure exceeded the 8-bar alert threshold and that an alert was sent.”
- **atomic / qualifier / support-parts**：`A1=alert threshold condition is pressure>8` from `E1`；`A2=pressure=8.6 at 11:05`, `A3=alert sent`, `Qattribution=Jo Lin's record` from `E2`。
- **evidence spans**：`E1=P1["if tank pressure exceeds 8 bar"]`；`E2=P2[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：`E*={{E1,E2}}`。
- **rationale**：作为 `MSG-C034` 的 base，完整保留 attribution；阈值比较需要两个 span 联合。
- **rival explanation**：`8.6>8` 可能由确定性算术解决；应单列 arithmetic-assisted subgroup。

### MSG-C036 — 多个不同但同样充分的跨段最小集合

- **case_id**：`MSG-C036`；family：`F10 redundant evidence`；tags：`redundant=yes`, `cross_span=yes`, `multiple_minimal_sets`。
- **base_case_id / operator**：`null / NATURAL_AUTHORED`。
- **provenance**：`generator_type=llm_or_agent`; `label_source=llm_generated`; `adjudication_status=provisional`。
- **source paragraphs**：`P1`：“The Elm survey included 64 households.”；`P2`：“The field note dates the Elm survey to October 2025.”；`P3`：“A summary card states that the 64-household Elm survey was conducted in October 2025.”
- **candidate**：“The Elm survey included 64 households and was conducted in October 2025.”
- **atomic / qualifier / support-parts**：`A1=64 households`；`Qdate=October 2025`；`E1+E2` compositionally supports，`E3` 单独支持。
- **evidence spans**：`E1=P1[full sentence]`；`E2=P2[full sentence]`；`E3=P3[full sentence]`。
- **expected**：`ADMIT / fully_supported`。
- **minimal sets**：inclusion-minimal `E*={{E1,E2},{E3}}`；minimum-cardinality only `{{E3}}`。
- **rationale**：显式区分 inclusion-minimal 与 minimum-cardinality；solver 不得把 `{E1,E2,E3}` 当作最小，也不得丢掉合法的两-span MEG。
- **rival explanation**：选择 E3 可由“最短集合”启发式完成；真正机制价值取决于是否正确枚举多解并在其它 case 中保持 support fidelity。

## 4. 覆盖矩阵与计数审计

### 4.1 十四个 case families

| Pilot family | 覆盖 cases | 最低要求检查 |
|---|---|---|
| F01 fully supported single-span | C001, C002 | 2 natural controls |
| F02 jointly supported cross-span | C003, C004, C033, C035 | 4；其中 1 个三段 |
| F03 entity replacement | C005, C006, C031 | base + counterfactual + positive sham |
| F04 number/date replacement | C007, C008, C009 | 同 base 的两个单轴反事实 |
| F05 negation flip | C010, C011, C030 | base + flip + lexical sham |
| F06 modality strengthening/weakening | C012–C015 | epistemic strengthening + deontic weakening |
| F07 deleted condition/scope/quantifier | C016–C018, C032 | condition deletion + scope expansion + sham |
| F08 attribution transfer | C019, C020 | base + source-owner transfer |
| F09 topic-related non-support | C021 | natural negative |
| F10 redundant evidence | C022, C023, C036 | exact、semantic、multiple-MEG redundancy |
| F11 contradictory spans | C024, C025 | unresolved conflict + explicit correction |
| F12 genuinely ambiguous | C026, C027 | attribution/coreference + threshold/identity |
| F13 non-self-sufficient fragment | C028 | claim-side failure |
| F14 over-composed unsupported atom | C029, C034, C035 | natural negative + programmatic/base pair |

### 4.2 Qualifier 与设计属性

| 属性 | 覆盖 |
|---|---|
| entity | C005–C006, C031, C033 |
| number | C003–C004, C007–C009, C027, C029, C033, C035–C036 |
| date/time | C002–C004, C007–C010, C017–C019, C024–C025, C029, C033, C035–C036 |
| negation | C010–C011, C030 |
| modality | C012–C015, C019–C021 |
| condition | C004, C012–C013, C015–C016, C032, C034–C035 |
| scope/quantifier | C001–C002, C010, C017–C018, C027, C030 |
| attribution | C019–C020, C026, C033–C035 |
| cross-span | C003, C004, C025, C029, C033–C036（8 个） |
| redundant evidence | C022, C023, C025, C036（至少 4 个；C025 的旧 notice 对 final claim 冗余） |
| contradiction/ambiguity | C024, C026, C027（3 个 REVIEW）；C025 是 resolved-conflict control |
| natural authored controls | 22 个 `NATURAL_AUTHORED` 项 |
| programmatic transforms | 14 个显式 operator 项 |

### 4.3 Expected decision 分布

- `ADMIT`：C001–C005, C007, C010, C012, C015, C017, C019, C022–C023, C025, C030–C033, C035–C036，共 20。
- `REJECT`：C006, C008–C009, C011, C013–C014, C016, C018, C020–C021, C028–C029, C034，共 13。
- `REVIEW`：C024, C026–C027，共 3。

总数为 36。三路分布不均衡是刻意的：REVIEW 只用于 genuine ambiguity/unresolved conflict，不用它填充配额。正式 benchmark 扩展时应增加独立 natural REVIEW blocks，而不是复制这三个近邻。

## 5. Pair、split 与 run-order 约束

### 5.1 Source-blocked pairs

以下 block 是不可拆分的 evaluation unit group：

| block_id | cases | 变化轴 |
|---|---|---|
| `B-ENTITY-01` | C005, C006, C031 | supported base / entity swap / semantic sham |
| `B-NUMDATE-01` | C007, C008, C009 | base / number / date |
| `B-NEG-01` | C010, C011, C030 | base / negation flip / polarity-preserving sham |
| `B-EPI-MODCOND-01` | C012, C013, C016, C032 | base / modality / condition / condition sham |
| `B-DEONTIC-01` | C014, C015 | obligation base / weakening |
| `B-SCOPE-01` | C017, C018 | restricted base / scope expansion |
| `B-ATTR-01` | C019, C020 | attributed base / source transfer |
| `B-DUP-01` | C001, C022 | base / evidence duplicate |
| `B-OVERCOMPOSE-01` | C034, C035 | cross-span base / unsupported mechanism atom |

训练、prompt tuning、threshold tuning 与 test 之间必须按 `block_id` 分割，而不是按 case 分割。否则同一 source 和几乎相同 candidate 会泄漏。初始 micro-benchmark 不用于训练；若只做冻结测试，run order 用 seed `17` 在 block 内外分别打乱，并以 seeds `29`、`47` 检查次序敏感性，不把三次次序当作独立样本。

### 5.2 Pair-level measurements

- counterfactual sensitivity：base ADMIT 且目标 corruption REJECT；两者都对才算 pair success。
- sham specificity：base 与 meaning-preserving sham 都 ADMIT；不能因任意 token/长度变化而拒绝。
- REVIEW fidelity：歧义 case 必须单列，不把 REVIEW 重编码为正确 REJECT。
- evidence minimality：对 C022/C023/C036 同时报告“完整 support 是否正确”和“是否选择任一合法最小集”；选择不同合法 `E*` 不算错误。

## 6. 泄漏、语法与标签循环审计

### 6.1 单词替换泄漏

当前 programmatic negatives 的确包含可见单轴编辑；这使 synthetic oracle 可审计，却也产生表面捷径。控制措施：

1. operator、base_case_id、expected label 和 rationale 永不进入 verifier/model input；
2. 同 source block 不跨 split；
3. 报告 surface-only baselines：token mismatch、长度、数字/专名变化、`not`/modal lexicon；
4. 每个主要 perturbation block 含保持标签为 ADMIT 的表述变化 sham；
5. primary 结果同时给 natural authored 子集与 programmatic 子集，不能用 programmatic 大量简单负例抬高总分；
6. 后续扩展在每个轴增加自然负例和位置/长度平衡 counterfactual，未完成前只称 micro-benchmark。

### 6.2 不自然语法检查

所有 candidate 均按完整英文句子撰写，避免硬替换造成 agreement、冠词或时态错误。仍需在物化前人工复核以下高风险项：

- C023 的 `completed` 是否足以支持 `successfully`；
- C014 中 deontic `must -> may` 是 qualifier fidelity 冲突还是可接受的弱蕴含；
- C026 的代词是否真有两个自然 antecedents。

任何失败项必须在首次模型评估前修订并提升 catalog 版本；看到结果后改写只能进入 exploratory v0.2，不能回填 v0.1。

### 6.3 标签循环与 programmatic oracle 限制

- programmatic operator 决定合成 expected label，因此这些项只能验证实现能否恢复预注册规则，不能证明人类同意、自然分布有效或真实下游价值。
- label 不得由待评 verifier、candidate generator 或最终 grader 生成；`fake_oracle` 只能做 plumbing upper bound。
- 不得让文件名、case family、operator、evidence ordering 或 span count 与 label 一一对应。REJECT 既有 1-span 也有 2-span，ADMIT 也覆盖相同结构；运行时 evidence order 应在不改变 ID/offset 的条件下 seeded shuffle。
- 对 C024/C026/C027 的 REVIEW，任何二值化都必须单独披露；不得把 abstention 计为准确拒绝。
- 本目录的 `provisional` natural labels 需要至少两名独立人类标注者和 adjudication 后，才可升级为 `human_gold`；programmatic items 即使人审通过，也应保留构造 provenance。

## 7. 物化前冻结检查单

1. 为每个 block 生成独立 `document_id`，共享 source 的 pair 复用同一 immutable snapshot。
2. 规范化换行后计算 SHA-256；记录 paragraph `snapshot_start/snapshot_end` 和 evidence paragraph-local offsets。
3. 自动验证所有 quoted span 精确出现且 offset 唯一；重复段落 C022 必须通过 paragraph ID 消歧。
4. 验证每个 programmatic item 的 base 存在、operator 在 allow-list、精确 diff 只触及目标轴。
5. 对每个 `E*` 做 deletion audit；对 C022/C023/C036 枚举全部已知 minimal sets。
6. 独立语言/语义审查第 6.2 节的三个风险项；保留初始判断与 adjudication，不静默覆盖。
7. 冻结 block split、run-order seed、candidate/evidence pool 和 downstream question templates 后再运行任何方法。
8. 运行并报告 token/length/name/number/modal surface baselines，确认主结论不是 operator leakage。
9. 分别报告 natural/provisional 与 programmatic-oracle 结果；两者都不能替代真实人标、多域 benchmark。
10. 若 strong holistic verifier 在 matched coverage/compute 下持平或更优，按 `NOVELTY_AUDIT.md` 降级结论，不用此 synthetic catalog 维持系统优越性主张。
