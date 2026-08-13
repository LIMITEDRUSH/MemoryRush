from memoryrush.domain import SourceDocument, SourceParagraph
from memoryrush.pipeline import (
    ArticleMemoryOutput,
    CoreIdea,
    EvidenceSpan,
    MemoryUnit,
    RecallQuestion,
    article_memory_output_from_dict,
    validate_article_memory_output,
)


def make_document() -> SourceDocument:
    return SourceDocument(
        document_id="doc_001",
        title="Sample",
        source_path="sample.md",
        document_type="md",
        paragraphs=[
            SourceParagraph(
                paragraph_id="p_001",
                document_id="doc_001",
                text="Retrieval failures can cause answer failures.",
                position=1,
                source_path="sample.md",
            ),
            SourceParagraph(
                paragraph_id="p_002",
                document_id="doc_001",
                text="Evidence links make generated memory easier to inspect.",
                position=2,
                source_path="sample.md",
            ),
        ],
    )


def make_valid_output() -> ArticleMemoryOutput:
    return ArticleMemoryOutput(
        summary="The article explains why evidence-grounded memory is useful.",
        core_ideas=[
            CoreIdea(
                idea="Retrieval failures can cause downstream answer failures.",
                why_it_matters="This distinguishes retrieval problems from generation problems.",
                evidence=EvidenceSpan(
                    paragraph_id="p_001",
                    quote="Retrieval failures can cause answer failures.",
                ),
                salience_score=0.9,
            )
        ],
        memory_units=[
            MemoryUnit(
                content="Retrieval failures can cause downstream answer failures.",
                memory_type="conceptual_insight",
                evidence_paragraph_ids=["p_001"],
                tags=["retrieval"],
                confidence=0.8,
            )
        ],
        recall_questions=[
            RecallQuestion(
                question="What can cause downstream answer failures?",
                expected_answer="Retrieval failures.",
                memory_unit_index=0,
            )
        ],
    )


def test_valid_output_has_no_validation_issues() -> None:
    report = validate_article_memory_output(make_document(), make_valid_output())

    assert report.is_valid
    assert report.issues == []


def test_validation_flags_unknown_evidence_paragraph() -> None:
    output = make_valid_output()
    output.memory_units[0].evidence_paragraph_ids = ["p_999"]

    report = validate_article_memory_output(make_document(), output)

    assert not report.is_valid
    assert any(issue.code == "unknown_evidence_paragraph" for issue in report.issues)


def test_validation_flags_empty_and_duplicate_memory_units() -> None:
    output = make_valid_output()
    output.memory_units = [
        MemoryUnit(
            content="",
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=0.8,
        ),
        MemoryUnit(
            content="Retrieval failures can cause downstream answer failures.",
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=0.8,
        ),
        MemoryUnit(
            content="Retrieval failures can cause downstream answer failures.",
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=0.8,
        ),
    ]

    report = validate_article_memory_output(make_document(), output)

    assert not report.is_valid
    assert any(issue.code == "empty_memory_unit" for issue in report.issues)
    assert any(issue.code == "duplicate_memory_unit" for issue in report.issues)


def test_contract_rejects_out_of_range_scores() -> None:
    try:
        MemoryUnit(
            content="A memory.",
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=1.5,
        )
    except ValueError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError("Expected out-of-range confidence to fail")


def test_article_memory_output_can_be_loaded_from_dict() -> None:
    data = {
        "summary": "A summary.",
        "core_ideas": [
            {
                "idea": "Evidence matters.",
                "why_it_matters": "It makes memory auditable.",
                "evidence": {"paragraph_id": "p_001", "quote": "Evidence matters."},
                "salience_score": 0.8,
            }
        ],
        "memory_units": [
            {
                "content": "Evidence matters for memory.",
                "memory_type": "conceptual_insight",
                "evidence_paragraph_ids": ["p_001"],
                "tags": ["evidence"],
                "confidence": 0.7,
            }
        ],
        "recall_questions": [
            {
                "question": "What matters for memory?",
                "expected_answer": "Evidence.",
                "memory_unit_index": 0,
            }
        ],
    }

    output = article_memory_output_from_dict(data)

    assert output.summary == "A summary."
    assert output.core_ideas[0].evidence.paragraph_id == "p_001"
    assert output.memory_units[0].tags == ["evidence"]
