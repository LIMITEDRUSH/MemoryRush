from unittest.mock import Mock

import pytest
from test_memory_bank import seed
from test_recall_chat import ChatModel

from memoryrush.bank import MemoryBank
from memoryrush.conversation import read_in_conversation
from memoryrush.providers import DeterministicPreviewProvider, ProviderError

TEXT = "# Fixture\n\nMemory decays over time.\n\nEvidence anchors answers."


def test_reading_receipt_persists_once_without_reinforcement(tmp_path):
    bank = MemoryBank(tmp_path / "memory.db")
    session = bank.new_session()
    provider = DeterministicPreviewProvider()
    turn = read_in_conversation(bank, provider, session, "fixture.md", TEXT, turn_id="read")
    assert turn["reading"]["preview"]
    assert turn["reading"]["active_count"] == 0
    assert turn["reading"]["run_id"] == bank.artifacts()[0]["run_id"]
    assert all(m["recall_count"] == 0 for m in bank.memories())
    reopened = MemoryBank(bank.path)
    assert reopened.turns(session) == [turn]
    # Replaying a submission never extracts, imports or records it again.
    assert (
        read_in_conversation(reopened, Mock(), session, "fixture.md", TEXT, turn_id="read") == turn
    )
    assert len(reopened.artifacts()) == 1
    assert len(reopened.turns(session)) == 1
    with pytest.raises(ValueError, match="another submission"):
        read_in_conversation(
            reopened, Mock(), bank.new_session(), "fixture.md", TEXT, turn_id="read"
        )


def test_invalid_reading_request_does_not_call_model(tmp_path):
    bank, provider = MemoryBank(tmp_path / "memory.db"), Mock()
    with pytest.raises(ValueError, match="Unknown conversation"):
        read_in_conversation(bank, provider, "missing", "fixture.md", TEXT)
    with pytest.raises(ValueError, match="1500"):
        read_in_conversation(
            bank, provider, bank.new_session(), "fixture.md", TEXT, question="x" * 1501
        )
    assert provider.mock_calls == []
    assert bank.artifacts() == []


def test_attachment_with_question_is_one_grounded_turn(tmp_path, monkeypatch):
    bank = MemoryBank(tmp_path / "memory.db")
    artifact = seed(bank)
    monkeypatch.setattr("memoryrush.conversation.process_document", lambda *a, **k: artifact)
    model, session = ChatModel(), bank.new_session()
    turn = read_in_conversation(
        bank, model, session, "fixture.md", TEXT, question="What is decay?", turn_id="read"
    )
    assert turn["used_memory_ids"]
    assert turn["reading"]["question"] == "What is decay?"
    assert turn["reading"]["run_id"] == artifact.run_id
    assert bank.turns(session) == [turn]
    other = bank.new_session()
    assert bank.turns(other) == []
    assert all(t["session_id"] == session for t in bank.turns(session))


def test_saved_article_survives_question_failure(tmp_path, monkeypatch):
    bank = MemoryBank(tmp_path / "memory.db")
    artifact = seed(bank)
    monkeypatch.setattr("memoryrush.conversation.process_document", lambda *a, **k: artifact)
    model = ChatModel()
    monkeypatch.setattr(model, "complete_json", Mock(side_effect=ProviderError("Fixture failure")))
    session = bank.new_session()
    turn = read_in_conversation(bank, model, session, "fixture.md", TEXT, question="Question?")
    assert turn["answer_error"] == "Fixture failure"
    assert turn["answer"] == artifact.output.summary
    assert bank.turns(session) == [turn]
    assert bank.artifacts()[0]["run_id"] == artifact.run_id
    assert all(m["recall_count"] == 0 for m in bank.memories())


def test_preview_question_does_not_pretend_to_answer(tmp_path):
    bank = MemoryBank(tmp_path / "memory.db")
    turn = read_in_conversation(
        bank,
        DeterministicPreviewProvider(),
        bank.new_session(),
        "fixture.md",
        TEXT,
        question="Why?",
    )
    assert turn["kind"] == "reading"
    assert turn["reading"]["preview"]
    assert not turn["used_memory_ids"]
