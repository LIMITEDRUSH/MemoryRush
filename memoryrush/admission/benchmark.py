"""Validated JSONL contracts for the Direction 1 synthetic pilot.

The loader is intentionally dependency-free and strict: a malformed source hash,
span offset, oracle reference, or provenance label fails before evaluation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

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
from memoryrush.admission.decision import (
    ConservativeDecisionPolicy,
    apply_claim_form_policy,
)
from memoryrush.admission.solver import InclusionMinimalSolver


SUPPORTED_SCHEMA_VERSION = "direction1.synthetic_oracle.v0.1"
LABEL_SOURCES = {"programmatic_oracle", "human", "llm_generated"}
ADJUDICATION_STATUSES = {"synthetic_oracle", "provisional", "human_gold"}
GENERATOR_TYPES = {"programmatic", "llm_or_agent", "human"}
CONTROLLED_PERTURBATION_OPERATORS = {
    "replace_entity",
    "replace_quantifier",
    "replace_time",
    "flip_negation",
    "delete_condition",
    "delete_scope",
    "replace_modality",
    "replace_attribution",
    "duplicate_evidence",
    "paraphrase_meaning_preserving",
    "paraphrase_condition_preserving",
    "overcompose_unsupported_atom",
}
ALLOWED_LABEL_STATUS_PAIRS = {
    ("programmatic_oracle", "synthetic_oracle"),
    ("llm_generated", "provisional"),
    ("human", "provisional"),
    ("human", "human_gold"),
}


@dataclass(frozen=True)
class _FrozenQualifierRelation:
    """Suite-specific certificate for one pre-registered synthetic edit.

    This is deliberately not a general semantic entailment rule.  It verifies
    that the checked-in paired fixture still has the exact typed, single-axis
    transition registered before evaluation.
    """

    base_case_id: str
    operator: str
    qualifier_kind: QualifierKind
    old_value: str
    new_value: str
    proposition_old: str
    proposition_new: str
    claim_old: str | None
    claim_new: str | None
    expected_cell_label: SupportLabel


_FROZEN_QUALIFIER_RELATIONS = {
    "MSG-C006": _FrozenQualifierRelation(
        "MSG-C005", "replace_entity", QualifierKind.ENTITY,
        "North Workshop", "South Workshop", "North Workshop", "South Workshop",
        "North Workshop", "South Workshop", SupportLabel.INSUFFICIENT,
    ),
    "MSG-C008": _FrozenQualifierRelation(
        "MSG-C007", "replace_quantifier", QualifierKind.QUANTIFIER,
        "48 participants", "84 participants", "Forty-eight", "Eighty-four",
        None, None, SupportLabel.CONTRADICTS,
    ),
    "MSG-C009": _FrozenQualifierRelation(
        "MSG-C007", "replace_time", QualifierKind.TIME,
        "12 March 2026", "21 March 2026", "12 March 2026", "21 March 2026",
        None, None, SupportLabel.CONTRADICTS,
    ),
    "MSG-C011": _FrozenQualifierRelation(
        "MSG-C010", "flip_negation", QualifierKind.NEGATION,
        "not operate", "affirmed operation", "did not operate", "operated",
        "did not operate", "operated", SupportLabel.CONTRADICTS,
    ),
    "MSG-C013": _FrozenQualifierRelation(
        "MSG-C012", "replace_modality", QualifierKind.MODALITY,
        "may", "asserted actual", "may reduce", "reduces",
        "may reduce", "reduces", SupportLabel.SUPPORTS,
    ),
    "MSG-C016": _FrozenQualifierRelation(
        "MSG-C012", "delete_condition", QualifierKind.CONDITION,
        "during peak load", "unrestricted operating conditions",
        "During peak load, t", "T", None, None, SupportLabel.SUPPORTS,
    ),
    "MSG-C018": _FrozenQualifierRelation(
        "MSG-C017", "delete_scope", QualifierKind.SCOPE,
        "night-shift staff only", "all staff", "only night-shift staff", "staff",
        None, None, SupportLabel.SUPPORTS,
    ),
    "MSG-C020": _FrozenQualifierRelation(
        "MSG-C019", "replace_attribution", QualifierKind.ATTRIBUTION,
        "Mira Sol's inspection note", "Tomas Reed", "Mira Sol", "Tomas Reed",
        None, None, SupportLabel.INSUFFICIENT,
    ),
}
_FROZEN_DUPLICATE_RELATION = {"MSG-C022": "MSG-C001"}
_FROZEN_BASE_SOURCE_SHA256 = {
    "MSG-C001": "71201198320cae60b26945c2dca1ff1386bebf3872e7c97b42845a4a7e31da32",
    "MSG-C005": "df69d71608dc07487e9d117b8f259284fe853750a04d7c0881a96930a325b4b5",
    "MSG-C007": "7acb0ac528d1e19c37c7c36606bcac1fbbffc519202ac0f9892ed84c6bd3e88e",
    "MSG-C010": "6478f4d1c20150c62c60ab51f5dcb670b2d8d7b4f43a672badf54c362608923b",
    "MSG-C012": "29fe3f5de5723aaaf1a9198742adb01b0be420b5e73b07b38db2a669d1066ad2",
    "MSG-C017": "ebe4f00a7b68ad4ebe84ccc7bed5bea14f0b6d5d6847690ac722b98d74c32b7c",
    "MSG-C019": "81b46cdb9b562b763431bd4b50a71eee168467d9b5a26c9124ffec1764ff1011",
}
_FROZEN_BASE_CASE_SHA256 = {
    "MSG-C001": "9e7eb6dd4f6250051de57a37f2d55350e15b4077aa313551057fa674ab18b47a",
    "MSG-C005": "f1c90b6ce1bfeaae09021406b7c1cd47cd41630888ff84f7fe4f68abd8eaabd5",
    "MSG-C007": "f1beedb5531f8fa09cdd8afbadcf56db33885551891dbb480d04dc398b51d1f0",
    "MSG-C010": "1256c1e4334c7ce92d8701a45e9858571e64f3e167f5828139abf37bec4635f3",
    "MSG-C012": "9933ef60ebe34feeb6ae1f18ad4e3b818605a8c1cc77a26081f0eca6005c3584",
    "MSG-C017": "8e3eb9c1ad3d8d8036f9ba12db055684edaaa153794ccd1d4bd24997fda08718",
    "MSG-C019": "1a4c645a649e7574caf9a972ed925900d09c3b547aae1dbe6edf0cacc94a3f7a",
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
    claim_form: ClaimFormAudit
    support_cells: tuple[SupportCell, ...]
    label_source: str
    adjudication_status: str


@dataclass(frozen=True)
class CaseProvenance:
    construction: str
    base_case_id: str | None
    perturbation_operator: str | None
    generator: str
    generator_type: str


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
    oracle = _parse_oracle(
        _require_mapping(root.get("oracle"), "oracle"), candidate, evidence_spans
    )
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
    case_ids = {case.case_id for case in cases}
    for case in cases:
        base_case_id = case.provenance.base_case_id
        if base_case_id == case.case_id:
            raise ValueError(f"case {case.case_id} cannot reference itself as base_case_id")
        if base_case_id is not None and base_case_id not in case_ids:
            raise ValueError(
                f"case {case.case_id} references unknown base_case_id: {base_case_id}"
            )
    _validate_base_case_graph(cases)
    _validate_frozen_programmatic_relations(cases)
    return tuple(cases)


def _validate_base_case_graph(cases: list[BenchmarkCase]) -> None:
    parents = {case.case_id: case.provenance.base_case_id for case in cases}
    for case_id in parents:
        seen: set[str] = set()
        current: str | None = case_id
        while current is not None:
            if current in seen:
                raise ValueError(f"cyclic base_case_id provenance involving {current}")
            seen.add(current)
            current = parents[current]


def _validate_frozen_programmatic_relations(cases: list[BenchmarkCase]) -> None:
    """Validate only the pre-registered relations in this frozen suite.

    Programmatic provenance is earned by an exact paired transformation, not
    by attaching an allow-listed operator name to a self-consistent oracle.
    The registered transitions below are fixture certificates, not reusable
    natural-language inference rules.
    """

    # Do not turn the generic v0.1 loader into a closed registry for every
    # future benchmark.  These certificates are activated only for the named
    # MSG-C frozen suite; other suites need their own committed relation layer.
    programmatic_cases = [
        case for case in cases if case.oracle.label_source == "programmatic_oracle"
    ]
    suite_cases = [case for case in cases if case.case_id.startswith("MSG-C")]
    if not suite_cases:
        if programmatic_cases:
            raise ValueError(
                "programmatic_oracle has no registered relation certificate suite"
            )
        return
    if len(suite_cases) != len(cases):
        raise ValueError("frozen MSG-C suite cannot be mixed with another case namespace")
    by_id = {case.case_id: case for case in cases}
    programmatic = {case.case_id: case for case in programmatic_cases}
    registered = set(_FROZEN_QUALIFIER_RELATIONS) | set(_FROZEN_DUPLICATE_RELATION)
    unknown = set(programmatic) - registered
    missing = registered - set(programmatic)
    if unknown or missing:
        raise ValueError(
            "programmatic relation registry mismatch: "
            f"unregistered={sorted(unknown)}, missing={sorted(missing)}"
        )
    for case_id, case in programmatic.items():
        if case_id in _FROZEN_QUALIFIER_RELATIONS:
            _validate_frozen_qualifier_relation(
                case, by_id, _FROZEN_QUALIFIER_RELATIONS[case_id]
            )
        else:
            _validate_frozen_duplicate_relation(
                case, by_id, _FROZEN_DUPLICATE_RELATION[case_id]
            )


def _validate_programmatic_base(
    case: BenchmarkCase,
    by_id: dict[str, BenchmarkCase],
    expected_base_id: str,
    expected_operator: str,
) -> BenchmarkCase:
    prefix = f"programmatic relation {case.case_id}"
    if (
        case.provenance.base_case_id != expected_base_id
        or case.provenance.perturbation_operator != expected_operator
    ):
        raise ValueError(f"{prefix} has an unregistered base/operator pair")
    base = by_id[expected_base_id]
    if base.provenance.base_case_id is not None:
        raise ValueError(f"{prefix} base must not itself be derived")
    if base.oracle.decision is not AdmissionDecision.ADMIT:
        raise ValueError(f"{prefix} base must have an ADMIT certificate")
    if base.document.source_sha256 != _FROZEN_BASE_SOURCE_SHA256[expected_base_id]:
        raise ValueError(f"{prefix} base does not match canonical source digest")
    if _canonical_case_digest(base) != _FROZEN_BASE_CASE_SHA256[expected_base_id]:
        raise ValueError(f"{prefix} base does not match canonical case digest")
    if case.document != base.document or case.evidence_spans != base.evidence_spans:
        raise ValueError(f"{prefix} changed frozen source or evidence")
    return base


def _replace_once(value: str, old: str, new: str) -> str | None:
    if value.count(old) != 1:
        return None
    return value.replace(old, new, 1)


def _canonical_case_digest(case: BenchmarkCase) -> str:
    payload = json.dumps(
        asdict(case),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _validate_frozen_qualifier_relation(
    case: BenchmarkCase,
    by_id: dict[str, BenchmarkCase],
    relation: _FrozenQualifierRelation,
) -> None:
    prefix = f"programmatic relation {case.case_id}"
    base = _validate_programmatic_base(
        case, by_id, relation.base_case_id, relation.operator
    )
    if len(base.candidate.atomic_claims) != 1 or len(case.candidate.atomic_claims) != 1:
        raise ValueError(f"{prefix} candidate transition must contain one atomic claim")
    base_claim = base.candidate.atomic_claims[0]
    case_claim = case.candidate.atomic_claims[0]
    expected_proposition = _replace_once(
        base.candidate.proposition, relation.proposition_old, relation.proposition_new
    )
    expected_claim_text = base_claim.text
    if relation.claim_old is not None and relation.claim_new is not None:
        expected_claim_text = _replace_once(
            base_claim.text, relation.claim_old, relation.claim_new
        )
    expected_qualifiers = tuple(
        QualifierSlot(slot.kind, relation.new_value)
        if slot.kind is relation.qualifier_kind and slot.value == relation.old_value
        else slot
        for slot in base_claim.qualifiers
    )
    changed_slots = sum(
        slot.kind is relation.qualifier_kind and slot.value == relation.old_value
        for slot in base_claim.qualifiers
    )
    if (
        expected_proposition is None
        or expected_claim_text is None
        or changed_slots != 1
        or case.candidate.candidate_id != f"{case.case_id}-candidate"
        or case.candidate.proposition != expected_proposition
        or case_claim.claim_id != base_claim.claim_id
        or case_claim.text != expected_claim_text
        or case_claim.qualifiers != expected_qualifiers
        or case_claim.required_support_parts != base_claim.required_support_parts
    ):
        raise ValueError(f"{prefix} candidate transition does not match registration")
    if case.oracle.decision is not AdmissionDecision.REJECT:
        raise ValueError(f"{prefix} expected decision REJECT")
    if case.oracle.minimal_evidence_sets:
        raise ValueError(f"{prefix} expected no sufficient evidence set")
    expected_cells = tuple(
        SupportCell(
            claim_id=cell.claim_id,
            span_id=cell.span_id,
            label=relation.expected_cell_label,
            rationale=current.rationale,
            supported_qualifiers=tuple(
                slot
                for slot in cell.supported_qualifiers
                if not (
                    slot.kind is relation.qualifier_kind
                    and slot.value == relation.old_value
                )
            ),
            supported_claim_parts=cell.supported_claim_parts,
        )
        for cell, current in zip(base.oracle.support_cells, case.oracle.support_cells)
    )
    if len(case.oracle.support_cells) != len(base.oracle.support_cells):
        raise ValueError(f"{prefix} support-cell shape changed")
    if case.oracle.support_cells != expected_cells:
        raise ValueError(f"{prefix} support cells do not match registered transition")


def _validate_frozen_duplicate_relation(
    case: BenchmarkCase,
    by_id: dict[str, BenchmarkCase],
    base_case_id: str,
) -> None:
    prefix = f"programmatic relation {case.case_id}"
    # Duplicate evidence changes the evidence tuple by definition, so validate
    # source identity here and derive the added span/cell from the base.
    if (
        case.provenance.base_case_id != base_case_id
        or case.provenance.perturbation_operator != "duplicate_evidence"
    ):
        raise ValueError(f"{prefix} has an unregistered base/operator pair")
    base = by_id[base_case_id]
    if (
        base.provenance.base_case_id is not None
        or base.oracle.decision is not AdmissionDecision.ADMIT
        or base.document.source_sha256 != _FROZEN_BASE_SOURCE_SHA256[base_case_id]
        or _canonical_case_digest(base) != _FROZEN_BASE_CASE_SHA256[base_case_id]
        or case.document != base.document
    ):
        raise ValueError(f"{prefix} has an invalid base or frozen source")
    if (
        case.candidate.candidate_id != f"{case.case_id}-candidate"
        or case.candidate.proposition != base.candidate.proposition
        or case.candidate.atomic_claims != base.candidate.atomic_claims
    ):
        raise ValueError(f"{prefix} candidate transition must preserve the candidate")
    if len(base.evidence_spans) != 1 or len(case.evidence_spans) != 2:
        raise ValueError(f"{prefix} must add exactly one evidence span")
    if case.oracle.decision is not AdmissionDecision.ADMIT:
        raise ValueError(f"{prefix} expected decision ADMIT")
    original, duplicate = case.evidence_spans
    base_span = base.evidence_spans[0]
    if original != base_span or duplicate.span_id == original.span_id or (
        duplicate.document_id,
        duplicate.paragraph_id,
        duplicate.text,
        duplicate.start_char,
        duplicate.end_char,
        duplicate.source_sha256,
    ) != (
        base_span.document_id,
        base_span.paragraph_id,
        base_span.text,
        base_span.start_char,
        base_span.end_char,
        base_span.source_sha256,
    ):
        raise ValueError(f"{prefix} evidence is not an exact duplicate")
    expected_cells: list[SupportCell] = []
    for base_cell in base.oracle.support_cells:
        for span_id in (original.span_id, duplicate.span_id):
            current = next(
                (
                    cell
                    for cell in case.oracle.support_cells
                    if cell.claim_id == base_cell.claim_id and cell.span_id == span_id
                ),
                None,
            )
            if current is None:
                raise ValueError(f"{prefix} support-cell clone is missing")
            expected_cells.append(
                SupportCell(
                    claim_id=base_cell.claim_id,
                    span_id=span_id,
                    label=base_cell.label,
                    rationale=current.rationale,
                    supported_qualifiers=base_cell.supported_qualifiers,
                    supported_claim_parts=base_cell.supported_claim_parts,
                )
            )
    if set(case.oracle.support_cells) != set(expected_cells):
        raise ValueError(f"{prefix} support cells are not cloned from the base")
    expected_sets = {(original.span_id,), (duplicate.span_id,)}
    if set(case.oracle.minimal_evidence_sets) != expected_sets:
        raise ValueError(f"{prefix} minimal evidence sets are not base-derived")


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
    payload: dict[str, Any],
    candidate: CandidateClaim,
    evidence_spans: tuple[EvidenceSpan, ...],
) -> OracleAnnotation:
    _reject_unknown_fields(
        payload,
        {
            "decision",
            "reason_codes",
            "minimal_evidence_sets",
            "claim_form",
            "support_cells",
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
    if len(minimal_sets) != len(set(minimal_sets)):
        raise ValueError("oracle contains a duplicate minimal evidence set")
    if decision is AdmissionDecision.ADMIT and not minimal_sets:
        raise ValueError("ADMIT oracle requires at least one minimal evidence set")

    claim_form = _parse_claim_form(
        _require_mapping(payload.get("claim_form"), "oracle.claim_form")
    )
    support_cells = _parse_support_cells(
        _require_list(payload.get("support_cells"), "oracle.support_cells")
    )
    # Reuse the runtime contract so the frozen oracle cannot omit or invent a
    # claim/span cell, qualifier slot, or compositional support part.
    matrix = SupportMatrix(
        candidate=candidate,
        evidence_spans=evidence_spans,
        cells=support_cells,
    )
    _validate_oracle_certificate(
        matrix=matrix,
        decision=decision,
        minimal_sets=tuple(minimal_sets),
        claim_form=claim_form,
    )
    return OracleAnnotation(
        decision=decision,
        reason_codes=reason_codes,
        minimal_evidence_sets=tuple(minimal_sets),
        claim_form=claim_form,
        support_cells=support_cells,
        label_source=label_source,
        adjudication_status=adjudication_status,
    )


def _validate_oracle_certificate(
    *,
    matrix: SupportMatrix,
    decision: AdmissionDecision,
    minimal_sets: tuple[tuple[str, ...], ...],
    claim_form: ClaimFormAudit,
) -> None:
    recomputed_sets = {
        solution.selected_span_ids for solution in InclusionMinimalSolver().solve(matrix)
    }
    declared_sets = set(minimal_sets)
    if declared_sets != recomputed_sets:
        raise ValueError(
            "oracle minimal evidence sets do not match recomputed inclusion-minimal sets"
        )

    solutions = InclusionMinimalSolver().solve(matrix)
    recomputed_decision, _ = ConservativeDecisionPolicy().decide(matrix, solutions)
    recomputed_decision, _ = apply_claim_form_policy(
        recomputed_decision,
        (),
        claim_form,
    )
    if decision is not recomputed_decision:
        raise ValueError(
            "oracle decision does not match recomputed certificate: "
            f"declared={decision.value}, recomputed={recomputed_decision.value}"
        )


def _parse_claim_form(payload: dict[str, Any]) -> ClaimFormAudit:
    _reject_unknown_fields(
        payload,
        {
            "self_sufficiency",
            "minimality",
            "reason_codes",
            "auditor_name",
            "auditor_version",
        },
        "oracle.claim_form",
    )
    try:
        self_sufficiency = ClaimFormStatus(
            _require_text(
                payload.get("self_sufficiency"),
                "oracle.claim_form.self_sufficiency",
            )
        )
        minimality = ClaimFormStatus(
            _require_text(payload.get("minimality"), "oracle.claim_form.minimality")
        )
    except ValueError as exc:
        raise ValueError("unsupported claim-form status") from exc
    return ClaimFormAudit(
        self_sufficiency=self_sufficiency,
        minimality=minimality,
        reason_codes=tuple(
            _require_text(reason, "oracle.claim_form reason code")
            for reason in _require_list(
                payload.get("reason_codes"), "oracle.claim_form.reason_codes"
            )
        ),
        auditor_name=_require_text(
            payload.get("auditor_name"), "oracle.claim_form.auditor_name"
        ),
        auditor_version=_require_text(
            payload.get("auditor_version"), "oracle.claim_form.auditor_version"
        ),
    )


def _parse_support_cells(payload: list[Any]) -> tuple[SupportCell, ...]:
    cells: list[SupportCell] = []
    for cell_index, raw_cell in enumerate(payload):
        cell = _require_mapping(raw_cell, f"oracle.support_cells[{cell_index}]")
        _reject_unknown_fields(
            cell,
            {
                "claim_id",
                "span_id",
                "label",
                "rationale",
                "supported_qualifiers",
                "supported_claim_parts",
            },
            f"oracle.support_cells[{cell_index}]",
        )
        try:
            label = SupportLabel(
                _require_text(cell.get("label"), "oracle support label")
            )
        except ValueError as exc:
            raise ValueError(f"unsupported oracle support label: {cell.get('label')}") from exc
        rationale = cell.get("rationale", "")
        if not isinstance(rationale, str):
            raise ValueError("oracle support rationale must be a string")
        qualifiers: list[QualifierSlot] = []
        for slot_index, raw_slot in enumerate(
            _require_list(
                cell.get("supported_qualifiers", []),
                "oracle supported_qualifiers",
            )
        ):
            slot = _require_mapping(
                raw_slot,
                f"oracle.support_cells[{cell_index}].supported_qualifiers[{slot_index}]",
            )
            _reject_unknown_fields(slot, {"kind", "value"}, "oracle supported qualifier")
            try:
                kind = QualifierKind(
                    _require_text(slot.get("kind"), "oracle supported qualifier kind")
                )
            except ValueError as exc:
                raise ValueError(
                    f"unsupported qualifier kind: {slot.get('kind')}"
                ) from exc
            qualifiers.append(
                QualifierSlot(
                    kind=kind,
                    value=_require_text(
                        slot.get("value"), "oracle supported qualifier value"
                    ),
                )
            )
        cells.append(
            SupportCell(
                claim_id=_require_text(cell.get("claim_id"), "oracle cell claim_id"),
                span_id=_require_text(cell.get("span_id"), "oracle cell span_id"),
                label=label,
                rationale=rationale,
                supported_qualifiers=tuple(qualifiers),
                supported_claim_parts=tuple(
                    _require_text(part, "oracle supported claim part")
                    for part in _require_list(
                        cell.get("supported_claim_parts", []),
                        "oracle supported_claim_parts",
                    )
                ),
            )
        )
    return tuple(cells)


def _parse_provenance(
    payload: dict[str, Any], oracle: OracleAnnotation
) -> CaseProvenance:
    _reject_unknown_fields(
        payload,
        {
            "construction",
            "base_case_id",
            "perturbation_operator",
            "generator",
            "generator_type",
        },
        "provenance",
    )
    construction = _require_text(payload.get("construction"), "provenance.construction")
    generator = _require_text(payload.get("generator"), "provenance.generator")
    generator_type = _require_text(
        payload.get("generator_type"), "provenance.generator_type"
    )
    if generator_type not in GENERATOR_TYPES:
        raise ValueError(f"unsupported provenance.generator_type: {generator_type}")
    base_case_id = payload.get("base_case_id")
    perturbation_operator = payload.get("perturbation_operator")
    if base_case_id is not None and not isinstance(base_case_id, str):
        raise ValueError("provenance.base_case_id must be a string or null")
    if perturbation_operator is not None and not isinstance(perturbation_operator, str):
        raise ValueError("provenance.perturbation_operator must be a string or null")
    if (base_case_id is None) != (perturbation_operator is None):
        raise ValueError(
            "provenance base_case_id and perturbation_operator must be paired"
        )
    if (
        perturbation_operator is not None
        and perturbation_operator not in CONTROLLED_PERTURBATION_OPERATORS
    ):
        raise ValueError(
            f"unsupported perturbation_operator: {perturbation_operator}"
        )
    expected_generator_types = {
        "programmatic_oracle": {"programmatic"},
        "llm_generated": {"llm_or_agent"},
        "human": {"human"},
    }
    if generator_type not in expected_generator_types[oracle.label_source]:
        raise ValueError(
            "oracle label source/generator type combination is inconsistent: "
            f"{oracle.label_source}/{generator_type}"
        )
    return CaseProvenance(
        construction=construction,
        base_case_id=base_case_id,
        perturbation_operator=perturbation_operator,
        generator=generator,
        generator_type=generator_type,
    )
