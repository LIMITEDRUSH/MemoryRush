from dataclasses import dataclass

import pytest

from memoryrush.admission import (
    AdmissionDecision,
    AtomicClaim,
    CandidateClaim,
    ClaimFormAudit,
    ClaimFormStatus,
    ConservativeDecisionPolicy,
    EvidenceSpan,
    InclusionMinimalSolver,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
    replace_qualifier,
    evaluate_admission,
)
from memoryrush.admission.solver import EvidenceSolution, evaluate_sufficiency


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


def _passing_claim_form_audit() -> ClaimFormAudit:
    return ClaimFormAudit(
        self_sufficiency=ClaimFormStatus.PASS,
        minimality=ClaimFormStatus.PASS,
        reason_codes=("fixture_pass",),
        auditor_name="fixture",
        auditor_version="test-v1",
    )


@dataclass
class MatrixVerifier:
    label: SupportLabel
    supported_qualifiers: tuple[QualifierSlot, ...] = ()
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
            supported_qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
        ),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
        claim_form_audit=_passing_claim_form_audit(),
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


def test_unselected_contradiction_in_candidate_pool_routes_to_review() -> None:
    supporting = _span()
    contradiction_text = "The system cannot save time."
    contradiction = EvidenceSpan(
        span_id="span-002",
        document_id="doc-001",
        paragraph_id="p_002",
        text=contradiction_text,
        start_char=0,
        end_char=len(contradiction_text),
        source_sha256="d" * 64,
    )

    class PoolConflictVerifier:
        verifier_name = "pool-conflict-fixture"
        verifier_version = "test-v1"

        def build_support_matrix(self, candidate, evidence_spans):
            return SupportMatrix(
                candidate=candidate,
                evidence_spans=evidence_spans,
                cells=(
                    SupportCell(
                        "claim-001",
                        "span-001",
                        SupportLabel.SUPPORTS,
                        supported_qualifiers=(
                            QualifierSlot(QualifierKind.MODALITY, "may"),
                        ),
                    ),
                    SupportCell("claim-001", "span-002", SupportLabel.CONTRADICTS),
                ),
            )

    result = evaluate_admission(
        _candidate(),
        (supporting, contradiction),
        PoolConflictVerifier(),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
    )

    assert result.decision is AdmissionDecision.REVIEW
    assert "candidate_pool_contradiction" in result.reason_codes


def test_undetected_semantic_perturbation_downgrades_admit_to_review() -> None:
    original = _candidate()
    perturbation = replace_qualifier(
        original,
        kind=QualifierKind.MODALITY,
        before="may",
        after="always",
    )

    class BlindVerifier:
        verifier_name = "blind-fixture"
        verifier_version = "test-v1"

        def build_support_matrix(self, candidate, evidence_spans):
            modality = next(
                slot
                for slot in candidate.atomic_claims[0].qualifiers
                if slot.kind is QualifierKind.MODALITY
            )
            return SupportMatrix(
                candidate=candidate,
                evidence_spans=evidence_spans,
                cells=(
                    SupportCell(
                        "claim-001",
                        "span-001",
                        SupportLabel.SUPPORTS,
                        supported_qualifiers=(modality,),
                    ),
                ),
            )

    result = evaluate_admission(
        original,
        (_span(),),
        BlindVerifier(),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
        perturbations=((perturbation, AdmissionDecision.REJECT),),
        claim_form_audit=_passing_claim_form_audit(),
    )

    assert result.decision is AdmissionDecision.REVIEW
    assert "perturbation_not_detected" in result.reason_codes
    assert result.perturbation_audits[0].actual_decision is AdmissionDecision.ADMIT
    assert not result.perturbation_audits[0].passed


