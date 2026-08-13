# Local Semantic Pilot Protocol v0.1

Protocol status: `DRAFT_PRE_RUN_GATE`; **model execution is not authorized by this draft**.
Decision status: `PROVISIONAL_AGENT_DESIGN`; this document does not settle any user-reserved schema, verifier, solver, REVIEW-policy, benchmark, metric, model-family, or architecture decision.
Model family under test: local Ollama `qwen3:8b`.
Frozen decoding seed: `17`. Primary schedule/evidence-order seed: `17`; schedule sensitivity seeds: `29`, `47`.

## 1. Purpose and epistemic boundary

This pilot asks whether a bounded local semantic verifier can recover source-support distinctions needed by Direction 1, and whether atomic joint evidence auditing adds anything over a detail-matched holistic judge. It tests only support relative to the frozen source snapshot and supplied evidence pool. It does not test real-world truth, salience, usefulness, retrieval quality, human agreement, natural-distribution performance, publication novelty, or permanent MemoryRush integration.

The run is a small, synthetic, falsification-oriented **oracle-informed annotated-representation development probe**. The atomic decomposition, qualifier slots, benchmark annotations, and prompts were designed in the same repository after the authors had inspected the complete 36-case benchmark. Runtime key hiding prevents direct prediction leakage, but it cannot remove this design-time target encoding. All model judgments are provisional model outputs. No result from this protocol may be described as statistically significant, generalizable, human-gold, confirmatory, or positive evidence that the annotated atomic method outperforms a holistic method. A positive method claim requires a fresh source-blocked holdout whose decomposition and prompts were frozen under label-blind conditions or supplied by an independent annotator.

The deterministic `static_oracle_upper_bound` remains a plumbing check only. It is not a semantic baseline, deployable method, or evidence for the proposed mechanism.

## 2. Benchmark lock and relationship gate

Candidate input path:

```text
data/benchmarks/direction1_synthetic_v0_1.jsonl
```

Frozen schema and size after the relationship-integrity correction:

- schema: `direction1.synthetic_oracle.v0.1`;
- 36 unique cases;
- byte size: `82639`;
- 9 `programmatic_oracle/synthetic_oracle/programmatic` cases;
- 27 `llm_generated/provisional/llm_or_agent` cases;
- exactly the nine registered mechanical relationships in Section 4.

The prior deterministic-run digest, `013c7fd918599ad5d37e7dcaacd35f09f1c5549186f474195a2957f69b533371`, identifies the pre-correction file and **does not authorize this model pilot**. The model-pilot input is frozen as:

```text
MODEL_PILOT_FROZEN_SHA256 = 36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321
MODEL_PILOT_FROZEN_BYTES  = 82639
```

No model run is valid until all of these gates pass from a clean Git commit:

1. the exact benchmark byte hash is written above and matches the loaded bytes;
2. the strict loader, source hashes, offsets, total support matrices, minimal-set certificates, base graph, and duplicate-set checks pass;
3. a relationship validator independently checks the conditional relation certificate for each registered base/transformation pair against a frozen registry of canonical base and source digests; it must reject a self-consistent forged label/certificate, a derived-only or coordinated base-plus-derived source mutation, an unregistered edit, a missing relation, and a duplicate relation;
4. `MSG-C014` and `MSG-C034` are not counted as mechanical oracles; both are `llm_generated/provisional/llm_or_agent` and are scored only in exploratory strata;
5. all prompts, response schemas, inference manifests, runner code, tests, and this protocol are committed before the first result artifact;
6. a separate inference manifest contains only model-visible candidate/evidence fields and opaque run-local IDs. It contains no oracle decision, support cells, claim-form annotation, minimal evidence set, reason code, label source, adjudication status, provenance, case family, base ID, or perturbation operator;
7. the inference-manifest hash and a separately held oracle-mapping hash are both recorded. The inference process cannot import or access the oracle mapping.

Failure of any gate produces `INVALID_RUN`; it cannot be repaired by excluding cases after seeing predictions.

## 3. Run classes

