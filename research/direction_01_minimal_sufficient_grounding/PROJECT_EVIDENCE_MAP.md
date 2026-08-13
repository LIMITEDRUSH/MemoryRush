# Project Evidence Map

Updated: `2026-08-14T06:55:00+08:00`

This map binds each research claim to inspectable repository evidence. It is a
provenance index, not a claim that the proposed method works. Agent- or
LLM-authored labels remain provisional; conditional programmatic relations are
mechanical transformation certificates relative to provisional bases, not
human semantic ground truth.

## Evidence-status vocabulary

- `VERIFIED_ENGINEERING`: executable behavior was checked by tests or a
  reproducible command, but scientific effectiveness is not implied.
- `DEBUGGING_OBSERVATION`: a bounded diagnostic result that may expose a bug or
  failure mode but is not confirmatory evidence.
- `LITERATURE_SUPPORTED`: supported by checked primary literature sources;
  non-discovery is never treated as proof of absence.
- `PROVISIONAL_MODEL_OR_AGENT`: generated or adjudicated without independent
  human-gold validation.
- `NOT_YET_TESTED`: required evidence has not been collected.
- `CONTRADICTED_UNDER_SEARCH`: the broad novelty formulation is contradicted by
  inspected prior or concurrent work.

## Claim-to-evidence matrix

| Claim ID | Calibrated claim | Status | Direct evidence | Missing evidence / limit |
|---|---|---|---|---|
| C01 | The production MemoryUnit validator can accept a semantically strengthened statement when its paragraph ID exists. | `DEBUGGING_OBSERVATION` | `tests/test_direction1_current_validator.py`; `CURRENT_RESULTS.md` (`run-debug-001`) | One synthetic counterexample establishes a blind spot, not its natural frequency. |
| C02 | The research framework represents candidates, atomic claims, typed qualifier slots, localized spans, total support matrices, three-way decisions, bounded solvers, deletion audits, and perturbations. | `VERIFIED_ENGINEERING` | `memoryrush/admission/models.py`, `solver.py`, `decision.py`, `perturbations.py`; corresponding `tests/test_admission_*.py` | These are provisional adapters, not the user-selected final schema, solver, verifier, or policy. |
| C03 | The frozen microbenchmark is byte-addressable and loader-validated at 36 cases, 82,639 bytes, SHA-256 `36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`. | `VERIFIED_ENGINEERING` | `data/benchmarks/direction1_synthetic_v0_1.jsonl`; `scripts/build_direction1_synthetic_benchmark.py`; benchmark loader/builder tests | It contains 0 human-gold cases and was authored after inspecting the task design. |
| C04 | Benchmark provenance is 27 LLM/agent provisional cases and 9 conditional programmatic relations; C014/C034 are provisional and C006/C020 expect insufficient evidence. | `VERIFIED_ENGINEERING` for provenance and relation contracts; labels remain provisional | `memoryrush/admission/benchmark.py`; benchmark JSONL; `ANNOTATION_GUIDE.md`; benchmark tests | Conditional certificates validate frozen registered transformations, not independent natural-language truth. |
| C05 | The inference manifest excludes original IDs and oracle/provenance fields, while an independently held outer mapping authenticates HMAC-derived opaque IDs. | `VERIFIED_ENGINEERING` | `memoryrush/admission/semantic_manifest.py`; `tests/test_semantic_manifest.py`; pushed commit `017b91b` | Process-level isolation still requires the inference runner to avoid importing or receiving the outer mapping. |
| C06 | Schedule ordering is deterministically bound for seeds 17, 29, and 47 while decoding seed stays 17. | `VERIFIED_ENGINEERING` | `semantic_manifest.py`; independent formula tests in `test_semantic_manifest.py`; `SEMANTIC_PILOT_PROTOCOL.md` | No model repeatability result exists yet. |
| C07 | Claim-form, atomic-support, and holistic-support prompts have strict schemas and enforce a complete 4,096-byte UTF-8 prompt cap before transport. | `VERIFIED_ENGINEERING` | `semantic_judges.py`, `ollama_verifier.py`, three versioned prompts; tests including frozen-36 preflight and exact byte boundaries; commits `212cf12`, `04c01b9` | Schema validity is not semantic correctness; claim/holistic contracts are not yet connected to live transport. |
| C08 | Raw attempts can be persisted as immutable PREPARED plus exactly one terminal RETURNED or TRANSPORT_FAILED record without overwrite. | `VERIFIED_ENGINEERING` | `semantic_attempts.py`; adversarial construction, recovery, tamper, and race tests; commit `7ddbb24` | The inference runner must prove it always persists RETURNED before parsing and honors the global/local failure state machine. |
| C09 | The current pre-run foundation passed 339 tests plus compileall and diff-check at pushed commit `ac493654cb402291483e39d747648d32fdbf16f9`. | `VERIFIED_ENGINEERING` | pytest/compile command recorded in the active research session; Git history | Test success does not establish verifier accuracy or method superiority. |
| C10 | Generic write-time support gating and every individual component have close prior or concurrent work. | `LITERATURE_SUPPORTED`; broad novelty `CONTRADICTED_UNDER_SEARCH` | `LITERATURE_LANDSCAPE.md`, `NOVELTY_AUDIT.md`, `papers.jsonl`; primary-source links therein | Literature search can miss work; the narrow interaction delta remains untested. |
| C11 | A narrow joint claim-side minimal/self-contained plus evidence-side minimal/sufficient intervention gate may remain distinguishable as a combined protocol. | `NOT_YET_TESTED` | Precisely scoped delta and closest-work matrix in `NOVELTY_AUDIT.md` | Requires strong ConsistencyGate/GAVEL/MEG/TriQua/holistic baselines, interaction ablations, matched native coverage/compute, and a fresh label-blind holdout. |
| C12 | The historical qwen3:8b extraction artifact is structurally valid but contains suspected modality/scope/attribution strengthening. | `DEBUGGING_OBSERVATION` | `CURRENT_RESULTS.md`; environment/artifact audit notes in `research-log.md` | Historical run lacks full model/config/input/hardware provenance; judgments are not human gold. |
| C13 | Atomic Method A, holistic Method B, or joint Method C has lower false-admission risk. | `NOT_YET_TESTED` | Pre-registered method and failure rules in `SEMANTIC_PILOT_PROTOCOL.md` | No semantic benchmark model run exists. The development set is oracle-informed and cannot support a positive superiority claim. |
| C14 | Joint admission reduces downstream unsupported answers. | `NOT_YET_TESTED` | H3 in `HYPOTHESES_AND_METHOD.md` and frozen design requirements | No frozen downstream propagation experiment exists. |

