import json
from dataclasses import replace

import pytest

from memoryrush.admission import admit_memories
from memoryrush.models import ValidationReport
from memoryrush.parsing import parse_document
from memoryrush.pipeline import _chunks, process_text
from memoryrush.providers import DeterministicPreviewProvider, ProviderError
from memoryrush.scoring import WEIGHTS, assess_memories


class Scorer:
    name, model_name = "test", "fixture-only"

    def __init__(self, bad=None):
        self.bad = bad

    def complete_json(self, prompt, max_tokens, schema=None):
        data = json.loads(prompt.split("DATA:\n", 1)[1])
        axes = list(WEIGHTS)[:-1] + ["durability"]
        result = []
        for item in data["candidates"]:
            scores = {a: (0.4 if item["index"] == 0 else 0.9) for a in axes}
            scores["evidence_strength"] = 1.0
            if self.bad is not None:
                scores["importance"] = self.bad
            result.append(
                {
                    "index": item["index"],
                    "scores": scores,
                    "reasons": {a: "Fixture rationale" for a in axes},
                }
            )
        return {"assessments": result}


def fixture_output():
    return process_text(
        "x.md",
        "Useful concept number one.\n\nA different practical mechanism.",
        DeterministicPreviewProvider(),
    ).output


def test_separate_model_scores_actually_change_admission():
    output = fixture_output()
    revised = assess_memories(output, Scorer())
    decisions = admit_memories(revised, ValidationReport(), budget=1)
    assert decisions[1].admitted and not decisions[0].admitted
    assert revised.memory_units[1].assessment["method"] == "llm"
    assert revised.memory_units[1].assessment["raw_assessment"]["scores"]["importance"] == 0.9
    assert revised.memory_units[0].scores.personal_relevance == 0.5
    assert revised.memory_units[0].scores.connectivity == 0


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 2, True, "0.9"])
def test_invalid_scores_never_silently_clamped(bad):
    with pytest.raises(ProviderError):
        assess_memories(fixture_output(), Scorer(bad))


def test_missing_rationale_blocks_assessment():
    class Missing(Scorer):
        def complete_json(self, prompt, max_tokens, schema=None):
            result = super().complete_json(prompt, max_tokens)
            result["assessments"][0]["reasons"]["importance"] = ""
            return result

    with pytest.raises(ProviderError):
        assess_memories(fixture_output(), Missing())


def test_highlight_is_user_signal_and_weak_evidence_not_admitted():
    output = assess_memories(fixture_output(), Scorer(), highlighted_ids=("p_001",))
    assert output.memory_units[0].scores.user_highlight == 1
    assert output.memory_units[1].scores.user_highlight == 0
    unit = output.memory_units[1]
    output = replace(
        output, memory_units=[replace(unit, scores=replace(unit.scores, evidence_strength=0.3))]
    )
    assert not admit_memories(output, ValidationReport())[0].admitted


def test_chunking_covers_long_unicode_source():
    text = "中文长段落。" * 2500
    doc = parse_document("long.txt", text)
    chunks = list(_chunks(doc))
    assert len(chunks) > 1
    assert "".join(p.text for c in chunks for p in c.paragraphs) == text
    assert all(sum(len(p.text.encode("utf-8")) + 30 for p in c.paragraphs) <= 4800 for c in chunks)
