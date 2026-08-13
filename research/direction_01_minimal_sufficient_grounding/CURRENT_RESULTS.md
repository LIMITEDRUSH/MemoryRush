# Current Results

Updated: `2026-08-14T02:58+08:00`  
Overall evidence status: `NOT_YET_TESTABLE`

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

### Provisional contract implementation

The first TDD slice added verifier/solver-agnostic contracts for candidate claims, atomic claims, qualifier slots, localized evidence spans, total support matrices and stable decision/support enums.

- RED: focused test collection failed with `ModuleNotFoundError: memoryrush.admission`.
- GREEN: `5 passed in 0.05s` for the baseline regression plus contract tests.
- Regression: `20 passed in 0.18s`; `compileall` exit 0.

This verifies type invariants only. No solver, verifier or admission advantage is yet implemented or measured.

## Failures Retained

1. Heartbeat creation rejected lowercase status enum; retry with `ACTIVE` succeeded.
2. First secret scan failed on a nested PowerShell path array; flattened retry succeeded.
3. A combined push/test/smoke command was blocked before execution because it included a dynamic temporary-file deletion; operations were split and no state was lost.
4. Existing `.venv` baseline pytest failed with `No module named pytest`.
5. Isolated-environment creation/install command ended with exit 1 only because `python -m pip show` was attempted in a uv environment without the `pip` module; `uv pip list` subsequently verified the installation.
6. Contract RED run failed at import as intended; raw failure is preserved in the research log.

## Not Yet Established

- semantic verifier accuracy;
- evidence solver correctness;
- deletion or perturbation audit benefit;
- matched-coverage results;
- downstream unsupported-answer reduction;
- cross-domain/model consistency;
- human annotation reliability;
- novelty beyond closest work.

