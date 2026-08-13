import hashlib

import pytest

from memoryrush.admission import (
    AdmissionDecision,
    MethodPrediction,
    evaluate_predictions,
    matched_admission_evaluation,
)


def _prediction(
    case_id: str,
    decision: AdmissionDecision,
    *,
    method_name: str = "joint-admission",
    method_version: str = "provisional-v1",
    admission_score: float = 0.5,
) -> MethodPrediction:
    return MethodPrediction(
        case_id=case_id,
        method_name=method_name,
        method_version=method_version,
        decision=decision,
        reason_codes=("fixture",),
        admission_score=admission_score,
        score_source="deterministic fixture ranking; not an objective probability",
    )


def test_method_prediction_accepts_a_strict_valid_record_without_oracle_data() -> None:
    prediction = _prediction(
        "case-001",
        AdmissionDecision.ADMIT,
        admission_score=0.75,
    )

    assert prediction.case_id == "case-001"
    assert prediction.admission_score == 0.75
    assert not hasattr(prediction, "oracle_decision")


@pytest.mark.parametrize("field_name", ["case_id", "method_name", "method_version", "score_source"])
def test_method_prediction_rejects_missing_text_fields(field_name: str) -> None:
    fields = {
        "case_id": "case-001",
        "method_name": "joint-admission",
        "method_version": "provisional-v1",
        "decision": AdmissionDecision.ADMIT,
        "reason_codes": ("fixture",),
        "admission_score": 0.5,
        "score_source": "fixture ranking",
    }
    fields[field_name] = "   "

    with pytest.raises(ValueError, match=field_name):
        MethodPrediction(**fields)  # type: ignore[arg-type]


def test_method_prediction_requires_a_decision_enum() -> None:
    with pytest.raises(TypeError, match="decision"):
        MethodPrediction(
            case_id="case-001",
            method_name="joint-admission",
            method_version="provisional-v1",
            decision="ADMIT",  # type: ignore[arg-type]
            reason_codes=("fixture",),
            admission_score=0.5,
            score_source="fixture ranking",
        )


@pytest.mark.parametrize(
    "reason_codes",
    [
        ["fixture"],
        ("",),
        (1,),
    ],
)
def test_method_prediction_strictly_validates_reason_code_tuple(reason_codes: object) -> None:
    with pytest.raises((TypeError, ValueError), match="reason_codes"):
        MethodPrediction(
            case_id="case-001",
            method_name="joint-admission",
            method_version="provisional-v1",
            decision=AdmissionDecision.ADMIT,
            reason_codes=reason_codes,  # type: ignore[arg-type]
            admission_score=0.5,
            score_source="fixture ranking",
        )


@pytest.mark.parametrize(
    "score",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        -0.01,
        1.01,
        True,
        1,
    ],
)
def test_method_prediction_rejects_invalid_admission_scores(score: object) -> None:
    with pytest.raises((TypeError, ValueError), match="admission_score"):
        MethodPrediction(
            case_id="case-001",
            method_name="joint-admission",
            method_version="provisional-v1",
            decision=AdmissionDecision.ADMIT,
            reason_codes=(),
            admission_score=score,  # type: ignore[arg-type]
            score_source="fixture ranking",
        )


def test_evaluation_summary_reports_descriptive_decision_and_risk_metrics() -> None:
    predictions = (
        _prediction("correct-admit", AdmissionDecision.ADMIT),
        _prediction("false-admit", AdmissionDecision.ADMIT),
        _prediction("missed-review", AdmissionDecision.REVIEW),
        _prediction("missed-reject", AdmissionDecision.REJECT),
        _prediction("correct-reject", AdmissionDecision.REJECT),
        _prediction("correct-review", AdmissionDecision.REVIEW),
    )
    oracle_decisions = {
        "correct-admit": AdmissionDecision.ADMIT,
        "false-admit": AdmissionDecision.REJECT,
        "missed-review": AdmissionDecision.ADMIT,
        "missed-reject": AdmissionDecision.ADMIT,
        "correct-reject": AdmissionDecision.REJECT,
        "correct-review": AdmissionDecision.REVIEW,
    }

    summary = evaluate_predictions(predictions, oracle_decisions)

    assert summary.n == 6
    assert summary.admit_count == 2
    assert summary.review_count == 2
    assert summary.reject_count == 2
    assert summary.coverage == pytest.approx(1 / 3)
    assert summary.false_admissions == 1
    assert summary.admission_risk == pytest.approx(0.5)
    assert summary.missed_admissions == 2
    assert summary.missed_as_review == 1
    assert summary.missed_as_reject == 1
    assert summary.decision_accuracy == pytest.approx(0.5)


