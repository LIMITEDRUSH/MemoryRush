# Direction 01 Result Artifacts

This directory retains immutable experiment artifacts. The artifacts below are
`DEBUGGING` evidence for the deterministic data and evaluation pipeline. They
are not semantic-model results, human-gold results, or confirmatory evidence.

## Artifact ledger

| Run | Artifact | Status | Bytes | SHA-256 |
|---|---|---|---:|---|
| `direction1-deterministic-debug-20260814-001` | `deterministic_debug_v0_1.json` | `INVALID_RUN` | 1,251 | `03fe9c47e87b27fab083c59f5265cb94d6cc8ec9df20a33864fdf07d4c13b098` |
| `direction1-deterministic-debug-20260814-002` | `deterministic_debug_v0_1_retry_lf.json` | `VALIDATED / DEBUGGING` | 53,006 | `9a83be0412600c324ac28788631dace5ec5b4d3cf6651b5f3692922ebcc16adc` |

Both artifacts are canonical UTF-8 JSON ending in LF. The first artifact is
retained rather than overwritten.

## Retained invalid run

The first run used a clean isolated Git worktree at commit `42b7b15`. Git for
Windows had converted the frozen JSONL from LF to CRLF because the repository
did not yet pin checkout line endings. The checked-out benchmark was 82,675
bytes with SHA-256
`e21807ada40d553d141f40a3bd9a8ccd58273719865b337b8906deb3920edf5e`,
not the frozen 82,639-byte input with SHA-256
`36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`.
The runner failed closed before producing predictions.

The repository then added `.gitattributes` and a regression test that requires
LF for the frozen benchmark, prompts, protocols, JSON, JSONL, Markdown, Python,
and YAML files. Commit `a76d12e` was pushed before the retry.

## Validated debugging run

The retry used a newly created, clean isolated worktree at commit `a76d12e`.
The benchmark, prompt, and protocol bytes matched the main worktree before the
run. The runner evaluated all 36 cases with seed `17` and produced no matched
admission result because fixed-count matching was not requested.

| Deterministic adapter | ADMIT / REVIEW / REJECT | False admissions | Coverage | Admission risk | Decision accuracy | Missed admissions |
|---|---:|---:|---:|---:|---:|---:|
| `id_only_support_proxy` | 36 / 0 / 0 | 16 | 1.0000 | 0.4444 | 0.5556 | 0 |
| `exact_copy` | 9 / 0 / 27 | 2 | 0.2500 | 0.2222 | 0.5556 | 13 |
| `static_oracle_upper_bound` | 20 / 3 / 13 | 0 | 0.5556 | 0.0000 | 1.0000 | 0 |

Interpretation is deliberately narrow:

- `id_only_support_proxy` simulates a structural support-validation blind spot;
  it is not an exact reproduction of the production article-memory pipeline.
- `exact_copy` is a deterministic normalized literal-copy baseline. Its lower
  risk occurs together with much lower coverage and 13 missed provisional
  admissions.
- `static_oracle_upper_bound` reads the frozen support certificates by design.
  Its perfect agreement proves evaluator plumbing, not semantic inference.
- The 36 labels comprise 27 agent/LLM-authored provisional cases and nine
  conditional relation certificates, with zero human-gold labels.
- No claim-form, atomic-support, holistic-support, or joint semantic method was
  run. These artifacts do not test the locked H1 interaction hypothesis.
