import json
from datetime import timedelta

import pytest
from test_memory_bank import START, seed

from memoryrush.bank import MemoryBank
from memoryrush.chat import answer, recall
from memoryrush.providers import ProviderError


class ChatModel:
    name, model_name = "fixture", "not-a-real-model"

    def __init__(self, score=0.9, invalid=False):
        self.score, self.invalid, self.prompts = score, invalid, []

    def complete_json(self, prompt, max_tokens, schema=None):
        self.prompts.append(prompt)
        data = json.loads(prompt.split("DATA:\n", 1)[1])
        if '"relevance"' in prompt:
            return {
                "relevance": [
                    {
                        "memory_id": m["memory_id"],
                        "score": self.score,
                        "reason": "Fixture relevance",
                    }
                    for m in data["memories"]
                ]
            }
        m = data["memories"][0]
        return {
            "insufficient_evidence": False,
            "paragraphs": [
                {
                    "text": "Grounded answer.",
                    "citations": [
                        {
                            "memory_id": "invented" if self.invalid else m["memory_id"],
                            "quote": m["evidence"][0]["quote"],
                        }
                    ],
                }
            ],
        }


def test_persistent_followup_automatic_recall_and_actual_citations(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    session = bank.new_session()
    model = ChatModel()
    first = answer(bank, model, session, "What is memory decay?", now=START, turn_id="first")
    assert len(first["used_memory_ids"]) == 1
    assert len(first["retrieval"]) == 2
    assert sum(m["recall_count"] for m in bank.memories()) == 1
    calls = len(model.prompts)
    assert (
        answer(bank, model, session, "What is memory decay?", now=START, turn_id="first") == first
    )
    assert len(model.prompts) == calls
    reopened = MemoryBank(tmp_path / "test.db")
    answer(reopened, model, session, "And how does it change?", now=START)
    assert "What is memory decay?" in model.prompts[-1]
    assert len(reopened.turns(session)) == 2


def test_unrelated_even_pinned_memories_are_not_recalled(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    for m in bank.memories():
        bank.pin(m["memory_id"], True, START)
    turn = answer(bank, ChatModel(0.2), bank.new_session(), "Unrelated weather?", now=START)
    assert turn["insufficient_evidence"] and not turn["used_memory_ids"]
    assert all(not r["selected"] for r in turn["retrieval"])
    assert sum(m["recall_count"] for m in bank.memories()) == 0


def test_invalid_citation_causes_no_partial_write_or_boost(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    session = bank.new_session()
    with pytest.raises(ProviderError):
        answer(bank, ChatModel(invalid=True), session, "Question?", now=START)
    assert bank.turns(session) == []
    assert all(m["recall_count"] == 0 for m in bank.memories())


def test_deactivated_memory_never_enters_model_context(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    removed = bank.memories(True)[0]
    bank.set_state(removed["memory_id"], "forgotten")
    model = ChatModel()
    answer(bank, model, bank.new_session(), "Question?", now=START)
    assert all(removed["memory_id"] not in prompt for prompt in model.prompts)


def test_strength_and_decay_change_recall_order_when_relevance_ties(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    first, second = bank.memories(True)
    with bank.connect() as db:
        db.execute(
            "UPDATE memories SET base_score=.8,anchor_strength=.8,half_life_days=1 WHERE memory_id=?",
            (first["memory_id"],),
        )
        db.execute(
            "UPDATE memories SET base_score=.6,anchor_strength=.6,half_life_days=60 WHERE memory_id=?",
            (second["memory_id"],),
        )
    selected, _ = recall(bank, ChatModel(0.8), "query", [], now=START, limit=1)
    assert selected[0]["memory_id"] == first["memory_id"]
    selected, _ = recall(bank, ChatModel(0.8), "query", [], now=START + timedelta(days=2), limit=1)
    assert selected[0]["memory_id"] == second["memory_id"]


def test_source_quote_fabrication_does_not_reinforce(tmp_path):
    class BadQuote(ChatModel):
        def complete_json(self, prompt, max_tokens, schema=None):
            result = super().complete_json(prompt, max_tokens, schema)
            if "paragraphs" in result:
                result["paragraphs"][0]["citations"][0]["quote"] = "Invented source quotation"
            return result

    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    session = bank.new_session()
    with pytest.raises(ProviderError, match="quotation"):
        answer(bank, BadQuote(), session, "Question?", now=START)
    assert bank.turns(session) == []
    assert all(m["recall_count"] == 0 for m in bank.memories())