def test_evaluation_summary_reports_none_risk_when_nothing_is_admitted() -> None:
    predictions = (
        _prediction("review", AdmissionDecision.REVIEW),
        _prediction("reject", AdmissionDecision.REJECT),
    )

    summary = evaluate_predictions(
        predictions,
        {
            "review": AdmissionDecision.ADMIT,
            "reject": AdmissionDecision.REJECT,
        },
    )

    assert summary.coverage == 0.0
    assert summary.false_admissions == 0
    assert summary.admission_risk is None


def test_evaluate_predictions_rejects_empty_or_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="at least one"):
        evaluate_predictions((), {})

    duplicate = _prediction("same", AdmissionDecision.ADMIT)
    with pytest.raises(ValueError, match="duplicate case_id"):
        evaluate_predictions(
            (duplicate, duplicate),
            {"same": AdmissionDecision.ADMIT},
        )


@pytest.mark.parametrize(
    ("method_name", "method_version"),
    [("other-method", "provisional-v1"), ("joint-admission", "provisional-v2")],
)
def test_evaluate_predictions_rejects_mixed_methods(
    method_name: str,
    method_version: str,
) -> None:
    with pytest.raises(ValueError, match="mixed method"):
        evaluate_predictions(
            (
                _prediction("case-001", AdmissionDecision.ADMIT),
                _prediction(
                    "case-002",
                    AdmissionDecision.ADMIT,
                    method_name=method_name,
                    method_version=method_version,
                ),
            ),
            {
                "case-001": AdmissionDecision.ADMIT,
                "case-002": AdmissionDecision.ADMIT,
            },
        )


@pytest.mark.parametrize(
    "oracle_decisions",
    [
        {"a": AdmissionDecision.ADMIT},
        {
            "a": AdmissionDecision.ADMIT,
            "b": AdmissionDecision.REJECT,
            "unknown": AdmissionDecision.REVIEW,
        },
        {"a": AdmissionDecision.ADMIT, "b": "REJECT"},
    ],
)
def test_evaluate_predictions_fails_closed_on_invalid_oracle_mapping(
    oracle_decisions: dict[str, object],
) -> None:
    predictions = (
        _prediction("a", AdmissionDecision.ADMIT),
        _prediction("b", AdmissionDecision.REJECT),
    )

    with pytest.raises((TypeError, ValueError), match="oracle_decisions"):
        evaluate_predictions(
            predictions,
            oracle_decisions,  # type: ignore[arg-type]
        )


def test_optional_group_and_family_mappings_produce_stratified_summaries() -> None:
    predictions = (
        _prediction("a", AdmissionDecision.ADMIT),
        _prediction("b", AdmissionDecision.REJECT),
        _prediction("c", AdmissionDecision.ADMIT),
    )
    oracle_decisions = {
        "a": AdmissionDecision.REJECT,
        "b": AdmissionDecision.REJECT,
        "c": AdmissionDecision.ADMIT,
    }

    summary = evaluate_predictions(
        predictions,
        oracle_decisions,
        case_groups={"a": "perturbed", "b": "perturbed", "c": "natural"},
        case_families={"a": "modality", "b": "modality", "c": "copy"},
    )

    assert summary.group_summaries["perturbed"].n == 2
    assert summary.group_summaries["perturbed"].admission_risk == 1.0
    assert summary.group_summaries["natural"].admission_risk == 0.0
    assert summary.family_summaries["modality"].false_admissions == 1
    assert summary.family_summaries["copy"].decision_accuracy == 1.0


@pytest.mark.parametrize(
    "case_groups",
    [
        {"a": "group-a"},
        {"a": "group-a", "b": "group-b", "unknown": "group-c"},
        {"a": "group-a", "b": "   "},
    ],
)
def test_stratified_evaluation_fails_closed_on_invalid_case_mapping(
    case_groups: dict[str, str],
) -> None:
    predictions = (
        _prediction("a", AdmissionDecision.ADMIT),
        _prediction("b", AdmissionDecision.REJECT),
    )
    oracle_decisions = {
        "a": AdmissionDecision.ADMIT,
        "b": AdmissionDecision.REJECT,
    }

    with pytest.raises((TypeError, ValueError), match="case_groups"):
        evaluate_predictions(
            predictions,
            oracle_decisions,
            case_groups=case_groups,
        )


