# Annotation Guide v0.1

Status: `PROVISIONAL`; no human annotation has been performed.

## Scope

Annotate only whether a candidate proposition is supported by a frozen source snapshot and localized evidence spans. Do not judge real-world truth, salience, usefulness, writing quality or whether the proposition deserves long-term storage.

## Annotation Unit

Each case contains a frozen document, one candidate proposition, provisional atomic claims and qualifier slots, localized evidence spans, provenance and an admission label. Inspect the full candidate and all provided evidence before labeling.

Every paragraph records ordered, non-overlapping `snapshot_start` / `snapshot_end` offsets into the frozen document. Evidence offsets remain paragraph-local. This two-level coordinate system prevents repeated paragraph text from being silently mapped to the wrong occurrence.

Every frozen oracle record must include a total `support_cells` matrix: exactly one label for every declared atomic-claim × evidence-span pair, with value-specific supported qualifier slots and any declared compositional support parts. It also includes a separate `claim_form` audit for self-sufficiency and proposition minimality. A final `ADMIT` label alone is not enough to reconstruct or audit the mechanism.

## Support Labels

- `fully_supported`: every atomic requirement and declared qualifier is directly or compositionally supported.
- `partially_supported`: some required content is supported, but at least one material atom or qualifier is absent.
- `contradicted`: selected evidence explicitly conflicts with a required atom or qualifier.
- `ambiguous`: the source reasonably admits incompatible readings that change admission.
- `insufficient_evidence`: evidence is related but does not license the proposition.

These support labels explain the oracle. The admission decision is separately `ADMIT`, `REVIEW` or `REJECT`.

## Atomic Claims

An atomic claim should be independently checkable against evidence while preserving enough context to be interpretable. Do not split away arguments or qualifiers needed to identify what is asserted. Cross-sentence relations may remain a single claim when decomposition would destroy the relation; record this as an adjudication issue rather than forcing a misleading split.

The formal atomic schema is a user-reserved decision. The current fields are pilot scaffolding only.

## Qualifier Slots

Check all material qualifiers present in the candidate:

- `entity`, `relation`, `object`;
- `time`, `scope`, `condition`, `quantifier`;
- `modality`, `negation`, `attribution`.

A claim is not fully supported when the source says *may* and the candidate says *does/always*, when a condition is dropped, when an attributed opinion becomes an unqualified fact, or when a number/date/entity changes.

## Evidence Sufficiency

Evidence is sufficient when the selected set jointly supports the complete proposition. Topic relevance is not support. Exact copying is neither necessary nor sufficient: paraphrases can be supported, and a copied phrase can be combined into an unsupported proposition.

For all frozen cases, list every known minimal evidence set. Repeating the same set is invalid even if its span IDs are reordered. Two provisional minimality notions are tracked:

- inclusion-minimal: deleting any selected span makes the set insufficient;
- minimum-cardinality: no sufficient set uses fewer spans.

Annotators must not decide which notion becomes formal policy.

## Three-Way Admission

- `ADMIT`: complete support and the case's configured minimality condition hold.
- `REJECT`: material support is missing or contradicted.
- `REVIEW`: genuine ambiguity, annotation disagreement, source defect, unresolved decomposition, or verifier failure prevents a responsible automatic decision.

The production disposition of REVIEW is not defined here.

## Disagreement

Record annotators independently before discussion. Preserve initial labels, rationale and timestamps; then record adjudication separately. Do not silently overwrite disagreement. Report agreement by decision and by qualifier family. The current repository contains no real human agreement measurements.

## Provenance and Truthful Labeling

- `programmatic_oracle`: permitted only for a suite-registered paired relation whose expected transition is mechanically checkable against a pinned canonical base and source.
- `llm_generated`: proposed by an LLM/agent; always provisional until independently reviewed.
- `human`: supplied by a named human annotation process.

The allowed source/status pairs are `programmatic_oracle/synthetic_oracle`, `llm_generated/provisional`, and `human/{provisional,human_gold}`. Provenance separately records `generator_type` as `programmatic`, `llm_or_agent`, or `human`; it must agree with the label source. An LLM/agent-generated label must never use `human_gold`.

`programmatic_oracle` is a conditional relation certificate, not a semantic ground-truth upgrade. The loader must reject any unregistered, missing, or duplicate relation and must pin the canonical source and complete base-case digests so a coordinated base-plus-derived mutation cannot pass. The derived transition can be mechanically checked, but the certificate still assumes the agent-authored provisional base annotation is correct. It is not a substitute for natural human-labeled data.

A paired case records both a valid `base_case_id` and an allow-listed `perturbation_operator`; neither field may appear alone, and the referenced base must be present in the same frozen JSONL file. Those fields may remain on a provisional semantic pair for auditability, but they confer no programmatic-oracle status. To claim `programmatic_oracle`, the pair must additionally match the suite's registered relation and canonical digests.

Do not infer contradiction merely because the evidence names a different entity or speaker. Under an open-world reading, “North Workshop did X” does not entail “South Workshop did not do X,” and “Mira wrote X” does not entail “Tomas did not write X.” When the candidate's entity or attribution is unsupported but not explicitly negated, use `insufficient_evidence`; reserve `contradicted` for explicit incompatible content.

## Minimal Examples

Source: “The system may reduce latency under peak load.”

- Candidate “The system may reduce latency under peak load.” → supported control.
- Candidate “The system always reduces latency.” → reject: modality strengthening plus deleted condition.
- Candidate “The system may reduce latency.” → reject or review according to whether the omitted condition materially changes scope; rationale required.

Source A: “The trial enrolled 120 people.” Source B: “Follow-up ended in 2025.”

- Candidate “The 120-person trial ended follow-up in 2025.” → may require the joint set `{A,B}`; neither span alone is sufficient.

## Quality Checklist

Before accepting an annotation record:

1. snapshot SHA-256 recomputes;
2. span text matches paragraph-local offsets;
3. every candidate qualifier has been inspected;
4. minimal evidence IDs exist and are deletion-checked;
5. minimal evidence sets are unique after treating each as an unordered set;
6. provenance and adjudication status are truthful; any programmatic label matches its registered pair and pinned base;
7. rationale distinguishes evidence absence, contradiction and ambiguity;
8. no private or copyrighted full-text material has been introduced.