- `DEBUGGING`: fake-transport, serialization, prompt-injection, truncation, failure-retention, and static-oracle plumbing checks. A local-model interface canary may be run only after the hash/prompt gates pass, and is never scored.
- `EXPLORATORY`: every `qwen3:8b` benchmark run under this protocol, including the mechanical-relation slice. This is the highest permitted class in v0.1.
- `CONFIRMATORY`: forbidden in v0.1. Passing the relationship validator does not upgrade an existing run. A later protocol version must explicitly authorize a frozen hash, inference manifest, hypotheses, analysis, and run IDs before any confirmatory request.
- `INVALID_RUN`: hash/digest drift, oracle leakage, context-risk, a missing required attempt record or lost returned raw output, invalid case universe, unapproved retry, or another integrity failure that prevents the declared run from being interpreted. An isolated, durably recorded transport/schema failure follows the REVIEW and stopping rules below.

The 9 mechanical transformations are conditional synthetic-oracle relation checks, but their seven unique positive bases have agent-provisional semantic labels. The registry certifies the expected consequence **conditional on accepting the base interpretation**; it does not independently prove that base interpretation. Consequently, even a perfect relationship table is not confirmatory evidence about natural language support.

## 4. Frozen relationship slice

There are nine registered conditions but only sixteen unique cases. `MSG-C007` and `MSG-C012` are each reused by two relations; repeated use is not an independent replicate.

| relation | transformed case | base control | operator | registered transformed decision |
|---|---|---|---|---|
| entity substitution | `MSG-C006` | `MSG-C005` | `replace_entity` | `REJECT` |
| quantity substitution | `MSG-C008` | `MSG-C007` | `replace_quantifier` | `REJECT` |
| date substitution | `MSG-C009` | `MSG-C007` | `replace_time` | `REJECT` |
| negation flip | `MSG-C011` | `MSG-C010` | `flip_negation` | `REJECT` |
| epistemic modality strengthening | `MSG-C013` | `MSG-C012` | `replace_modality` | `REJECT` |
| condition deletion | `MSG-C016` | `MSG-C012` | `delete_condition` | `REJECT` |
| scope expansion | `MSG-C018` | `MSG-C017` | `delete_scope` | `REJECT` |
| attribution transfer | `MSG-C020` | `MSG-C019` | `replace_attribution` | `REJECT` |
| duplicate-evidence invariance | `MSG-C022` | `MSG-C001` | `duplicate_evidence` | `ADMIT` |

The seven unique positive controls are `MSG-C001`, `MSG-C005`, `MSG-C007`, `MSG-C010`, `MSG-C012`, `MSG-C017`, and `MSG-C019`. Their `ADMIT` labels remain agent-provisional. The model receives neither the table nor any relation metadata.

For the support-cell interpretation, `MSG-C006` and `MSG-C020` have expected label `insufficient`, not `contradicts`: their source passages name North Workshop and Mira Sol but do not explicitly exclude every alternative entity or author. Their relation-level transformed admission decision remains `REJECT` because the substituted entity/attribution is unsupported under the conditional base relation. The other registered negatives may expose direct contradiction or missing qualifier support according to their frozen certificates; aggregate reporting must not collapse `insufficient` into `contradicts`.

`MSG-C014` (deontic `must`/`may`) and `MSG-C034` (cross-span unsupported mechanism atom) are explicitly high-risk exploratory items, together with their controls `MSG-C015` and `MSG-C035`. Their outcomes are printed case-by-case, never folded into the mechanical-oracle count. Every other `llm_generated/provisional` label is likewise reported only in an exploratory stratum.

## 5. Experimental unit, order, and seeds

The prediction unit is one unique `(case, method, schedule_seed)` attempt. The relation table is a paired diagnostic over predictions, not a new collection of independent cases. Schedule seeds `29` and `47` are repeated measurements of the same 36 cases, not extra sample size.

For each schedule seed, source blocks are deterministically permuted by `SHA256(schedule_seed | block_id)`, then cases inside each block by `SHA256(schedule_seed | block_id | opaque_case_id)`. The exact schedule is persisted before inference. Atomic and holistic call order is balanced by a precomputed hash rule so neither method is always the cold-start call. Evidence order uses the same schedule-seed-derived permutation for both methods while retaining an outer map to original span IDs.

