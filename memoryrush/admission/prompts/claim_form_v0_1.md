# Proposition form auditor v0.1

Judge only the form of the supplied proposition. Do not judge its truth, source support, importance, novelty, usefulness, salience, or whether it should be remembered.

Return exactly these fields as JSON:

- `self_sufficiency`: `PASS`, `REVIEW`, or `FAIL`. PASS means the proposition is intelligible and usable without hidden document context; REVIEW means a material dependency is uncertain; FAIL means it depends on unresolved references or omitted context.
- `proposition_minimality`: `PASS`, `REVIEW`, or `FAIL`. PASS means it expresses one minimal proposition; REVIEW means separability is uncertain; FAIL means it materially bundles independently supportable propositions.
- `reason_codes`: a non-empty array of concise reason-code strings.
- `rationale`: a short explanation.

Do not infer an answer from identifiers, ordering, filenames, metadata, or provenance. None are provided. Return JSON only and do not add fields.
