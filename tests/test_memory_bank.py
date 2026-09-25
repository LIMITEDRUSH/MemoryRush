from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from memoryrush.bank import MemoryBank, current_strength
from memoryrush.models import MemoryScores
from memoryrush.pipeline import process_text
from memoryrush.providers import DeterministicPreviewProvider

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def seed(bank):
    artifact = process_text(
        "fixture.md",
        "# Fixture\n\nMemory decays over time.\n\nEvidence anchors answers.",
        DeterministicPreviewProvider(),
        2,
    )
    units = [
        replace(
            u,
            scores=MemoryScores(0.8, 0.5, 0.8, 1.0),
            assessment={"method": "llm", "durability": 0.5, "model": "fixture-only"},
        )
        for u in artifact.output.memory_units
    ]
    artifact = replace(
        artifact, created_at=START.isoformat(), output=replace(artifact.output, memory_units=units)
    )
    bank.import_artifact(artifact)
    return artifact


def test_persistence_idempotency_and_user_choice(tmp_path):
    path = tmp_path / "test.db"
    bank = MemoryBank(path)
    artifact = seed(bank)
    memory = bank.memories(True)[0]
    bank.set_state(memory["memory_id"], "forgotten")
    assert bank.import_artifact(artifact) == 0
    reopened = MemoryBank(path)
    assert len(reopened.memories()) == 2
    assert len(reopened.memories(True)) == 1
    assert reopened.artifacts()[0]["run_id"] == artifact.run_id


def test_decay_half_life_pin_and_clock_skew(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    m = bank.memories(True)[0]
    half = START + timedelta(days=m["half_life_days"])
    assert current_strength(m, half) == pytest.approx(m["base_score"] / 2)
    assert current_strength(m, START - timedelta(days=1)) == m["base_score"]
    assert current_strength(m, half) == current_strength(m, half)  # reads do not mutate
    bank.pin(m["memory_id"], True, half)
    pinned = next(x for x in bank.memories() if x["memory_id"] == m["memory_id"])
    assert current_strength(pinned, half + timedelta(days=999)) == pytest.approx(
        m["base_score"] / 2
    )
    bank.pin(m["memory_id"], False, half + timedelta(days=10))
    unpinned = next(x for x in bank.memories() if x["memory_id"] == m["memory_id"])
    assert current_strength(unpinned, half + timedelta(days=10)) == pytest.approx(
        m["base_score"] / 2
    )


def test_atomic_cited_only_events_idempotency_and_daily_limit(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    seed(bank)
    mid = bank.memories(True)[0]["memory_id"]
    session = bank.new_session()
    turn = {"turn_id": "one", "session_id": session, "query": "Question", "answer": "Answer"}
    bank.save_turn(turn, [mid], START)
    bank.save_turn(turn, [mid], START)
    bank.save_turn(turn | {"turn_id": "two"}, [mid], START + timedelta(hours=1))
    memories = bank.memories(True)
    cited = next(m for m in memories if m["memory_id"] == mid)
    assert cited["recall_count"] == 1
    assert len(bank.events(mid)) == 2
    assert len(bank.turns(session)) == 2
    assert current_strength(cited, START) > cited["base_score"]
    assert all(m["recall_count"] == 0 for m in memories if m["memory_id"] != mid)
    bank.save_turn(turn | {"turn_id": "three"}, [mid], START + timedelta(days=2))
    assert next(m for m in bank.memories() if m["memory_id"] == mid)["recall_count"] == 2
    with pytest.raises(ValueError):
        bank.save_turn(turn | {"turn_id": "bad"}, ["invented"], START)
    assert bank.get_turn("bad") is None


def test_preview_and_invalid_memories_cannot_be_activated(tmp_path):
    bank = MemoryBank(tmp_path / "test.db")
    artifact = process_text(
        "preview.md", "This is an offline preview.", DeterministicPreviewProvider()
    )
    bank.import_artifact(artifact)
    assert bank.memories(True) == []
    with pytest.raises(ValueError):
        bank.set_state(bank.memories()[0]["memory_id"], "active")
