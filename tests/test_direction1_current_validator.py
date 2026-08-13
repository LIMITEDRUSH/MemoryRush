"""Regression evidence for the structural validator's semantic blind spot."""

from memoryrush.domain import SourceDocument, SourceParagraph
from memoryrush.pipeline import (
    ArticleMemoryOutput,
    CoreIdea,
    EvidenceSpan,
    MemoryUnit,
    validate_article_memory_output,
)


def test_id_only_memory_unit_accepts_unsupported_modality_strengthening() -> None:
    document = SourceDocument(
        document_id="doc_modality",
        title="A cautious finding",
        source_path="public-safe-synthetic.txt",
        document_type="txt",
        paragraphs=[
            SourceParagraph(
                paragraph_id="p_001",
                document_id="doc_modality",
                text="The intervention may reduce latency under the tested configuration.",
                position=1,
                source_path="public-safe-synthetic.txt",
            )
        ],
    )
    output = ArticleMemoryOutput(
        summary="A cautious synthetic result.",
        core_ideas=[
            CoreIdea(
                idea="The finding is conditional and uncertain.",
                why_it_matters="It isolates the MemoryUnit semantic-support check.",
                evidence=EvidenceSpan(
                    paragraph_id="p_001",
                    quote="may reduce latency under the tested configuration",
                ),
                salience_score=0.5,
            )
        ],
        memory_units=[
            MemoryUnit(
                content="The intervention always reduces latency.",
                memory_type="synthetic_claim",
                evidence_paragraph_ids=["p_001"],
                confidence=0.99,
            )
        ],
        recall_questions=[],
    )

    report = validate_article_memory_output(document, output)

    # This passing assertion deliberately captures the baseline defect: the current
    # validator checks only that a MemoryUnit references an existing paragraph ID.
    assert report.is_valid
