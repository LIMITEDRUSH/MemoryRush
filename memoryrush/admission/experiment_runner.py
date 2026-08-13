"""Deterministic provisional runner for the frozen Direction 1 benchmark."""

from __future__ import annotations

import json
import math
import os
import platform
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from memoryrush.admission.benchmark import BenchmarkCase, load_benchmark
from memoryrush.admission.decision import ConservativeDecisionPolicy, evaluate_admission
from memoryrush.admission.evaluation import (
    EvaluationSummary,
    MatchedAdmissionResult,
    MethodPrediction,
    evaluate_predictions,
    matched_admission_evaluation,
)
from memoryrush.admission.models import (
    AdmissionDecision,
    ClaimFormAudit,
    ClaimFormStatus,
)
from memoryrush.admission.solver import InclusionMinimalSolver
from memoryrush.admission.verifiers import ExactCopyVerifier, StaticOracleVerifier


ID_ONLY_PROXY = "id_only_support_proxy"
# Transitional Python import alias. Serialized artifacts always use ID_ONLY_PROXY.
CURRENT_ID_ONLY = ID_ONLY_PROXY
EXACT_COPY = "exact_copy"
STATIC_ORACLE_UPPER_BOUND = "static_oracle_upper_bound"
SUPPORTED_METHODS = (ID_ONLY_PROXY, EXACT_COPY, STATIC_ORACLE_UPPER_BOUND)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")


def _require_text(value: str, field_name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


class RunClass(str, Enum):
    """Declared epistemic status of an experiment run."""

    DEBUGGING = "DEBUGGING"
    EXPLORATORY = "EXPLORATORY"
    CONFIRMATORY = "CONFIRMATORY"
    INVALID_RUN = "INVALID_RUN"


class ArtifactValidationStatus(str, Enum):
    """Validation outcome recorded in an experiment artifact."""

    VALIDATED = "VALIDATED"
    INVALID_RUN = "INVALID_RUN"


@dataclass(frozen=True)
class ExperimentConfig:
    run_id: str
    run_class: RunClass
    benchmark_sha256: str
    seed: str
    methods: tuple[str, ...]
    prompt_version: str
    config_version: str

    def __post_init__(self) -> None:
        for field_name in ("run_id", "seed", "prompt_version", "config_version"):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.run_class, RunClass):
            raise TypeError("run_class must be a RunClass")
        if self.run_class is not RunClass.DEBUGGING:
            raise ValueError("provisional runner only supports DEBUGGING runs")
        if type(self.benchmark_sha256) is not str or not _SHA256_RE.fullmatch(
            self.benchmark_sha256
        ):
            raise ValueError("benchmark_sha256 must be a lowercase SHA-256 digest")
        if type(self.methods) is not tuple:
            raise TypeError("methods must be an exact tuple")
        if not self.methods:
            raise ValueError("methods must not be empty")
        if any(type(method) is not str for method in self.methods):
            raise TypeError("methods must contain strings")
        if len(self.methods) != len(set(self.methods)):
            raise ValueError("methods must not contain duplicates")
        unknown = set(self.methods) - set(SUPPORTED_METHODS)
        if unknown:
            raise ValueError(f"unsupported methods: {', '.join(sorted(unknown))}")


@dataclass(frozen=True)
class FrozenBenchmark:
    benchmark_path: str
    benchmark_sha256: str
    benchmark_byte_size: int
    cases: tuple[BenchmarkCase, ...]

    def __post_init__(self) -> None:
        _require_text(self.benchmark_path, "benchmark_path")
        if not Path(self.benchmark_path).is_absolute():
            raise ValueError("benchmark_path must be absolute")
        if not _SHA256_RE.fullmatch(self.benchmark_sha256):
            raise ValueError("benchmark_sha256 must be a lowercase SHA-256 digest")
        if type(self.benchmark_byte_size) is not int or self.benchmark_byte_size <= 0:
            raise ValueError("benchmark_byte_size must be a positive integer")
        if type(self.cases) is not tuple or any(
            not isinstance(case, BenchmarkCase) for case in self.cases
        ):
            raise TypeError("cases must be a tuple of BenchmarkCase values")
        if not self.cases:
            raise ValueError("cases must not be empty")


