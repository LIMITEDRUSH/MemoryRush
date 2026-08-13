"""Small pipeline runner for article-memory extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from memoryrush.domain import SourceDocument
from memoryrush.pipeline.contracts import ArticleMemoryOutput, ProcessingArtifact
from memoryrush.pipeline.validation import validate_article_memory_output


class MemoryExtractionProvider(Protocol):
    provider_name: str

    def generate(self, prompt_context: str) -> ArticleMemoryOutput:
        """Generate structured article-memory output from prompt context."""


def build_prompt_context(document: SourceDocument, prompt_template: str | None = None) -> str:
    lines = [
        f"Document ID: {document.document_id}",
        f"Title: {document.title}",
        "Paragraphs:",
    ]
    for paragraph in document.paragraphs:
        lines.append(f"{paragraph.paragraph_id}: {paragraph.text}")
    source_context = "\n".join(lines)
    if prompt_template is None:
        return source_context
    return f"{prompt_template.strip()}\n\nSOURCE CONTEXT:\n{source_context}"


def load_prompt_template(prompt_version: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / f"{prompt_version}.md"
    return prompt_path.read_text(encoding="utf-8")


def run_article_memory_pipeline(
    document: SourceDocument,
    provider: MemoryExtractionProvider,
    prompt_version: str,
    model_name: str,
) -> ProcessingArtifact:
    prompt_template = load_prompt_template(prompt_version)
    prompt_context = build_prompt_context(document, prompt_template=prompt_template)
    output = provider.generate(prompt_context)
    validation_report = validate_article_memory_output(document, output)
    return ProcessingArtifact(
        document_id=document.document_id,
        prompt_version=prompt_version,
        model_name=model_name,
        output=output,
        validation_report=validation_report,
        raw_output=getattr(provider, "last_raw_output", None),
    )