No prompt, threshold, failure policy, relationship, case text, or model decoding option may change between schedules. The Ollama decoding seed remains exactly `17` in every request; only the precomputed source-block, case, role, and evidence order changes with schedule seeds `17`, `29`, and `47`. Schedule `17` is collected and sealed first. Schedules `29` and `47` run only if schedule 17 is structurally valid; continuation is based on integrity checks, never on whether results look favorable. Sensitivity schedules cannot fill in, replace, or average away a failed primary attempt. This separation makes observed changes an order/backend-repeatability diagnostic rather than a confounded decoding-seed-plus-order effect.

## 6. Frozen local inference envelope

Every real request uses the same local model tag and immutable content digest:

```text
model             = qwen3:8b
endpoint          = http://localhost:11434/api/generate
stream            = false
think             = false
temperature       = 0.0
seed              = 17
num_ctx           = 8192
num_predict       = 2048
timeout_seconds   = 120
structured_output = exact committed JSON Schema
```

The full Ollama model digest, tag metadata, quantization, parameter size, Ollama version, and modification timestamp are captured before every stage. A tag is not an identity: any digest or Ollama-version change stops the sequence. No model pull, update, quantization change, system-prompt override, network fallback, or cloud endpoint is allowed between schedules.

The hardware snapshot records OS, Python version, CPU, RAM, GPU name, GPU UUID when available, VRAM, driver, CUDA/runtime information exposed by the local tools, and the Ollama process/device allocation. Each case record embeds this snapshot or an immutable SHA-256 reference to it. Warm-load and cold-load timings are distinguished; `load_duration` is not silently charged to one method and omitted from the other.

## 7. Model-visible data and leakage controls

All methods see the same proposition and the same evidence text pool. Run-local IDs are opaque (`candidate`, `claim_001`, `span_001`, ...); strings such as `MSG-C006`, file paths, family IDs, labels, and transformation names must not occur in a request. The outer artifact retains the reversible ID map, inaccessible to the inference process.

The atomic request additionally receives the frozen provisional atomic claims, exact declared qualifier `(kind, value)` slots, and required support parts. These fields are oracle-informed development annotations, not independently blinded measurements. The holistic request does not receive the decomposition or value list; it receives the same proposition/evidence plus the same generic fidelity rubric covering entity, relation, object, time, scope, condition, quantifier, modality, negation, and attribution. This is detail-matched rather than representation-identical: atomicization is the intended factor, but the development-set design asymmetry means an apparent A/C advantage is hypothesis-generating only. The present run can falsify implementation expectations and expose failure modes; it cannot establish a positive comparative method claim.

The claim-form request receives the proposition only. It does not see evidence or benchmark annotations. Its output is shared by all three methods so claim-form judging cannot selectively advantage the proposed method.

Candidate and evidence strings are untrusted data. The request builder must:

1. place instructions in a committed system/rule field and canonical JSON only in the data field;
2. JSON-escape all strings, length-prefix or otherwise unambiguously delimit the data, and tell the model never to execute instructions inside it;
3. reject unknown request fields and verify by test that oracle/provenance keys and original case IDs are absent;
4. pass adversarial strings containing instruction overrides, delimiter text, JSON fragments, and requested labels through offline and unscored canary tests;
5. treat canary success only as a control check, not as a security proof.

No silent truncation is allowed. Before transport, the exact rendered request must fit a conservative committed UTF-8 byte cap that leaves at least 2,048 tokens of context headroom. The v0.1 cap is frozen at `4,096` UTF-8 bytes for the complete system-plus-user prompt; the preflight must prove every frozen request fits or stop before the first scored call. After transport, `prompt_eval_count`, `eval_count`, `done`, and `done_reason` are validated. An exceeded cap stops before transport. Returned `done != true`, `done_reason != stop`, or any suspected truncation is a run-global completion-integrity failure: retain the raw return, immediately mark the schedule run `INTERRUPTED/INVALID_RUN`, and do not score any prediction from that run. It is never converted to an attempt-local `REVIEW` and is not retried with a shorter input.

