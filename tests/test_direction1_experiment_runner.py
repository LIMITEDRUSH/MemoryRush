from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from memoryrush.admission import AdmissionDecision
from memoryrush.admission.benchmark import parse_benchmark_case
from memoryrush.admission.experiment_runner import (
    CURRENT_ID_ONLY,
    EXACT_COPY,
    ID_ONLY_PROXY,
    STATIC_ORACLE_UPPER_BOUND,
    ArtifactValidationStatus,
    ExperimentConfig,
    FrozenBenchmark,
    RunClass,
    artifact_to_dict,
    load_frozen_benchmark,
    run_direction1_experiment,
    run_method_predictions,
    write_experiment_artifact,
)


def _case_payload(case_id: str, *, supported: bool) -> dict[str, object]:
    if supported:
        paragraph = "The trial may finish in 2025."
        claim = paragraph
        decision = "ADMIT"
        label = "supports"
        supported_qualifiers = [
            {"kind": "modality", "value": "may"},
            {"kind": "time", "value": "2025"},
        ]
        minimal_sets = [[f"{case_id}-span"]]
    else:
        paragraph = "The trial ended in 2024."
        claim = "The trial may finish in 2025."
        decision = "REJECT"
        label = "insufficient"
        supported_qualifiers = []
        minimal_sets = []
    document_hash = sha256(paragraph.encode("utf-8")).hexdigest()
    return {
        "schema_version": "direction1.synthetic_oracle.v0.1",
        "case_id": case_id,
        "case_family": "F01 supported" if supported else "F02 unsupported",
        "document": {
            "document_id": f"{case_id}-doc",
            "title": "Tiny public synthetic fixture",
            "snapshot_text": paragraph,
            "source_sha256": document_hash,
            "paragraphs": [
                {
                    "paragraph_id": f"{case_id}-p",
                    "text": paragraph,
                    "snapshot_start": 0,
                    "snapshot_end": len(paragraph),
                }
            ],
        },
        "candidate": {
            "candidate_id": f"{case_id}-candidate",
            "proposition": claim,
            "atomic_claims": [
                {
                    "claim_id": f"{case_id}-claim",
                    "text": claim,
                    "qualifiers": [
                        {"kind": "modality", "value": "may"},
                        {"kind": "time", "value": "2025"},
                    ],
                    "required_support_parts": [],
                }
            ],
        },
        "evidence_spans": [
            {
                "span_id": f"{case_id}-span",
                "paragraph_id": f"{case_id}-p",
                "start_char": 0,
                "end_char": len(paragraph),
                "text": paragraph,
            }
        ],
        "oracle": {
            "decision": decision,
            "reason_codes": ["tiny_fixture"],
            "minimal_evidence_sets": minimal_sets,
            "claim_form": {
                "self_sufficiency": "PASS",
                "minimality": "PASS",
                "reason_codes": ["synthetic_control"],
                "auditor_name": "programmatic_fixture",
                "auditor_version": "v0.1",
            },
            "support_cells": [
                {
                    "claim_id": f"{case_id}-claim",
                    "span_id": f"{case_id}-span",
                    "label": label,
                    "rationale": "Tiny deterministic fixture annotation.",
                    "supported_qualifiers": supported_qualifiers,
                    "supported_claim_parts": [],
                }
            ],
            "label_source": "llm_generated",
            "adjudication_status": "provisional",
        },
        "provenance": {
            "construction": "project_authored_synthetic",
            "base_case_id": None,
            "perturbation_operator": None,
            "generator": "test_fixture",
            "generator_type": "llm_or_agent",
        },
    }


def _write_tiny_benchmark(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "tiny_direction1.jsonl"
    text = "\n".join(
        json.dumps(_case_payload(case_id, supported=supported), sort_keys=True)
        for case_id, supported in (("supported", True), ("unsupported", False))
    ) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path, sha256(text.encode("utf-8")).hexdigest()


def _config(benchmark_hash: str) -> ExperimentConfig:
    return ExperimentConfig(
        run_id="tiny-debug-run",
        run_class=RunClass.DEBUGGING,
        benchmark_sha256=benchmark_hash,
        seed="fixed-seed",
        methods=(CURRENT_ID_ONLY, EXACT_COPY, STATIC_ORACLE_UPPER_BOUND),
        prompt_version="deterministic-no-prompt-v1",
        config_version="direction1-runner-v0.1",
    )


def test_config_is_strictly_typed_and_run_class_is_explicit() -> None:
    digest = "a" * 64
    valid = _config(digest)
    assert valid.run_class is RunClass.DEBUGGING

    with pytest.raises(TypeError, match="run_class"):
        replace(valid, run_class="CONFIRMATORY")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="methods"):
        replace(valid, methods=[CURRENT_ID_ONLY])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="methods"):
        replace(valid, methods=(CURRENT_ID_ONLY, CURRENT_ID_ONLY))
    with pytest.raises(ValueError, match="benchmark_sha256"):
        replace(valid, benchmark_sha256="not-a-digest")
    with pytest.raises(ValueError, match="prompt_version"):
        replace(valid, prompt_version=" ")
    for unsupported_class in (
        RunClass.EXPLORATORY,
        RunClass.CONFIRMATORY,
        RunClass.INVALID_RUN,
    ):
        with pytest.raises(ValueError, match="only supports DEBUGGING"):
            replace(valid, run_class=unsupported_class)


