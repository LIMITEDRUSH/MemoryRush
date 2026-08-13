import pytest

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
    empty_memory_unit = MemoryUnit(
        content="Initially valid.",
        memory_type="conceptual_insight",
        evidence_paragraph_ids=["p_001"],
        confidence=0.8,
    )
    empty_memory_unit.content = ""
    output.memory_units = [
        empty_memory_unit,
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


@pytest.mark.parametrize("content", [None, "", "   "])
def test_contract_rejects_missing_memory_content(content: object) -> None:
    with pytest.raises((TypeError, ValueError), match="content"):
        MemoryUnit(
            content=content,  # type: ignore[arg-type]
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=0.8,
        )


@pytest.mark.parametrize("score", [float("nan"), float("inf"), float("-inf")])
def test_contract_rejects_non_finite_scores(score: float) -> None:
    with pytest.raises(ValueError, match="confidence"):
        MemoryUnit(
            content="A memory.",
            memory_type="conceptual_insight",
            evidence_paragraph_ids=["p_001"],
            confidence=score,
        )


@pytest.mark.parametrize("score", [True, False])
def test_contract_rejects_boolean_scores(score: bool) -> None:
    with pytest.raises(TypeError, match="salience_score"):
        CoreIdea(
            idea="Evidence matters.",
            why_it_matters="It makes memory auditable.",
            evidence=EvidenceSpan(paragraph_id="p_001", quote="Evidence matters."),
            salience_score=score,
        )


def test_loader_rejects_none_summary_instead_of_stringifying_it() -> None:
    with pytest.raises(TypeError, match="summary"):
        article_memory_output_from_dict({"summary": None})


@pytest.mark.parametrize("field_name", ["question", "expected_answer"])
def test_loader_rejects_none_recall_text_instead_of_stringifying_it(field_name: str) -> None:
    recall_question = {
        "question": "What matters?",
        "expected_answer": "Evidence.",
        "memory_unit_index": 0,
    }
    recall_question[field_name] = None

    with pytest.raises(TypeError, match=field_name):
        article_memory_output_from_dict(
            {
                "summary": "A summary.",
                "recall_questions": [recall_question],
            }
        )


def test_loader_rejects_boolean_recall_index_instead_of_coercing_it() -> None:
    with pytest.raises(TypeError, match="memory_unit_index"):
        article_memory_output_from_dict(
            {
                "summary": "A summary.",
                "recall_questions": [
                    {
                        "question": "What matters?",
                        "expected_answer": "Evidence.",
                        "memory_unit_index": True,
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("evidence_paragraph_ids", "p_001"),
        ("tags", "evidence"),
    ],
)
def test_loader_rejects_string_where_string_list_is_required(
    field_name: str,
    field_value: str,
) -> None:
    memory_unit = {
        "content": "Evidence matters for memory.",
        "memory_type": "conceptual_insight",
        "evidence_paragraph_ids": ["p_001"],
        "tags": ["evidence"],
        "confidence": 0.7,
    }
    memory_unit[field_name] = field_value

    with pytest.raises(TypeError, match=field_name):
        article_memory_output_from_dict(
            {
                "summary": "A summary.",
                "memory_units": [memory_unit],
            }
        )


@pytest.mark.parametrize("score", [float("nan"), float("inf"), True])
def test_loader_rejects_invalid_json_scores(score: float | bool) -> None:
    with pytest.raises((TypeError, ValueError), match="confidence"):
        article_memory_output_from_dict(
            {
                "summary": "A summary.",
                "memory_units": [
                    {
                        "content": "Evidence matters for memory.",
                        "memory_type": "conceptual_insight",
                        "evidence_paragraph_ids": ["p_001"],
                        "tags": ["evidence"],
                        "confidence": score,
                    }
                ],
            }
        )


def test_validation_rejects_summary_only_output() -> None:
    output = ArticleMemoryOutput(
        summary="An invented summary with no grounded core output.",
        core_ideas=[],
        memory_units=[],
        recall_questions=[],
    )

    report = validate_article_memory_output(make_document(), output)

    assert not report.is_valid
    assert {issue.code for issue in report.issues} >= {
        "missing_core_ideas",
        "missing_memory_units",
    }


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
