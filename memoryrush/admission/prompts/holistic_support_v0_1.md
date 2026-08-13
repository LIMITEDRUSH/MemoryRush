# Detail-matched whole-proposition support auditor v0.1

Judge only whether the supplied evidence pool supports the whole proposition relative to the given text. Do not judge real-world truth, importance, novelty, salience, usefulness, or whether the proposition should be remembered. Do not decompose the proposition into hidden atomic claims.

Return exactly these fields as JSON:

- `overall_relation`: one of `fully_supported`, `contradicted`, `ambiguous`, or `insufficient`.
- `dimension_statuses`: an object containing exactly `entity`, `relation`, `object`, `time`, `scope`, `condition`, `quantifier`, `modality`, `negation`, and `attribution`. Each value is one of `supported`, `contradicted`, `missing`, `ambiguous`, or `not_applicable`.
- `selected_evidence_ids`: evidence IDs whose text supports the judgment. This must be non-empty for `fully_supported`; use only supplied IDs.
- `pool_conflict`: `present` when any supplied evidence materially contradicts the proposition or selected support; otherwise `absent`.
- `pool_ambiguity`: `present` when the supplied evidence pool permits materially different readings that change support; otherwise `absent`.
- `reason_codes`: a non-empty array of concise reason-code strings.
- `rationale`: a short explanation.

A topical match is not support. Check every applicable fidelity dimension, preserving entities, relation, object, time, scope, conditions, quantities, modality, negation, and attribution literally and semantically. A `fully_supported` judgment cannot contain a contradicted, missing, or ambiguous dimension. Do not infer answers from IDs, order, filenames, labels, transformations, or provenance; none are provided. Return JSON only and do not add fields.
