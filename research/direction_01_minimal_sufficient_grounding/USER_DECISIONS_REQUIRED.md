# User Decisions Required

Updated: `2026-08-14T06:55:00+08:00`

All entries are `PROPOSED`. The current repository implements replaceable
research adapters so work can continue without silently turning an agent choice
into the user's permanent MemoryRush architecture.

## D01 - Formal atomic and qualifier schema

- **Question:** Which claim decomposition and qualifier ontology should become
  the formal representation?
- **Options:** (A) current typed slots and atomic claims; (B) a richer relation
  graph; (C) retain raw proposition plus independently annotated facets.
- **Evidence for / against:** Typed slots make exact coverage auditable and have
  working contracts, but the development decomposition is oracle-informed and
  may damage cross-sentence semantics. Graphs are more expressive but add
  annotation and verifier burden. Facets reduce decomposition commitment but
  weaken mechanized minimality.
- **Impact:** Changes prompts, annotation schema, verifier output, solver inputs,
  benchmark format, and comparability with the current pilot.
- **Agent recommendation:** Keep the current schema as a versioned provisional
  adapter; obtain label-blind independent decomposition evidence before formal
  adoption.
- **Status:** `PROPOSED`
## D02 - Evidence minimality objective

- **Question:** Should formal minimality mean inclusion-minimal or globally
  minimum cardinality?
- **Options:** (A) inclusion-minimal sets; (B) minimum-cardinality sets; (C)
  report both and avoid choosing until failure patterns are measured.
- **Evidence for / against:** Inclusion minimality directly supports deletion
  certificates and may yield several valid evidence groups. Minimum cardinality
  is easier to summarize but can prefer brittle evidence and is more expensive.
  Both provisional solvers are implemented.
- **Impact:** Changes admission certificates, solver complexity, annotation of
  acceptable MEGs, and interpretation of redundant evidence.
- **Agent recommendation:** Use option C for research reporting; do not elevate
  either solver to permanent policy yet.
- **Status:** `PROPOSED`

## D03 - Final semantic verifier architecture

- **Question:** Which verifier should populate the support matrix in a formal
  system?
- **Options:** (A) local generative structured judge; (B) NLI/cross-encoder per
  cell; (C) hybrid retrieval/extractive checks plus semantic judge; (D) human
  review for uncertain cases.
- **Evidence for / against:** The local qwen3:8b adapter is offline-tested but
  has no benchmark accuracy result. Generative judging is flexible but costly
  and potentially circular; NLI is cheaper but qualifier/compositional coverage
  is uncertain; hybrids may fail closed more reliably but add components.
- **Impact:** Dominates compute, latency, calibration, error correlation, and
  the credibility of any interaction claim.
- **Agent recommendation:** Compare at least one strong holistic generative
  judge and one independently trained NLI-style verifier before selecting.
- **Status:** `PROPOSED`

## D04 - Formal support solver

- **Question:** Which solver and conflict semantics should be permanent?
- **Options:** exhaustive inclusion-minimal, exhaustive minimum-cardinality,
  ILP/SAT-style optimization, or bounded heuristic with REVIEW on exhaustion.
- **Evidence for / against:** Exhaustive solvers are transparent and adequate
  for the microbenchmark but do not prove scale. Pool contradictions and
  ambiguities can be treated as hard constraints or conservative REVIEW gates.
- **Impact:** Affects reproducibility, worst-case cost, admissibility invariants,
  and production failure behavior.
- **Agent recommendation:** Keep exhaustive bounded solvers as scientific
  references; benchmark scaling before choosing an optimized implementation.
- **Status:** `PROPOSED`

## D05 - Formal REVIEW policy

- **Question:** What happens to a candidate classified REVIEW?
- **Options:** (A) abstain from persistence; (B) queue for human review; (C)
  retain in an isolated provisional tier; (D) configurable policy by context.
- **Evidence for / against:** Treating REVIEW as REJECT lowers coverage and can
  manufacture apparent safety. Persisting it in normal memory weakens the
  integrity boundary. No user-workflow or cost study exists.
- **Impact:** Changes native coverage/risk, UI requirements, storage semantics,
  and evaluation denominators.