## Evidence flow and non-circularity boundary

```text
frozen benchmark + provisional annotations
             |
             +--> sealed outer mapping + oracle (outer evaluator only)
             |
             +--> oracle-free inference manifest + schedule
                         |
                         +--> exact request -> PREPARED -> transport
                                             -> RETURNED/TRANSPORT_FAILED
                         |
                         +--> raw model outputs (still provisional)
                                      |
                                      +--> outer ID join and parsing
                                      +--> method predictions
                                      +--> oracle join only for metrics
```

Any inference process access to the outer mapping, original case IDs, oracle
labels, provenance, family, perturbation operator, or minimal-evidence answer
invalidates the run. A correct pipeline can prevent direct runtime leakage, but
it cannot undo design-time target encoding in this already inspected synthetic
development set.

## Current highest-value missing evidence

1. A clean, pushed, inference-only runner and outer-only evaluator that pass
   adversarial isolation tests.
2. An immutable environment/model/preflight record followed by a bounded
   qwen3:8b `DEBUGGING` run with every raw return retained.
3. Native-policy three-way risk/coverage and exact failure strata; deterministic
   matched-count subsampling is descriptive only.
4. A fresh source-blocked, label-blind holdout with independently frozen
   decompositions/prompts before any positive comparative claim.
5. A fixed-downstream propagation study and human annotation reliability study.
