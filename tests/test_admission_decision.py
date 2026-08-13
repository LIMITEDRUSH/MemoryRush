from dataclasses import dataclass

from memoryrush.admission import (
    AdmissionDecision,
    AtomicClaim,
    CandidateClaim,
    ConservativeDecisionPolicy,
    EvidenceSpan,
    InclusionMinimalSolver,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
    evaluate_admission,
)


def _candidate() -> CandidateClaim:
    return CandidateClaim(
        candidate_id="candidate-001",
        proposition="The system may save time.",
        atomic_claims=(
            AtomicClaim(
                claim_id="claim-001",
                text="The system may save time.",
                qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
            ),
        ),
    )


def _span() -> EvidenceSpan:
    text = "The system may save time."
    return EvidenceSpan(
        span_id="span-001",
        document_id="doc-001",
        paragraph_id="p_001",
        text=text,
        start_char=0,
        end_char=len(text),
        source_sha256="d" * 64,
    )


@dataclass
class MatrixVerifier:
    label: SupportLabel
    supported_qualifiers: tuple[QualifierKind, ...] = ()
    verifier_name: str = "matrix-fixture"
    verifier_version: str = "test-v1"

    def build_support_matrix(self, candidate, evidence_spans) -> SupportMatrix:
        return SupportMatrix(
            candidate=candidate,
            evidence_spans=evidence_spans,
            cells=(
                SupportCell(
                    claim_id="claim-001",
                    span_id="span-001",
                    label=self.label,
                    supported_qualifiers=self.supported_qualifiers,
                ),
            ),
        )


def test_admission_result_is_structured_and_auditable() -> None:
    result = evaluate_admission(
        candidate=_candidate(),
        evidence_spans=(_span(),),
        verifier=MatrixVerifier(
            SupportLabel.SUPPORTS,
            supported_qualifiers=(QualifierKind.MODALITY,),
        ),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
    )

    assert result.decision is AdmissionDecision.ADMIT
    assert result.selected_span_ids == ("span-001",)
    assert result.deletion_audit is not None
    assert result.deletion_audit.is_inclusion_minimal
    assert result.verifier_name == "matrix-fixture"
    assert result.solver_name == "exhaustive_inclusion_minimal_v0"
    assert "jointly_sufficient" in result.reason_codes


def test_contradiction_rejects_and_ambiguity_reviews() -> None:
    contradiction = evaluate_admission(
        _candidate(),
        (_span(),),
        MatrixVerifier(SupportLabel.CONTRADICTS),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
    )
    ambiguity = evaluate_admission(
        _candidate(),
        (_span(),),
        MatrixVerifier(SupportLabel.AMBIGUOUS),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
    )

    assert contradiction.decision is AdmissionDecision.REJECT
    assert "contradicted" in contradiction.reason_codes
    assert ambiguity.decision is AdmissionDecision.REVIEW
    assert "ambiguous_support" in ambiguity.reason_codes


def test_missing_support_or_qualifier_rejects() -> None:
    insufficient = evaluate_admission(
        _candidate(),
        (_span(),),
        MatrixVerifier(SupportLabel.INSUFFICIENT),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
    )
    missing_qualifier = evaluate_admission(
        _candidate(),
        (_span(),),
        MatrixVerifier(SupportLabel.SUPPORTS),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
    )

    assert insufficient.decision is AdmissionDecision.REJECT
    assert "insufficient_support" in insufficient.reason_codes
    assert missing_qualifier.decision is AdmissionDecision.REJECT
    assert "missing_qualifier_support" in missing_qualifier.reason_codes