@dataclass(frozen=True)
class MethodExperimentResult:
    predictions: tuple[MethodPrediction, ...]
    summary: EvaluationSummary
    native_coverage: float
    native_admission_risk: float | None


@dataclass(frozen=True)
class ExperimentArtifact:
    artifact_schema_version: str
    run_id: str
    run_class: RunClass
    started_at: str
    ended_at: str
    timezone: str
    python_version: str
    platform: str
    git_head: str
    git_dirty: bool
    benchmark_path: str
    benchmark_sha256: str
    benchmark_byte_size: int
    benchmark_schema_version: str
    case_count: int
    provenance_counts: Mapping[str, Mapping[str, int]]
    provenance_strata_fields: tuple[str, ...]
    provenance_strata_counts: Mapping[str, int]
    oracle_mapping_sha256: str
    seed: str
    prompt_version: str
    config_version: str
    method_results: Mapping[str, MethodExperimentResult]
    matched_admission: Mapping[str, MatchedAdmissionResult] | None
    validation_status: ArtifactValidationStatus
    exit_code: int
    failures: tuple[str, ...]


@dataclass(frozen=True)
class InvalidExperimentArtifact:
    """Minimal failure artifact; it never represents a completed evaluation."""

    artifact_schema_version: str
    run_id: str
    run_class: RunClass
    started_at: str
    ended_at: str
    timezone: str
    python_version: str
    platform: str
    git_head: str
    git_dirty: bool
    benchmark_path: str
    benchmark_sha256: str
    benchmark_byte_size: int
    benchmark_schema_version: None
    case_count: None
    provenance_counts: Mapping[str, Mapping[str, int]]
    provenance_strata_fields: tuple[str, ...]
    provenance_strata_counts: Mapping[str, int]
    oracle_mapping_sha256: None
    seed: str
    prompt_version: str
    config_version: str
    method_results: Mapping[str, MethodExperimentResult]
    matched_admission: None
    validation_status: ArtifactValidationStatus
    exit_code: int
    failures: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.run_class is not RunClass.INVALID_RUN:
            raise ValueError("invalid artifact run_class must be INVALID_RUN")
        if self.validation_status is not ArtifactValidationStatus.INVALID_RUN:
            raise ValueError("invalid artifact validation_status must be INVALID_RUN")
        if self.exit_code == 0:
            raise ValueError("invalid artifact exit_code must be nonzero")
        if type(self.failures) is not tuple or not self.failures:
            raise ValueError("invalid artifact failures must be a non-empty tuple")
        if any(type(failure) is not str or not failure.strip() for failure in self.failures):
            raise ValueError("invalid artifact failures must contain non-empty strings")
        if type(self.git_dirty) is not bool:
            raise TypeError("invalid artifact git_dirty must be an exact bool")


def load_frozen_benchmark(
    benchmark_path: str | Path,
    expected_sha256: str,
) -> FrozenBenchmark:
    """Read, hash, and strictly load an externally identified benchmark file."""

    if type(expected_sha256) is not str or not _SHA256_RE.fullmatch(expected_sha256):
        raise ValueError("expected benchmark SHA-256 must be a lowercase digest")
    resolved = Path(benchmark_path).resolve()
    raw = resolved.read_bytes()
    actual = sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError(
            f"benchmark SHA-256 mismatch: expected {expected_sha256}, actual {actual}"
        )
    return FrozenBenchmark(
        benchmark_path=str(resolved),
        benchmark_sha256=actual,
        benchmark_byte_size=len(raw),
        cases=load_benchmark(resolved),
    )


def run_method_predictions(
    method_name: str,
    cases: tuple[BenchmarkCase, ...],
) -> tuple[MethodPrediction, ...]:
    """Run one deterministic method adapter over an already validated case tuple."""

    if method_name == ID_ONLY_PROXY:
        return tuple(_current_id_only_prediction(case) for case in cases)
    if method_name == EXACT_COPY:
        return tuple(_exact_copy_prediction(case) for case in cases)
    if method_name == STATIC_ORACLE_UPPER_BOUND:
        return tuple(_static_oracle_prediction(case) for case in cases)
    raise ValueError(f"unsupported method: {method_name}")