def test_frozen_loader_binds_external_path_hash_and_cases(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)

    frozen = load_frozen_benchmark(path, digest)

    assert frozen.benchmark_path == str(path.resolve())
    assert frozen.benchmark_sha256 == digest
    assert frozen.benchmark_byte_size == path.stat().st_size
    assert tuple(case.case_id for case in frozen.cases) == ("supported", "unsupported")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_frozen_benchmark(path, "0" * 64)


def test_frozen_benchmark_contract_is_strict(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    valid = load_frozen_benchmark(path, digest)

    with pytest.raises(TypeError, match="cases"):
        replace(valid, cases=list(valid.cases))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="benchmark_byte_size"):
        replace(valid, benchmark_byte_size=0)
    with pytest.raises(ValueError, match="absolute"):
        FrozenBenchmark(
            benchmark_path="relative.jsonl",
            benchmark_sha256=digest,
            benchmark_byte_size=1,
            cases=valid.cases,
        )


class _OracleTrapCase:
    def __init__(self, source_case: object) -> None:
        self.case_id = source_case.case_id
        self.candidate = source_case.candidate
        self.evidence_spans = source_case.evidence_spans

    @property
    def oracle(self) -> object:
        raise AssertionError("baseline adapter accessed oracle data")


@pytest.mark.parametrize("method_name", [CURRENT_ID_ONLY, EXACT_COPY])
def test_nonoracle_baselines_cannot_read_oracle_fields(method_name: str) -> None:
    case = parse_benchmark_case(_case_payload("supported", supported=True))
    guarded_case = _OracleTrapCase(case)

    predictions = run_method_predictions(
        method_name,
        (guarded_case,),  # type: ignore[arg-type]
    )

    assert predictions[0].decision is AdmissionDecision.ADMIT
    assert not hasattr(predictions[0], "oracle_decision")


