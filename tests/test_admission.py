from memoryrush.admission import admit_memories, information_value
from memoryrush.models import (
    ArticleMemoryOutput,
    EvidenceSpan,
    MemoryScores,
    MemoryUnit,
    ValidationReport,
)


def _unit(content: str, importance: float) -> MemoryUnit:
    return MemoryUnit(
        content=content,
        memory_type="concept",
        evidence=[EvidenceSpan("p_001", content)],
        tags=[],
        confidence=0.9,
        scores=MemoryScores(importance, 0.7, 0.8, 1.0),
    )


def test_admission_respects_budget_and_penalizes_redundancy() -> None:
    primary = _unit("Retrieval failure can cause unsupported answers.", 0.95)
    duplicate = _unit("Retrieval failure can cause unsupported answers.", 0.9)
    distinct = _unit("Exact evidence spans make memories auditable.", 0.82)
    output = ArticleMemoryOutput("", [], [primary, duplicate, distinct], [])

    decisions = admit_memories(output, ValidationReport(), budget=2)
    admitted = [decision.memory_unit_index for decision in decisions if decision.admitted]

    assert len(admitted) == 2
    assert 0 in admitted
    assert 2 in admitted
    assert not decisions[1].admitted
    assert decisions[1].redundancy == 1.0
    assert information_value(primary) > information_value(distinct)
