"""Structured admission decisions over replaceable verifier and solver outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from memoryrush.admission.models import (
    AdmissionDecision,
    CandidateClaim,
    ClaimFormAudit,
    ClaimFormStatus,
    EvidenceSpan,
    SupportLabel,
    SupportMatrix,
)
from memoryrush.admission.perturbations import CandidatePerturbation
from memoryrush.admission.protocols import Verifier
from memoryrush.admission.solver import (
    DeletionAudit,
    EvidenceSetSolver,
    EvidenceSolution,
    SufficiencyResult,
    audit_evidence_deletions,
    evaluate_sufficiency,
)


@dataclass(frozen=True)
class PerturbationAudit:
    operator: str
    perturbed_candidate_id: str
    expected_decision: AdmissionDecision
    actual_decision: AdmissionDecision
    passed: bool
    actual_reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class AdmissionResult:
    candidate_id: str
    decision: AdmissionDecision
    reason_codes: tuple[str, ...]
    selected_span_ids: tuple[str, ...]
    verifier_name: str
    verifier_version: str
    solver_name: str
    sufficiency: SufficiencyResult
    deletion_audit: DeletionAudit | None
    perturbation_audits: tuple[PerturbationAudit, ...] = ()
    claim_form_audit: ClaimFormAudit | None = None


class DecisionPolicy(Protocol):
    policy_name: str

    def decide(
        self,
        matrix: SupportMatrix,
        solutions: tuple[EvidenceSolution, ...],
    ) -> tuple[AdmissionDecision, tuple[str, ...]]:
        """Choose a three-way decision without mutating verifier or solver evidence."""


class ConservativeDecisionPolicy:
    """Provisional policy that abstains on ambiguity and rejects missing support."""

    policy_name = "conservative_v0"

    def decide(
        self,
        matrix: SupportMatrix,
        solutions: tuple[EvidenceSolution, ...],
    ) -> tuple[AdmissionDecision, tuple[str, ...]]:
        if solutions:
            all_span_ids = tuple(sorted(span.span_id for span in matrix.evidence_spans))
            selected_span_ids = set(solutions[0].selected_span_ids)
            unselected_span_ids = tuple(
                span_id for span_id in all_span_ids if span_id not in selected_span_ids
            )
            if any(
                matrix.cell(claim.claim_id, span_id).label is SupportLabel.CONTRADICTS
                for claim in matrix.candidate.atomic_claims
                for span_id in unselected_span_ids
            ):
                return AdmissionDecision.REVIEW, (
                    "jointly_sufficient",
                    "candidate_pool_contradiction",
            )
            if any(
                matrix.cell(claim.claim_id, span_id).label is SupportLabel.AMBIGUOUS
                for claim in matrix.candidate.atomic_claims
                for span_id in unselected_span_ids
            ):
                return AdmissionDecision.REVIEW, (
                    "jointly_sufficient",
                    "candidate_pool_ambiguity",
                )
            return AdmissionDecision.ADMIT, ("jointly_sufficient",)

        all_span_ids = tuple(sorted(span.span_id for span in matrix.evidence_spans))
        diagnostic = evaluate_sufficiency(matrix, all_span_ids)
        if diagnostic.contradicted_claim_ids:
            return AdmissionDecision.REJECT, ("contradicted",)
        if diagnostic.ambiguous_claim_ids:
            return AdmissionDecision.REVIEW, ("ambiguous_support",)
        if diagnostic.missing_qualifiers:
            return AdmissionDecision.REJECT, ("missing_qualifier_support",)
        return AdmissionDecision.REJECT, ("insufficient_support",)


def evaluate_admission(
    candidate: CandidateClaim,
    evidence_spans: tuple[EvidenceSpan, ...],
    verifier: Verifier,
    solver: EvidenceSetSolver,
    policy: DecisionPolicy,
    perturbations: tuple[tuple[CandidatePerturbation, AdmissionDecision], ...] = (),
    claim_form_audit: ClaimFormAudit | None = None,
) -> AdmissionResult:
    """Run one auditable admission decision using replaceable components."""

    matrix = verifier.build_support_matrix(candidate, evidence_spans)
    if matrix.candidate != candidate or matrix.evidence_spans != evidence_spans:
        raise ValueError("verifier returned a support matrix for different inputs")
    solutions = solver.solve(matrix)
    for solution in solutions:
        recomputed = evaluate_sufficiency(matrix, solution.selected_span_ids)
        if recomputed != solution.sufficiency:
            raise ValueError(
                "solver returned inconsistent sufficiency for selected evidence spans"
            )
    decision, reason_codes = policy.decide(matrix, solutions)
    if decision is AdmissionDecision.ADMIT and not solutions:
        raise ValueError("policy admitted without sufficient evidence")

    if solutions:
        selected = solutions[0].selected_span_ids
        sufficiency = solutions[0].sufficiency
        deletion_audit = audit_evidence_deletions(matrix, selected)
        if not deletion_audit.is_inclusion_minimal:
            decision = AdmissionDecision.REVIEW
            reason_codes = (*reason_codes, "deletion_audit_not_minimal")
    else:
        selected = tuple(sorted(span.span_id for span in evidence_spans))
        sufficiency = evaluate_sufficiency(matrix, selected)
        deletion_audit = None

    perturbation_audits: list[PerturbationAudit] = []
    for perturbation, expected_decision in perturbations:
        if perturbation.original_candidate != candidate:
            raise ValueError("perturbation was not derived from the evaluated candidate")
        perturbed_result = evaluate_admission(
            candidate=perturbation.perturbed_candidate,
            evidence_spans=evidence_spans,
            verifier=verifier,
            solver=solver,
            policy=policy,
            claim_form_audit=claim_form_audit,
        )
        passed = perturbed_result.decision is expected_decision
        perturbation_audits.append(
            PerturbationAudit(
                operator=perturbation.operator,
                perturbed_candidate_id=perturbation.perturbed_candidate.candidate_id,
                expected_decision=expected_decision,
                actual_decision=perturbed_result.decision,
                passed=passed,
                actual_reason_codes=perturbed_result.reason_codes,
            )
        )

    if decision is AdmissionDecision.ADMIT and any(
        not audit.passed for audit in perturbation_audits
    ):
        decision = AdmissionDecision.REVIEW
        reason_codes = (*reason_codes, "perturbation_not_detected")

    if claim_form_audit is None:
        if decision is AdmissionDecision.ADMIT:
            decision = AdmissionDecision.REVIEW
        reason_codes = (*reason_codes, "claim_form_not_audited")
    else:
        if claim_form_audit.self_sufficiency is ClaimFormStatus.FAIL:
            decision = AdmissionDecision.REJECT
            reason_codes = (*reason_codes, "claim_not_self_sufficient")
        elif claim_form_audit.self_sufficiency is ClaimFormStatus.REVIEW:
            if decision is AdmissionDecision.ADMIT:
                decision = AdmissionDecision.REVIEW
            reason_codes = (*reason_codes, "claim_self_sufficiency_unresolved")

        if claim_form_audit.minimality is ClaimFormStatus.FAIL:
            decision = AdmissionDecision.REJECT
            reason_codes = (*reason_codes, "claim_not_minimal")
        elif claim_form_audit.minimality is ClaimFormStatus.REVIEW:
            if decision is AdmissionDecision.ADMIT:
                decision = AdmissionDecision.REVIEW
            reason_codes = (*reason_codes, "claim_minimality_unresolved")

    return AdmissionResult(
        candidate_id=candidate.candidate_id,
        decision=decision,
        reason_codes=reason_codes,
        selected_span_ids=selected,
        verifier_name=verifier.verifier_name,
        verifier_version=verifier.verifier_version,
        solver_name=solver.solver_name,
        sufficiency=sufficiency,
        deletion_audit=deletion_audit,
        perturbation_audits=tuple(perturbation_audits),
        claim_form_audit=claim_form_audit,
    )
