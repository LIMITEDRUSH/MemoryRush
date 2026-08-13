"""Small provisional, descriptive evaluators for admission experiments."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from memoryrush.admission.models import AdmissionDecision


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class MethodPrediction:
    """One provisional method result; admission_score is not an objective probability."""

    case_id: str
    method_name: str
    method_version: str
    decision: AdmissionDecision
    reason_codes: tuple[str, ...]
    admission_score: float
    score_source: str

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.method_name, "method_name")
        _require_text(self.method_version, "method_version")
        _require_text(self.score_source, "score_source")
        if not isinstance(self.decision, AdmissionDecision):
            raise TypeError("decision must be an AdmissionDecision")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be a tuple of strings")
        if any(not isinstance(code, str) for code in self.reason_codes):
            raise TypeError("reason_codes must contain only strings")
        if any(not code.strip() for code in self.reason_codes):
            raise ValueError("reason_codes must not contain empty strings")
        if not isinstance(self.admission_score, float):
            raise TypeError("admission_score must be a float, not a probability claim")
        if not math.isfinite(self.admission_score):
            raise ValueError("admission_score must be finite")
        if not 0.0 <= self.admission_score <= 1.0:
            raise ValueError("admission_score must be between 0 and 1")


@dataclass(frozen=True)
class EvaluationSummary:
    """Provisional descriptive counts and rates, without inferential claims."""

    method_name: str
    method_version: str
    n: int
    admit_count: int
    review_count: int
    reject_count: int
    coverage: float
    false_admissions: int
    admission_risk: float | None
    missed_admissions: int
    missed_as_review: int
    missed_as_reject: int
    decision_accuracy: float
    group_summaries: Mapping[str, "EvaluationSummary"] = field(default_factory=dict)
    family_summaries: Mapping[str, "EvaluationSummary"] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "group_summaries",
            MappingProxyType(dict(self.group_summaries)),
        )
        object.__setattr__(
            self,
            "family_summaries",
            MappingProxyType(dict(self.family_summaries)),
        )


@dataclass(frozen=True)
class MatchedAdmissionResult:
    """A provisional fixed-count ADMIT subset, not a complete method evaluation."""

    method_name: str
    method_version: str
    target_count: int
    seed: str
    selected_case_ids: tuple[str, ...]
    false_admissions: int
    admission_risk: float


def evaluate_predictions(
    predictions: tuple[MethodPrediction, ...],
    oracle_decisions: Mapping[str, AdmissionDecision],
    *,
    case_groups: Mapping[str, str] | None = None,
    case_families: Mapping[str, str] | None = None,
) -> EvaluationSummary:
    """Return provisional descriptive metrics joined to a separate, total oracle."""

    method_name, method_version = _validate_prediction_batch(predictions)
    _validate_oracle_decisions(predictions, oracle_decisions)
    group_summaries = _stratify(
        predictions,
        oracle_decisions,
        case_groups,
        "case_groups",
    )
    family_summaries = _stratify(
        predictions,
        oracle_decisions,
        case_families,
        "case_families",
    )
    return _summarize(
        predictions,
        oracle_decisions,
        method_name,
        method_version,
        group_summaries=group_summaries,
        family_summaries=family_summaries,
    )


def matched_admission_evaluation(
    method_predictions: Mapping[str, tuple[MethodPrediction, ...]],
    oracle_decisions: Mapping[str, AdmissionDecision],
    *,
    target_count: int,
    seed: str,
) -> dict[str, MatchedAdmissionResult]:
    """Return a provisional fixed-count selection against one separate oracle.

    ``admission_score`` is a method-supplied ranking, not an objective probability.
    Matching counts does not establish fairness, calibration, or method equivalence.
    """

    if isinstance(target_count, bool) or not isinstance(target_count, int) or target_count <= 0:
        raise ValueError("target_count must be a positive integer")
    _require_text(seed, "seed")
    if not isinstance(method_predictions, Mapping) or not method_predictions:
        raise ValueError("method_predictions must contain at least one method")

    validated: list[
        tuple[str, tuple[MethodPrediction, ...], str, str]
    ] = []
    common_case_ids: set[str] | None = None
    for method_key, predictions in method_predictions.items():
        _require_text(method_key, "method key")
        method_name, method_version = _validate_prediction_batch(predictions)
        case_ids = {prediction.case_id for prediction in predictions}
        if common_case_ids is None:
            common_case_ids = case_ids
        elif case_ids != common_case_ids:
            raise ValueError(
                "matched evaluation requires an identical case_id universe for every method"
            )
        validated.append((method_key, predictions, method_name, method_version))

    first_predictions = validated[0][1]
    _validate_oracle_decisions(first_predictions, oracle_decisions)

    results: dict[str, MatchedAdmissionResult] = {}
    for method_key, predictions, method_name, method_version in validated:
        admitted = [
            prediction
            for prediction in predictions
            if prediction.decision is AdmissionDecision.ADMIT
        ]
        if len(admitted) < target_count:
            raise ValueError(
                f"insufficient ADMIT pool for {method_key}: "
                f"required {target_count}, found {len(admitted)}"
            )
        selected = sorted(
            admitted,
            key=lambda prediction: (
                -prediction.admission_score,
                _tie_break(seed, prediction.case_id),
            ),
        )[:target_count]
        false_admissions = sum(
            oracle_decisions[prediction.case_id] is not AdmissionDecision.ADMIT
            for prediction in selected
        )
        results[method_key] = MatchedAdmissionResult(
            method_name=method_name,
            method_version=method_version,
            target_count=target_count,
            seed=seed,
            selected_case_ids=tuple(prediction.case_id for prediction in selected),
            false_admissions=false_admissions,
            admission_risk=false_admissions / target_count,
        )
    return results


def _validate_prediction_batch(
    predictions: tuple[MethodPrediction, ...],
) -> tuple[str, str]:
    if not isinstance(predictions, tuple):
        raise TypeError("predictions must be a tuple")
    if not predictions:
        raise ValueError("predictions must contain at least one item")
    if any(not isinstance(prediction, MethodPrediction) for prediction in predictions):
        raise TypeError("predictions must contain only MethodPrediction records")
    case_ids = [prediction.case_id for prediction in predictions]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case_id in predictions")
    methods = {(prediction.method_name, prediction.method_version) for prediction in predictions}
    if len(methods) != 1:
        raise ValueError("mixed method name/version in predictions")
    return next(iter(methods))


def _summarize(
    predictions: tuple[MethodPrediction, ...],
    oracle_decisions: Mapping[str, AdmissionDecision],
    method_name: str,
    method_version: str,
    *,
    group_summaries: Mapping[str, EvaluationSummary] | None = None,
    family_summaries: Mapping[str, EvaluationSummary] | None = None,
) -> EvaluationSummary:
    n = len(predictions)
    admit_count = sum(p.decision is AdmissionDecision.ADMIT for p in predictions)
    review_count = sum(p.decision is AdmissionDecision.REVIEW for p in predictions)
    reject_count = sum(p.decision is AdmissionDecision.REJECT for p in predictions)
    false_admissions = sum(
        p.decision is AdmissionDecision.ADMIT
        and oracle_decisions[p.case_id] is not AdmissionDecision.ADMIT
        for p in predictions
    )
    missed_as_review = sum(
        oracle_decisions[p.case_id] is AdmissionDecision.ADMIT
        and p.decision is AdmissionDecision.REVIEW
        for p in predictions
    )
    missed_as_reject = sum(
        oracle_decisions[p.case_id] is AdmissionDecision.ADMIT
        and p.decision is AdmissionDecision.REJECT
        for p in predictions
    )
    correct = sum(
        p.decision is oracle_decisions[p.case_id]
        for p in predictions
    )
    return EvaluationSummary(
        method_name=method_name,
        method_version=method_version,
        n=n,
        admit_count=admit_count,
        review_count=review_count,
        reject_count=reject_count,
        coverage=admit_count / n,
        false_admissions=false_admissions,
        admission_risk=false_admissions / admit_count if admit_count else None,
        missed_admissions=missed_as_review + missed_as_reject,
        missed_as_review=missed_as_review,
        missed_as_reject=missed_as_reject,
        decision_accuracy=correct / n,
        group_summaries=group_summaries or {},
        family_summaries=family_summaries or {},
    )


def _stratify(
    predictions: tuple[MethodPrediction, ...],
    oracle_decisions: Mapping[str, AdmissionDecision],
    assignments: Mapping[str, str] | None,
    field_name: str,
) -> dict[str, EvaluationSummary]:
    if assignments is None:
        return {}
    if not isinstance(assignments, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    case_ids = {prediction.case_id for prediction in predictions}
    if set(assignments) != case_ids:
        raise ValueError(f"{field_name} must map every and only evaluated case")
    if any(not isinstance(value, str) or not value.strip() for value in assignments.values()):
        raise ValueError(f"{field_name} values must be non-empty strings")

    method_name, method_version = _validate_prediction_batch(predictions)
    strata: dict[str, list[MethodPrediction]] = {}
    for prediction in predictions:
        strata.setdefault(assignments[prediction.case_id], []).append(prediction)
    return {
        name: _summarize(
            tuple(items),
            oracle_decisions,
            method_name,
            method_version,
        )
        for name, items in sorted(strata.items())
    }


def _validate_oracle_decisions(
    predictions: tuple[MethodPrediction, ...],
    oracle_decisions: Mapping[str, AdmissionDecision],
) -> None:
    if not isinstance(oracle_decisions, Mapping):
        raise TypeError("oracle_decisions must be a mapping")
    if any(not isinstance(case_id, str) or not case_id.strip() for case_id in oracle_decisions):
        raise TypeError("oracle_decisions keys must be non-empty strings")
    if any(
        not isinstance(decision, AdmissionDecision)
        for decision in oracle_decisions.values()
    ):
        raise TypeError("oracle_decisions values must be AdmissionDecision members")
    case_ids = {prediction.case_id for prediction in predictions}
    if set(oracle_decisions) != case_ids:
        raise ValueError("oracle_decisions must map every and only evaluated case")


def _tie_break(seed: str, case_id: str) -> str:
    return hashlib.sha256(f"{seed}|{case_id}".encode("utf-8")).hexdigest()
