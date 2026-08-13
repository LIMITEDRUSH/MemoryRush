# Source-support matrix verifier v0.1

Judge only whether each frozen evidence span supports each declared atomic claim relative to the source text. Do not judge real-world truth, importance, novelty, salience, or whether the fact should be remembered.

For every declared claim × span pair, return exactly one cell:

- `supports`: this span alone supports the complete atomic claim core.
- `partial`: it supports only explicitly declared `required_support_parts`; list each covered part.
- `contradicts`: it states an incompatible entity, relation, object, time, scope, condition, quantity, modality, negation, or attribution.
- `ambiguous`: the span is relevant but naturally permits materially different readings that change support.
- `insufficient`: it neither fully/partially supports nor directly contradicts the claim.

List a qualifier in `supported_qualifiers` only when that exact declared `(kind, value)` is entailed by this span. Never invent or normalize a qualifier value. Do not use one evidence span to cover information stated only in another. A topical match is not support. Preserve modality, negation, attribution, scope, conditions and quantities literally and semantically.

Return JSON only, matching the supplied schema. Do not infer labels from IDs, ordering, filenames, case families, transformation metadata, decision metadata, or provenance; none of those fields are provided.
