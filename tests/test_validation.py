from memoryrush.models import (
    ArticleMemoryOutput,
    EvidenceSpan,
    MemoryScores,
    MemoryUnit,
    RecallQuestion,
)
from memoryrush.parsing import parse_document
from memoryrush.validation import invalid_memory_indices, validate_article_memory_output


def _unit(content: str, paragraph_id: str, quote: str) -> MemoryUnit:
    return MemoryUnit(
        content=content,
        memory_type="claim",
        evidence=[EvidenceSpan(paragraph_id, quote)],
        tags=["test"],
        confidence=0.8,
        scores=MemoryScores(0.8, 0.7, 0.8, 1.0),
    )


def test_validator_checks_quotes_duplicates_and_question_links() -> None:
    document = parse_document("test.md", "# Title\n\nEvidence lives here.\n\nAnother source.")
    output = ArticleMemoryOutput(
        summary="Summary",
        core_ideas=[],
        memory_units=[
            _unit("Grounded fact", "p_001", "Evidence lives here."),
            _unit("Grounded fact", "p_404", "Invented quote"),
        ],
        recall_questions=[RecallQuestion("Question?", "Answer", 9)],
    )

    report = validate_article_memory_output(document, output)
    codes = {issue.code for issue in report.issues}

    assert not report.valid
    assert {"duplicate_memory", "unknown_paragraph_id", "invalid_memory_unit_index"} <= codes
    assert invalid_memory_indices(report) == {1}
