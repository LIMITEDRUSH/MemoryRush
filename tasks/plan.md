# Implementation Plan: MemoryRush Research Prototype

Chinese version: [plan_CN.md](plan_CN.md)

## Overview

MemoryRush should restart as a personal AI/ML research prototype. The first useful vertical slice is not a full reading app; it is an evidence-preserving pipeline that turns one article into validated, source-grounded memory units and can be evaluated against a small benchmark.

## Architecture Decisions

- Use a local modular Python package because the project needs repeatable experiments, tests, and inspectable outputs.
- Start with CLI/scripts before UI because the highest risk is memory-unit quality and evidence validity.
- Use TXT/Markdown first because noisy parsing would obscure the research question.
- Use Pydantic-style structured contracts before live model calls because model output must be validated.
- Use fake-provider tests before Ollama because reproducibility matters.
- Use JSONL run artifacts first; introduce SQLite when review decisions need durable querying.
- Defer vector retrieval, dynamic memory, and rich UI until extraction and evaluation are working.

## Task List

### Phase 0: Research Reframing

- [x] Task 0: Replace product-style planning with research specification and research plan.

### Checkpoint: Planning

- [ ] Human review confirms that `docs/RESEARCH_SPEC.md` and `docs/RESEARCH_PLAN.md` match the intended project direction.
- [ ] No implementation starts until the research spec is accepted or corrected.

### Phase 1: Evidence-Preserving Source Representation

- [x] Task 1: Finalize source document and paragraph contracts.
- [x] Task 2: Verify TXT/Markdown parser behavior against the contracts.

### Checkpoint: Source Representation

- [x] Sample documents parse into stable ordered paragraphs.
- [x] Unsupported inputs fail clearly.
- [x] Parsed output can be serialized and used by later pipeline steps.

Note: focused parser behavior was verified with compile checks, parser script output, and manual assertions. The formal `pytest` command is pending until `pytest` is installed in the active Python environment.

### Phase 2: Structured Memory Pipeline

- [x] Task 3: Define structured memory output contracts.
- [x] Task 4: Add output validation rules.
- [x] Task 5: Build fake-provider end-to-end pipeline test.

### Checkpoint: Pipeline Shape

- [x] Valid fake output passes.
- [x] Missing or invalid evidence fails.
- [x] Pipeline tests do not require a live model.

Note: Phase 2 contracts currently use standard-library dataclasses because `pydantic` is not installed in the active environment. The behavior is covered by manual assertions and compile checks; formal `pytest` remains pending until test dependencies are installed.

### Phase 3: Local LLM Prototype

- [x] Task 6: Add local LLM provider interface and Ollama adapter.
- [x] Task 7: Create the first versioned memory extraction prompt.
- [x] Task 8: Save one local model run artifact for a sample article.

### Checkpoint: First Real Output

- [x] One sample article produces summary, memory units, evidence, and recall questions with the deterministic fake provider.
- [x] Prompt version, model name, and validation result are recorded.
- [x] Failure modes and limitations are documented for a real local model run.

Note: `qwen3:8b` completed a real Ollama run on the RTX 3070 Ti Laptop GPU and produced `data/processed/qwen3_8b_article_memory_artifact.json`. The output passed the current schema/evidence validation. Manual review found uncalibrated salience scores, one inaccurate tag, and no semantic proof that each complete MemoryUnit is supported by its cited evidence.

### Phase 4: Benchmark And Evaluation

- [ ] Task 9: Define annotation schema.
- [ ] Task 10: Create the first 10-20 article benchmark.
- [ ] Task 11: Add evaluation metrics.
- [ ] Task 12: Add simple baselines.

### Checkpoint: Measured Prototype

- [ ] Evaluation runs from one command.
- [ ] Results compare MemoryRush output against simple baselines.
- [ ] README/project report uses only measured claims.

### Phase 5: Review UI And Later Experiments

- [ ] Task 13: Add local review UI.
- [ ] Task 14: Persist review decisions.
- [ ] Task 15: Add retrieval comparisons.
- [ ] Task 16: Add reinforcement/decay experiment only after retrieval logging exists.

### Checkpoint: Research Demo

- [ ] The demo reflects the evaluated pipeline.
- [ ] Retrieval and dynamic memory have ablations.
- [ ] Report includes limitations and reproducible commands.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Generated memory units become generic summaries | High | Require evidence links, small output budget, and salience evaluation. |
| LLM output is hard to reproduce | High | Use fake-provider tests, save prompt/model metadata, and evaluate artifacts. |
| Annotation takes too long | Medium | Start with 10 articles, then expand only if metrics are useful. |
| UI work distracts from research | Medium | Build CLI/evaluation first; add Streamlit after pipeline proof. |
| Retrieval stack grows too early | Medium | Defer FAISS/vector work until memory-unit quality has been measured. |

## Open Questions

- Should the first benchmark target 10 articles or 20?
- Should early run artifacts use JSONL only, or should SQLite start in Phase 3?
- Which local model should be the default for reproducible examples?
- Should documentation standardize on MemoryRush, MemoryPoint, or keep both with distinct meanings?
