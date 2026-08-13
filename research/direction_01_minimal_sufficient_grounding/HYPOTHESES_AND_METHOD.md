# Hypotheses and Method v0.1

## Method Thesis

Write-time memory admission should be a joint constrained decision over a self-sufficient proposition and a minimal evidence set that supports every atomic requirement and qualifier, with counterfactual deletion and semantic perturbations exposing brittle support.

## Falsifiable Hypotheses

### H1 — Admission integrity

At matched coverage and compute, joint admission has lower false-admission risk than ID-only, ID+exact-quote and a strong semantic baseline.

### H2 — Audit identification

Evidence deletion identifies redundant or insufficient support, while controlled qualifier perturbations identify semantic strengthening that structural and quote checks miss.

### H3 — Error propagation

Under frozen downstream conditions, lower false admission results in fewer unsupported answers per original candidate, not merely fewer answers.

## Rival Explanations

R1 stronger verifier/more compute; R2 lower coverage; R3 atomicization destroys cross-sentence meaning; R4 shorter accepted text causes downstream gain; R5 shared generator/verifier/grader creates circular self-validation; R6 only explicit single-paragraph facts work; R7 holistic, MEG-style or extractive-copy baseline already suffices.

## Provisional Mechanism

1. Parse a candidate into a main proposition, atomic requirements and qualifier slots.
2. Localize candidate evidence from paragraphs to spans.
3. Populate a claim-requirement × evidence-span support matrix through a replaceable verifier protocol.
4. Solve a sufficient evidence set under configurable minimality.
5. Delete each selected span and retest sufficiency.
6. Apply controlled semantic perturbations and require the decision to change when support no longer holds.
7. Emit a structured `ADMIT`, `REVIEW` or `REJECT` result with auditable reasons and provenance.

All representation, solver, verifier and policy choices remain provisional adapters pending user decisions and evidence.

