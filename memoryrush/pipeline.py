"""End-to-end article-memory processing pipeline."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from memoryrush.admission import admit_memories
from memoryrush.models import ArticleMemoryOutput, ProcessingArtifact, SourceDocument
from memoryrush.parsing import parse_document
from memoryrush.prompting import PROMPT_VERSION, build_prompt_context
from memoryrush.providers import MemoryExtractionProvider, ProviderError
from memoryrush.scoring import SCORING_VERSION, assess_memories
from memoryrush.validation import validate_article_memory_output


def _chunks(document: SourceDocument, byte_budget: int = 4800):
    """Bound requests, preserve paragraph IDs and cover all source characters."""
    current, size = [], 0
    for paragraph in document.paragraphs:
        for start in range(0, len(paragraph.text), 1100):
            piece = paragraph.text[start : start + 1100]
            cost = len(piece.encode("utf-8")) + 30
            if current and size + cost > byte_budget:
                yield replace(document, paragraphs=current)
                current, size = [], 0
            current.append(replace(paragraph, text=piece))
            size += cost
    if current:
        yield replace(document, paragraphs=current)


def process_document(
    document: SourceDocument,
    provider: MemoryExtractionProvider,
    memory_budget: int = 5,
    *,
    profile: str = "",
    highlighted_ids: tuple[str, ...] = (),
    prior_memories: list[dict] | None = None,
) -> ProcessingArtifact:
    if not 1 <= memory_budget <= 50:
        raise ValueError("Memory budget must be between 1 and 50.")
    if len(profile) > 500:
        raise ValueError("Reading interests must be at most 500 characters.")
    if not set(highlighted_ids) <= {p.paragraph_id for p in document.paragraphs}:
        raise ValueError("Highlight references an unknown source paragraph.")
    summaries, ideas, units, questions, raw = [], [], [], [], []
    chunks = _chunks(document) if hasattr(provider, "complete_json") else [document]
    for chunk in chunks:
        generated = provider.generate(chunk, build_prompt_context(chunk, candidate_limit=4))
        part = generated.output
        if len(part.memory_units) > 12:
            raise ProviderError("Model exceeded the candidate limit; no partial import.")
        questions.extend(
            replace(q, memory_unit_index=q.memory_unit_index + len(units))
            for q in part.recall_questions
        )
        summaries.append(part.summary)
        ideas.extend(part.core_ideas)
        units.extend(part.memory_units)
        raw.append(generated.raw_output)
    output = ArticleMemoryOutput("\n\n".join(summaries), ideas, units, questions)
    if hasattr(provider, "complete_json"):
        output = assess_memories(output, provider, profile, highlighted_ids, prior_memories)
    validation = validate_article_memory_output(document, output)
    admission = admit_memories(output, validation, budget=memory_budget)
    created_at = datetime.now(timezone.utc).isoformat()
    return ProcessingArtifact(
        run_id=f"run_{uuid4().hex[:16]}",
        created_at=created_at,
        prompt_version=PROMPT_VERSION,
        provider_name=provider.name,
        model_name=provider.model_name,
        memory_budget=memory_budget,
        document=document,
        output=output,
        validation=validation,
        admission=admission,
        raw_output=json.dumps(raw, ensure_ascii=False),
        scoring_context={
            "version": SCORING_VERSION,
            "profile": profile,
            "highlighted_ids": list(highlighted_ids),
            "novelty_scope": "five lexical-nearest stored memories per scoring batch",
        },
    )


def process_text(
    source_name: str,
    text: str,
    provider: MemoryExtractionProvider,
    memory_budget: int = 5,
    **kwargs,
) -> ProcessingArtifact:
    return process_document(parse_document(source_name, text), provider, memory_budget, **kwargs)
