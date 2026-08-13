"""Validation for generated article-memory output."""

from __future__ import annotations

from memoryrush.domain import SourceDocument
from memoryrush.pipeline.contracts import ArticleMemoryOutput, ValidationIssue, ValidationReport


def validate_article_memory_output(
    document: SourceDocument,
    output: ArticleMemoryOutput,
) -> ValidationReport:
    paragraph_ids = {paragraph.paragraph_id for paragraph in document.paragraphs}
    issues: list[ValidationIssue] = []
    seen_memory_content: set[str] = set()

    if not output.core_ideas:
        issues.append(
            ValidationIssue(
                code="missing_core_ideas",
                message="Output must contain at least one evidence-linked core idea.",
                location="core_ideas",
            )
        )
    if not output.memory_units:
        issues.append(
            ValidationIssue(
                code="missing_memory_units",
                message="Output must contain at least one evidence-linked memory unit.",
                location="memory_units",
            )
        )

    for index, core_idea in enumerate(output.core_ideas):
        location = f"core_ideas[{index}].evidence"
        _validate_paragraph_id(
            paragraph_id=core_idea.evidence.paragraph_id,
            known_paragraph_ids=paragraph_ids,
            location=location,
            issues=issues,
        )
        if core_idea.evidence.quote not in _paragraph_text(document, core_idea.evidence.paragraph_id):
            issues.append(
                ValidationIssue(
                    code="unsupported_quote",
                    message="Evidence quote is not present in the referenced source paragraph.",
                    location=location,
                )
            )

    for index, memory_unit in enumerate(output.memory_units):
        location = f"memory_units[{index}]"
        normalized_content = " ".join(memory_unit.content.split()).lower()
        if not normalized_content:
            issues.append(
                ValidationIssue(
                    code="empty_memory_unit",
                    message="Memory unit content must not be empty.",
                    location=f"{location}.content",
                )
            )
        elif normalized_content in seen_memory_content:
            issues.append(
                ValidationIssue(
                    code="duplicate_memory_unit",
                    message="Memory unit content duplicates an earlier memory unit.",
                    location=f"{location}.content",
                )
            )
        seen_memory_content.add(normalized_content)

        if not memory_unit.evidence_paragraph_ids:
            issues.append(
                ValidationIssue(
                    code="missing_evidence",
                    message="Memory unit must reference at least one evidence paragraph.",
                    location=f"{location}.evidence_paragraph_ids",
                )
            )
        for paragraph_id in memory_unit.evidence_paragraph_ids:
            _validate_paragraph_id(
                paragraph_id=paragraph_id,
                known_paragraph_ids=paragraph_ids,
                location=f"{location}.evidence_paragraph_ids",
                issues=issues,
            )

    memory_unit_count = len(output.memory_units)
    for index, question in enumerate(output.recall_questions):
        if question.memory_unit_index >= memory_unit_count:
            issues.append(
                ValidationIssue(
                    code="unknown_memory_unit_index",
                    message="Recall question references a missing memory unit.",
                    location=f"recall_questions[{index}].memory_unit_index",
                )
            )

    return ValidationReport(issues=issues)


def _validate_paragraph_id(
    paragraph_id: str,
    known_paragraph_ids: set[str],
    location: str,
    issues: list[ValidationIssue],
) -> None:
    if paragraph_id not in known_paragraph_ids:
        issues.append(
            ValidationIssue(
                code="unknown_evidence_paragraph",
                message=f"Evidence paragraph ID does not exist in source document: {paragraph_id}",
                location=location,
            )
        )


def _paragraph_text(document: SourceDocument, paragraph_id: str) -> str:
    for paragraph in document.paragraphs:
        if paragraph.paragraph_id == paragraph_id:
            return paragraph.text
    return ""