def _current_id_only_prediction(case: BenchmarkCase) -> MethodPrediction:
    """Simulate the current support-validator blind spot, not the full pipeline."""

    return MethodPrediction(
        case_id=case.case_id,
        method_name=ID_ONLY_PROXY,
        method_version="support-validator-proxy-v1",
        decision=AdmissionDecision.ADMIT,
        reason_codes=("structural_ids_present", "structural_false_positive_baseline"),
        admission_score=1.0,
        score_source=(
            "structural false-positive support-validator blind-spot simulation; "
            "not a complete production pipeline or a probability"
        ),
    )


def _exact_copy_prediction(case: BenchmarkCase) -> MethodPrediction:
    claim_form = ClaimFormAudit(
        self_sufficiency=ClaimFormStatus.PASS,
        minimality=ClaimFormStatus.PASS,
        reason_codes=("baseline_assumes_candidate_form",),
        auditor_name="fixed_nonoracle_baseline_assumption",
        auditor_version="v1",
    )
    result = evaluate_admission(
        candidate=case.candidate,
        evidence_spans=case.evidence_spans,
        verifier=ExactCopyVerifier(),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
        claim_form_audit=claim_form,
    )
    score = {
        AdmissionDecision.ADMIT: 1.0,
        AdmissionDecision.REVIEW: 0.5,
        AdmissionDecision.REJECT: 0.0,
    }[result.decision]
    return MethodPrediction(
        case_id=case.case_id,
        method_name=EXACT_COPY,
        method_version="normalized-copy-v1",
        decision=result.decision,
        reason_codes=(*result.reason_codes, "baseline_assumes_candidate_form"),
        admission_score=score,
        score_source="fixed decision rank ADMIT=1 REVIEW=0.5 REJECT=0; not a probability",
    )


def _static_oracle_prediction(case: BenchmarkCase) -> MethodPrediction:
    result = evaluate_admission(
        candidate=case.candidate,
        evidence_spans=case.evidence_spans,
        verifier=StaticOracleVerifier(case.oracle.support_cells),
        solver=InclusionMinimalSolver(),
        policy=ConservativeDecisionPolicy(),
        claim_form_audit=case.oracle.claim_form,
    )
    if result.decision is not case.oracle.decision:
        raise ValueError(
            f"static oracle recomputation does not match declared oracle for {case.case_id}"
        )
    score = {
        AdmissionDecision.ADMIT: 1.0,
        AdmissionDecision.REVIEW: 0.5,
        AdmissionDecision.REJECT: 0.0,
    }[result.decision]
    return MethodPrediction(
        case_id=case.case_id,
        method_name=STATIC_ORACLE_UPPER_BOUND,
        method_version="static-annotation-v1",
        decision=result.decision,
        reason_codes=result.reason_codes,
        admission_score=score,
        score_source="oracle-certificate upper-bound decision rank; not a probability",
    )


