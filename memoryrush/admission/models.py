"""Provisional contracts for joint proposition/evidence admission research.

These types are deliberately verifier- and solver-agnostic.  They encode the
minimum invariants needed by the pilot without declaring the schema permanent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


class AdmissionDecision(str, Enum):
    ADMIT = "ADMIT"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class QualifierKind(str, Enum):
    ENTITY = "entity"
    RELATION = "relation"
    OBJECT = "object"
    TIME = "time"
    SCOPE = "scope"
    CONDITION = "condition"
    QUANTIFIER = "quantifier"
    MODALITY = "modality"
    NEGATION = "negation"
    ATTRIBUTION = "attribution"


class SupportLabel(str, Enum):
    SUPPORTS = "supports"
    PARTIAL = "partial"
    CONTRADICTS = "contradicts"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class QualifierSlot:
    kind: QualifierKind
    value: str

    def __post_init__(self) -> None:
        _require_text(self.value, "qualifier value")


@dataclass(frozen=True)
class AtomicClaim:
    claim_id: str
    text: str
    qualifiers: tuple[QualifierSlot, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.text, "atomic claim text")
        qualifier_keys = [(slot.kind, slot.value.casefold()) for slot in self.qualifiers]
        if len(qualifier_keys) != len(set(qualifier_keys)):
            raise ValueError("atomic claim qualifiers must not contain duplicates")


@dataclass(frozen=True)
class CandidateClaim:
    candidate_id: str
    proposition: str
    atomic_claims: tuple[AtomicClaim, ...]

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        _require_text(self.proposition, "proposition")
        if not self.atomic_claims:
            raise ValueError("candidate must contain at least one atomic claim")
        claim_ids = [claim.claim_id for claim in self.atomic_claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("atomic claim IDs must be unique within a candidate")


@dataclass(frozen=True)
class EvidenceSpan:
    span_id: str
    document_id: str
    paragraph_id: str
    text: str
    start_char: int
    end_char: int
    source_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.span_id, "span_id")
        _require_text(self.document_id, "document_id")
        _require_text(self.paragraph_id, "paragraph_id")
        _require_text(self.text, "evidence text")
        if self.start_char < 0 or self.end_char <= self.start_char:
            raise ValueError("evidence offsets must be non-negative half-open offsets")
        if self.end_char - self.start_char != len(self.text):
            raise ValueError("evidence offsets must match evidence text length")
        if not _SHA256_RE.fullmatch(self.source_sha256):
            raise ValueError("source_sha256 must be a lowercase 64-character SHA-256 digest")


@dataclass(frozen=True)
class SupportCell:
    claim_id: str
    span_id: str
    label: SupportLabel
    rationale: str = ""
    supported_qualifiers: tuple[QualifierKind, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.span_id, "span_id")
        if len(self.supported_qualifiers) != len(set(self.supported_qualifiers)):
            raise ValueError("supported qualifiers must not contain duplicates")


@dataclass(frozen=True)
class SupportMatrix:
    candidate: CandidateClaim
    evidence_spans: tuple[EvidenceSpan, ...]
    cells: tuple[SupportCell, ...]
    _cell_index: dict[tuple[str, str], SupportCell] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.evidence_spans:
            raise ValueError("support matrix requires at least one evidence span")
        span_ids = [span.span_id for span in self.evidence_spans]
        if len(span_ids) != len(set(span_ids)):
            raise ValueError("evidence span IDs must be unique")

        expected = {
            (claim.claim_id, span.span_id)
            for claim in self.candidate.atomic_claims
            for span in self.evidence_spans
        }
        index: dict[tuple[str, str], SupportCell] = {}
        for cell in self.cells:
            key = (cell.claim_id, cell.span_id)
            if key in index:
                raise ValueError(f"duplicate support cell: {cell.claim_id}/{cell.span_id}")
            if key not in expected:
                raise ValueError(f"unknown support cell: {cell.claim_id}/{cell.span_id}")
            index[key] = cell

        missing = expected - set(index)
        if missing:
            rendered = ", ".join(f"{claim}/{span}" for claim, span in sorted(missing))
            raise ValueError(f"missing support cells: {rendered}")
        object.__setattr__(self, "_cell_index", index)

    def cell(self, claim_id: str, span_id: str) -> SupportCell:
        return self._cell_index[(claim_id, span_id)]

