"""Oracle-isolated inputs and deterministic schedules for the semantic pilot.

The inference manifest is intentionally a narrower contract than the benchmark:
it contains only text and run-local identifiers that a model may see.  The
reversible identifier/source-block mapping is a distinct outer artifact and is
needed only by orchestration and post-hoc evaluation.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from hmac import new as hmac_new
from hashlib import sha256
from typing import Any

from memoryrush.admission.benchmark import BenchmarkCase


DECODING_SEED = 17
INFERENCE_MANIFEST_SCHEMA_VERSION = "direction1.semantic_inference_manifest.v0.1"
OUTER_MAPPING_SCHEMA_VERSION = "direction1.semantic_outer_mapping.v0.1"
INFERENCE_SCHEDULE_SCHEMA_VERSION = "direction1.semantic_inference_schedule.v0.1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_CASE_RE = re.compile(r"^case_[0-9a-f]{12}$")
_OPAQUE_CLAIM_RE = re.compile(r"^claim_[0-9]{3}$")
_OPAQUE_SPAN_RE = re.compile(r"^span_[0-9]{3}$")
_QUALIFIER_KINDS = {
    "entity",
    "relation",
    "object",
    "time",
    "scope",
    "condition",
    "quantifier",
    "modality",
    "negation",
    "attribution",
}
_REQUEST_ROLES = {"claim_form", "atomic_support", "holistic_support"}
_SCHEDULE_SEEDS = {17, 29, 47}


def _require_text(value: object, field_name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_integer(value: object, field_name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")


def _require_tuple(value: object, field_name: str, item_type: type) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if any(type(item) is not item_type for item in value):
        raise TypeError(f"{field_name} must contain {item_type.__name__} values")


def _require_unique(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique")


def _require_digest(value: object, field_name: str) -> None:
    _require_text(value, field_name)
    if not _SHA256_RE.fullmatch(value):  # type: ignore[arg-type]
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        asdict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class _CanonicalArtifact:
    __slots__ = ()

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self)

    @property
    def sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class InferenceQualifier:
    kind: str
    value: str

    def __post_init__(self) -> None:
        _require_text(self.kind, "qualifier kind")
        _require_text(self.value, "qualifier value")
        if self.kind not in _QUALIFIER_KINDS:
            raise ValueError(f"unsupported qualifier kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class InferenceAtomicClaim:
    claim_id: str
    text: str
    qualifiers: tuple[InferenceQualifier, ...]
    required_support_parts: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        if not _OPAQUE_CLAIM_RE.fullmatch(self.claim_id):
            raise ValueError("claim_id must be an opaque claim identifier")
        _require_text(self.text, "atomic claim text")
        _require_tuple(self.qualifiers, "qualifiers", InferenceQualifier)
        _require_tuple(self.required_support_parts, "required_support_parts", str)
        if any(not part.strip() for part in self.required_support_parts):
            raise ValueError("required_support_parts must not contain empty strings")
        qualifier_pairs = tuple((item.kind, item.value) for item in self.qualifiers)
        _require_unique(qualifier_pairs, "qualifiers")  # type: ignore[arg-type]
        _require_unique(self.required_support_parts, "required_support_parts")


@dataclass(frozen=True, slots=True)
class InferenceEvidence:
    span_id: str
    text: str

    def __post_init__(self) -> None:
        _require_text(self.span_id, "span_id")
        if not _OPAQUE_SPAN_RE.fullmatch(self.span_id):
            raise ValueError("span_id must be an opaque span identifier")
        _require_text(self.text, "evidence text")


@dataclass(frozen=True, slots=True)
class InferenceCase:
    case_id: str
    proposition: str
    atomic_claims: tuple[InferenceAtomicClaim, ...]
    evidence: tuple[InferenceEvidence, ...]

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        if not _OPAQUE_CASE_RE.fullmatch(self.case_id):
            raise ValueError("case_id must be an opaque case identifier")
        _require_text(self.proposition, "proposition")
        _require_tuple(self.atomic_claims, "atomic_claims", InferenceAtomicClaim)
        _require_tuple(self.evidence, "evidence", InferenceEvidence)
        if not self.atomic_claims or not self.evidence:
            raise ValueError("inference cases require atomic claims and evidence")
        _require_unique(tuple(item.claim_id for item in self.atomic_claims), "claim IDs")
        _require_unique(tuple(item.span_id for item in self.evidence), "span IDs")


@dataclass(frozen=True, slots=True)
class InferenceManifest(_CanonicalArtifact):
    schema_version: str
    cases: tuple[InferenceCase, ...]

    def __post_init__(self) -> None:
        _require_text(self.schema_version, "schema_version")
        if self.schema_version != INFERENCE_MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported inference manifest schema_version")
        _require_tuple(self.cases, "cases", InferenceCase)
        if not self.cases:
            raise ValueError("inference manifest must contain cases")
        _require_unique(tuple(item.case_id for item in self.cases), "case IDs")


@dataclass(frozen=True, slots=True)
class OpaqueIdPair:
    opaque_id: str
    original_id: str

    def __post_init__(self) -> None:
        _require_text(self.opaque_id, "opaque_id")
        if not _OPAQUE_CLAIM_RE.fullmatch(self.opaque_id):
            raise ValueError("opaque_id must be an opaque claim identifier")
        _require_text(self.original_id, "original_id")


@dataclass(frozen=True, slots=True)
class OpaqueSpanIdPair:
    opaque_id: str
    original_id: str
    original_paragraph_id: str

    def __post_init__(self) -> None:
        _require_text(self.opaque_id, "opaque_id")
        if not _OPAQUE_SPAN_RE.fullmatch(self.opaque_id):
            raise ValueError("opaque_id must be an opaque span identifier")
        _require_text(self.original_id, "original_id")
        _require_text(self.original_paragraph_id, "original_paragraph_id")


@dataclass(frozen=True, slots=True)
class OuterCaseMapping:
    opaque_case_id: str
    original_case_id: str
    original_document_id: str
    original_candidate_id: str
    source_block_identity: str
    claim_ids: tuple[OpaqueIdPair, ...]
    span_ids: tuple[OpaqueSpanIdPair, ...]

    def __post_init__(self) -> None:
        _require_text(self.opaque_case_id, "opaque_case_id")
        if not _OPAQUE_CASE_RE.fullmatch(self.opaque_case_id):
            raise ValueError("opaque_case_id must be an opaque case identifier")
        _require_text(self.original_case_id, "original_case_id")
        _require_text(self.original_document_id, "original_document_id")
        _require_text(self.original_candidate_id, "original_candidate_id")
        _require_digest(self.source_block_identity, "source_block_identity")
        _require_tuple(self.claim_ids, "claim_ids", OpaqueIdPair)
        _require_tuple(self.span_ids, "span_ids", OpaqueSpanIdPair)
        if not self.claim_ids or not self.span_ids:
            raise ValueError("outer case mappings require claim and span mappings")
        _require_unique(tuple(item.opaque_id for item in self.claim_ids), "opaque claim IDs")
        _require_unique(tuple(item.original_id for item in self.claim_ids), "original claim IDs")
        _require_unique(tuple(item.opaque_id for item in self.span_ids), "opaque span IDs")
        _require_unique(tuple(item.original_id for item in self.span_ids), "original span IDs")


@dataclass(frozen=True, slots=True)
class OuterMapping(_CanonicalArtifact):
    schema_version: str
    opaque_namespace: str
    inference_manifest_sha256: str
    cases: tuple[OuterCaseMapping, ...]

    def __post_init__(self) -> None:
        _require_text(self.schema_version, "schema_version")
        if self.schema_version != OUTER_MAPPING_SCHEMA_VERSION:
            raise ValueError("unsupported outer mapping schema_version")
        _require_digest(self.opaque_namespace, "opaque_namespace")
        _require_digest(self.inference_manifest_sha256, "inference_manifest_sha256")
        _require_tuple(self.cases, "cases", OuterCaseMapping)
        if not self.cases:
            raise ValueError("outer mapping must contain cases")
        _require_unique(tuple(item.opaque_case_id for item in self.cases), "opaque case IDs")
        _require_unique(tuple(item.original_case_id for item in self.cases), "original case IDs")
        if any(
            item.opaque_case_id
            != _opaque_case_id(self.opaque_namespace, item.original_case_id)
            for item in self.cases
        ):
            raise ValueError("opaque_namespace does not authenticate opaque case IDs")


@dataclass(frozen=True, slots=True)
class ScheduledCase:
    case_id: str
    request_roles: tuple[str, ...]
    evidence_order: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        if not _OPAQUE_CASE_RE.fullmatch(self.case_id):
            raise ValueError("scheduled case_id must be opaque")
        _require_tuple(self.request_roles, "request_roles", str)
        _require_tuple(self.evidence_order, "evidence_order", str)
        if (
            len(self.request_roles) != 3
            or self.request_roles[0] != "claim_form"
            or set(self.request_roles) != _REQUEST_ROLES
        ):
            raise ValueError("request_roles must contain the frozen three-role order")
        if not self.evidence_order:
            raise ValueError("evidence_order must not be empty")
        _require_unique(self.evidence_order, "evidence_order")
        if any(not _OPAQUE_SPAN_RE.fullmatch(item) for item in self.evidence_order):
            raise ValueError("evidence_order must contain opaque span identifiers")


@dataclass(frozen=True, slots=True)
class InferenceSchedule(_CanonicalArtifact):
    schema_version: str
    inference_manifest_sha256: str
    outer_mapping_sha256: str
    schedule_seed: int
    decoding_seed: int
    cases: tuple[ScheduledCase, ...]

    def __post_init__(self) -> None:
        _require_text(self.schema_version, "schema_version")
        if self.schema_version != INFERENCE_SCHEDULE_SCHEMA_VERSION:
            raise ValueError("unsupported inference schedule schema_version")
        _require_digest(self.inference_manifest_sha256, "inference_manifest_sha256")
        _require_digest(self.outer_mapping_sha256, "outer_mapping_sha256")
        _require_integer(self.schedule_seed, "schedule_seed")
        _require_integer(self.decoding_seed, "decoding_seed")
        if self.schedule_seed < 0:
            raise ValueError("schedule_seed must be non-negative")
        if self.schedule_seed not in _SCHEDULE_SEEDS:
            raise ValueError("schedule_seed must be one of 17, 29, or 47")
        if self.decoding_seed != DECODING_SEED:
            raise ValueError(f"decoding_seed must be {DECODING_SEED}")
        _require_tuple(self.cases, "cases", ScheduledCase)
        if not self.cases:
            raise ValueError("inference schedule must contain cases")
        _require_unique(tuple(item.case_id for item in self.cases), "scheduled case IDs")


def build_inference_artifacts(
    cases: tuple[BenchmarkCase, ...],
    *,
    opaque_namespace: str,
) -> tuple[InferenceManifest, OuterMapping]:
    _require_tuple(cases, "cases", BenchmarkCase)
    _require_digest(opaque_namespace, "opaque_namespace")
    if not cases:
        raise ValueError("cases must not be empty")
    original_case_ids = tuple(case.case_id for case in cases)
    _require_unique(original_case_ids, "original case IDs")

    visible_fingerprints = {
        case.case_id: _visible_case_fingerprint(case) for case in cases
    }
    if len(set(visible_fingerprints.values())) != len(cases):
        raise ValueError("cases must have unique model-visible content")

    inference_cases: list[InferenceCase] = []
    outer_cases: list[OuterCaseMapping] = []
    for case in sorted(cases, key=lambda item: visible_fingerprints[item.case_id]):
        opaque_case_id = _opaque_case_id(opaque_namespace, case.case_id)
        claim_pairs = tuple(
            OpaqueIdPair(f"claim_{index:03d}", claim.claim_id)
            for index, claim in enumerate(case.candidate.atomic_claims, 1)
        )
        span_pairs = tuple(
            OpaqueSpanIdPair(f"span_{index:03d}", span.span_id, span.paragraph_id)
            for index, span in enumerate(case.evidence_spans, 1)
        )
        inference_cases.append(
            InferenceCase(
                case_id=opaque_case_id,
                proposition=case.candidate.proposition,
                atomic_claims=tuple(
                    InferenceAtomicClaim(
                        claim_id=pair.opaque_id,
                        text=claim.text,
                        qualifiers=tuple(
                            InferenceQualifier(slot.kind.value, slot.value)
                            for slot in claim.qualifiers
                        ),
                        required_support_parts=claim.required_support_parts,
                    )
                    for pair, claim in zip(claim_pairs, case.candidate.atomic_claims)
                ),
                evidence=tuple(
                    InferenceEvidence(pair.opaque_id, span.text)
                    for pair, span in zip(span_pairs, case.evidence_spans)
                ),
            )
        )
        outer_cases.append(
            OuterCaseMapping(
                opaque_case_id=opaque_case_id,
                original_case_id=case.case_id,
                original_document_id=case.document.document_id,
                original_candidate_id=case.candidate.candidate_id,
                source_block_identity=case.document.source_sha256,
                claim_ids=claim_pairs,
                span_ids=span_pairs,
            )
        )

    manifest = InferenceManifest(
        schema_version=INFERENCE_MANIFEST_SCHEMA_VERSION,
        cases=tuple(inference_cases),
    )
    _reject_original_identifiers_in_manifest(manifest, cases)
    outer_mapping = OuterMapping(
        schema_version=OUTER_MAPPING_SCHEMA_VERSION,
        opaque_namespace=opaque_namespace,
        inference_manifest_sha256=manifest.sha256,
        cases=tuple(outer_cases),
    )
    return manifest, outer_mapping


def build_inference_schedule(
    manifest: InferenceManifest,
    outer_mapping: OuterMapping,
    schedule_seed: int,
) -> InferenceSchedule:
    if type(manifest) is not InferenceManifest:
        raise TypeError("manifest must be an InferenceManifest")
    if type(outer_mapping) is not OuterMapping:
        raise TypeError("outer_mapping must be an OuterMapping")
    _require_integer(schedule_seed, "schedule_seed")
    if schedule_seed not in _SCHEDULE_SEEDS:
        raise ValueError("schedule_seed must be one of 17, 29, or 47")
    if outer_mapping.inference_manifest_sha256 != manifest.sha256:
        raise ValueError("outer mapping does not match inference manifest")

    manifest_by_id = {item.case_id: item for item in manifest.cases}
    mapping_by_id = {item.opaque_case_id: item for item in outer_mapping.cases}
    if set(mapping_by_id) != set(manifest_by_id):
        raise ValueError("outer mapping and inference manifest case IDs differ")
    for case_id, visible_case in manifest_by_id.items():
        mapping = mapping_by_id[case_id]
        if (
            tuple(item.opaque_id for item in mapping.claim_ids)
            != tuple(item.claim_id for item in visible_case.atomic_claims)
            or tuple(item.opaque_id for item in mapping.span_ids)
            != tuple(item.span_id for item in visible_case.evidence)
        ):
            raise ValueError("outer opaque claim/span mapping differs from inference manifest")

    blocks: dict[str, list[str]] = {}
    for item in outer_mapping.cases:
        blocks.setdefault(item.source_block_identity, []).append(item.opaque_case_id)
    ordered_blocks = sorted(
        blocks,
        key=lambda block_id: (
            _schedule_digest(f"{schedule_seed}|{block_id}"),
            block_id,
        ),
    )
    ordered_case_ids = tuple(
        case_id
        for block_id in ordered_blocks
        for case_id in sorted(
            blocks[block_id],
            key=lambda value: (
                _schedule_digest(f"{schedule_seed}|{block_id}|{value}"),
                value,
            ),
        )
    )

    role_ranked_case_ids = sorted(
        manifest_by_id,
        key=lambda case_id: (
            _schedule_digest(f"{schedule_seed}|role|{case_id}"),
            case_id,
        ),
    )
    atomic_first_case_ids = set(
        role_ranked_case_ids[: len(role_ranked_case_ids) // 2]
    )
    scheduled_cases = []
    for case_id in ordered_case_ids:
        visible_case = manifest_by_id[case_id]
        evidence_order = tuple(
            item.span_id
            for item in sorted(
                visible_case.evidence,
                key=lambda evidence: (
                    _schedule_digest(
                        f"{schedule_seed}|{case_id}|{evidence.span_id}"
                    ),
                    evidence.span_id,
                ),
            )
        )
        support_roles = (
            ("atomic_support", "holistic_support")
            if case_id in atomic_first_case_ids
            else ("holistic_support", "atomic_support")
        )
        scheduled_cases.append(
            ScheduledCase(
                case_id=case_id,
                request_roles=("claim_form", *support_roles),
                evidence_order=evidence_order,
            )
        )
    return InferenceSchedule(
        schema_version=INFERENCE_SCHEDULE_SCHEMA_VERSION,
        inference_manifest_sha256=manifest.sha256,
        outer_mapping_sha256=outer_mapping.sha256,
        schedule_seed=schedule_seed,
        decoding_seed=DECODING_SEED,
        cases=tuple(scheduled_cases),
    )


def parse_inference_manifest(payload: object) -> InferenceManifest:
    root = _mapping(payload, "inference manifest")
    _only_fields(root, {"schema_version", "cases"}, "inference manifest")
    cases = tuple(
        _parse_inference_case(item, index)
        for index, item in enumerate(_list(root.get("cases"), "cases"), 1)
    )
    return InferenceManifest(
        schema_version=_parsed_text(root.get("schema_version"), "schema_version"),
        cases=cases,
    )


def parse_outer_mapping(payload: object) -> OuterMapping:
    root = _mapping(payload, "outer mapping")
    _only_fields(
        root,
        {
            "schema_version",
            "opaque_namespace",
            "inference_manifest_sha256",
            "cases",
        },
        "outer mapping",
    )
    return OuterMapping(
        schema_version=_parsed_text(root.get("schema_version"), "schema_version"),
        opaque_namespace=_parsed_text(
            root.get("opaque_namespace"), "opaque_namespace"
        ),
        inference_manifest_sha256=_parsed_text(
            root.get("inference_manifest_sha256"), "inference_manifest_sha256"
        ),
        cases=tuple(
            _parse_outer_case(item, index)
            for index, item in enumerate(_list(root.get("cases"), "cases"), 1)
        ),
    )


def parse_inference_schedule(payload: object) -> InferenceSchedule:
    root = _mapping(payload, "inference schedule")
    _only_fields(
        root,
        {
            "schema_version",
            "inference_manifest_sha256",
            "outer_mapping_sha256",
            "schedule_seed",
            "decoding_seed",
            "cases",
        },
        "inference schedule",
    )
    return InferenceSchedule(
        schema_version=_parsed_text(root.get("schema_version"), "schema_version"),
        inference_manifest_sha256=_parsed_text(
            root.get("inference_manifest_sha256"), "inference_manifest_sha256"
        ),
        outer_mapping_sha256=_parsed_text(
            root.get("outer_mapping_sha256"), "outer_mapping_sha256"
        ),
        schedule_seed=_parsed_integer(root.get("schedule_seed"), "schedule_seed"),
        decoding_seed=_parsed_integer(root.get("decoding_seed"), "decoding_seed"),
        cases=tuple(
            _parse_scheduled_case(item, index)
            for index, item in enumerate(_list(root.get("cases"), "cases"), 1)
        ),
    )


def _opaque_case_id(opaque_namespace: str, original_case_id: str) -> str:
    digest = hmac_new(
        bytes.fromhex(opaque_namespace),
        f"case\0{original_case_id}".encode("utf-8"),
        sha256,
    ).hexdigest()
    return f"case_{digest[:12]}"


def _schedule_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _visible_case_fingerprint(case: BenchmarkCase) -> str:
    """Hash exactly the semantic fields copied into an inference case."""

    payload = {
        "proposition": case.candidate.proposition,
        "atomic_claims": [
            {
                "text": claim.text,
                "qualifiers": [
                    {"kind": slot.kind.value, "value": slot.value}
                    for slot in claim.qualifiers
                ],
                "required_support_parts": list(claim.required_support_parts),
            }
            for claim in case.candidate.atomic_claims
        ],
        "evidence": [span.text for span in case.evidence_spans],
    }
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject_original_identifiers_in_manifest(
    manifest: InferenceManifest, cases: tuple[BenchmarkCase, ...]
) -> None:
    serialized = manifest.canonical_bytes().decode("utf-8")
    original_ids = {
        identifier
        for case in cases
        for identifier in (
            case.case_id,
            case.document.document_id,
            case.candidate.candidate_id,
            *(claim.claim_id for claim in case.candidate.atomic_claims),
            *(span.span_id for span in case.evidence_spans),
            *(span.paragraph_id for span in case.evidence_spans),
        )
    }
    leaked = sorted(identifier for identifier in original_ids if identifier in serialized)
    if leaked:
        raise ValueError(
            "original identifier occurs in model-visible manifest: "
            + ", ".join(leaked)
        )


def _mapping(value: object, field_name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be an object")
    return value  # type: ignore[return-value]


def _list(value: object, field_name: str) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value  # type: ignore[return-value]


def _parsed_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _parsed_integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an integer")
    return value


def _only_fields(payload: dict[str, Any], allowed: set[str], field_name: str) -> None:
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(
            f"{field_name} has unknown fields: {', '.join(sorted(unknown))}"
        )
    missing = allowed - set(payload)
    if missing:
        raise ValueError(
            f"{field_name} is missing fields: {', '.join(sorted(missing))}"
        )


def _parse_inference_case(value: object, index: int) -> InferenceCase:
    payload = _mapping(value, f"cases[{index}]")
    _only_fields(
        payload,
        {"case_id", "proposition", "atomic_claims", "evidence"},
        f"cases[{index}]",
    )
    return InferenceCase(
        case_id=_parsed_text(payload.get("case_id"), f"cases[{index}].case_id"),
        proposition=_parsed_text(
            payload.get("proposition"), f"cases[{index}].proposition"
        ),
        atomic_claims=tuple(
            _parse_inference_claim(item, index, claim_index)
            for claim_index, item in enumerate(
                _list(payload.get("atomic_claims"), f"cases[{index}].atomic_claims"), 1
            )
        ),
        evidence=tuple(
            _parse_inference_evidence(item, index, evidence_index)
            for evidence_index, item in enumerate(
                _list(payload.get("evidence"), f"cases[{index}].evidence"), 1
            )
        ),
    )


def _parse_inference_claim(
    value: object, case_index: int, claim_index: int
) -> InferenceAtomicClaim:
    name = f"cases[{case_index}].atomic_claims[{claim_index}]"
    payload = _mapping(value, name)
    _only_fields(
        payload,
        {"claim_id", "text", "qualifiers", "required_support_parts"},
        name,
    )
    return InferenceAtomicClaim(
        claim_id=_parsed_text(payload.get("claim_id"), f"{name}.claim_id"),
        text=_parsed_text(payload.get("text"), f"{name}.text"),
        qualifiers=tuple(
            _parse_inference_qualifier(item, name, slot_index)
            for slot_index, item in enumerate(
                _list(payload.get("qualifiers"), f"{name}.qualifiers"), 1
            )
        ),
        required_support_parts=tuple(
            _parsed_text(item, f"{name}.required_support_parts[{part_index}]")
            for part_index, item in enumerate(
                _list(
                    payload.get("required_support_parts"),
                    f"{name}.required_support_parts",
                ),
                1,
            )
        ),
    )


def _parse_inference_qualifier(
    value: object, claim_name: str, slot_index: int
) -> InferenceQualifier:
    name = f"{claim_name}.qualifiers[{slot_index}]"
    payload = _mapping(value, name)
    _only_fields(payload, {"kind", "value"}, name)
    return InferenceQualifier(
        kind=_parsed_text(payload.get("kind"), f"{name}.kind"),
        value=_parsed_text(payload.get("value"), f"{name}.value"),
    )


def _parse_inference_evidence(
    value: object, case_index: int, evidence_index: int
) -> InferenceEvidence:
    name = f"cases[{case_index}].evidence[{evidence_index}]"
    payload = _mapping(value, name)
    _only_fields(payload, {"span_id", "text"}, name)
    return InferenceEvidence(
        span_id=_parsed_text(payload.get("span_id"), f"{name}.span_id"),
        text=_parsed_text(payload.get("text"), f"{name}.text"),
    )


def _parse_outer_case(value: object, index: int) -> OuterCaseMapping:
    name = f"cases[{index}]"
    payload = _mapping(value, name)
    _only_fields(
        payload,
        {
            "opaque_case_id",
            "original_case_id",
            "original_document_id",
            "original_candidate_id",
            "source_block_identity",
            "claim_ids",
            "span_ids",
        },
        name,
    )
    return OuterCaseMapping(
        opaque_case_id=_parsed_text(payload.get("opaque_case_id"), f"{name}.opaque_case_id"),
        original_case_id=_parsed_text(
            payload.get("original_case_id"), f"{name}.original_case_id"
        ),
        original_document_id=_parsed_text(
            payload.get("original_document_id"), f"{name}.original_document_id"
        ),
        original_candidate_id=_parsed_text(
            payload.get("original_candidate_id"), f"{name}.original_candidate_id"
        ),
        source_block_identity=_parsed_text(
            payload.get("source_block_identity"), f"{name}.source_block_identity"
        ),
        claim_ids=tuple(
            _parse_id_pair(item, name, pair_index)
            for pair_index, item in enumerate(
                _list(payload.get("claim_ids"), f"{name}.claim_ids"), 1
            )
        ),
        span_ids=tuple(
            _parse_span_id_pair(item, name, pair_index)
            for pair_index, item in enumerate(
                _list(payload.get("span_ids"), f"{name}.span_ids"), 1
            )
        ),
    )


def _parse_id_pair(value: object, case_name: str, index: int) -> OpaqueIdPair:
    name = f"{case_name}.claim_ids[{index}]"
    payload = _mapping(value, name)
    _only_fields(payload, {"opaque_id", "original_id"}, name)
    return OpaqueIdPair(
        opaque_id=_parsed_text(payload.get("opaque_id"), f"{name}.opaque_id"),
        original_id=_parsed_text(payload.get("original_id"), f"{name}.original_id"),
    )


def _parse_span_id_pair(value: object, case_name: str, index: int) -> OpaqueSpanIdPair:
    name = f"{case_name}.span_ids[{index}]"
    payload = _mapping(value, name)
    _only_fields(
        payload,
        {"opaque_id", "original_id", "original_paragraph_id"},
        name,
    )
    return OpaqueSpanIdPair(
        opaque_id=_parsed_text(payload.get("opaque_id"), f"{name}.opaque_id"),
        original_id=_parsed_text(payload.get("original_id"), f"{name}.original_id"),
        original_paragraph_id=_parsed_text(
            payload.get("original_paragraph_id"), f"{name}.original_paragraph_id"
        ),
    )


def _parse_scheduled_case(value: object, index: int) -> ScheduledCase:
    name = f"cases[{index}]"
    payload = _mapping(value, name)
    _only_fields(payload, {"case_id", "request_roles", "evidence_order"}, name)
    return ScheduledCase(
        case_id=_parsed_text(payload.get("case_id"), f"{name}.case_id"),
        request_roles=tuple(
            _parsed_text(item, f"{name}.request_roles[{role_index}]")
            for role_index, item in enumerate(
                _list(payload.get("request_roles"), f"{name}.request_roles"), 1
            )
        ),
        evidence_order=tuple(
            _parsed_text(item, f"{name}.evidence_order[{span_index}]")
            for span_index, item in enumerate(
                _list(payload.get("evidence_order"), f"{name}.evidence_order"), 1
            )
        ),
    )