def test_detected_semantic_perturbation_preserves_original_admit() -> None:
    original = _candidate()
    perturbation = replace_qualifier(
        original,
        kind=QualifierKind.MODALITY,
        before="may",
        after="always",
    )

    class ModalityAwareVerifier:
        verifier_name = "modality-aware-fixture"
        verifier_version = "test-v1"

        def build_support_matrix(self, candidate, evidence_spans):
            modality = next(
                slot
                for slot in candidate.atomic_claims[0].qualifiers
                if slot.kind is QualifierKind.MODALITY
            )
            if modality.value == "may":
                label = SupportLabel.SUPPORTS
                qualifiers = (modality,)
            else:
                label = SupportLabel.INSUFFICIENT
                qualifiers = ()
            return SupportMatrix(
                candidate=candidate,
                evidence_spans=evidence_spans,
                cells=(SupportCell("claim-001", "span-001", label, supported_qualifiers=qualifiers),),
            )

    result = evaluate_admission(
        original,
        (_span(),),
        ModalityAwareVerifier(),
        InclusionMinimalSolver(),
        ConservativeDecisionPolicy(),
        perturbations=((perturbation, AdmissionDecision.REJECT),),
        claim_form_audit=_passing_claim_form_audit(),
    )

    assert result.decision is AdmissionDecision.ADMIT
    assert result.perturbation_audits[0].passed


def test_admission_rejects_a_solver_result_with_forged_sufficiency() -> None:
    candidate = _candidate()
    span = _span()
    verifier = MatrixVerifier(SupportLabel.INSUFFICIENT)
    matrix = verifier.build_support_matrix(candidate, (span,))
    actual = evaluate_sufficiency(matrix, (span.span_id,))

    class ForgedSolver:
        solver_name = "forged-test-solver"

        def solve(self, supplied_matrix):
            forged = actual.__class__(
                selected_span_ids=actual.selected_span_ids,
                supported_claim_ids=("claim-001",),
                missing_claim_ids=(),
                contradicted_claim_ids=(),
                ambiguous_claim_ids=(),
            )
            return (EvidenceSolution((span.span_id,), forged),)

    with pytest.raises(ValueError, match="solver returned inconsistent sufficiency"):
        evaluate_admission(
            candidate,
            (span,),
            verifier,
            ForgedSolver(),
            ConservativeDecisionPolicy(),
        )


def test_claim_form_failure_prevents_evidence_supported_admission() -> None:
    result = evaluate_admission(
        candidate=_candidate(),
        evidence_spans=(_span(),),
        verifier=MatrixVerifier(
            SupportLabel.SUPPORTS,
            supported_qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
        ),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
        claim_form_audit=ClaimFormAudit(
            self_sufficiency=ClaimFormStatus.FAIL,
            minimality=ClaimFormStatus.PASS,
            reason_codes=("context_dependent_fragment",),
            auditor_name="fixture",
            auditor_version="test-v1",
        ),
    )

    assert result.decision is AdmissionDecision.REJECT
    assert "claim_not_self_sufficient" in result.reason_codes
    assert result.claim_form_audit is not None


def test_unresolved_claim_minimality_routes_to_review() -> None:
    result = evaluate_admission(
        candidate=_candidate(),
        evidence_spans=(_span(),),
        verifier=MatrixVerifier(
            SupportLabel.SUPPORTS,
            supported_qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
        ),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
        claim_form_audit=ClaimFormAudit(
            self_sufficiency=ClaimFormStatus.PASS,
            minimality=ClaimFormStatus.REVIEW,
            reason_codes=("decomposition_disagreement",),
            auditor_name="fixture",
            auditor_version="test-v1",
        ),
    )

    assert result.decision is AdmissionDecision.REVIEW
    assert "claim_minimality_unresolved" in result.reason_codes


def test_missing_claim_form_audit_is_explicitly_reviewed() -> None:
    result = evaluate_admission(
        candidate=_candidate(),
        evidence_spans=(_span(),),
        verifier=MatrixVerifier(
            SupportLabel.SUPPORTS,
            supported_qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
        ),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
    )

    assert result.decision is AdmissionDecision.REVIEW
    assert "claim_form_not_audited" in result.reason_codes


def test_policy_cannot_admit_without_a_sufficient_evidence_solution() -> None:
    class FailOpenPolicy:
        policy_name = "fail-open-test-policy"

        def decide(self, matrix, solutions):
            return AdmissionDecision.ADMIT, ("forced_admit",)

    with pytest.raises(ValueError, match="policy admitted without sufficient evidence"):
        evaluate_admission(
            candidate=_candidate(),
            evidence_spans=(_span(),),
            verifier=MatrixVerifier(SupportLabel.INSUFFICIENT),
            solver=InclusionMinimalSolver(),
            policy=FailOpenPolicy(),
            claim_form_audit=_passing_claim_form_audit(),
        )
