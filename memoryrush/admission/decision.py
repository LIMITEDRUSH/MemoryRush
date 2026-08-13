"""Structured admission decisions over replaceable verifier and solver outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from memoryrush.admission.models import (
    AdmissionDecision,
    CandidateClaim,
    EvidenceSpan,
    SupportMatrix,
)
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
) -> AdmissionResult:
    """Run one auditable admission decision using replaceable components."""

    matrix = verifier.build_support_matrix(candidate, evidence_spans)
    if matrix.candidate != candidate or matrix.evidence_spans != evidence_spans:
        raise ValueError("verifier returned a support matrix for different inputs")
    solutions = solver.solve(matrix)
    decision, reason_codes = policy.decide(matrix, solutions)

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
    )