def run_direction1_experiment(
    frozen: FrozenBenchmark,
    config: ExperimentConfig,
    *,
    git_head: str,
    git_dirty: bool,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    matched_target: int | None = None,
) -> ExperimentArtifact:
    """Run selected deterministic adapters and join oracle labels only for evaluation."""

    if type(git_head) is not str or not _GIT_HEAD_RE.fullmatch(git_head):
        raise ValueError("git_head must be a lowercase 40-character commit digest")
    if type(git_dirty) is not bool:
        raise TypeError("git_dirty must be an exact bool")
    if frozen.benchmark_sha256 != config.benchmark_sha256:
        raise ValueError("config benchmark_sha256 does not match frozen benchmark")
    reloaded = load_frozen_benchmark(
        frozen.benchmark_path,
        config.benchmark_sha256,
    )
    if reloaded.benchmark_byte_size != frozen.benchmark_byte_size:
        raise ValueError("frozen benchmark byte size does not match reloaded file")
    if reloaded.cases != frozen.cases:
        raise ValueError("frozen benchmark cases do not match reloaded file")
    if matched_target is not None and (
        type(matched_target) is not int or matched_target <= 0
    ):
        raise ValueError("matched_target must be a positive integer or None")

    oracle = {case.case_id: case.oracle.decision for case in frozen.cases}
    families = {
        case.case_id: _family_id(case.case_family)
        for case in frozen.cases
    }
    strata_fields = ("label_source", "adjudication_status", "generator_type")
    provenance_strata = {
        case.case_id: (
            f"label_source={case.oracle.label_source}|"
            f"adjudication_status={case.oracle.adjudication_status}|"
            f"generator_type={case.provenance.generator_type}"
        )
        for case in frozen.cases
    }
    method_predictions: dict[str, tuple[MethodPrediction, ...]] = {}
    method_results: dict[str, MethodExperimentResult] = {}
    expected_case_ids = set(oracle)
    for method_name in config.methods:
        predictions = run_method_predictions(method_name, frozen.cases)
        if {prediction.case_id for prediction in predictions} != expected_case_ids:
            raise ValueError("all methods must return the same case universe")
        summary = evaluate_predictions(
            predictions,
            oracle,
            case_groups=provenance_strata,
            case_families=families,
        )
        method_predictions[method_name] = predictions
        method_results[method_name] = MethodExperimentResult(
            predictions=predictions,
            summary=summary,
            native_coverage=summary.coverage,
            native_admission_risk=summary.admission_risk,
        )

    matched = (
        matched_admission_evaluation(
            method_predictions,
            oracle,
            target_count=matched_target,
            seed=config.seed,
        )
        if matched_target is not None
        else None
    )
    start = started_at or datetime.now().astimezone()
    end = ended_at or datetime.now().astimezone()
    if (
        start.tzinfo is None
        or start.utcoffset() is None
        or end.tzinfo is None
        or end.utcoffset() is None
    ):
        raise ValueError("started_at and ended_at must be timezone-aware")
    if end < start:
        raise ValueError("ended_at must not precede started_at")
    schema_versions = {case.schema_version for case in frozen.cases}
    if len(schema_versions) != 1:
        raise ValueError("benchmark must contain exactly one schema version")
    return ExperimentArtifact(
        artifact_schema_version="direction1.experiment_artifact.v0.1",
        run_id=config.run_id,
        run_class=config.run_class,
        started_at=start.isoformat(),
        ended_at=end.isoformat(),
        timezone=str(start.tzinfo),
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        git_head=git_head,
        git_dirty=git_dirty,
        benchmark_path=frozen.benchmark_path,
        benchmark_sha256=frozen.benchmark_sha256,
        benchmark_byte_size=frozen.benchmark_byte_size,
        benchmark_schema_version=next(iter(schema_versions)),
        case_count=len(frozen.cases),
        provenance_counts=_provenance_counts(frozen.cases),
        provenance_strata_fields=strata_fields,
        provenance_strata_counts=MappingProxyType(
            dict(sorted(Counter(provenance_strata.values()).items()))
        ),
        oracle_mapping_sha256=_oracle_mapping_hash(oracle),
        seed=config.seed,
        prompt_version=config.prompt_version,
        config_version=config.config_version,
        method_results=MappingProxyType(method_results),
        matched_admission=MappingProxyType(matched) if matched is not None else None,
        validation_status=ArtifactValidationStatus.VALIDATED,
        exit_code=0,
        failures=(),
    )


def _family_id(case_family: str) -> str:
    token = case_family.split(maxsplit=1)[0]
    if re.fullmatch(r"F\d{2}", token) is None:
        raise ValueError(
            f"case_family {case_family!r} must start with family ID F00 matching F[0-9]{{2}}"
        )
    return token


