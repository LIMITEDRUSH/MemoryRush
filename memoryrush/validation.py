"""Evidence and contract validation for generated reading memories."""

from __future__ import annotations

import math
import re
from dataclasses import asdict

from memoryrush.models import (
    ArticleMemoryOutput,
    EvidenceSpan,
    SourceDocument,
    ValidationIssue,
    ValidationReport,
)


def _normalized_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalized_key(value: str) -> str:
    return _normalized_whitespace(value).casefold()


def _validate_evidence(
    evidence: list[EvidenceSpan],
    paragraph_map: dict[str, str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not evidence:
        issues.append(
            ValidationIssue(
                "error", "missing_evidence", path, "At least one evidence span is required."
            )
        )
        return

    for evidence_index, span in enumerate(evidence):
        evidence_path = f"{path}.evidence.{evidence_index}"
        if span.paragraph_id not in paragraph_map:
            issues.append(
                ValidationIssue(
                    "error",
                    "unknown_paragraph_id",
                    evidence_path,
                    f"Paragraph {span.paragraph_id!r} does not exist in the source document.",
                )
            )
            continue
        if not span.quote.strip():
            issues.append(
                ValidationIssue("error", "empty_quote", evidence_path, "Evidence quote is empty.")
            )
            continue
        if _normalized_whitespace(span.quote) not in _normalized_whitespace(
            paragraph_map[span.paragraph_id]
        ):
            issues.append(
                ValidationIssue(
                    "error",
                    "quote_not_in_source",
                    evidence_path,
                    "Evidence quote is not an exact normalized substring of the cited paragraph.",
                )
            )


def validate_article_memory_output(
    document: SourceDocument, output: ArticleMemoryOutput
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    paragraph_map = {paragraph.paragraph_id: paragraph.text for paragraph in document.paragraphs}

    if not output.summary:
        issues.append(ValidationIssue("warning", "empty_summary", "summary", "Summary is empty."))

    for index, idea in enumerate(output.core_ideas):
        path = f"core_ideas.{index}"
        if not idea.idea:
            issues.append(ValidationIssue("error", "empty_core_idea", path, "Core idea is empty."))
        _validate_evidence(idea.evidence, paragraph_map, path, issues)

    seen_units: dict[str, int] = {}
    for index, unit in enumerate(output.memory_units):
        path = f"memory_units.{index}"
        for key, value in (asdict(unit.scores) | {"confidence": unit.confidence}).items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                issues.append(
                    ValidationIssue(
                        "error",
                        "invalid_score",
                        f"{path}.{key}",
                        "Scores must be finite numbers in [0,1].",
                    )
                )
        if (
            len(unit.content) > 500
            or len(unit.evidence) > 3
            or any(len(e.quote) > 600 for e in unit.evidence)
        ):
            issues.append(
                ValidationIssue(
                    "error",
                    "oversized_memory",
                    path,
                    "A point must be atomic: content <=500 characters, <=3 quotes of <=600 characters.",
                )
            )
        normalized_content = _normalized_key(unit.content)
        if not normalized_content:
            issues.append(
                ValidationIssue("error", "empty_memory", path, "Memory content is empty.")
            )
        elif normalized_content in seen_units:
            issues.append(
                ValidationIssue(
                    "error",
                    "duplicate_memory",
                    path,
                    f"Duplicates memory_units.{seen_units[normalized_content]}.",
                )
            )
        else:
            seen_units[normalized_content] = index
        _validate_evidence(unit.evidence, paragraph_map, path, issues)

    for index, question in enumerate(output.recall_questions):
        path = f"recall_questions.{index}"
        if not question.question:
            issues.append(
                ValidationIssue("error", "empty_recall_question", path, "Recall question is empty.")
            )
        if not 0 <= question.memory_unit_index < len(output.memory_units):
            issues.append(
                ValidationIssue(
                    "error",
                    "invalid_memory_unit_index",
                    path,
                    "Recall question points outside the memory-unit list.",
                )
            )

    if not output.memory_units:
        issues.append(
            ValidationIssue(
                "error", "no_memory_units", "memory_units", "No memory units were generated."
            )
        )
    return ValidationReport(issues=issues)


def invalid_memory_indices(report: ValidationReport) -> set[int]:
    invalid: set[int] = set()
    for issue in report.issues:
        if issue.severity != "error":
            continue
        match = re.match(r"memory_units\.(\d+)", issue.path)
        if match:
            invalid.add(int(match.group(1)))
    return invalid
