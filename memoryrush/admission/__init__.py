"""Provisional, replaceable write-time admission research framework."""

from memoryrush.admission.decision import (
    AdmissionResult,
    ConservativeDecisionPolicy,
    DecisionPolicy,
    PerturbationAudit,
    evaluate_admission,
)
from memoryrush.admission.evaluation import (
    EvaluationSummary,
    MatchedAdmissionResult,
    MethodPrediction,
    evaluate_predictions,
    matched_admission_evaluation,
)
from memoryrush.admission.models import (
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
from memoryrush.admission.verifiers import ExactCopyVerifier, IdOnlyVerifier, StaticOracleVerifier

__all__ = [
    "AdmissionDecision",
    "AdmissionResult",
    "AtomicClaim",
    "CandidateClaim",
    "CandidatePerturbation",
    "ClaimFormAudit",
    "ClaimFormStatus",
    "ConservativeDecisionPolicy",
    "DeletionAudit",
    "DeletionTrial",
    "DecisionPolicy",
    "EvidenceSpan",
    "EvaluationSummary",
    "EvidenceSetSolver",
    "EvidenceSolution",
    "InclusionMinimalSolver",
    "ExactCopyVerifier",
    "IdOnlyVerifier",
    "MinimumCardinalitySolver",
    "MatchedAdmissionResult",
    "MethodPrediction",
    "PerturbationAudit",
    "QualifierKind",
    "QualifierSlot",
    "SupportCell",
    "SupportLabel",
    "SupportMatrix",
    "StaticOracleVerifier",
    "SufficiencyResult",
    "Verifier",
    "audit_evidence_deletions",
    "evaluate_admission",
    "evaluate_predictions",
    "evaluate_sufficiency",
    "matched_admission_evaluation",
    "replace_qualifier",
]