def build_invalid_experiment_artifact(
    *,
    run_id: str,
    benchmark_path: str | Path,
    benchmark_sha256: str,
    benchmark_byte_size: int,
    seed: str,
    prompt_version: str,
    config_version: str,
    git_head: str,
    git_dirty: bool,
    started_at: datetime,
    ended_at: datetime,
    failure: str,
) -> InvalidExperimentArtifact:
    """Build an explicit non-result artifact for a caught CLI failure."""

    for field_name, value in (
        ("run_id", run_id),
        ("seed", seed),
        ("prompt_version", prompt_version),
        ("config_version", config_version),
        ("git_head", git_head),
        ("failure", failure),
    ):
        _require_text(value, field_name)
    if not _GIT_HEAD_RE.fullmatch(git_head):
        raise ValueError("git_head must be a lowercase 40-character commit digest")
    if type(git_dirty) is not bool:
        raise TypeError("git_dirty must be an exact bool")
    if type(benchmark_sha256) is not str or not _SHA256_RE.fullmatch(benchmark_sha256):
        raise ValueError("benchmark_sha256 must be a lowercase SHA-256 digest")
    if type(benchmark_byte_size) is not int or benchmark_byte_size < 0:
        raise ValueError("benchmark_byte_size must be a non-negative integer")
    if (
        started_at.tzinfo is None
        or started_at.utcoffset() is None
        or ended_at.tzinfo is None
        or ended_at.utcoffset() is None
    ):
        raise ValueError("invalid artifact timestamps must be timezone-aware")
    return InvalidExperimentArtifact(
        artifact_schema_version="direction1.experiment_artifact.v0.1",
        run_id=run_id,
        run_class=RunClass.INVALID_RUN,
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        timezone=str(started_at.tzinfo),
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        git_head=git_head,
        git_dirty=git_dirty,
        benchmark_path=str(Path(benchmark_path).resolve()),
        benchmark_sha256=benchmark_sha256,
        benchmark_byte_size=benchmark_byte_size,
        benchmark_schema_version=None,
        case_count=None,
        provenance_counts=MappingProxyType({}),
        provenance_strata_fields=(
            "label_source",
            "adjudication_status",
            "generator_type",
        ),
        provenance_strata_counts=MappingProxyType({}),
        oracle_mapping_sha256=None,
        seed=seed,
        prompt_version=prompt_version,
        config_version=config_version,
        method_results=MappingProxyType({}),
        matched_admission=None,
        validation_status=ArtifactValidationStatus.INVALID_RUN,
        exit_code=1,
        failures=(failure,),
    )


def _provenance_counts(
    cases: tuple[BenchmarkCase, ...],
) -> Mapping[str, Mapping[str, int]]:
    return MappingProxyType(
        {
            field_name: MappingProxyType(
                dict(
                    sorted(
                        Counter(
                            getattr(case.provenance, field_name) or "null"
                            for case in cases
                        ).items()
                    )
                )
            )
            for field_name in (
                "construction",
                "generator",
                "generator_type",
                "perturbation_operator",
            )
        }
    )


def _oracle_mapping_hash(oracle: Mapping[str, AdmissionDecision]) -> str:
    payload = {case_id: decision.value for case_id, decision in sorted(oracle.items())}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def artifact_to_dict(
    artifact: ExperimentArtifact | InvalidExperimentArtifact,
) -> dict[str, Any]:
    """Convert an artifact to canonical JSON-compatible primitives."""

    if not isinstance(artifact, (ExperimentArtifact, InvalidExperimentArtifact)):
        raise TypeError("artifact must be a valid or invalid ExperimentArtifact")
    return _json_primitive(artifact)


def _json_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _json_primitive(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {key: _json_primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_primitive(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("artifact floats must be finite; NaN/Inf are forbidden")
        return value
    raise TypeError(f"artifact contains non-JSON type: {type(value).__name__}")


def write_experiment_artifact(
    output_path: str | Path,
    artifact: ExperimentArtifact | InvalidExperimentArtifact,
) -> None:
    """Validate and atomically replace one canonical UTF-8/LF JSON artifact."""

    output = Path(output_path)
    if not output.parent.is_dir():
        raise ValueError("output parent directory must already exist")
    payload = artifact_to_dict(artifact)
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if json.loads(encoded.decode("utf-8")) != payload:
        raise ValueError("artifact JSON roundtrip validation failed")

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
