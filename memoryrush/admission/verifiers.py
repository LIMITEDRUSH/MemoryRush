"""Deterministic provisional verifier adapters for admission baselines."""

from __future__ import annotations

import re

from memoryrush.admission.models import (
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    SupportCell,
    SupportLabel,
    SupportMatrix,
)


class IdOnlyVerifier:
    """Structural false-positive baseline that trusts every declared span ID."""

    verifier_name = "id-only-structural-false-positive-baseline"
    verifier_version = "provisional-v1"

    def build_support_matrix(
        self,
        candidate: CandidateClaim,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> SupportMatrix:
        cells = tuple(
            SupportCell(
                claim_id=claim.claim_id,
                span_id=span.span_id,
                label=SupportLabel.SUPPORTS,
                rationale=(
                    "Provisional structural false-positive baseline: a declared evidence ID "
                    "is treated as supporting the claim and all of its qualifier slots."
                ),
                supported_qualifiers=claim.qualifiers,
                supported_claim_parts=claim.required_support_parts,
            )
            for claim in candidate.atomic_claims
            for span in evidence_spans
        )
        return SupportMatrix(candidate=candidate, evidence_spans=evidence_spans, cells=cells)


class ExactCopyVerifier:
    """Provisional lexical-copy baseline with no semantic inference."""

    verifier_name = "normalized-exact-copy-baseline"
    verifier_version = "provisional-v1"

    def build_support_matrix(
        self,
        candidate: CandidateClaim,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> SupportMatrix:
        cells = tuple(
            self._cell(claim, span)
            for claim in candidate.atomic_claims
            for span in evidence_spans
        )
        return SupportMatrix(candidate=candidate, evidence_spans=evidence_spans, cells=cells)

    @staticmethod
    def _cell(claim: AtomicClaim, span: EvidenceSpan) -> SupportCell:
        normalized_claim = _normalize_text(claim.text)
        normalized_span = _normalize_text(span.text)
        is_copy = _contains_at_boundaries(normalized_span, normalized_claim)
        supported_qualifiers = (
            tuple(
                slot
                for slot in claim.qualifiers
                if _contains_at_boundaries(normalized_span, _normalize_text(slot.value))
            )
            if is_copy
            else ()
        )
        return SupportCell(
            claim_id=claim.claim_id,
            span_id=span.span_id,
            label=SupportLabel.SUPPORTS if is_copy else SupportLabel.INSUFFICIENT,
            rationale=(
                "Normalized claim text is copied at text boundaries; no semantic inference."
                if is_copy
                else "Claim text is not a normalized boundary copy; no semantic inference."
            ),
            supported_qualifiers=supported_qualifiers,
            supported_claim_parts=claim.required_support_parts if is_copy else (),
        )


class StaticOracleVerifier:
    """Static provisional oracle backed by a total set of supplied cell annotations."""

    verifier_name = "static-annotation-oracle"
    verifier_version = "provisional-v1"

    def __init__(self, annotations: tuple[SupportCell, ...]) -> None:
        self._annotations = annotations

    def build_support_matrix(
        self,
        candidate: CandidateClaim,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> SupportMatrix:
        expected = {
            (claim.claim_id, span.span_id)
            for claim in candidate.atomic_claims
            for span in evidence_spans
        }
        supplied = {(cell.claim_id, cell.span_id) for cell in self._annotations}
        unknown = supplied - expected
        if unknown:
            raise ValueError(f"unknown oracle references: {_render_keys(unknown)}")
        missing = expected - supplied
        if missing:
            raise ValueError(f"missing oracle annotations: {_render_keys(missing)}")
        if len(supplied) != len(self._annotations):
            raise ValueError("duplicate oracle annotations")
        return SupportMatrix(
            candidate=candidate,
            evidence_spans=evidence_spans,
            cells=self._annotations,
        )


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _contains_at_boundaries(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    pattern = rf"(?<!\w){re.escape(needle)}(?!\w)"
    return re.search(pattern, haystack, flags=re.UNICODE) is not None


def _render_keys(keys: set[tuple[str, str]]) -> str:
    return ", ".join(f"{claim_id}/{span_id}" for claim_id, span_id in sorted(keys))
