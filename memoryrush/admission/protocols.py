"""Replaceable interfaces for provisional admission verification."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from memoryrush.admission.models import CandidateClaim, EvidenceSpan, SupportMatrix


@runtime_checkable
class Verifier(Protocol):
    """Build claim/evidence support judgments without choosing a solver."""

    verifier_name: str
    verifier_version: str

    def build_support_matrix(
        self,
        candidate: CandidateClaim,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> SupportMatrix:
        """Return one total support cell for every claim/span pair."""

