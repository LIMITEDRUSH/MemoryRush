# Deterministic Baseline Run Protocol v0.1

Protocol status: `LOCKED_BEFORE_RESULTS`  
Decision status: `PROVISIONAL_AGENT_DESIGN`  
Frozen input commit: `e450662`  
Frozen benchmark: `data/benchmarks/direction1_synthetic_v0_1.jsonl`  
Frozen benchmark SHA-256: `013c7fd918599ad5d37e7dcaacd35f09f1c5549186f474195a2957f69b533371`

## 1. Purpose and Run Classes

The first deterministic run is `DEBUGGING`, not a method-effect experiment. It checks end-to-end loading, oracle isolation, typed predictions, three-way metrics, artifact provenance and expected structural-baseline failure modes over all 36 frozen cases.

A narrow `CONFIRMATORY` descriptive slice may report exact outcomes only for mechanically labelled programmatic transformations whose interpretation does not depend on human semantic equivalence. The following ten cases are frozen for that slice:

`MSG-C006`, `MSG-C008`, `MSG-C009`, `MSG-C011`, `MSG-C013`, `MSG-C016`, `MSG-C018`, `MSG-C020`, `MSG-C022`, `MSG-C034`.

`MSG-C014` remains programmatically transformed but is excluded from the confirmatory slice because whether deontic `must` supports or conflicts with `may` is an unresolved protocol choice. It is reported separately as `EXPLORATORY_HIGH_RISK`. C023 and C026 are also high-risk agent-authored cases. All 25 agent/LLM-authored labels remain provisional and cannot be called human gold or confirmatory natural-distribution evidence.

No statistical significance, generalization, human agreement or proposed-method superiority claim is permitted from this microbenchmark.

## 2. Frozen Methods

All methods receive the same candidate and evidence spans in the same case universe.

1. `id_only_support_proxy_v0`: structural false-positive proxy. It admits every loader-valid CandidateClaim case with score `1.0`. It isolates the support blind spot but is not a case-by-case replay of the full production `ArticleMemoryOutput` validator, which also applies unrelated shape, non-empty, ID and CoreIdea-quote checks.
2. `exact_copy_v0`: deterministic Unicode-casefold/whitespace-normalized literal atomic-claim containment. It uses the provisional inclusion-minimal solver and conservative three-way policy. Its fixed claim-form audit is explicitly named `baseline_assumes_candidate_form`; it is not oracle-derived.
3. `static_oracle_upper_bound_v0`: uses the frozen support cells and claim-form annotation. It must exactly reproduce every oracle decision or the run is invalid. It is a plumbing upper bound, not deployable and not evidence for the proposed method.

The first run does not include a strong semantic verifier, atomic-vs-holistic ablation, MEG-style baseline or proposed joint method. Therefore it cannot test H1. Those require a later committed protocol and raw model artifacts.

## 3. Oracle Isolation

- Baseline prediction records contain no oracle label.
- Oracle decisions are joined from the frozen benchmark only inside evaluation.
- ID-only and exact-copy code must not read oracle support cells, claim-form audits, decisions or reason codes.
- The artifact records the benchmark hash and a separately derived oracle-mapping hash.
- Static oracle access is isolated by method name and treated only as a sanity check.
- Any case-universe mismatch, duplicate prediction, unknown case, malformed enum, non-finite score or benchmark-hash mismatch invalidates the run.

## 4. Measurements

For each method, report exact counts only:

- ADMIT / REVIEW / REJECT;
- native admission coverage;
- false admissions among ADMIT decisions;
- native admission risk (`false admissions / admissions`, undefined when no admissions);
- missed admissions split into REVIEW abstention and REJECT;
- exact three-way decision accuracy;
- family and provenance strata.

`admission_score` is a method-supplied deterministic ranking field, not a probability or calibrated confidence.

## 5. Matched Admission

The initial native run does not silently choose a matched target. A matched run requires an explicit positive target committed or recorded before its matched artifact is produced. Selection is score descending with SHA-256(`seed|case_id`) tie-breaking over each method's ADMIT pool. All methods must have the identical case universe and use the common frozen oracle mapping.

Equal admitted count does not prove equal compute, calibration, difficulty or fairness. If the feasible common target is too small to be scientifically meaningful, matched results are reported as unavailable rather than presented as a win.

## 6. Seeds and Ordering

Primary deterministic seed: `17`; order-sensitivity checks: `29`, `47`. These methods should be invariant except for documented tie selection. Any decision change across seeds is a bug or hidden-state finding, not an independent replicate.

## 7. Artifact Requirements

Each artifact must record:

- run ID and class;
- timezone-aware start/end timestamps;
- Git HEAD and dirty status supplied by the orchestrating command;
- Python/platform information;
- benchmark path, schema, byte size, SHA-256 and case/provenance counts;
- method names/versions, prediction reason codes and non-probabilistic ranking scores;
- separate oracle mapping hash;
- summaries and optional explicit matched result;
- failures and validation status;
- canonical UTF-8/LF JSON with no NaN or Infinity.

Raw failures are retained and classified `INVALID_RUN` when validation cannot complete.

## 8. Expected Falsification Value

- The ID-only support proxy is expected to expose false admission because it has no semantic check. Its exact rate is not prespecified and must not be reported as the full production validator's benchmark rate.
- Exact-copy may reduce false admission while causing missed admissions on paraphrases/cross-span claims; either outcome is descriptive.
- Static oracle must reproduce 36/36 decisions; failure falsifies plumbing integrity.
- These results do not establish that deletion, perturbation or joint admission adds value over a strong semantic verifier.

The next model protocol is permitted only after this runner and artifact format pass offline tests and this protocol commit predates the result commit.
