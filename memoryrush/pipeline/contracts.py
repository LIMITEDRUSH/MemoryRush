"""Contracts for source-grounded article memory output."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from numbers import Real
from typing import Any


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_score(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a number")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _require_string_list(value: list[str], field_name: str) -> None:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list of strings")
    if any(not isinstance(item, str) for item in value):
        raise TypeError(f"{field_name} must contain only strings")


def _require_non_negative_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass
class EvidenceSpan:
    paragraph_id: str
    quote: str

    def __post_init__(self) -> None:
        _require_text(self.paragraph_id, "paragraph_id")
        _require_text(self.quote, "quote")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CoreIdea:
    idea: str
    why_it_matters: str
    evidence: EvidenceSpan
    salience_score: float

    def __post_init__(self) -> None:
        _require_text(self.idea, "idea")
        _require_text(self.why_it_matters, "why_it_matters")
        _require_score(self.salience_score, "salience_score")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryUnit:
    content: str
    memory_type: str
    evidence_paragraph_ids: list[str]
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        _require_text(self.content, "content")
        _require_text(self.memory_type, "memory_type")
        _require_string_list(self.evidence_paragraph_ids, "evidence_paragraph_ids")
        _require_string_list(self.tags, "tags")
        _require_score(self.confidence, "confidence")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecallQuestion:
    question: str
    expected_answer: str
    memory_unit_index: int

    def __post_init__(self) -> None:
        _require_text(self.question, "question")
        _require_text(self.expected_answer, "expected_answer")
        _require_non_negative_integer(self.memory_unit_index, "memory_unit_index")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArticleMemoryOutput:
    summary: str
    core_ideas: list[CoreIdea]
    memory_units: list[MemoryUnit]
    recall_questions: list[RecallQuestion]

    def __post_init__(self) -> None:
        _require_text(self.summary, "summary")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    location: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class ProcessingArtifact:
    document_id: str
    prompt_version: str
    model_name: str
    output: ArticleMemoryOutput
    validation_report: ValidationReport
    raw_output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "prompt_version": self.prompt_version,
            "model_name": self.model_name,
            "raw_output": self.raw_output,
            "output": self.output.to_dict(),
            "validation_report": self.validation_report.to_dict(),
        }


def article_memory_output_from_dict(data: dict[str, Any]) -> ArticleMemoryOutput:
    return ArticleMemoryOutput(
        summary=data["summary"],
        core_ideas=[
            CoreIdea(
                idea=item["idea"],
                why_it_matters=item["why_it_matters"],
                evidence=EvidenceSpan(
                    paragraph_id=item["evidence"]["paragraph_id"],
                    quote=item["evidence"]["quote"],
                ),
                salience_score=item["salience_score"],
            )
            for item in data.get("core_ideas", [])
        ],
        memory_units=[
            MemoryUnit(
                content=item["content"],
                memory_type=item["memory_type"],
                evidence_paragraph_ids=item.get("evidence_paragraph_ids", []),
                tags=item.get("tags", []),
                confidence=item["confidence"],
            )
            for item in data.get("memory_units", [])
        ],
        recall_questions=[
            RecallQuestion(
                question=item["question"],
                expected_answer=item["expected_answer"],
                memory_unit_index=item["memory_unit_index"],
            )
            for item in data.get("recall_questions", [])
        ],
    )