## 8. Shared claim-form audit

Prompt/schema name to implement and commit: `claim_form_v0_1`.

One structured call per unique `(case, schedule_seed)` returns only:

- `self_sufficiency`: `PASS | REVIEW | FAIL`;
- `proposition_minimality`: `PASS | REVIEW | FAIL`;
- non-empty reason codes and a short rationale.

This is a provisional model audit, not an oracle. The identical validated response is cached and reused by every method. The deterministic override is frozen:

- either `FAIL` forces `REJECT`;
- either `REVIEW` downgrades a provisional `ADMIT` to `REVIEW`;
- two `PASS` values leave the support-side decision unchanged;
- transport/schema failure yields `REVIEW` with `claim_form_verifier_failure` and is counted as a failure.

## 9. Method A - atomic semantic support baseline

Frozen name: `atomic_semantic_support_v0`.
Support prompt: existing `semantic_support_v0_1`, with its committed template SHA-256 recorded.
Calls per unique case/schedule: one claim-form call shared across methods plus one atomic support call shared with Method C.

The support call returns exactly one cell for every declared atomic-claim x evidence-span pair. Core label and qualifier coverage remain orthogonal. The response must be total, typed, free of unknown fields, and reference only supplied opaque IDs and exact declared qualifier values/support parts.

Method A deliberately has no evidence-set search, deletion qualification, or cross-case perturbation qualification. It evaluates the full evidence pool:

1. any material contradiction -> provisional `REJECT`;
2. otherwise any material ambiguity -> provisional `REVIEW`;
3. otherwise any missing atomic core, required support part, or qualifier slot -> provisional `REJECT`;
4. otherwise -> provisional `ADMIT`;
5. apply the shared claim-form override from Section 8.

Its score is the fixed decision rank `ADMIT=1.0`, `REVIEW=0.5`, `REJECT=0.0`. It is not confidence or a probability and must never be calibrated or threshold-tuned on this benchmark.

## 10. Method B - detail-matched holistic audit baseline

Frozen name: `holistic_detail_matched_v0`.
Prompt/schema name to implement and commit: `holistic_support_v0_1`.
Calls per unique case/schedule: one shared claim-form call plus one holistic support call.

The holistic call judges the whole proposition without receiving atomic claims. Its strict response contains:

- overall relation: `fully_supported | contradicted | ambiguous | insufficient`;
- one status for every generic fidelity dimension: `supported | contradicted | missing | ambiguous | not_applicable`;
- a non-empty selected evidence-ID subset when claiming full support;
- an explicit pool-conflict and pool-ambiguity status;
- reason codes and a short rationale.

The call therefore has the same semantic checklist, candidate/evidence pool, maximum context/output budget, claim-form audit, and conservative pool-conflict policy as Method C, while withholding the atomic decomposition. Prompt and output token counts need not be identical and are reported rather than assumed equal. Evidence-set deletion is intentionally absent: Method B is the strongest one-call whole-proposition support alternative, while Method C's solver/deletion mechanism is the tested increment. A later mechanism-isolating ablation can add physical removed-evidence calls to both representations; this micro-pilot cannot claim to isolate decomposition from deletion.

The deterministic mapping is:

1. `contradicted` or `insufficient` -> provisional `REJECT`;
2. `ambiguous` -> provisional `REVIEW`;
3. `fully_supported` with a pool contradiction/ambiguity or missing selection -> provisional `REVIEW`;
4. otherwise -> provisional `ADMIT`;
5. apply the shared claim-form override.

The score is the same non-probabilistic fixed decision rank used by Method A.

## 11. Method C - joint atomic/evidence audit prototype

Frozen name: `joint_audit_prototype_v0`.
Calls per unique case/schedule: one shared claim-form call plus the **same cached atomic support response** used by Method A. Method C must not re-query the model for a more favorable matrix.

Method C applies the provisional, exhaustive inclusion-minimal solver to that matrix, then the conservative three-way policy:

