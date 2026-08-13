"""Controlled semantic perturbations for declared candidate qualifiers."""

from __future__ import annotations

from dataclasses import dataclass

from memoryrush.admission.models import (
    AtomicClaim,
    CandidateClaim,
    QualifierKind,
    QualifierSlot,
)


@dataclass(frozen=True)
class CandidatePerturbation:
    operator: str
    qualifier_kind: QualifierKind
    before: str
    after: str
    original_candidate: CandidateClaim
    perturbed_candidate: CandidateClaim
    changed_claim_ids: tuple[str, ...]


def replace_qualifier(
    candidate: CandidateClaim,
    *,
    kind: QualifierKind,
    before: str,
    after: str,
) -> CandidatePerturbation:
    """Replace one explicitly declared qualifier without mutating the source candidate."""

    if not before.strip() or not after.strip():
        raise ValueError("qualifier replacement values must not be empty")
    if before == after:
        raise ValueError("qualifier replacement values must differ")

    matching_slots = [
        (claim.claim_id, slot)
        for claim in candidate.atomic_claims
        for slot in claim.qualifiers
        if slot.kind is kind and slot.value == before
    ]
    if not matching_slots:
        raise ValueError(f"qualifier {kind.value}={before!r} is not declared by the candidate")
    if before not in candidate.proposition:
        raise ValueError("declared qualifier text is not present in the main proposition")

    changed_claim_ids: list[str] = []
    atomic_claims: list[AtomicClaim] = []
    for claim in candidate.atomic_claims:
        has_matching_slot = any(slot.kind is kind and slot.value == before for slot in claim.qualifiers)
        if not has_matching_slot:
            atomic_claims.append(claim)
            continue
        if before not in claim.text:
            raise ValueError(
                f"declared qualifier text is not present in atomic claim {claim.claim_id}"
            )
        qualifiers = tuple(
            QualifierSlot(kind=slot.kind, value=after)
            if slot.kind is kind and slot.value == before
            else slot
            for slot in claim.qualifiers
        )
        atomic_claims.append(
            AtomicClaim(
                claim_id=claim.claim_id,
                text=claim.text.replace(before, after),
                qualifiers=qualifiers,
            )
        )
        changed_claim_ids.append(claim.claim_id)

    perturbed = CandidateClaim(
        candidate_id=f"{candidate.candidate_id}__{kind.value}_{after}",
        proposition=candidate.proposition.replace(before, after),
        atomic_claims=tuple(atomic_claims),
    )
    return CandidatePerturbation(
        operator=f"replace_{kind.value}",
        qualifier_kind=kind,
        before=before,
        after=after,
        original_candidate=candidate,
        perturbed_candidate=perturbed,
        changed_claim_ids=tuple(changed_claim_ids),
    )

