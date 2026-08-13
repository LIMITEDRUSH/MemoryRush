# Pilot Protocol v0.1

Protocol status: `HISTORICAL_DESIGN_LOCK`; run authorization superseded by `SEMANTIC_PILOT_PROTOCOL.md`
Decision status: `PROVISIONAL_AGENT_DESIGN`
Planned analysis class: `DEBUGGING` for deterministic plumbing and at most `EXPLORATORY` for the bounded model pilot. `CONFIRMATORY` is forbidden under the active v0.1 protocols.

Amendment after pre-result adversarial audit: the materialized benchmark now contains 27 agent/LLM provisional labels and 9 conditional programmatic relation certificates. Those certificates remain conditional on provisional base interpretations and are not human gold. The authoritative frozen hash, run gates, methods, failure policy, and kill rules are in `SEMANTIC_PILOT_PROTOCOL.md`; this file retains the broader historical design rationale only.

## 1. Claim Under Test

Under a frozen candidate pool, evidence window, compute envelope and downstream answer condition, a joint write-time admission mechanism that tests proposition self-sufficiency, qualifier fidelity, joint evidence sufficiency and evidence minimality will reduce false admission relative to ID-only, ID+exact-quote and a semantic-verifier baseline at matched admission coverage.

This protocol does **not** claim real-world truth, salience, user value, retrieval novelty or final benchmark validity.

## 2. Units and Frozen Inputs

One evaluation unit contains:

- immutable source snapshot and SHA-256;
- stable document and paragraph identifiers;
- one candidate proposition;
- one or more localized evidence spans;
- provisional atomic requirements and qualifier slots;
- oracle admission label and structured rationale for synthetic cases only;
- provenance showing whether the item is human-authored, programmatically perturbed, or LLM-generated.

Initial pilot uses public-safe, repository-authored synthetic explanatory passages. It may diagnose the existing public sample artifact, but that artifact cannot be treated as gold. No private documents or fabricated human annotations are allowed.

## 3. Case Families

The frozen micro-benchmark must cover at least:

1. fully supported single-span claim;
2. jointly supported cross-span claim;
3. entity replacement;
4. number/date replacement;
5. negation flip;
6. modality strengthening or weakening;
7. deleted condition, temporal scope or quantifier;
8. attribution transfer;
9. topic-related but non-supporting evidence;
10. redundant evidence;
11. contradictory spans;
12. genuinely ambiguous evidence;
13. claim fragment that is not self-sufficient;
14. over-composed claim containing one unsupported atom.

Programmatic transformations must preserve the unperturbed control and record the exact operator. LLM-generated cases or labels remain explicitly provisional.

## 4. Methods

All methods receive the same candidate/evidence pool.

- `id_only`: accepts when referenced paragraph IDs exist (current MemoryRush behavior for MemoryUnit support).
- `exact_quote`: requires localized quote occurrence but does not infer whole-proposition support.
- `fake_oracle`: deterministic upper-bound fixture using frozen oracle labels; never reported as a deployable method.
- `semantic_verifier`: replaceable adapter with the same evidence and decision budget; a lexical deterministic adapter may be used for pipeline tests, but cannot stand in for a strong NLI result.
- `atomic_same_verifier`: provisional decomposition plus the same verifier, without evidence-minimality audit.
- `holistic_same_verifier`: one whole-candidate judgment with matched verifier calls.
- `meg_style`: evidence selection aimed at sufficiency/minimality without the full joint proposition constraints.
- `joint_admission`: provisional joint support matrix, solver, deletion and semantic-perturbation audits.

Verifier call count, tokens where observable, latency and failures must be logged. A method exceeding the compute envelope is not silently compared as matched.

## 5. Provisional Representation and Solver

For the pilot only, a candidate is represented by a main proposition, atomic support requirements and typed qualifier slots (`entity`, `relation`, `object`, `time`, `scope`, `condition`, `quantifier`, `modality`, `negation`, `attribution`). The schema is provisional, not a user-confirmed permanent contract.

Two solver modes must be configurable:

- inclusion-minimal: no selected evidence span can be deleted while retaining full required support;
- minimum-cardinality: among sufficient sets, choose a smallest-cardinality set with deterministic tie-breaking.

Neither mode is declared final. Differences are reported for the user decision ledger.

## 6. Decisions

- `ADMIT`: all required proposition/qualifier elements are supported, a sufficient evidence set exists, configured minimality holds, and mandated audits do not expose fragility inconsistent with the oracle case.
- `REJECT`: known contradiction, missing required support, or a controlled perturbation is incorrectly treated as supported.
- `REVIEW`: ambiguity, verifier failure/disagreement, multiple incompatible support interpretations, or insufficient information to decide safely.

