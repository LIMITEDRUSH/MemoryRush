"""Provisional, replaceable write-time admission research framework."""

from memoryrush.admission.decision import (
    AdmissionResult,
    ConservativeDecisionPolicy,
    DecisionPolicy,
    evaluate_admission,
)
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
from memoryrush.admission.perturbations import CandidatePerturbation, replace_qualifier
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
    "AdmissionResult",
    "AtomicClaim",
    "CandidateClaim",
    "CandidatePerturbation",
    "ConservativeDecisionPolicy",
    "DeletionAudit",
    "DeletionTrial",
    "DecisionPolicy",
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
    "evaluate_admission",
    "evaluate_sufficiency",
    "replace_qualifier",
]