- **Agent recommendation:** For experiments, keep REVIEW distinct and report it
  exactly; for local production, fail closed unless a clearly isolated tier or
  human workflow is explicitly chosen.
- **Status:** `PROPOSED`

## D06 - Formal benchmark corpus, scale, and split

- **Question:** What sources, domains, sizes, and splits should define the real
  benchmark?
- **Options:** source-blocked explanatory long-form documents; conversation
  memory; mixed-domain corpus; staged combination.
- **Evidence for / against:** The current 36-case set exercises controlled
  failure families but has 0 human gold and design-time leakage. Source-blocked
  splits reduce document leakage; mixed domains test scope but raise annotation
  cost.
- **Impact:** Determines external validity, annotation budget, contamination
  risk, and acceptable claims.
- **Agent recommendation:** First create a modest source-blocked, label-blind
  explanatory-document holdout; only then expand domains.
- **Status:** `PROPOSED`

## D07 - Formal model family

- **Question:** Which local or external model family should be the permanent
  verifier?
- **Options:** qwen3:8b local baseline, smaller NLI model, multiple local models,
  or a controlled external API comparator.
- **Evidence for / against:** qwen3:8b is available locally and reproducible by
  digest, but one model cannot establish cross-model validity. External APIs add
  cost/version drift and are outside the local-first default.
- **Impact:** Hardware, privacy, latency, cost, reproducibility, and generality.
- **Agent recommendation:** Treat qwen3:8b only as the first bounded debugging
  verifier; postpone a formal choice until cross-model evidence exists.
- **Status:** `PROPOSED`

## D08 - Human annotation and adjudication plan

- **Question:** Who annotates atomicity, qualifier fidelity, support, MEGs, and
  disagreement, and how is adjudication performed?
- **Options:** two independent trained annotators plus adjudicator; domain
  experts; hybrid agent suggestions followed by blinded human verification.
- **Evidence for / against:** No human annotations currently exist. Agent
  suggestions can reduce effort but must not be relabeled as human gold.
- **Impact:** Determines label reliability, cost, reporting obligations, and
  whether semantic accuracy can be claimed.
- **Agent recommendation:** Pilot a double-annotation guideline study with
  disagreement retained; keep model suggestions hidden until first-pass labels
  are frozen.
- **Status:** `PROPOSED`

## D09 - Primary metric and numerical threshold

- **Question:** Which metric and threshold decide continuation or adoption?
- **Options:** false-admission risk at native coverage; risk at pre-registered
  matched coverage; three-way utility with explicit REVIEW cost; downstream
  unsupported answers per original candidate.
- **Evidence for / against:** Risk/coverage is required to prevent rejection-rate
  gaming. Fixed-count tie subsampling is not a calibrated frontier. There are no
  measured distributions from which to justify a numerical threshold.
- **Impact:** Controls sample size, power analysis, model selection, and claims.
- **Agent recommendation:** Report native three-way risk/coverage and downstream
  rate jointly; defer a numerical pass threshold until pilot variance and human
  label reliability are known.
- **Status:** `PROPOSED`

## D10 - Permanent integration into MemoryRush

- **Question:** Should this experimental admission mechanism become production
  architecture?
- **Options:** no integration; shadow-mode diagnostics; opt-in experimental
  gate; permanent default.
- **Evidence for / against:** Engineering plumbing is substantial, but semantic
  benefit, latency, coverage, cross-domain validity, and user workflow are not
  established.
- **Impact:** Production compatibility, migration, latency, storage behavior,
  and user trust.
- **Agent recommendation:** At most shadow mode after a valid pilot; permanent
  integration is not supported by current evidence.
- **Status:** `PROPOSED`

## D11 - Target venue and publication framing

- **Question:** Is the work aimed at a paper, workshop artifact, negative-result
  report, or internal research package?
- **Options:** defer; workshop/system demonstration; full empirical paper;
  rigorous negative-result/artifact report.
- **Evidence for / against:** Broad novelty is already rejected by closest work;
  the narrow interaction delta is untested. Venue speculation cannot substitute
  for evidence.
- **Impact:** Determines experiment scale, review standards, writing format, and
  deadlines.
- **Agent recommendation:** Defer venue selection; preserve the package so either
  a narrow empirical contribution or an honest negative result remains viable.
- **Status:** `PROPOSED`
