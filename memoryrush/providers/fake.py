"""Deterministic provider used for local pipeline checks."""

from __future__ import annotations

from memoryrush.pipeline import ArticleMemoryOutput, CoreIdea, EvidenceSpan, MemoryUnit, RecallQuestion


class FakeMemoryProvider:
    provider_name = "fake"
    model_name = "fake-model"
    last_raw_output: str | None = None

    def generate(self, prompt_context: str) -> ArticleMemoryOutput:
        paragraph_id, paragraph_text = _first_paragraph_from_context(prompt_context)
        quote = paragraph_text[:160]
        self.last_raw_output = "fake provider output"
        return ArticleMemoryOutput(
            summary="This article contains a source-grounded reading memory candidate.",
            core_ideas=[
                CoreIdea(
                    idea="Reading memory should preserve source evidence.",
                    why_it_matters="Evidence makes generated memory auditable.",
                    evidence=EvidenceSpan(paragraph_id=paragraph_id, quote=quote),
                    salience_score=0.8,
                )
            ],
            memory_units=[
                MemoryUnit(
                    content="Reading memory should preserve source evidence.",
                    memory_type="conceptual_insight",
                    evidence_paragraph_ids=[paragraph_id],
                    tags=["reading-memory"],
                    confidence=0.8,
                )
            ],
            recall_questions=[
                RecallQuestion(
                    question="What should reading memory preserve?",
                    expected_answer="Source evidence.",
                    memory_unit_index=0,
                )
            ],
        )


def _first_paragraph_from_context(prompt_context: str) -> tuple[str, str]:
    for line in prompt_context.splitlines():
        if line.startswith("p_") and ": " in line:
            paragraph_id, text = line.split(": ", 1)
            return paragraph_id, text
    raise ValueError("Prompt context does not contain any source paragraphs.")
