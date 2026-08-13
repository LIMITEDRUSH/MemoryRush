"""Provisional, replaceable write-time admission research framework."""

from memoryrush.admission.models import (
    AdmissionDecision,
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
)
from memoryrush.admission.protocols import Verifier
from memoryrush.admission.solver import (
    DeletionAudit,
    DeletionTrial,
    EvidenceSetSolver,
    EvidenceSolution,
    InclusionMinimalSolver,
    MinimumCardinalitySolver,
    SufficiencyResult,
    audit_evidence_deletions,
    evaluate_sufficiency,
)

__all__ = [
    "AdmissionDecision",
    "AtomicClaim",
    "CandidateClaim",
    "DeletionAudit",
    "DeletionTrial",
    "EvidenceSpan",
    "EvidenceSetSolver",
    "EvidenceSolution",
    "InclusionMinimalSolver",
    "MinimumCardinalitySolver",
    "QualifierKind",
    "QualifierSlot",
    "SupportCell",
    "SupportLabel",
    "SupportMatrix",
    "SufficiencyResult",
    "Verifier",
    "audit_evidence_deletions",
    "evaluate_sufficiency",
]