1. no jointly sufficient set plus contradiction -> provisional `REJECT`;
2. no jointly sufficient set plus ambiguity -> provisional `REVIEW`;
3. no jointly sufficient set because of missing core/part/qualifier -> provisional `REJECT`;
4. a sufficient set plus contradiction or ambiguity elsewhere in the candidate evidence pool -> provisional `REVIEW`;
5. otherwise select the deterministically first inclusion-minimal set and provisionally `ADMIT`;
6. delete every selected span and recompute sufficiency. Any deletion that remains sufficient is a solver/audit disagreement and downgrades to `REVIEW`;
7. apply the shared claim-form override.

All known inclusion-minimal solutions are retained. A different valid choice among the frozen alternatives for C022/C023/C036 is not an error. This protocol does not choose inclusion-minimality as the permanent policy; minimum-cardinality remains a user-reserved comparison.

The score is again `1.0/0.5/0.0` by final decision only, never a probability.

For any support request, an isolated transport/HTTP failure, response-body JSON decode failure, response-schema failure, or incomplete matrix/audit output yields attempt-local `REVIEW` with a method-specific verifier-failure reason. It cannot reuse a previous successful response. A stale-cache mismatch, returned model-identity mismatch, incomplete-completion signal, forbidden field, or artifact-integrity failure is instead run-global `INVALID_RUN` under the state table in Section 13. Subject to the systemic stopping rules, the remaining pre-scheduled support roles are still attempted after an attempt-local failure so a claim-form failure or one method failure cannot selectively suppress its comparator.

## 12. Relationship evaluation without oracle prediction leakage

The table in Section 4 is held-out evaluation metadata. It is equivalent to asking whether independently generated case predictions recover the pre-registered base/transformation relation. It is never imported by a method, prompt, cache key, threshold, or three-way decision function.

After every independent case prediction is sealed, the evaluator computes:

- for each of the eight negative transformations, whether the base is `ADMIT` and the transformed case is `REJECT`; transformed `REVIEW` is an abstention and not a success;
- for duplicate invariance, whether C001 and C022 are both `ADMIT`, and whether Method C selected one legal singleton for C022 rather than the redundant pair;
- base preservation, transformed-case detection, paired success, and REVIEW outcomes separately.

No relationship outcome changes either member's prediction. This prevents the registered synthetic answer from generating the answer being scored. Consequently, v0.1 evaluates semantic-perturbation sensitivity but does not yet integrate it as a production admission-time gate. A future production-like perturbation generator must operate without benchmark relation metadata and be evaluated on a fresh source-blocked split.

## 13. Raw artifact and failure retention

Every request uses two-phase append-only persistence. Before transport, an immutable `PREPARED` record containing the canonical request, hashes, schedule position, and start time is written via temporary file, flush/fsync, atomic rename, and byte-hash verification. Immediately after return or exception, and **before** response parsing, scoring, or the next call, a separate immutable `RETURNED` or `TRANSPORT_FAILED` record is durably written and linked to `PREPARED`. A process crash can therefore leave a visible incomplete attempt rather than erase it. Absence of an Ollama envelope is explicit rather than fabricated.

Each case artifact records at least:

- experiment/run/attempt ID, run class, method/prompt role, fixed decoding seed, schedule seed, opaque and outer case IDs;
- timezone-aware start/end timestamps and monotonic wall duration;
- clean Git HEAD/dirty flag;
- benchmark, inference-manifest, schedule, prompt-template, full rendered prompt, response-schema, canonical request, and, when present, raw-envelope and raw-response SHA-256 values;
- exact canonical request bytes and nullable raw Ollama envelope bytes/text;
- requested model tag, returned model tag, immutable model digest, Ollama version, decoding/options, endpoint, HTTP status;
- hardware snapshot or its immutable digest/reference;
- `total_duration`, `load_duration`, `prompt_eval_count`, `prompt_eval_duration`, `eval_count`, and `eval_duration` exactly as returned;
- transport, envelope, JSON-schema, total-matrix, semantic-contract, and final validation status;
- exit code, exception type/message, and failure reason without discarding partial output.

