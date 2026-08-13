# MemoryRush Project Context

## Purpose

This is MemoryRush's persistent project memory. Codex consults only the relevant sections of `docs/PROJECT_CONTEXT_CN.md` when a task concerns project requirements, architecture, implementation, progress, or the next development step. It is not required reading before every answer. The Chinese file is primary; this file is its English counterpart.

Last updated: 2026-08-12

## Project Positioning

MemoryRush is a personal, local-first, research-oriented AI/ML engineering project. It studies whether long-form reading can be transformed into a small number of source-grounded memory units that improve later recall compared with summaries and ordinary chunk retrieval.

It is not currently a startup, SaaS service, subscription product, enterprise platform, or commercial system.

## Collaboration Requirements

- Communicate in Chinese by default and teach at a beginner-accessible level.
- Explain goals, principles, data flow, choices, alternatives, trade-offs, problems, and verification.
- Before any project implementation, file edit, state-changing command, model run, installation, commit, or push, present a concise action checklist and wait for the user's explicit confirmation.
- The checklist must state the goal and scope, likely files or commands, and verification. Approval covers only the listed scope; request confirmation again if the scope expands materially.
- Explanations, direct answers, and the minimal read-only inspection needed to prepare the checklist do not require confirmation.
- After a checklist is shown, the user's reply of "确认", "开始", or "继续" counts as approval.
- Do not commit or push unless it was explicitly included in the approved checklist.
- When reporting progress, distinguish planned, locally implemented, verified, committed, and pushed states.
- Do not load the full project context for simple or unrelated answers; read only the sections needed for the current project task.

## Current Source Of Truth

Use, in order: the user's latest explicit instruction; `docs/PROJECT_CONTEXT_CN.md`; `docs/RESEARCH_SPEC_CN.md`; `docs/RESEARCH_PLAN_CN.md`; `tasks/plan_CN.md` and `tasks/todo_CN.md`; then older `MemoryPoint_*` documents as background only.

## Current Status

- Phase 0 is complete.
- Phase 1 parsing and stable source paragraphs are implemented locally.
- Phase 2 contracts, evidence-reference checks, and the fake-provider pipeline are implemented locally.
- Phase 3 has an Ollama provider, versioned prompt, fake artifact, and a real `qwen3:8b` artifact locally.
- Benchmarking, evaluation, review UI, persistent memory storage, retrieval, reinforcement, and decay are not implemented.
- Current local implementation changes have not been committed or pushed.
- `compileall` passes, and both fake and `qwen3:8b` artifacts validate. The Ollama JSON smoke test passes and the model runs fully on the RTX 3070 Ti Laptop GPU. The active virtual environment still lacks `pytest`.

## AI Responsibility Boundary

The local generative LLM proposes core ideas and memory units, generates recall questions, later classifies relationships among retrieved evidence-bound candidates, and later writes answers from retrieved memory plus source evidence. It does not parse or store files, decide final truth, search the entire memory database, or control reinforcement and decay.

An embedding model performs first-stage retrieval. An optional reranker may refine candidates later. Deterministic Python code owns contracts, validation, persistence, score calculation, recall-event logging, and state updates. The user supplies personal-value signals through review and explicit feedback.

The current preferred real local model is `qwen3:8b` through Ollama. The code default may still reference `qwen2.5:7b-instruct` and should be aligned during the real-model task.

The current inference baseline remains local. Fine-tuning is deferred until a benchmark, a defined training objective, and repeated failure modes exist. At that point, rented GPU-cluster capacity may be used for controlled LoRA/QLoRA experiments, while routine use and baseline inference remain local-first.

## Planned Memory Recall

```text
query
-> query embedding
-> retrieve accepted memory units
-> hybrid ranking
-> fetch exact source evidence
-> local LLM writes a cited answer from those inputs
-> log memories actually used or confirmed
-> update memory strength later
```

For new-article associations, embedding retrieval selects historical candidates before the LLM classifies support, conflict, complement, or extension using evidence from both sides.

Candidate-list exposure alone must not reinforce a memory. Reinforcement requires meaningful use or explicit user feedback to avoid a self-reinforcing ranking loop.

## Scoring Direction

The current direct LLM `salience_score` is an uncalibrated baseline, not a final score. Later scoring separates:

- `intrinsic_salience`: centrality, information gain, transferability, specificity, and non-redundancy.
- `grounding_score`: evidence coverage, directness, citation correctness, and faithfulness.
- `personal_relevance`: explicit user review and feedback.
- `query_relevance`: per-query semantic and reranker relevance.
- `memory_strength`: validated recall history, decay, and feedback.

The next scoring prompt should request rubric-anchored component judgments and reasons. Python should calculate experimental scores. Within-document ranking is preferred over treating model-generated absolute scores as calibrated across documents. Final ranking weights must be justified by labels, baselines, and ablations.

## Development Sequence

1. Install and run the formal test dependencies.
2. Save a real `qwen3:8b` Ollama extraction artifact.
3. Document real-model failure modes.
4. Define annotations and build a small human-labeled benchmark.
5. Compare extraction with summary and heuristic baselines.
6. Add review state, stable memory IDs, and persistence only after extraction quality is acceptable.
7. Compare chunk, summary, and memory-unit retrieval on the same queries.
8. Add reinforcement and decay only after real recall events exist.
9. Use rented GPU-cluster capacity for LoRA/QLoRA only when a measured baseline shows that prompting or a lightweight ranker cannot resolve a defined problem; compare against the unfine-tuned model reproducibly.

## Known Open Problems

- The first `qwen3:8b` artifact passes current validation, which proves formatting, paragraph-ID, and core-idea quote checks only; it does not prove full semantic support for every MemoryUnit.
- `pytest` is missing from the active environment.
- Memory-unit semantic support is not fully validated.
- Whole-article prompting does not yet handle context-window limits.
- Persistent records need stable `memory_id` values rather than array indexes.
- No memory store, embedding index, retrieval API, or recall-event log exists yet.

## Update Rule

When the user explicitly confirms a scope, architecture, route, collaboration, phase, or verification change, update this file and `docs/PROJECT_CONTEXT_CN.md`. Do not record tentative brainstorming as an accepted decision.
