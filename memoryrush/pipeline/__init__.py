"""Structured article-memory pipeline contracts and helpers."""

from memoryrush.pipeline.article_memory_pipeline import (
    MemoryExtractionProvider,
    build_prompt_context,
    run_article_memory_pipeline,
)
from memoryrush.pipeline.contracts import (
    ArticleMemoryOutput,
    CoreIdea,
    EvidenceSpan,
    MemoryUnit,
    ProcessingArtifact,
    RecallQuestion,
    ValidationIssue,
    ValidationReport,
    article_memory_output_from_dict,
)
from memoryrush.pipeline.validation import validate_article_memory_output

__all__ = [
    "ArticleMemoryOutput",
    "CoreIdea",
    "EvidenceSpan",
    "MemoryExtractionProvider",
    "MemoryUnit",
    "ProcessingArtifact",
    "RecallQuestion",
    "ValidationIssue",
    "ValidationReport",
    "article_memory_output_from_dict",
    "build_prompt_context",
    "run_article_memory_pipeline",
    "validate_article_memory_output",
]
