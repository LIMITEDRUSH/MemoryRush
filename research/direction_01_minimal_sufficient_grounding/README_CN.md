# Direction 1：联合最小—充分证据的写入时记忆准入

状态：`ACTIVE / INCOMPLETE`

证据总状态：`MIXED`

冻结核心：由用户锁定，不得由代理改题

当前工程检查点：`ac493654cb402291483e39d747648d32fdbf16f9`（已推送）

## 这项研究在问什么

给定冻结原文 `D`、候选记忆命题 `c` 和可定位证据跨度集合 `E`，本方向研究：命题—证据组合在什么条件下才有资格在 write time 进入持久记忆。

唯一主贡献假设是“双侧联合约束”：命题最小但自足，同时证据集合最小但足以支持完整命题。范围只包括 source-support integrity，不判断来源在现实世界中是否为真，也不把 salience、个性化、检索或回答生成改成主问题。

## 当前结论边界

- 广义“write-time support gate / evidence binding / atomic claim / minimal evidence”等新颖性已被最接近工作显著覆盖，当前状态为 `CONTRADICTED_UNDER_TESTED_LITERATURE_SEARCH`。
- 仅剩一个尚未展示的窄组合 delta：在同一个写入门内联合约束命题侧 minimal+self-contained 与证据侧 inclusion-minimal+sufficient，并用 deletion / qualifier intervention 产生三路准入，再在 matched native coverage/compute 与固定下游条件下检验 false-admission amplification。
- 工程框架、冻结 synthetic microbenchmark、关系证书、oracle 隔离 manifest、三种 schedule、三类严格 prompt/schema 与不可覆盖 attempt store 已实现并离线验证。
- 当前没有 36-case semantic model 结果、没有 human gold、没有方法优势、没有统计显著性、没有 confirmatory run。
- synthetic development set 在设计时被作者/代理看过 oracle，因此未来即使出现有利结果，也只能是 falsification-oriented debugging observation；正向比较需要 fresh source-blocked、label-blind holdout。

## 冻结研究工件

- benchmark：`data/benchmarks/direction1_synthetic_v0_1.jsonl`
- SHA-256：`36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`
- 大小：82,639 bytes；36 cases；20 ADMIT / 13 REJECT / 3 REVIEW
- provenance：27 agent/LLM provisional；9 conditional programmatic relations；0 human gold
- semantic protocol：`SEMANTIC_PILOT_PROTOCOL.md`
- decoding seed：17；schedule/evidence-order seeds：17、29、47
- 模型运行候选：本地 Ollama `qwen3:8b`，必须按 digest 固定；尚未运行本 benchmark

## 阅读顺序

1. [DIRECTION_CHARTER.md](DIRECTION_CHARTER.md)：用户锁定的研究核心与禁区。
2. [PROJECT_EVIDENCE_MAP.md](PROJECT_EVIDENCE_MAP.md)：每条主张对应的代码、测试、工件和缺失证据。
3. [CURRENT_RESULTS.md](CURRENT_RESULTS.md)：已验证结果、失败与明确未建立的结论。
4. [NOVELTY_AUDIT.md](NOVELTY_AUDIT.md) 与 [LITERATURE_LANDSCAPE.md](LITERATURE_LANDSCAPE.md)：closest/concurrent work 与窄 delta。
5. [HYPOTHESES_AND_METHOD.md](HYPOTHESES_AND_METHOD.md)：可证伪假设、竞争解释与 provisional 方法。
6. [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md)、[BENCHMARK_CASE_CATALOG.md](BENCHMARK_CASE_CATALOG.md)、[annotation-schema.json](annotation-schema.json)：标注与 frozen fixture。
7. [SEMANTIC_PILOT_PROTOCOL.md](SEMANTIC_PILOT_PROTOCOL.md)：模型调用前锁定的 oracle 隔离、状态机、计算和结论规则。
8. [USER_DECISIONS_REQUIRED.md](USER_DECISIONS_REQUIRED.md)：仍由用户保留的正式架构与研究决策。
9. [research-state.yaml](research-state.yaml)、[research-log.md](research-log.md)、[findings.md](findings.md)、[EXPERIMENT_LOG.jsonl](EXPERIMENT_LOG.jsonl)：机器可读状态与持续日志。
10. [REPRODUCE.md](REPRODUCE.md)：复现命令与“尚不可运行”的诚实边界。

## 当前代码链路

```text
frozen benchmark
  -> strict loader + conditional relation certificates
  -> oracle-free HMAC inference manifest
  -> deterministic schedule (17/29/47; decoding seed fixed 17)
  -> exact claim-form / atomic / holistic requests
  -> immutable PREPARED
  -> local Ollama transport
  -> immutable RETURNED or TRANSPORT_FAILED before parsing
  -> sealed outer ID join
  -> Method A atomic / Method B holistic / Method C joint predictions
  -> oracle join only for native three-way risk/coverage and diagnostics
```

截至本文件生成时，链路已实现到不可覆盖 attempt store；inference runner、outer evaluator 和真实模型 preflight 正在 TDD，尚未形成结果工件。

## 不得误读的术语

- `programmatic_oracle` 只表示注册变换相对冻结 provisional base 的条件机械证书，不表示自然语言事实是人类金标准。
- `SCHEMA_VALID` 只表示 envelope/schema/contract 有效，不表示模型判断在语义上正确。
- `DEBUGGING` 结果可以反驳工程预期或暴露失败，不可称 confirmatory evidence。
- `REVIEW` 必须与 `REJECT` 分开报告；不能用更低 coverage 假装更安全。
- fixed-count matched admission 是描述性敏感性分析，不是校准曲线、公平性证明或 success/kill 依据。

## 最小本地验证

```powershell
$py = Resolve-Path 'venv/research/Scripts/python.exe'
& $py -B -m pytest -q -p no:cacheprovider
& $py -B -m compileall -q memoryrush scripts tests
git diff --check
```

当前已推送检查点的全套结果是 `339 passed`。这只证明工程回归，不证明研究假设。
