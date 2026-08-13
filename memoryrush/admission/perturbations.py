"""Controlled semantic perturbations for declared candidate qualifiers."""

from __future__ import annotations

import re
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


def _replace_declared_phrase(text: str, before: str, after: str) -> str:
    pattern = re.compile(rf"(?<!\w){re.escape(before)}(?!\w)")
    replaced, count = pattern.subn(after, text)
    if count == 0:
        raise ValueError(f"declared qualifier phrase {before!r} is not present as a boundary-safe span")
    return replaced


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
    perturbed_proposition = _replace_declared_phrase(candidate.proposition, before, after)

    changed_claim_ids: list[str] = []
    atomic_claims: list[AtomicClaim] = []
    for claim in candidate.atomic_claims:
        has_matching_slot = any(slot.kind is kind and slot.value == before for slot in claim.qualifiers)
        if not has_matching_slot:
            atomic_claims.append(claim)
            continue
        perturbed_claim_text = _replace_declared_phrase(claim.text, before, after)
        qualifiers = tuple(
            QualifierSlot(kind=slot.kind, value=after)
            if slot.kind is kind and slot.value == before
            else slot
            for slot in claim.qualifiers
        )
        atomic_claims.append(
            AtomicClaim(
                claim_id=claim.claim_id,
                text=perturbed_claim_text,
                qualifiers=qualifiers,
                required_support_parts=claim.required_support_parts,
            )
        )
        changed_claim_ids.append(claim.claim_id)

    perturbed = CandidateClaim(
        candidate_id=f"{candidate.candidate_id}__{kind.value}_{after}",
        proposition=perturbed_proposition,
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
