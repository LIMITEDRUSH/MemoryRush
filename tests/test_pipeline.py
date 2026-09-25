import json

from memoryrush.pipeline import process_text
from memoryrush.providers import DeterministicPreviewProvider
from memoryrush.storage import artifact_json


def test_preview_pipeline_creates_valid_reviewable_artifact() -> None:
    text = """# Memory systems

Stable source identifiers let a reader return from a generated memory to the exact paragraph.

An admission policy should prefer useful information while holding back redundant candidates.

Active recall asks the reader to retrieve an idea before revealing the answer and its evidence.
"""
    artifact = process_text(
        "memory.md",
        text,
        DeterministicPreviewProvider(candidate_limit=6),
        memory_budget=2,
    )

    assert artifact.validation.valid
    assert sum(decision.admitted for decision in artifact.admission) == 2
    assert artifact.output.recall_questions
    payload = json.loads(artifact_json(artifact))
    assert payload["document"]["paragraphs"][0]["paragraph_id"] == "p_001"
    assert payload["provider_name"] == "deterministic-preview"
