"""Information-value and redundancy-aware memory admission."""

from __future__ import annotations

import re

from memoryrush.models import AdmissionDecision, ArticleMemoryOutput, MemoryUnit, ValidationReport
from memoryrush.validation import invalid_memory_indices


def information_value(unit: MemoryUnit) -> float:
    scores = unit.scores
    weighted = (
        0.18 * scores.importance
        + 0.14 * scores.usefulness
        + 0.12 * scores.novelty
        + 0.06 * scores.evidence_strength
        + 0.18 * scores.personal_relevance
        + 0.10 * scores.surprise
        + 0.12 * scores.connectivity
        + 0.10 * scores.user_highlight
    )
    return max(0.0, min(1.0, weighted))


def _features(text: str) -> set[str]:
    compact = re.sub(r"\s+", " ", text.casefold()).strip()
    words = re.findall(r"\w+", compact, flags=re.UNICODE)
    features = set(words)
    squashed = re.sub(r"\W+", "", compact, flags=re.UNICODE)
    features.update(squashed[i : i + 3] for i in range(max(0, len(squashed) - 2)))
    return {feature for feature in features if feature}


def redundancy(left: str, right: str) -> float:
    left_features = _features(left)
    right_features = _features(right)
    if not left_features or not right_features:
        return 0.0
    return len(left_features & right_features) / len(left_features | right_features)


def admit_memories(
    output: ArticleMemoryOutput,
    validation: ValidationReport,
    budget: int = 5,
    redundancy_weight: float = 0.45,
    duplicate_threshold: float = 0.82,
    minimum_value: float = 0.35,
) -> list[AdmissionDecision]:
    if budget < 1:
        raise ValueError("Memory budget must be at least 1.")

    invalid = invalid_memory_indices(validation)
    remaining = [index for index in range(len(output.memory_units)) if index not in invalid]
    selected: list[int] = []
    decisions: dict[int, AdmissionDecision] = {}

    for index in sorted(invalid):
        decisions[index] = AdmissionDecision(
            memory_unit_index=index,
            admitted=False,
            information_value=information_value(output.memory_units[index]),
            redundancy=0.0,
            priority_score=0.0,
            rank=None,
            reason="Rejected because source-grounding validation failed.",
        )

    while remaining and len(selected) < budget:
        scored: list[tuple[float, float, float, int]] = []
        for index in remaining:
            unit = output.memory_units[index]
            info = information_value(unit)
            overlap = max(
                (
                    redundancy(unit.content, output.memory_units[chosen].content)
                    for chosen in selected
                ),
                default=0.0,
            )
            priority = max(0.0, info - redundancy_weight * overlap)
            scored.append((priority, info, -overlap, index))

        priority, info, negative_overlap, winner = max(scored)
        overlap = -negative_overlap
        remaining.remove(winner)
        if info < minimum_value or output.memory_units[winner].scores.evidence_strength < 0.6:
            decisions[winner] = AdmissionDecision(
                winner,
                False,
                round(info, 4),
                round(overlap, 4),
                round(priority, 4),
                None,
                "Held back: insufficient information value or model-rated evidence support.",
            )
            continue
        if overlap >= duplicate_threshold:
            decisions[winner] = AdmissionDecision(
                memory_unit_index=winner,
                admitted=False,
                information_value=round(info, 4),
                redundancy=round(overlap, 4),
                priority_score=round(priority, 4),
                rank=None,
                reason="Held back because it is too redundant with a higher-priority memory.",
            )
            continue

        selected.append(winner)
        decisions[winner] = AdmissionDecision(
            memory_unit_index=winner,
            admitted=True,
            information_value=round(info, 4),
            redundancy=round(overlap, 4),
            priority_score=round(priority, 4),
            rank=len(selected),
            reason="Admitted within the memory budget after evidence and redundancy checks.",
        )

    for index in remaining:
        unit = output.memory_units[index]
        info = information_value(unit)
        overlap = max(
            (redundancy(unit.content, output.memory_units[chosen].content) for chosen in selected),
            default=0.0,
        )
        decisions[index] = AdmissionDecision(
            memory_unit_index=index,
            admitted=False,
            information_value=round(info, 4),
            redundancy=round(overlap, 4),
            priority_score=round(max(0.0, info - redundancy_weight * overlap), 4),
            rank=None,
            reason="Held back because the configured memory budget is full.",
        )

    return [decisions[index] for index in range(len(output.memory_units))]
