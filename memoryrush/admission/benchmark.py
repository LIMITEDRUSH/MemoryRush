"""Validated JSONL contracts for the Direction 1 synthetic pilot.

The loader is intentionally dependency-free and strict: a malformed source hash,
span offset, oracle reference, or provenance label fails before evaluation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from memoryrush.admission.models import (
    AdmissionDecision,
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    QualifierKind,
    QualifierSlot,
)


SUPPORTED_SCHEMA_VERSION = "direction1.synthetic_oracle.v0.1"
LABEL_SOURCES = {"programmatic_oracle", "human", "llm_generated"}
ADJUDICATION_STATUSES = {"synthetic_oracle", "provisional", "human_gold"}
ALLOWED_LABEL_STATUS_PAIRS = {
    ("programmatic_oracle", "synthetic_oracle"),
    ("llm_generated", "provisional"),
    ("human", "provisional"),
    ("human", "human_gold"),
}


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _reject_unknown_fields(
    payload: dict[str, Any], allowed: set[str], field_name: str
) -> None:
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(
            f"{field_name} has unknown fields: {', '.join(sorted(unknown))}"
        )


@dataclass(frozen=True)
class BenchmarkParagraph:
    paragraph_id: str
    text: str
    snapshot_start: int
    snapshot_end: int


@dataclass(frozen=True)
class BenchmarkDocument:
    document_id: str
    title: str
    snapshot_text: str
    source_sha256: str
    paragraphs: tuple[BenchmarkParagraph, ...]


@dataclass(frozen=True)
class OracleAnnotation:
    decision: AdmissionDecision
    reason_codes: tuple[str, ...]
    minimal_evidence_sets: tuple[tuple[str, ...], ...]
    label_source: str
    adjudication_status: str


@dataclass(frozen=True)
class CaseProvenance:
    construction: str
    base_case_id: str | None
    perturbation_operator: str | None
    generator: str


@dataclass(frozen=True)
class BenchmarkCase:
    schema_version: str
    case_id: str
    case_family: str
    document: BenchmarkDocument
    candidate: CandidateClaim
    evidence_spans: tuple[EvidenceSpan, ...]
    oracle: OracleAnnotation
    provenance: CaseProvenance


def parse_benchmark_case(payload: dict[str, Any]) -> BenchmarkCase:
    """Parse and cross-validate one JSON-compatible benchmark payload."""

    root = _require_mapping(payload, "case")
    _reject_unknown_fields(
        root,
        {
            "schema_version",
            "case_id",
            "case_family",
            "document",
            "candidate",
            "evidence_spans",
            "oracle",
            "provenance",
        },
        "case",
    )
    schema_version = _require_text(root.get("schema_version"), "schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {schema_version}")
    case_id = _require_text(root.get("case_id"), "case_id")
    case_family = _require_text(root.get("case_family"), "case_family")

    document = _parse_document(_require_mapping(root.get("document"), "document"))
    candidate = _parse_candidate(_require_mapping(root.get("candidate"), "candidate"))
    evidence_spans = _parse_evidence_spans(
        _require_list(root.get("evidence_spans"), "evidence_spans"),
        document,
    )
    oracle = _parse_oracle(_require_mapping(root.get("oracle"), "oracle"), evidence_spans)
    provenance = _parse_provenance(
        _require_mapping(root.get("provenance"), "provenance"), oracle
    )
    return BenchmarkCase(
        schema_version=schema_version,
        case_id=case_id,
        case_family=case_family,
        document=document,
        candidate=candidate,
        evidence_spans=evidence_spans,
        oracle=oracle,
        provenance=provenance,
    )


def load_benchmark(path: str | Path) -> tuple[BenchmarkCase, ...]:
    """Load newline-delimited cases and reject blank, invalid, or duplicate records."""

    benchmark_path = Path(path)
    cases: list[BenchmarkCase] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(benchmark_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            case = parse_benchmark_case(payload)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise ValueError(f"invalid benchmark case on line {line_number}: {exc}") from exc
        if case.case_id in seen_ids:
            raise ValueError(f"duplicate case_id on line {line_number}: {case.case_id}")
        seen_ids.add(case.case_id)
        cases.append(case)
    if not cases:
        raise ValueError("benchmark must contain at least one case")
    return tuple(cases)


def _parse_document(payload: dict[str, Any]) -> BenchmarkDocument:
    _reject_unknown_fields(
        payload,
        {"document_id", "title", "snapshot_text", "source_sha256", "paragraphs"},
        "document",
    )
    document_id = _require_text(payload.get("document_id"), "document.document_id")
    title = _require_text(payload.get("title"), "document.title")
    snapshot = _require_text(payload.get("snapshot_text"), "document.snapshot_text")
    claimed_hash = _require_text(payload.get("source_sha256"), "document.source_sha256")
    actual_hash = sha256(snapshot.encode("utf-8")).hexdigest()
    if claimed_hash != actual_hash:
        raise ValueError(
            f"document.source_sha256 does not match snapshot: expected {actual_hash}"
        )

    paragraphs: list[BenchmarkParagraph] = []
    seen_ids: set[str] = set()
    previous_end = 0
    for index, raw in enumerate(_require_list(payload.get("paragraphs"), "document.paragraphs")):
        item = _require_mapping(raw, f"document.paragraphs[{index}]")
        _reject_unknown_fields(
            item,
            {"paragraph_id", "text", "snapshot_start", "snapshot_end"},
            f"document.paragraphs[{index}]",
        )
        paragraph_id = _require_text(item.get("paragraph_id"), "paragraph_id")
        text = _require_text(item.get("text"), "paragraph text")
        snapshot_start = _require_int(item.get("snapshot_start"), "snapshot_start")
        snapshot_end = _require_int(item.get("snapshot_end"), "snapshot_end")
        if paragraph_id in seen_ids:
            raise ValueError(f"duplicate paragraph_id: {paragraph_id}")
        if (
            snapshot_start < previous_end
            or snapshot_end <= snapshot_start
            or snapshot_end > len(snapshot)
        ):
            raise ValueError(
                "document paragraph offsets must be ordered, non-overlapping, "
                "and inside the frozen snapshot"
            )
        if snapshot[snapshot_start:snapshot_end] != text:
            raise ValueError(
                f"paragraph {paragraph_id} does not match its frozen snapshot offsets"
            )
        seen_ids.add(paragraph_id)
        paragraphs.append(
            BenchmarkParagraph(
                paragraph_id=paragraph_id,
                text=text,
                snapshot_start=snapshot_start,
                snapshot_end=snapshot_end,
            )
        )
        previous_end = snapshot_end
    if not paragraphs:
        raise ValueError("document must contain at least one paragraph")
    return BenchmarkDocument(
        document_id=document_id,
        title=title,
        snapshot_text=snapshot,
        source_sha256=actual_hash,
        paragraphs=tuple(paragraphs),
    )


def _parse_candidate(payload: dict[str, Any]) -> CandidateClaim:
    _reject_unknown_fields(
        payload, {"candidate_id", "proposition", "atomic_claims"}, "candidate"
    )
    atomic_claims: list[AtomicClaim] = []
    for claim_index, raw_claim in enumerate(
        _require_list(payload.get("atomic_claims"), "candidate.atomic_claims")
    ):
        claim = _require_mapping(raw_claim, f"candidate.atomic_claims[{claim_index}]")
        _reject_unknown_fields(
            claim,
            {"claim_id", "text", "qualifiers", "required_support_parts"},
            f"candidate.atomic_claims[{claim_index}]",
        )
        qualifiers: list[QualifierSlot] = []
        for slot_index, raw_slot in enumerate(
            _require_list(claim.get("qualifiers", []), "atomic claim qualifiers")
        ):
            slot = _require_mapping(raw_slot, f"qualifiers[{slot_index}]")
            _reject_unknown_fields(
                slot, {"kind", "value"}, f"qualifiers[{slot_index}]"
            )
            try:
                kind = QualifierKind(_require_text(slot.get("kind"), "qualifier kind"))
            except ValueError as exc:
                raise ValueError(f"unsupported qualifier kind: {slot.get('kind')}") from exc
            qualifiers.append(
                QualifierSlot(kind=kind, value=_require_text(slot.get("value"), "qualifier value"))
            )
        atomic_claims.append(
            AtomicClaim(
                claim_id=_require_text(claim.get("claim_id"), "claim_id"),
                text=_require_text(claim.get("text"), "atomic claim text"),
                qualifiers=tuple(qualifiers),
                required_support_parts=tuple(
                    _require_text(part, "required support part")
                    for part in _require_list(
                        claim.get("required_support_parts", []),
                        "atomic claim required_support_parts",
                    )
                ),
            )
        )
    return CandidateClaim(
        candidate_id=_require_text(payload.get("candidate_id"), "candidate_id"),
        proposition=_require_text(payload.get("proposition"), "candidate proposition"),
        atomic_claims=tuple(atomic_claims),
    )


def _parse_evidence_spans(
    payload: list[Any], document: BenchmarkDocument
) -> tuple[EvidenceSpan, ...]:
    paragraphs = {paragraph.paragraph_id: paragraph.text for paragraph in document.paragraphs}
    spans: list[EvidenceSpan] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(payload):
        item = _require_mapping(raw, f"evidence_spans[{index}]")
        _reject_unknown_fields(
            item,
            {"span_id", "paragraph_id", "start_char", "end_char", "text"},
            f"evidence_spans[{index}]",
        )
        span_id = _require_text(item.get("span_id"), "span_id")
        paragraph_id = _require_text(item.get("paragraph_id"), "paragraph_id")
        text = _require_text(item.get("text"), "evidence span text")
        start = _require_int(item.get("start_char"), "start_char")
        end = _require_int(item.get("end_char"), "end_char")
        if span_id in seen_ids:
            raise ValueError(f"duplicate span_id: {span_id}")
        if paragraph_id not in paragraphs:
            raise ValueError(f"unknown evidence paragraph: {paragraph_id}")
        paragraph_text = paragraphs[paragraph_id]
        if start < 0 or end <= start or end > len(paragraph_text):
            raise ValueError(f"evidence span {span_id} has invalid paragraph-local offsets")
        if paragraph_text[start:end] != text:
            raise ValueError(f"evidence span {span_id} does not match paragraph offsets")
        spans.append(
            EvidenceSpan(
                span_id=span_id,
                document_id=document.document_id,
                paragraph_id=paragraph_id,
                text=text,
                start_char=start,
                end_char=end,
                source_sha256=document.source_sha256,
            )
        )
        seen_ids.add(span_id)
    if not spans:
        raise ValueError("case must contain at least one evidence span")
    return tuple(spans)


def _parse_oracle(
    payload: dict[str, Any], evidence_spans: tuple[EvidenceSpan, ...]
) -> OracleAnnotation:
    _reject_unknown_fields(
        payload,
        {
            "decision",
            "reason_codes",
            "minimal_evidence_sets",
            "label_source",
            "adjudication_status",
        },
        "oracle",
    )
    try:
        decision = AdmissionDecision(_require_text(payload.get("decision"), "oracle.decision"))
    except ValueError as exc:
        raise ValueError(f"unsupported oracle decision: {payload.get('decision')}") from exc
    reason_codes = tuple(
        _require_text(value, "oracle reason code")
        for value in _require_list(payload.get("reason_codes"), "oracle.reason_codes")
    )
    label_source = _require_text(payload.get("label_source"), "oracle.label_source")
    adjudication_status = _require_text(
        payload.get("adjudication_status"), "oracle.adjudication_status"
    )
    if label_source not in LABEL_SOURCES:
        raise ValueError(f"unsupported oracle label_source: {label_source}")
    if adjudication_status not in ADJUDICATION_STATUSES:
        raise ValueError(f"unsupported adjudication_status: {adjudication_status}")
    if (label_source, adjudication_status) not in ALLOWED_LABEL_STATUS_PAIRS:
        if label_source == "llm_generated" and adjudication_status == "human_gold":
            raise ValueError("LLM-generated label cannot claim human_gold adjudication")
        raise ValueError(
            "unsupported label_source/adjudication_status combination: "
            f"{label_source}/{adjudication_status}"
        )

    known_span_ids = {span.span_id for span in evidence_spans}
    minimal_sets: list[tuple[str, ...]] = []
    for set_index, raw_set in enumerate(
        _require_list(payload.get("minimal_evidence_sets"), "oracle.minimal_evidence_sets")
    ):
        span_ids = tuple(
            _require_text(value, f"minimal_evidence_sets[{set_index}] span")
            for value in _require_list(raw_set, f"minimal_evidence_sets[{set_index}]")
        )
        if not span_ids or len(span_ids) != len(set(span_ids)):
            raise ValueError("oracle minimal evidence set must be non-empty and unique")
        unknown = set(span_ids) - known_span_ids
        if unknown:
            raise ValueError(f"oracle references unknown evidence span: {', '.join(sorted(unknown))}")
        minimal_sets.append(span_ids)
    if decision is AdmissionDecision.ADMIT and not minimal_sets:
        raise ValueError("ADMIT oracle requires at least one minimal evidence set")
    return OracleAnnotation(
        decision=decision,
        reason_codes=reason_codes,
        minimal_evidence_sets=tuple(minimal_sets),
        label_source=label_source,
        adjudication_status=adjudication_status,
    )


def _parse_provenance(
    payload: dict[str, Any], oracle: OracleAnnotation
) -> CaseProvenance:
    _reject_unknown_fields(
        payload,
        {"construction", "base_case_id", "perturbation_operator", "generator"},
        "provenance",
    )
    construction = _require_text(payload.get("construction"), "provenance.construction")
    generator = _require_text(payload.get("generator"), "provenance.generator")
    base_case_id = payload.get("base_case_id")
    perturbation_operator = payload.get("perturbation_operator")
    if base_case_id is not None and not isinstance(base_case_id, str):
        raise ValueError("provenance.base_case_id must be a string or null")
    if perturbation_operator is not None and not isinstance(perturbation_operator, str):
        raise ValueError("provenance.perturbation_operator must be a string or null")
    if oracle.label_source == "human" and "agent" in generator.casefold():
        raise ValueError("agent-generated provenance cannot claim a human label source")
    return CaseProvenance(
        construction=construction,
        base_case_id=base_case_id,
        perturbation_operator=perturbation_operator,
        generator=generator,
    )
