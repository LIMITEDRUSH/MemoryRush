"""Provisional contracts for joint proposition/evidence admission research.

These types are deliberately verifier- and solver-agnostic.  They encode the
minimum invariants needed by the pilot without declaring the schema permanent.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TypeVar


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


_T = TypeVar("_T")


def _require_text(value: str, field_name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_typed_tuple(
    value: tuple[_T, ...],
    field_name: str,
    item_type: type[_T],
    item_name: str,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if any(type(item) is not item_type for item in value):
        raise TypeError(f"{field_name} must contain {item_name}")


class AdmissionDecision(str, Enum):
    ADMIT = "ADMIT"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class ClaimFormStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


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
class ClaimFormAudit:
    """Provisional independent audit of the candidate's proposition-side form."""

    self_sufficiency: ClaimFormStatus
    minimality: ClaimFormStatus
    reason_codes: tuple[str, ...]
    auditor_name: str
    auditor_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.self_sufficiency, ClaimFormStatus):
            raise TypeError("claim-form self_sufficiency must be a ClaimFormStatus")
        if not isinstance(self.minimality, ClaimFormStatus):
            raise TypeError("claim-form minimality must be a ClaimFormStatus")
        _require_typed_tuple(self.reason_codes, "reason_codes", str, "strings")
        _require_text(self.auditor_name, "claim-form auditor name")
        _require_text(self.auditor_version, "claim-form auditor version")
        if any(not reason.strip() for reason in self.reason_codes):
            raise ValueError("claim-form reason codes must not be empty")


@dataclass(frozen=True)
class QualifierSlot:
    kind: QualifierKind
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, QualifierKind):
            raise TypeError("qualifier kind must be a QualifierKind")
        _require_text(self.value, "qualifier value")


@dataclass(frozen=True)
class AtomicClaim:
    claim_id: str
    text: str
    qualifiers: tuple[QualifierSlot, ...] = ()
    required_support_parts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.text, "atomic claim text")
        _require_typed_tuple(
            self.qualifiers,
            "qualifiers",
            QualifierSlot,
            "QualifierSlot values",
        )
        _require_typed_tuple(
            self.required_support_parts,
            "required_support_parts",
            str,
            "strings",
        )
        qualifier_keys = [(slot.kind, slot.value.casefold()) for slot in self.qualifiers]
        if len(qualifier_keys) != len(set(qualifier_keys)):
            raise ValueError("atomic claim qualifiers must not contain duplicates")
        normalized_parts = [part.strip().casefold() for part in self.required_support_parts]
        if any(not part for part in normalized_parts):
            raise ValueError("required support parts must not be empty")
        if len(normalized_parts) != len(set(normalized_parts)):
            raise ValueError("required support parts must not contain duplicates")


@dataclass(frozen=True)
class CandidateClaim:
    candidate_id: str
    proposition: str
    atomic_claims: tuple[AtomicClaim, ...]

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        _require_text(self.proposition, "proposition")
        _require_typed_tuple(
            self.atomic_claims,
            "atomic_claims",
            AtomicClaim,
            "AtomicClaim values",
        )
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
        _require_text(self.source_sha256, "source_sha256")
        if type(self.start_char) is not int or type(self.end_char) is not int:
            raise TypeError("evidence start_char and end_char must be integers")
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
    supported_qualifiers: tuple[QualifierSlot, ...] = ()
    supported_claim_parts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.span_id, "span_id")
        if not isinstance(self.label, SupportLabel):
            raise TypeError("support label must be a SupportLabel")
        if type(self.rationale) is not str:
            raise TypeError("support rationale must be a string")
        _require_typed_tuple(
            self.supported_qualifiers,
            "supported_qualifiers",
            QualifierSlot,
            "QualifierSlot values",
        )
        _require_typed_tuple(
            self.supported_claim_parts,
            "supported_claim_parts",
            str,
            "strings",
        )
        if len(self.supported_qualifiers) != len(set(self.supported_qualifiers)):
            raise ValueError("supported qualifiers must not contain duplicates")
        normalized_parts = [part.strip().casefold() for part in self.supported_claim_parts]
        if any(not part for part in normalized_parts):
            raise ValueError("supported claim parts must not be empty")
        if len(normalized_parts) != len(set(normalized_parts)):
            raise ValueError("supported claim parts must not contain duplicates")


@dataclass(frozen=True)
class SupportMatrix:
    candidate: CandidateClaim
    evidence_spans: tuple[EvidenceSpan, ...]
    cells: tuple[SupportCell, ...]
    _cell_index: Mapping[tuple[str, str], SupportCell] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, CandidateClaim):
            raise TypeError("support matrix candidate must be a CandidateClaim")
        _require_typed_tuple(
            self.evidence_spans,
            "evidence_spans",
            EvidenceSpan,
            "EvidenceSpan values",
        )
        _require_typed_tuple(
            self.cells,
            "cells",
            SupportCell,
            "SupportCell values",
        )
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
        claims = {claim.claim_id: claim for claim in self.candidate.atomic_claims}
        for cell in self.cells:
            key = (cell.claim_id, cell.span_id)
            if key in index:
                raise ValueError(f"duplicate support cell: {cell.claim_id}/{cell.span_id}")
            if key not in expected:
                raise ValueError(f"unknown support cell: {cell.claim_id}/{cell.span_id}")
            claim = claims[cell.claim_id]
            unknown_qualifiers = set(cell.supported_qualifiers) - set(claim.qualifiers)
            if unknown_qualifiers:
                raise ValueError(
                    f"support cell references undeclared qualifier slots: {cell.claim_id}"
                )
            unknown_parts = set(cell.supported_claim_parts) - set(claim.required_support_parts)
            if unknown_parts:
                raise ValueError(
                    f"support cell references undeclared claim parts: {cell.claim_id}"
                )
            index[key] = cell

        missing = expected - set(index)
        if missing:
            rendered = ", ".join(f"{claim}/{span}" for claim, span in sorted(missing))
            raise ValueError(f"missing support cells: {rendered}")
        object.__setattr__(self, "_cell_index", MappingProxyType(index))

    def cell(self, claim_id: str, span_id: str) -> SupportCell:
        return self._cell_index[(claim_id, span_id)]