def test_matched_admission_uses_explicit_count_scores_and_hash_tie_break() -> None:
    seed = "seed-17"
    tied_ids = ("a", "b", "c")
    expected_tied = tuple(
        sorted(
            tied_ids,
            key=lambda case_id: hashlib.sha256(f"{seed}|{case_id}".encode()).hexdigest(),
        )[:2]
    )
    method_a = tuple(
        _prediction(
            case_id,
            AdmissionDecision.ADMIT,
            admission_score=0.8,
        )
        for case_id in tied_ids
    )
    method_b = (
        _prediction(
            "a",
            AdmissionDecision.ADMIT,
            method_name="exact-copy",
            admission_score=0.9,
        ),
        _prediction(
            "b",
            AdmissionDecision.ADMIT,
            method_name="exact-copy",
            admission_score=0.7,
        ),
        _prediction(
            "c",
            AdmissionDecision.REVIEW,
            method_name="exact-copy",
            admission_score=1.0,
        ),
    )
    oracle_decisions = {
        "a": AdmissionDecision.ADMIT,
        "b": AdmissionDecision.REJECT,
        "c": AdmissionDecision.ADMIT,
    }

    matched = matched_admission_evaluation(
        {"joint": method_a, "copy": method_b},
        oracle_decisions,
        target_count=2,
        seed=seed,
    )

    assert matched["joint"].selected_case_ids == expected_tied
    assert matched["copy"].selected_case_ids == ("a", "b")
    assert matched["copy"].false_admissions == 1
    assert matched["copy"].admission_risk == pytest.approx(0.5)


def test_matched_admission_rejects_nonpositive_target_and_insufficient_pool() -> None:
    predictions = (
        _prediction("only-admit", AdmissionDecision.ADMIT),
        _prediction("review", AdmissionDecision.REVIEW),
    )
    oracle_decisions = {
        "only-admit": AdmissionDecision.ADMIT,
        "review": AdmissionDecision.ADMIT,
    }

    with pytest.raises(ValueError, match="target_count"):
        matched_admission_evaluation(
            {"joint": predictions},
            oracle_decisions,
            target_count=0,
            seed="seed",
        )
    with pytest.raises(ValueError, match="insufficient ADMIT pool"):
        matched_admission_evaluation(
            {"joint": predictions},
            oracle_decisions,
            target_count=2,
            seed="seed",
        )


def test_matched_admission_requires_identical_case_universes() -> None:
    method_a = (
        _prediction("a", AdmissionDecision.ADMIT),
        _prediction("b", AdmissionDecision.ADMIT),
    )
    method_b = (
        _prediction("a", AdmissionDecision.ADMIT, method_name="copy"),
        _prediction("c", AdmissionDecision.ADMIT, method_name="copy"),
    )

    with pytest.raises(ValueError, match="identical case_id universe"):
        matched_admission_evaluation(
            {"joint": method_a, "copy": method_b},
            {
                "a": AdmissionDecision.ADMIT,
                "b": AdmissionDecision.REJECT,
            },
            target_count=1,
            seed="seed",
        )


@pytest.mark.parametrize(
    "oracle_decisions",
    [
        {"a": AdmissionDecision.ADMIT},
        {
            "a": AdmissionDecision.ADMIT,
            "b": AdmissionDecision.REJECT,
            "unknown": AdmissionDecision.REVIEW,
        },
        {"a": AdmissionDecision.ADMIT, "b": "REJECT"},
    ],
)
def test_matched_admission_fails_closed_on_invalid_common_oracle_mapping(
    oracle_decisions: dict[str, object],
) -> None:
    method_a = (
        _prediction("a", AdmissionDecision.ADMIT),
        _prediction("b", AdmissionDecision.ADMIT),
    )
    method_b = (
        _prediction("a", AdmissionDecision.ADMIT, method_name="copy"),
        _prediction("b", AdmissionDecision.ADMIT, method_name="copy"),
    )

    with pytest.raises((TypeError, ValueError), match="oracle_decisions"):
        matched_admission_evaluation(
            {"joint": method_a, "copy": method_b},
            oracle_decisions,  # type: ignore[arg-type]
            target_count=1,
            seed="seed",
        )


def test_evaluator_documentation_states_provisional_limits() -> None:
    assert "not an objective probability" in MethodPrediction.__doc__
    assert "descriptive" in evaluate_predictions.__doc__
    assert "does not establish fairness" in matched_admission_evaluation.__doc__
    assert "not an objective probability" in matched_admission_evaluation.__doc__
    assert "fixed-count" in matched_admission_evaluation.__doc__


def test_evaluation_summary_strata_are_immutable_snapshots() -> None:
    predictions = (_prediction("a", AdmissionDecision.ADMIT),)
    groups = {"a": "natural"}
    summary = evaluate_predictions(
        predictions,
        {"a": AdmissionDecision.ADMIT},
        case_groups=groups,
    )

    groups["a"] = "mutated-after-evaluation"
    assert tuple(summary.group_summaries) == ("natural",)
    with pytest.raises(TypeError):
        summary.group_summaries["new"] = summary  # type: ignore[index]