def test_method_adapters_have_declared_deterministic_behavior(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    cases = load_frozen_benchmark(path, digest).cases

    id_only = run_method_predictions(CURRENT_ID_ONLY, cases)
    exact_copy = run_method_predictions(EXACT_COPY, cases)
    oracle_upper = run_method_predictions(STATIC_ORACLE_UPPER_BOUND, cases)

    assert tuple(p.decision for p in id_only) == (
        AdmissionDecision.ADMIT,
        AdmissionDecision.ADMIT,
    )
    assert all(p.admission_score == 1.0 for p in id_only)
    assert ID_ONLY_PROXY == "id_only_support_proxy"
    assert id_only[0].method_name == "id_only_support_proxy"
    assert "structural false-positive" in id_only[0].score_source
    assert "support-validator blind-spot simulation" in id_only[0].score_source
    assert "not a complete production pipeline" in id_only[0].score_source
    assert tuple(p.decision for p in exact_copy) == (
        AdmissionDecision.ADMIT,
        AdmissionDecision.REJECT,
    )
    assert exact_copy[0].reason_codes[-1] == "baseline_assumes_candidate_form"
    assert tuple(p.admission_score for p in exact_copy) == (1.0, 0.0)
    assert tuple(p.decision for p in oracle_upper) == (
        AdmissionDecision.ADMIT,
        AdmissionDecision.REJECT,
    )


def test_static_oracle_upper_bound_fails_if_recomputed_decision_disagrees() -> None:
    case = parse_benchmark_case(_case_payload("supported", supported=True))
    inconsistent_oracle = replace(case.oracle, decision=AdmissionDecision.REJECT)
    inconsistent_case = replace(case, oracle=inconsistent_oracle)

    with pytest.raises(ValueError, match="static oracle.*does not match"):
        run_method_predictions(STATIC_ORACLE_UPPER_BOUND, (inconsistent_case,))


def test_runner_joins_oracle_internally_and_records_provenance(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    frozen = load_frozen_benchmark(path, digest)

    artifact = run_direction1_experiment(
        frozen,
        _config(digest),
        git_head="a" * 40,
        git_dirty=False,
        started_at=datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 8, 14, 12, 1, tzinfo=timezone.utc),
    )

    assert artifact.started_at == "2026-08-14T12:00:00+00:00"
    assert artifact.ended_at == "2026-08-14T12:01:00+00:00"
    assert artifact.timezone == "UTC"
    assert artifact.git_head == "a" * 40
    assert artifact.git_dirty is False
    assert artifact.benchmark_path == str(path.resolve())
    assert artifact.benchmark_sha256 == digest
    assert artifact.benchmark_byte_size == path.stat().st_size
    assert artifact.benchmark_schema_version == "direction1.synthetic_oracle.v0.1"
    assert artifact.case_count == 2
    assert artifact.provenance_counts["generator_type"] == {"llm_or_agent": 2}
    assert len(artifact.oracle_mapping_sha256) == 64
    assert artifact.matched_admission is None
    assert artifact.validation_status is ArtifactValidationStatus.VALIDATED
    assert artifact.exit_code == 0
    assert artifact.failures == ()
    assert artifact.provenance_strata_fields == (
        "label_source",
        "adjudication_status",
        "generator_type",
    )
    expected_stratum = (
        "label_source=llm_generated|"
        "adjudication_status=provisional|generator_type=llm_or_agent"
    )
    assert artifact.provenance_strata_counts == {expected_stratum: 2}

    id_result = artifact.method_results[CURRENT_ID_ONLY]
    assert id_result.native_coverage == 1.0
    assert id_result.native_admission_risk == 0.5
    assert id_result.summary.false_admissions == 1
    assert id_result.summary.group_summaries[expected_stratum].n == 2
    assert set(id_result.summary.family_summaries) == {"F01", "F02"}
    serialized_predictions = artifact_to_dict(artifact)["method_results"][
        CURRENT_ID_ONLY
    ]["predictions"]
    assert all("oracle" not in prediction for prediction in serialized_predictions)


def test_runner_fails_if_any_method_prediction_universe_differs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import memoryrush.admission.experiment_runner as runner

    path, digest = _write_tiny_benchmark(tmp_path)
    frozen = load_frozen_benchmark(path, digest)
    original = runner.run_method_predictions

    def incomplete(method_name: str, cases: tuple[object, ...]):
        predictions = original(method_name, cases)
        return predictions[:-1] if method_name == EXACT_COPY else predictions

    monkeypatch.setattr(runner, "run_method_predictions", incomplete)

    with pytest.raises(ValueError, match="same case universe"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
        )


def test_matched_evaluation_is_opt_in_and_insufficient_target_fails(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    frozen = load_frozen_benchmark(path, digest)

    matched = run_direction1_experiment(
        frozen,
        _config(digest),
        git_head="a" * 40,
        git_dirty=False,
        matched_target=1,
    )
    assert matched.matched_admission is not None
    assert set(matched.matched_admission) == set(_config(digest).methods)

    with pytest.raises(ValueError, match="insufficient ADMIT pool"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
            matched_target=2,
        )


def test_runner_reloads_path_and_rejects_forged_or_changed_frozen_state(
    tmp_path: Path,
) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    frozen = load_frozen_benchmark(path, digest)
    forged = replace(frozen, cases=frozen.cases[:1])

    with pytest.raises(ValueError, match="frozen benchmark cases"):
        run_direction1_experiment(
            forged,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
        )

    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
        )


def test_runner_rejects_case_family_without_strict_family_id(tmp_path: Path) -> None:
    path = tmp_path / "invalid-family.jsonl"
    payloads = (
        _case_payload("supported", supported=True),
        _case_payload("unsupported", supported=False),
    )
    payloads[0]["case_family"] = "supported"
    text = "\n".join(json.dumps(payload, sort_keys=True) for payload in payloads) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    digest = sha256(text.encode("utf-8")).hexdigest()
    frozen = load_frozen_benchmark(path, digest)

    with pytest.raises(ValueError, match="case_family.*F\\d{2}"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
        )


def test_runner_rejects_invalid_git_dirty_and_naive_timestamps(tmp_path: Path) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    frozen = load_frozen_benchmark(path, digest)

    with pytest.raises(TypeError, match="git_dirty"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="git_head"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="not-a-commit",
            git_dirty=False,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        run_direction1_experiment(
            frozen,
            _config(digest),
            git_head="a" * 40,
            git_dirty=False,
            started_at=datetime(2026, 8, 14, 12, 0),
        )


def test_canonical_writer_is_utf8_lf_roundtrippable_and_rejects_nan(
    tmp_path: Path,
) -> None:
    path, digest = _write_tiny_benchmark(tmp_path)
    artifact = run_direction1_experiment(
        load_frozen_benchmark(path, digest),
        _config(digest),
        git_head="a" * 40,
        git_dirty=False,
        started_at=datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 8, 14, 12, 1, tzinfo=timezone.utc),
    )
    output = tmp_path / "results" / "artifact.json"
    output.parent.mkdir()

    write_experiment_artifact(output, artifact)

    raw = output.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    decoded = json.loads(raw.decode("utf-8"))
    assert decoded == artifact_to_dict(artifact)
    assert list(decoded) == sorted(decoded)
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))

    method_results = dict(artifact.method_results)
    method_results[CURRENT_ID_ONLY] = replace(
        method_results[CURRENT_ID_ONLY],
        native_coverage=float("nan"),
    )
    invalid_artifact = replace(artifact, method_results=method_results)
    with pytest.raises(ValueError, match="finite|NaN"):
        write_experiment_artifact(output, invalid_artifact)


