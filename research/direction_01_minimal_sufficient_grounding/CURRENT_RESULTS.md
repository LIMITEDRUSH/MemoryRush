# Current Results

Updated: `2026-08-14T05:18:00+08:00`
Overall evidence status: `MIXED`

## Verified This Run

### Phase 0 repository baseline

- The repository's pre-research dirty state was preserved in checkpoint `8499f5f` and pushed.
- Existing `.venv` uses Python `3.14.5rc1`, outside `pyproject.toml`'s declared `>=3.10,<3.14`, and lacked `pytest`, `pydantic` and `requests`.
- System `python` is `3.8.6`, below the declared range.
- A separate ignored `venv/research` was created with Python `3.13.14`; `pytest 8.4.2` was installed through `uv`.
- Before Direction 1 code changes, the existing full test suite passed: `15 passed in 0.26s`.
- Existing `compileall`, CLI sample listing and deterministic fake-provider pipeline passed.
- The ignored fake artifact is 1,292 bytes with SHA-256 `7b3250e1bdc7530b360dfd34e178f1284c7c9c22712e5677bf12ddca749cb567`.

These checks establish an engineering baseline only. They do not validate semantic source support.

### Existing validator false-positive reproduction (`run-debug-001`)

Synthetic source:

> The intervention may reduce latency under the tested configuration.

Candidate MemoryUnit:

> The intervention always reduces latency.

The candidate references the real paragraph ID. `validate_article_memory_output` returns a valid report because its MemoryUnit path checks paragraph-ID existence but does not compare proposition semantics, qualifiers or evidence text. The regression test passes and documents that baseline blind spot.

Classification: `DEBUGGING`, not confirmatory. The exact fixture was written after protocol lock and is not evidence that the proposed method works.

### Provisional research framework and frozen microbenchmark

The current TDD slices add verifier/solver-agnostic contracts, slot-specific qualifier coverage, localized evidence spans, total support matrices, bounded inclusion-minimal and minimum-cardinality solvers, deletion audits, boundary-safe qualifier perturbations, three-way decisions and a strict synthetic-benchmark loader.

- Initial RED: focused test collection failed with `ModuleNotFoundError: memoryrush.admission`.
- Perturbation RED: `2 failed, 45 passed` because the audit interface was not implemented.
- Benchmark-integrity RED: 15 failures exposed repeated-text provenance ambiguity, unknown-field acceptance and untruthful label/status combinations.
- Current full-suite GREEN after the runner, Ollama-attempt isolation and relation-certificate hardening: `221 passed`.

The repository now contains a canonical 36-case, 82,639-byte JSONL microbenchmark at SHA-256 `36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`: 20 ADMIT, 13 REJECT and 3 REVIEW across 14 families. Provenance is 27 agent/LLM-authored provisional labels and 9 conditional programmatic relation labels. None are human gold. The programmatic labels certify only registered transformations relative to frozen provisional bases; they are not independent semantic ground truth. C006 and C020 use `insufficient`, not `contradicts`, for their expected support cells. C014 (`must -> may`) and C034 (unsupported over-composed atom) were downgraded from programmatic-oracle provenance to provisional status because their labels are not mechanically established. C014/C023/C026/C034 therefore remain explicit semantic risks.

The evaluator keeps oracle decisions outside prediction records, requires exact case-universe joins and reports REVIEW separately from REJECT. Fixed-count matched admission is explicit opt-in and is documented as neither calibrated nor automatically fair. A local Ollama adapter for `qwen3:8b` now uses a versioned prompt, JSON schema, seed/temperature/context controls, strict envelope validation and raw-run metadata. Its offline tests include frozen qualifier-edge matrices, but it has not yet been run on the benchmark.

The provenance-safe deterministic runner and CLI are implemented, covered by adversarial tests, committed in `92cc8cd`, and pushed. They are intentionally `DEBUGGING`-only: they do not convert the synthetic labels into confirmatory evidence, and no deterministic benchmark result artifact is reported here. The relation-certificate hardening and benchmark revision were pushed in `d6fde5f`; the semantic pilot protocol was then locked and pushed in `ca40b68`, still before any benchmark model run.

The Ollama semantic-verifier adapter is implemented, offline-tested, committed and pushed (including attempt-state isolation in `eaf41b0`). It has not been run on this 36-case benchmark; therefore there is no benchmark model result, semantic accuracy claim or model-comparison result.

This verifies framework behavior and adversarial invariants only. No strong semantic verifier or admission advantage has yet been measured.

### Closest-work novelty audit

The independent audit searched and deduplicated 41 candidates and deeply inspected 20 closest works using primary paper/proceedings sources. Every individual component and generic write-time support-gating claim has prior art. The surviving statement is deliberately narrow: a single double-sided, counterfactual write certificate may still be novel as a benchmark/evaluation protocol if an interaction gain survives strong compositional baselines and matched coverage/compute/downstream conditions.

Status: broad novelty `REJECTED / CONTRADICTED_UNDER_TESTED_LITERATURE_SEARCH`; narrow delta `MIXED / NOT_YET_DEMONSTRATED`. Search non-discovery is not proof of absence, and no experiment has yet demonstrated the narrow interaction claim.

### Existing qwen artifact audit

The ignored qwen artifact revalidates structurally, but independent human semantic inspection found modality, attribution and scope strengthening. Historical model digest, decoding, seed, input hash, hardware and latency are absent, so the original run is not fully reproducible. These observations are audit judgments, not human-gold benchmark labels.

## Failures Retained

1. Heartbeat creation rejected lowercase status enum; retry with `ACTIVE` succeeded.
2. First secret scan failed on a nested PowerShell path array; flattened retry succeeded.
3. A combined push/test/smoke command was blocked before execution because it included a dynamic temporary-file deletion; operations were split and no state was lost.
4. Existing `.venv` baseline pytest failed with `No module named pytest`.
5. Isolated-environment creation/install command ended with exit 1 only because `python -m pip show` was attempted in a uv environment without the `pip` module; `uv pip list` subsequently verified the installation.
6. Contract RED run failed at import as intended; raw failure is preserved in the research log.

## Not Yet Established

- semantic verifier benchmark accuracy (the adapter/plumbing alone is verified);
- evidence solver effectiveness beyond synthetic certificate recomputation;
- deletion or perturbation audit benefit;
- matched-coverage results;
- downstream unsupported-answer reduction;
- cross-domain/model consistency;
- human annotation reliability;
- novelty beyond closest work.
- interaction benefit over ConsistencyGate/GAVEL/MEG/TriQua/holistic baselines;
- any confirmatory synthetic benchmark result.
