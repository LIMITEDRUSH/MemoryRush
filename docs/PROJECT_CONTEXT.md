# MemoryRush Project Context

## Purpose

This is MemoryRush's persistent project memory. Codex consults only the relevant sections of `docs/PROJECT_CONTEXT_CN.md` when a task concerns project requirements, architecture, implementation, progress, or the next development step. It is not required reading before every answer. The Chinese file is primary; this file is its English counterpart.

Last updated: 2026-08-14

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
- The Direction 1 Phase 4 research branch now implements provisional admission contracts, a strict synthetic-benchmark loader, a provenance-safe evaluator, a `DEBUGGING`-only deterministic runner/CLI, and a local Ollama semantic-verifier adapter. These engineering changes are committed and pushed on `codex/direction1-autoresearch` through `ca40b68`.
- The frozen research microbenchmark has 36 cases / 82,639 bytes at SHA-256 `36390f9563463036d1b4d0ca7c095069080a20ee667d99d6fd0e88a859f88321`: 20 ADMIT / 13 REJECT / 3 REVIEW, with 27 agent/LLM provisional labels and 9 conditional programmatic-relation labels, and no human gold.
- The nine programmatic labels certify registered transformations only relative to frozen provisional bases; they are not independent semantic truth. C006/C020 expect `insufficient` support cells. C014/C034 were downgraded to provisional because their decisions are not mechanically established.
- The semantic pilot protocol is locked and pushed in `ca40b68`. The Ollama adapter is implemented, offline-tested, committed, and pushed, but it has not been run on this 36-case benchmark. There is no semantic-accuracy, method-superiority, or confirmatory result.
- The formal annotation schema, human-labeled benchmark, final verifier/solver, REVIEW policy, model family, metrics, thresholds, and human-annotation plan remain user decisions. Review UI, persistent memory storage, retrieval, reinforcement, and decay are not implemented.
- A separate Python 3.13 research environment has the test dependencies; the current full suite passes with `221 passed`. The committed deterministic runner can produce only `DEBUGGING` evidence, not semantic validation.
- The broad novelty claim for generic write-time support gating is rejected by the closest-work audit. The remaining narrow joint-certificate interaction delta is not yet demonstrated; search non-discovery is not proof of absence.

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

1. The isolated test environment and full regression suite are established.
2. A real `qwen3:8b` Ollama extraction artifact has been saved and audited; it is structurally valid, not semantic ground truth.
3. Under the locked Direction 1 protocol, implement and audit the atomic-versus-holistic semantic-pilot runner before running the bounded local-model pilot.
4. Keep all synthetic/provisional results separate from human gold; the formal annotation schema, human benchmark, model, REVIEW policy, metrics, and thresholds remain user decisions.
5. Claim a narrow increment only if it survives strong compositional baselines and matched coverage, compute, and downstream conditions.
6. Add review state, stable memory IDs, and persistence only after extraction quality is acceptable.
7. Compare chunk, summary, and memory-unit retrieval on the same queries.
8. Add reinforcement and decay only after real recall events exist.
9. Use rented GPU-cluster capacity for LoRA/QLoRA only when a measured baseline shows that prompting or a lightweight ranker cannot resolve a defined problem; compare against the unfine-tuned model reproducibly.

## Known Open Problems

- The first `qwen3:8b` artifact passes current validation, which proves formatting, paragraph-ID, and core-idea quote checks only; it does not prove full semantic support for every MemoryUnit.
- Memory-unit semantic support is not fully validated.
- The 36-case microbenchmark has no human gold; 27 provisional and 9 conditional programmatic-relation labels cannot establish natural-distribution performance or generalization.
- The semantic pilot protocol is locked, but the benchmark model run, matched-coverage comparison, and downstream propagation experiment have not been executed.
- Broad novelty is rejected by the closest-work audit; the narrow joint-certificate interaction delta remains undemonstrated.
- Whole-article prompting does not yet handle context-window limits.
- Persistent records need stable `memory_id` values rather than array indexes.
- No memory store, embedding index, retrieval API, or recall-event log exists yet.

## Update Rule

When the user explicitly confirms a scope, architecture, route, collaboration, phase, or verification change, update this file and `docs/PROJECT_CONTEXT_CN.md`. Do not record tentative brainstorming as an accepted decision.
