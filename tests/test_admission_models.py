import pytest

from memoryrush.admission import (
    AdmissionDecision,
    AtomicClaim,
    CandidateClaim,
    ClaimFormAudit,
    ClaimFormStatus,
    EvidenceSpan,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
)


def test_candidate_claim_requires_at_least_one_atomic_claim() -> None:
    with pytest.raises(ValueError, match="atomic claim"):
        CandidateClaim(
            candidate_id="candidate-001",
            proposition="The system may reduce latency under load.",
            atomic_claims=(),
        )


def test_evidence_span_offsets_must_match_frozen_text() -> None:
    with pytest.raises(ValueError, match="offsets"):
        EvidenceSpan(
            span_id="span-001",
            document_id="doc-001",
            paragraph_id="p_001",
            text="latency",
            start_char=10,
            end_char=4,
            source_sha256="a" * 64,
        )


def test_support_matrix_is_total_over_claim_span_pairs() -> None:
    candidate = CandidateClaim(
        candidate_id="candidate-001",
        proposition="The system may reduce latency under load.",
        atomic_claims=(
            AtomicClaim(
                claim_id="claim-001",
                text="The system may reduce latency.",
                qualifiers=(
                    QualifierSlot(kind=QualifierKind.MODALITY, value="may"),
                    QualifierSlot(kind=QualifierKind.CONDITION, value="under load"),
                ),
            ),
        ),
    )
    span = EvidenceSpan(
        span_id="span-001",
        document_id="doc-001",
        paragraph_id="p_001",
        text="The system may reduce latency under load.",
        start_char=0,
        end_char=41,
        source_sha256="b" * 64,
    )

    with pytest.raises(ValueError, match="missing support cells"):
        SupportMatrix(candidate=candidate, evidence_spans=(span,), cells=())


def test_admission_decision_values_are_stable() -> None:
    assert [decision.value for decision in AdmissionDecision] == [
        "ADMIT",
        "REVIEW",
        "REJECT",
    ]
    assert SupportLabel.SUPPORTS.value == "supports"


def test_runtime_contracts_reject_raw_strings_for_enum_fields() -> None:
    with pytest.raises(TypeError, match="claim-form self_sufficiency"):
        ClaimFormAudit(
            self_sufficiency="FAIL",  # type: ignore[arg-type]
            minimality=ClaimFormStatus.PASS,
            reason_codes=("fixture",),
            auditor_name="fixture",
            auditor_version="v1",
        )

    with pytest.raises(TypeError, match="qualifier kind"):
        QualifierSlot(kind="entity", value="Alice")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="support label"):
        SupportCell("claim", "span", "supports")  # type: ignore[arg-type]