def test_cli_check_input_only_validates_without_running_methods(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.evaluate_direction1_admission as cli

    path, digest = _write_tiny_benchmark(tmp_path)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("input-only check ran a method")

    monkeypatch.setattr(cli, "run_direction1_experiment", forbidden)
    exit_code = cli.main(
        [
            str(path),
            "--benchmark-sha256",
            digest,
            "--run-id",
            "check-only",
            "--run-class",
            "DEBUGGING",
            "--methods",
            CURRENT_ID_ONLY,
            EXACT_COPY,
            "--check-input-only",
        ]
    )

    response = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert response["valid"] is True
    assert response["mode"] == "check-input-only"
    assert response["case_count"] == 2


def test_cli_requires_explicit_run_class(tmp_path: Path) -> None:
    import scripts.evaluate_direction1_admission as cli

    path, digest = _write_tiny_benchmark(tmp_path)
    with pytest.raises(SystemExit):
        cli.main(
            [
                str(path),
                "--benchmark-sha256",
                digest,
                "--run-id",
                "missing-class",
                "--check-input-only",
            ]
        )


def test_cli_writes_explicit_invalid_run_artifact_on_caught_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.evaluate_direction1_admission as cli

    path, digest = _write_tiny_benchmark(tmp_path)
    output = tmp_path / "missing" / "nested" / "invalid-run.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(cli, "read_git_state", lambda _: ("a" * 40, False))

    try:
        exit_code = cli.main(
            [
                str(path),
                "--benchmark-sha256",
                "0" * 64,
                "--run-id",
                "invalid-hash-run",
                "--run-class",
                "DEBUGGING",
                "--methods",
                ID_ONLY_PROXY,
                "--output",
                str(output),
                "--git-head",
                "a" * 40,
                "--git-dirty",
                "false",
            ]
        )
    finally:
        monkeypatch.undo()

    response = json.loads(capsys.readouterr().out)
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert response["valid"] is False
    assert response["invalid_artifact_written"] is True
    assert artifact["run_class"] == "INVALID_RUN"
    assert artifact["validation_status"] == "INVALID_RUN"
    assert artifact["exit_code"] == 1
    assert artifact["failures"]
    assert artifact["benchmark_sha256"] == "0" * 64


def test_cli_rejects_injected_git_provenance_that_disagrees_with_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.evaluate_direction1_admission as cli

    path, digest = _write_tiny_benchmark(tmp_path)
    output = tmp_path / "invalid-git.json"
    monkeypatch.setattr(cli, "read_git_state", lambda _: ("b" * 40, True))

    exit_code = cli.main(
        [
            str(path),
            "--benchmark-sha256",
            digest,
            "--run-id",
            "forged-git",
            "--run-class",
            "DEBUGGING",
            "--methods",
            ID_ONLY_PROXY,
            "--output",
            str(output),
            "--git-head",
            "a" * 40,
            "--git-dirty",
            "false",
        ]
    )

    response = json.loads(capsys.readouterr().out)
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "git-head does not match" in response["error"]
    assert artifact["validation_status"] == "INVALID_RUN"
