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


def test_runtime_contracts_reject_mutable_sequence_fields() -> None:
    slot = QualifierSlot(QualifierKind.ENTITY, "Alice")
    with pytest.raises(TypeError, match="qualifiers must be a tuple"):
        AtomicClaim("claim", "Alice arrived.", [slot])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="atomic_claims must be a tuple"):
        CandidateClaim(
            "candidate",
            "Alice arrived.",
            [AtomicClaim("claim", "Alice arrived.")],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="reason_codes must be a tuple"):
        ClaimFormAudit(
            ClaimFormStatus.PASS,
            ClaimFormStatus.PASS,
            ["fixture"],  # type: ignore[arg-type]
            "fixture",
            "v1",
        )
    with pytest.raises(TypeError, match="supported_qualifiers must be a tuple"):
        SupportCell(
            "claim",
            "span",
            SupportLabel.SUPPORTS,
            supported_qualifiers=[slot],  # type: ignore[arg-type]
        )


def test_runtime_contracts_reject_wrong_nested_element_types() -> None:
    with pytest.raises(TypeError, match="qualifiers must contain QualifierSlot"):
        AtomicClaim("claim", "Alice arrived.", ("Alice",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="atomic_claims must contain AtomicClaim"):
        CandidateClaim("candidate", "Alice arrived.", ("claim",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="reason_codes must contain strings"):
        ClaimFormAudit(
            ClaimFormStatus.PASS,
            ClaimFormStatus.PASS,
            (1,),  # type: ignore[arg-type]
            "fixture",
            "v1",
        )


def test_evidence_offsets_require_exact_integers_not_booleans() -> None:
    with pytest.raises(TypeError, match="start_char and end_char must be integers"):
        EvidenceSpan(
            span_id="span",
            document_id="doc",
            paragraph_id="p_001",
            text="A",
            start_char=False,  # type: ignore[arg-type]
            end_char=1,
            source_sha256="a" * 64,
        )


def test_text_contracts_raise_type_errors_instead_of_attribute_errors() -> None:
    with pytest.raises(TypeError, match="candidate_id must be a string"):
        CandidateClaim(1, "Alice arrived.", (AtomicClaim("c", "Alice arrived."),))  # type: ignore[arg-type]


def test_validated_support_matrix_cannot_be_changed_through_caller_lists() -> None:
    qualifiers = [QualifierSlot(QualifierKind.ENTITY, "Alice")]
    claims = [AtomicClaim("claim", "Alice arrived.")]

    with pytest.raises(TypeError):
        AtomicClaim("claim", "Alice arrived.", qualifiers)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        CandidateClaim("candidate", "Alice arrived.", claims)  # type: ignore[arg-type]

    assert len(qualifiers) == 1
    assert len(claims) == 1