No automatic retry is allowed in the primary artifact. A retry is a new attempt/run ID and cannot replace the failure. Parsed predictions and evaluation summaries are derived only after the raw manifest proves that every attempted request has a retained artifact.

The attempt-to-run state machine is frozen as follows; the first matching row controls, so an event cannot be both scored as `REVIEW` and invalidate the run:

| observed event | attempt state | prediction contribution | failure-threshold accounting | schedule-run state / next action |
|---|---|---|---|---|
| valid envelope and valid role schema | `SCHEMA_VALID` | derive the frozen three-way prediction | none | remain `RUNNING`; continue |
| transport exception, timeout before any valid HTTP response, non-2xx HTTP status, raw body that is not a JSON envelope, role-output JSON/schema failure, or incomplete role matrix | `LOCAL_FAILURE` | `REVIEW` with role-specific verifier-failure code | counts toward consecutive and per-role local-failure thresholds | continue unless threshold is reached |
| second consecutive local failure, or fourth local failure among the 36 attempts of one role | `LOCAL_FAILURE_THRESHOLD_REACHED` | no schedule-run result is scored | threshold trigger | durably mark `INTERRUPTED/INVALID_RUN`; stop before next request |
| `done != true`, `done_reason != stop`, suspected truncation, returned model mismatch, sealed digest/version/config drift, stale-cache mismatch, opaque-manifest leakage, forbidden original ID/key, request/schedule drift, or raw-artifact/hash loss | `GLOBAL_INTEGRITY_FAILURE` | none; even earlier provisional predictions from this schedule are non-results | never counted as a local failure | durably mark `INTERRUPTED/INVALID_RUN`; stop immediately |
| process crash or operator stop after `PREPARED` without a terminal attempt record | `INCOMPLETE_ATTEMPT` on recovery | none | never imputed as REVIEW | schedule remains `INTERRUPTED/INVALID_RUN`; preserve record and do not resume under the same run ID |

Only `LOCAL_FAILURE` enters the all-case denominator as `REVIEW`. Consecutive means adjacent scheduled attempts regardless of role; the per-role threshold is evaluated separately for `claim_form`, `atomic_support`, and `holistic_support`. A valid attempt resets the consecutive-local-failure counter. Global integrity failures and incomplete attempts bypass these counters and invalidate the schedule immediately. No both-success subset can rehabilitate an invalid schedule.

## 14. Compute accounting

For 36 unique cases under one schedule seed, the planned physical model work is:

| request role | unique calls | reused by |
|---|---:|---|
| shared claim-form audit | 36 | A, B, C |
| atomic support matrix | 36 | A, C |
| holistic support audit | 36 | B |
| total | 108 | n/a |

The relation audit adds no new physical benchmark call because its nine transformed inputs are already in the 36-case universe. Nevertheless, report both physical calls and logical per-base audit dependencies so cache reuse is not presented as free production compute.

For every method/schedule and pairwise comparison report:

- attempted, successful, schema-valid, failed, cached, and logically attributed calls;
- prompt, evaluation, and total tokens: exact sum, median, minimum, maximum, and per-case values;
- wall, total, load, prompt-evaluation, and generation duration with the same summaries;
- deterministic CPU time for solver/deletion work;
- peak observed VRAM when available;
- failure and abstention counts.

`budget_matched=true` requires the same model digest, fixed decoding seed, schedule seed, decoding options, context/output caps, case universe, and support-call count. `observed_compute_matched=true` additionally requires equal successful-call counts and a maximum/minimum ratio no greater than `1.10` for total evaluated tokens. If either flag is false, results are reported as unmatched; latency or cache savings cannot be used to claim method superiority.

## 15. Coverage, risk, and exact reporting

For each method, schedule seed, full 36-case universe, 16-unique-case relationship slice, provenance stratum, and family, report exact:

- `ADMIT / REVIEW / REJECT` counts;
- coverage = `ADMIT / all unique cases`;
- false admissions = admitted cases whose held-out oracle decision is not `ADMIT`;
- admission risk = `false admissions / ADMIT`, undefined when `ADMIT=0`;
- missed oracle admissions split into `REVIEW` and `REJECT`;
- the full three-way confusion matrix;
- model failures separately, even though the frozen operational mapping is `REVIEW`.

