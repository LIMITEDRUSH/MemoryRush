from memoryrush.domain import SourceDocument, SourceParagraph
from memoryrush.pipeline import (
    ArticleMemoryOutput,
    CoreIdea,
    EvidenceSpan,
    MemoryExtractionProvider,
    MemoryUnit,
    RecallQuestion,
    run_article_memory_pipeline,
)


class FakeMemoryProvider:
    provider_name = "fake"

    def generate(self, prompt_context: str) -> ArticleMemoryOutput:
        assert "p_001" in prompt_context
        return ArticleMemoryOutput(
            summary="A short summary.",
            core_ideas=[
                CoreIdea(
                    idea="Reading memory should preserve evidence.",
                    why_it_matters="Evidence makes generated memory auditable.",
                    evidence=EvidenceSpan(
                        paragraph_id="p_001",
                        quote="Reading memory should preserve evidence.",
                    ),
                    salience_score=0.85,
                )
            ],
            memory_units=[
                MemoryUnit(
                    content="Reading memory should preserve evidence.",
                    memory_type="conceptual_insight",
                    evidence_paragraph_ids=["p_001"],
                    tags=["memory"],
                    confidence=0.8,
                )
            ],
            recall_questions=[
                RecallQuestion(
                    question="What should reading memory preserve?",
                    expected_answer="Evidence.",
                    memory_unit_index=0,
                )
            ],
        )


def test_fake_provider_pipeline_returns_valid_artifact() -> None:
    document = SourceDocument(
        document_id="doc_001",
        title="Evidence",
        source_path="evidence.md",
        document_type="md",
        paragraphs=[
            SourceParagraph(
                paragraph_id="p_001",
                document_id="doc_001",
                text="Reading memory should preserve evidence.",
                position=1,
                source_path="evidence.md",
            )
        ],
    )

    provider: MemoryExtractionProvider = FakeMemoryProvider()
    artifact = run_article_memory_pipeline(
        document=document,
        provider=provider,
        prompt_version="article_memory_v1",
        model_name="fake-model",
    )

    assert artifact.document_id == "doc_001"
    assert artifact.prompt_version == "article_memory_v1"
    assert artifact.model_name == "fake-model"
    assert artifact.validation_report.is_valid
    assert artifact.output.memory_units[0].evidence_paragraph_ids == ["p_001"]
