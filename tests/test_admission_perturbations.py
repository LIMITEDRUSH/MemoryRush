import pytest

from memoryrush.admission import (
    AtomicClaim,
    CandidateClaim,
    QualifierKind,
    QualifierSlot,
    replace_qualifier,
)


def _candidate() -> CandidateClaim:
    return CandidateClaim(
        candidate_id="candidate-001",
        proposition="According to the report, the system may save 12 ms under peak load in 2025.",
        atomic_claims=(
            AtomicClaim(
                claim_id="claim-001",
                text="The system may save 12 ms under peak load in 2025.",
                qualifiers=(
                    QualifierSlot(QualifierKind.ATTRIBUTION, "According to the report"),
                    QualifierSlot(QualifierKind.MODALITY, "may"),
                    QualifierSlot(QualifierKind.QUANTIFIER, "12"),
                    QualifierSlot(QualifierKind.CONDITION, "under peak load"),
                    QualifierSlot(QualifierKind.TIME, "2025"),
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    ("kind", "before", "after"),
    [
        (QualifierKind.MODALITY, "may", "always"),
        (QualifierKind.QUANTIFIER, "12", "21"),
        (QualifierKind.TIME, "2025", "2024"),
        (QualifierKind.CONDITION, "under peak load", "under all loads"),
    ],
)
def test_replace_qualifier_changes_proposition_claim_and_slot(kind, before, after) -> None:
    perturbation = replace_qualifier(_candidate(), kind=kind, before=before, after=after)

    assert before not in perturbation.perturbed_candidate.proposition
    assert after in perturbation.perturbed_candidate.proposition
    assert after in perturbation.perturbed_candidate.atomic_claims[0].text
    slot_values = {
        slot.kind: slot.value
        for slot in perturbation.perturbed_candidate.atomic_claims[0].qualifiers
    }
    assert slot_values[kind] == after
    assert perturbation.operator == f"replace_{kind.value}"


def test_perturbation_rejects_untracked_or_noop_replacement() -> None:
    with pytest.raises(ValueError, match="not declared"):
        replace_qualifier(
            _candidate(),
            kind=QualifierKind.ENTITY,
            before="system",
            after="service",
        )

    with pytest.raises(ValueError, match="must differ"):
        replace_qualifier(
            _candidate(),
            kind=QualifierKind.MODALITY,
            before="may",
            after="may",
        )


def test_perturbation_does_not_mutate_original_candidate() -> None:
    original = _candidate()

    replace_qualifier(
        original,
        kind=QualifierKind.MODALITY,
        before="may",
        after="always",
    )

    assert "may" in original.proposition
    assert original.atomic_claims[0].qualifiers[1].value == "may"