The evaluator joins held-out oracle decisions only after predictions and request hashes are sealed. It never changes a prediction. REVIEW is neither a correct rejection nor an admission.

Because all methods expose only a three-level decision rank, no smooth risk-coverage curve or calibrated confidence claim is allowed. Native coverage is primary. The only pre-registered descriptive matched-admission points are:

- full suite: `k = 9` and `k = 18` admitted cases;
- 16-case relationship slice: `k = 4` and `k = 8` admitted cases.

A point is unavailable if any compared method has fewer than `k` native ADMITs. Within an ADMIT tie, select by ascending `SHA256(schedule_seed | opaque_case_id)` with no method name in the hash; persist selected IDs and intersections. This deterministic subsampling is an artificial tie policy whose result can change with schedule seed or opaque-ID assignment despite unchanged method decisions. It is therefore reported only as descriptive sensitivity, never as positive evidence, superiority, a success criterion, a downgrade trigger, or a kill criterion. No quantifier over "available points" is evaluated when the available-point set is empty.

For the nine relationships, print one row per relation and exact aggregate counts:

- negative detection: transformed case is `REJECT`;
- paired success: provisional base is `ADMIT` and transformed case is `REJECT`;
- duplicate invariance: C001 and C022 are both `ADMIT`;
- C022 evidence-set validity: one of the two legal singleton sets is selected and the redundant pair is not selected.

C007 and C012 reuse is disclosed beside every aggregate. No p-value, confidence interval, bootstrap, or effective sample-size inflation is permitted.

## 16. Frozen falsifiable expectations

These are pre-run expectations, not results:

1. **Value-fidelity expectation:** Method C rejects all eight registered negative transformations while preserving the seven provisional positive bases. Any exception falsifies perfect recovery on the corresponding controlled axis.
2. **Duplicate expectation:** Method C admits both C001 and C022 and selects exactly one legal singleton for C022. Failure falsifies the current redundancy/minimality behavior on its cleanest control.
3. **Development-comparison expectation:** on the native, un-subsampled three-way policies, print whether Method C has a relationship success that Method B lacks, every reverse difference, native admission risk/coverage, and compute. Because the decomposition and prompts are oracle-informed on this development set, even the favorable pattern is only a hypothesis-generating observation; an unfavorable pattern falsifies the corresponding repository-authored expectation. Descriptive matched-count sensitivity cannot satisfy or rescue this expectation.
4. **Atomic-ablation expectation:** relative to Method A, Method C produces a valid inclusion-minimal/deletion certificate for C022 and at least one multi-span case without worsening the final relationship count. If final three-way decisions are unchanged, this supports only certificate plumbing, not a decision-quality gain from the solver/deletion layer.
5. **Order expectation:** with decoding seed fixed at `17`, the 16 unique relationship-slice decisions are invariant across schedule seeds `17/29/47` at temperature zero. Any change is reported as backend/order sensitivity, not independent supporting evidence.

Perfect performance would still show only that one local model and fixed prompts recover repository-authored synthetic distinctions.

## 17. Downgrade and kill rules

Downgrade any positive result to a narrower diagnostic observation when:

- the gain exists only on the nine registered transformations or disappears on agent-provisional cases;
- native coverage, successful-call count, token use, or failure abstention is unmatched;
- the conclusion changes across schedule seeds;
- positive bases are rejected/reviewed, especially C007/C012 reused controls;
- improvement comes only from cross-case audit downgrades rather than better source-support discrimination;
- holistic prompt/schema validation is weaker, less detailed, or given less compute;
- C014/C034 or another agent label is used as if mechanically or human validated.

