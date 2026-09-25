"""Domain models for source-grounded reading memories.

The core package intentionally has no dependency on Streamlit, Ollama, or a
database.  A processing artifact is plain data and can therefore be tested,
serialized, and inspected independently from the user interface.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceParagraph:
    paragraph_id: str
    position: int
    text: str


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str
    source_name: str
    paragraphs: list[SourceParagraph]


@dataclass(frozen=True)
class EvidenceSpan:
    paragraph_id: str
    quote: str


@dataclass(frozen=True)
class CoreIdea:
    idea: str
    why_it_matters: str
    evidence: list[EvidenceSpan]
    salience_score: float


@dataclass(frozen=True)
class MemoryScores:
    importance: float
    novelty: float
    usefulness: float
    evidence_strength: float
    personal_relevance: float = 0.5
    surprise: float = 0.5
    connectivity: float = 0.5
    user_highlight: float = 0.0


@dataclass(frozen=True)
class MemoryUnit:
    content: str
    memory_type: str
    evidence: list[EvidenceSpan]
    tags: list[str]
    confidence: float
    scores: MemoryScores
    assessment: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecallQuestion:
    question: str
    answer: str
    memory_unit_index: int


@dataclass(frozen=True)
class ArticleMemoryOutput:
    summary: str
    core_ideas: list[CoreIdea]
    memory_units: list[MemoryUnit]
    recall_questions: list[RecallQuestion]


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)


@dataclass(frozen=True)
class AdmissionDecision:
    memory_unit_index: int
    admitted: bool
    information_value: float
    redundancy: float
    priority_score: float
    rank: int | None
    reason: str


@dataclass(frozen=True)
class ProcessingArtifact:
    run_id: str
    created_at: str
    prompt_version: str
    provider_name: str
    model_name: str
    memory_budget: int
    document: SourceDocument
    output: ArticleMemoryOutput
    validation: ValidationReport
    admission: list[AdmissionDecision]
    raw_output: str
    scoring_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid score.")  # noqa: TRY004
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        if value is None:
            return default
        raise ValueError("Scores must be numeric.") from None
    if not math.isfinite(parsed) or not 0 <= parsed <= 1:
        raise ValueError("Scores must be finite and between 0 and 1; never silently clamped.")
    return parsed


def _evidence_from_dict(value: Any) -> list[EvidenceSpan]:
    if not isinstance(value, list):
        return []
    spans: list[EvidenceSpan] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        spans.append(
            EvidenceSpan(
                paragraph_id=_text(item.get("paragraph_id")),
                quote=_text(item.get("quote")),
            )
        )
    return spans


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def article_memory_output_from_dict(data: dict[str, Any]) -> ArticleMemoryOutput:
    """Convert provider JSON into the strict domain model.

    Shape validation is deliberately separated from evidence validation.  This
    converter is tolerant enough to retain imperfect local-model output so the
    validator can report concrete, reviewable failures.
    """

    core_ideas: list[CoreIdea] = []
    for item in data.get("core_ideas", []) if isinstance(data.get("core_ideas"), list) else []:
        if not isinstance(item, dict):
            continue
        core_ideas.append(
            CoreIdea(
                idea=_text(item.get("idea")),
                why_it_matters=_text(item.get("why_it_matters")),
                evidence=_evidence_from_dict(item.get("evidence", [])),
                salience_score=_as_float(item.get("salience_score")),
            )
        )

    memory_units: list[MemoryUnit] = []
    raw_units = data.get("memory_units", [])
    if isinstance(raw_units, list):
        for item in raw_units:
            if not isinstance(item, dict):
                raise ValueError("Every memory unit must be an object; indices must not shift.")  # noqa: TRY004
            raw_scores = item.get("scores", {})
            if not isinstance(raw_scores, dict):
                raw_scores = {}
            memory_units.append(
                MemoryUnit(
                    content=_text(item.get("content")),
                    memory_type=str(item.get("memory_type", "concept")).strip() or "concept",
                    evidence=_evidence_from_dict(item.get("evidence", [])),
                    tags=[str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()]
                    if isinstance(item.get("tags"), list)
                    else [],
                    confidence=_as_float(item.get("confidence")),
                    scores=MemoryScores(
                        importance=_as_float(raw_scores.get("importance")),
                        novelty=_as_float(raw_scores.get("novelty")),
                        usefulness=_as_float(raw_scores.get("usefulness")),
                        evidence_strength=_as_float(raw_scores.get("evidence_strength")),
                    ),
                )
            )

    recall_questions: list[RecallQuestion] = []
    raw_questions = data.get("recall_questions", [])
    if isinstance(raw_questions, list):
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            raw_index = item.get("memory_unit_index")
            memory_index = raw_index if type(raw_index) is int else -1
            recall_questions.append(
                RecallQuestion(
                    question=_text(item.get("question")),
                    answer=_text(item.get("answer")),
                    memory_unit_index=memory_index,
                )
            )

    return ArticleMemoryOutput(
        summary=_text(data.get("summary")),
        core_ideas=core_ideas,
        memory_units=memory_units,
        recall_questions=recall_questions,
    )