The production policy for `REVIEW` is not decided here.

## 7. Primary and Secondary Measurements

Primary family:

- false-admission risk among admitted items;
- coverage = admitted candidates / all candidates;
- risk–coverage curve when a method exposes a score;
- false-admission risk at shared coverage points;
- paired false-admission difference on a common admitted subset where meaningful.

Secondary:

- ADMIT/REVIEW/REJECT confusion matrix;
- qualifier-family recall and false-admission rate;
- deletion-audit detection rate;
- semantic-perturbation detection rate;
- evidence-set sufficiency and minimality accuracy on synthetic oracle cases;
- verifier calls, latency, tokens where observable and failure rate;
- unsupported-answer rate in the frozen downstream smoke probe;
- admitted text/evidence length, to test the “shorter text” explanation.

No statistical significance claim is permitted for an undersized micro-benchmark. Report exact counts and bootstrap intervals only when resampling assumptions and sample size are disclosed.

## 8. Coverage Matching

Primary comparisons cannot use raw accuracy alone. For each pair:

1. hold candidate pool fixed;
2. calculate native coverage and risk;
3. compare at the intersection of achievable coverage points by deterministic score thresholding when available;
4. if a method has no score, use an explicitly documented deterministic subsampling/tie policy and label the limitation;
5. report abstentions/reviews separately rather than recoding them as correct rejections.

A gain that vanishes at matched coverage supports the competing “rejects more” explanation.

## 9. Ablations and Negative Controls

- remove proposition atomicization while keeping verifier/evidence fixed;
- remove evidence-set solver;
- remove deletion audit;
- remove qualifier perturbation audit;
- swap inclusion-minimal and minimum-cardinality modes;
- add irrelevant but topically related evidence;
- duplicate a sufficient span (redundancy negative control);
- length-match accepted memory text/evidence across methods;
- use shuffled evidence IDs while keeping document topic fixed;
- compare generator/verifier identity where a second verifier is available.

## 10. Frozen Downstream Smoke Probe

The downstream stage is auxiliary. For each admitted candidate, a frozen deterministic question/template requests only the candidate's asserted fact from the selected evidence. The retriever, prompt, answer adapter, decoding and budget remain identical across admission methods. In the first oracle run, a deterministic answerability oracle is acceptable to test propagation plumbing; any LLM-based probe is exploratory until question and grader independence are established.

Measure unsupported answers per original candidate and per answered/admitted candidate. Also report coverage so admission cannot win by silence.

## 11. Reproducibility Record

Every run records: run ID/class, Git commit and dirty flag, config and prompt version, seed, input/source hashes, method/verifier/model/version, decoding, hardware, start/end time, latency, raw output path, validation result, exit code and failure. Failed and invalid runs are retained.

Initial deterministic seeds: `17`, `29`, `47`. Deterministic oracle logic should not vary; seeds exercise ordering/tie behavior only. Model probes use the same seeds when the backend supports them and disclose when it does not.

## 12. Success, Downgrade and Kill Criteria

Pilot success is provisional evidence only if joint admission:

- has lower false-admission risk than ID-only and exact-quote at at least one shared nontrivial coverage point;
- is not dominated by the strongest semantic/holistic baseline across shared coverage;
- detects multiple qualifier families and a cross-span case rather than only lexical single-span errors;
- retains its direction after length and compute controls;
- reduces the frozen downstream unsupported-answer measure without an unreported coverage loss.

Downgrade if benefit is confined to deterministic synthetic perturbations, one verifier, or unmatched coverage; if the strong holistic baseline ties; or if cross-span atomicization causes material false rejections.

Kill the current method claim under tested conditions if a detail-matched holistic or strong semantic baseline weakly dominates risk at every shared coverage point within the compute envelope, or if the proposed audits fail to distinguish supported controls from the principal qualifier perturbations. A kill does not authorize pivoting away from Direction 1; it triggers a negative-result analysis of the locked core.

## 13. Leakage and Circularity Controls

- synthetic case construction and oracle labels are frozen before method evaluation;
- artifact diagnosis is separated from confirmatory benchmark scoring;
- no benchmark label enters candidate generation or verifier prompt unless explicitly part of the fake-oracle baseline;
- when an LLM is used, record whether generator, verifier, question author or grader share a model family;
- source-level splits are mandatory before any learned or prompt-tuned method is evaluated;
- post-result edits create a new protocol version and are exploratory until rerun on a fresh frozen split.

## 14. Known Limits

This pilot cannot establish human annotation reliability, broad-domain generalization, statistical superiority, final schema validity, or publishable novelty. It is designed to obtain early falsification evidence and prove the research plumbing.
