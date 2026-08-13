"""Small, deterministic evidence-set solvers and deletion audits.

The exhaustive algorithms are intentional for the bounded pilot: their behavior
is inspectable and they provide oracle references for future optimized solvers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Protocol

from memoryrush.admission.models import QualifierKind, SupportLabel, SupportMatrix


@dataclass(frozen=True)
class SufficiencyResult:
    selected_span_ids: tuple[str, ...]
    supported_claim_ids: tuple[str, ...]
    missing_claim_ids: tuple[str, ...]
    contradicted_claim_ids: tuple[str, ...]
    ambiguous_claim_ids: tuple[str, ...]
    missing_qualifiers: dict[str, tuple[QualifierKind, ...]] = field(default_factory=dict)

    @property
    def is_sufficient(self) -> bool:
        return not (
            self.missing_claim_ids
            or self.contradicted_claim_ids
            or self.ambiguous_claim_ids
            or self.missing_qualifiers
        )


@dataclass(frozen=True)
class EvidenceSolution:
    selected_span_ids: tuple[str, ...]
    sufficiency: SufficiencyResult


@dataclass(frozen=True)
class DeletionTrial:
    deleted_span_id: str
    remaining_span_ids: tuple[str, ...]
    remains_sufficient: bool
    sufficiency: SufficiencyResult


@dataclass(frozen=True)
class DeletionAudit:
    selected_span_ids: tuple[str, ...]
    original_is_sufficient: bool
    trials: tuple[DeletionTrial, ...]

    @property
    def is_inclusion_minimal(self) -> bool:
        return self.original_is_sufficient and all(
            not trial.remains_sufficient for trial in self.trials
        )


class EvidenceSetSolver(Protocol):
    solver_name: str

    def solve(self, matrix: SupportMatrix) -> tuple[EvidenceSolution, ...]:
        """Return deterministic sufficient evidence solutions."""


def evaluate_sufficiency(
    matrix: SupportMatrix,
    selected_span_ids: tuple[str, ...],
) -> SufficiencyResult:
    """Evaluate strict whole-candidate support for a selected evidence subset."""

    known_span_ids = {span.span_id for span in matrix.evidence_spans}
    if len(selected_span_ids) != len(set(selected_span_ids)):
        raise ValueError("selected evidence span IDs must be unique")
    unknown = set(selected_span_ids) - known_span_ids
    if unknown:
        raise ValueError(f"unknown selected evidence spans: {', '.join(sorted(unknown))}")

    supported: list[str] = []
    missing: list[str] = []
    contradicted: list[str] = []
    ambiguous: list[str] = []
    missing_qualifiers: dict[str, tuple[QualifierKind, ...]] = {}

    for claim in matrix.candidate.atomic_claims:
        cells = [matrix.cell(claim.claim_id, span_id) for span_id in selected_span_ids]
        labels = {cell.label for cell in cells}
        if SupportLabel.CONTRADICTS in labels:
            contradicted.append(claim.claim_id)
            continue
        if SupportLabel.AMBIGUOUS in labels:
            ambiguous.append(claim.claim_id)
            continue

        supporting_cells = [cell for cell in cells if cell.label is SupportLabel.SUPPORTS]
        if not supporting_cells:
            missing.append(claim.claim_id)
            continue

        required_qualifiers = {slot.kind for slot in claim.qualifiers}
        covered_qualifiers = {
            kind for cell in supporting_cells for kind in cell.supported_qualifiers
        }
        uncovered = required_qualifiers - covered_qualifiers
        if uncovered:
            missing_qualifiers[claim.claim_id] = tuple(sorted(uncovered, key=lambda item: item.value))
            continue
        supported.append(claim.claim_id)

    return SufficiencyResult(
        selected_span_ids=tuple(selected_span_ids),
        supported_claim_ids=tuple(supported),
        missing_claim_ids=tuple(missing),
        contradicted_claim_ids=tuple(contradicted),
        ambiguous_claim_ids=tuple(ambiguous),
        missing_qualifiers=missing_qualifiers,
    )


def audit_evidence_deletions(
    matrix: SupportMatrix,
    selected_span_ids: tuple[str, ...],
) -> DeletionAudit:
    """Delete each selected span once and recompute strict sufficiency."""

    original = evaluate_sufficiency(matrix, selected_span_ids)
    trials = []
    for deleted_span_id in selected_span_ids:
        remaining = tuple(span_id for span_id in selected_span_ids if span_id != deleted_span_id)
        sufficiency = evaluate_sufficiency(matrix, remaining)
        trials.append(
            DeletionTrial(
                deleted_span_id=deleted_span_id,
                remaining_span_ids=remaining,
                remains_sufficient=sufficiency.is_sufficient,
                sufficiency=sufficiency,
            )
        )
    return DeletionAudit(
        selected_span_ids=selected_span_ids,
        original_is_sufficient=original.is_sufficient,
        trials=tuple(trials),
    )


class _ExhaustiveSolverBase:
    max_evidence_spans = 20

    @staticmethod
    def _ordered_span_ids(matrix: SupportMatrix) -> tuple[str, ...]:
        span_ids = tuple(sorted(span.span_id for span in matrix.evidence_spans))
        if len(span_ids) > _ExhaustiveSolverBase.max_evidence_spans:
            raise ValueError(
                "bounded exhaustive solver supports at most "
                f"{_ExhaustiveSolverBase.max_evidence_spans} evidence spans"
            )
        return span_ids

    @staticmethod
    def _solution(matrix: SupportMatrix, span_ids: tuple[str, ...]) -> EvidenceSolution | None:
        result = evaluate_sufficiency(matrix, span_ids)
        if not result.is_sufficient:
            return None
        return EvidenceSolution(selected_span_ids=span_ids, sufficiency=result)


class InclusionMinimalSolver(_ExhaustiveSolverBase):
    """Return every sufficient set with no sufficient proper subset."""

    solver_name = "exhaustive_inclusion_minimal_v0"

    def solve(self, matrix: SupportMatrix) -> tuple[EvidenceSolution, ...]:
        span_ids = self._ordered_span_ids(matrix)
        minimal_sets: list[frozenset[str]] = []
        solutions: list[EvidenceSolution] = []
        for size in range(1, len(span_ids) + 1):
            for selected in combinations(span_ids, size):
                selected_set = frozenset(selected)
                if any(known_minimal < selected_set for known_minimal in minimal_sets):
                    continue
                solution = self._solution(matrix, selected)
                if solution is not None:
                    minimal_sets.append(selected_set)
                    solutions.append(solution)
        return tuple(solutions)


class MinimumCardinalitySolver(_ExhaustiveSolverBase):
    """Return all sufficient sets at the globally smallest cardinality."""

    solver_name = "exhaustive_minimum_cardinality_v0"

    def solve(self, matrix: SupportMatrix) -> tuple[EvidenceSolution, ...]:
        span_ids = self._ordered_span_ids(matrix)
        for size in range(1, len(span_ids) + 1):
            solutions = tuple(
                solution
                for selected in combinations(span_ids, size)
                if (solution := self._solution(matrix, selected)) is not None
            )
            if solutions:
                return solutions
        return ()