This development probe cannot establish the current incremental method claim, so its native-policy comparisons are used only for falsification. The tested implementation expectation is killed when a valid detail-matched Method B weakly dominates Method C on the complete native-policy case universe: no higher native admission risk, no lower native coverage, no worse relationship count, and no greater observed compute. It is also killed if Method C fails the duplicate control or repeatedly admits registered corruptions. Descriptive matched-count points never trigger or prevent a kill, and an empty comparison set has no logical consequence. A kill result triggers negative-result analysis inside locked Direction 1; it does not authorize a pivot to a different research question. Any future positive comparative claim requires the fresh label-blind source-blocked holdout described in Section 1.

A failed prediction caused by an invalid runner, leaked oracle, changed model, or lost artifact kills the run, not the scientific direction. Repairs require a new committed protocol/code version and a new run ID; old failures remain visible.

## 18. Sequence and stopping conditions

Execution order is fixed:

1. finish and pass the relationship validator; verify the corrected C014/C034 provenance and the locked benchmark SHA/byte size in this document;
2. implement versioned claim-form and holistic prompts/adapters, opaque inference manifests, immediate raw persistence, and exact artifact validation using TDD only;
3. run the static oracle as a separate offline plumbing check; it must reproduce 36/36 declared decisions, but its output is not included as a semantic-method result;
4. run fake-transport and adversarial prompt/context/failure-retention DEBUGGING tests;
5. record a clean environment snapshot, model digest, schedule, and free-disk check; seal all hashes;
6. optionally execute one fixed, unscored, non-benchmark local canary for endpoint/schema integrity; do not tune prompts from it;
7. execute and immediately persist schedule-seed-17 requests with decoding seed fixed at 17; scoring remains unavailable to the inference process;
8. validate and seal the complete schedule-seed-17 raw manifest, then evaluate once;
9. if and only if integrity, not performance, permits continuation, repeat with schedule seeds 29 and 47 while keeping decoding seed fixed at 17;
10. publish exact tables, raw paths/hashes, failures, and limitations before any prompt revision.

Stop immediately and mark the affected run `INTERRUPTED/INVALID_RUN` when any of the following occurs:

- benchmark, prompt, schema, inference-manifest, schedule, model, Ollama, Git, or hardware identity differs from the sealed record;
- a request contains an original case ID or forbidden oracle/provenance field;
- preflight byte/context headroom fails or Ollama reports non-`stop` completion;
- a raw artifact cannot be durably written and hash-verified before the next call;
- the static oracle does not reproduce all 36 decisions;
- the relation registry/count or C014/C034 provenance gate fails;
- the canonical Section 13 state machine reaches `LOCAL_FAILURE_THRESHOLD_REACHED`: two consecutive `LOCAL_FAILURE` events of any listed local-failure kind, or the fourth `LOCAL_FAILURE` among the 36 attempts for one request role;
- disk space falls below the pre-recorded safe reserve;
- an operator manually edits, retries, skips, or reorders a scored request outside the frozen schedule.

Isolated failures below the systemic-stop threshold remain in the all-case denominator and map to REVIEW as specified. A both-success subset may be shown only as secondary diagnosis, never substituted for the primary all-case report.

## 19. Current capability check

As of drafting, the repository has an offline-tested `OllamaSemanticVerifier` for one `semantic_support_v0_1` structured atomic-matrix request. It records prompt/request hashes, raw response/envelope, Ollama usage fields, and rejects model mismatch, incomplete completion, malformed/partial matrices, invented slots, oversized serialized input, and several type errors. The existing prompt explicitly treats claim/evidence text as untrusted data.

This is **not yet sufficient to run this protocol**:

- the newly locked benchmark hash and byte size still require a clean preflight recomputation immediately before the first model call;
- the relationship gate must pass its complete adversarial test suite on the exact frozen bytes;
- claim-form and holistic prompts/adapters do not yet exist;
- no semantic experiment runner yet guarantees opaque inference-only input, balanced schedule, immediate per-case failure persistence, or the artifact fields above;
- the existing character cap is not by itself the full conservative rendered-prompt/context proof required here;
- model digest, Ollama version, hardware snapshot, `num_predict`, and per-attempt durable failure records are not all enforced by the current adapter.

Accordingly, this file is a design artifact only. It contains no model result and cannot be cited as evidence that any method works.
