"""Private SQLite memory bank, atomic imports and event-driven reinforcement."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from memoryrush.admission import information_value
from memoryrush.validation import invalid_memory_indices


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def data_directory() -> Path:
    override = os.environ.get("MEMORYRUSH_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    # Keep new personal data OUTSIDE the OneDrive-backed source checkout by default.
    return (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "MemoryRush"
    )


def current_strength(memory: dict, now: datetime | None = None) -> float:
    now = now or now_utc()
    elapsed = max(0.0, (now - datetime.fromisoformat(memory["anchor_at"])).total_seconds() / 86400)
    if memory["pinned"]:
        return float(memory["anchor_strength"])
    return float(memory["anchor_strength"]) * math.exp(
        -math.log(2) * elapsed / memory["half_life_days"]
    )


def initial_half_life(memory_type: str, durability: float) -> float:
    days = {
        "concept": 60,
        "mechanism": 60,
        "claim": 30,
        "fact": 21,
        "example": 14,
        "temporary": 3,
    }.get(memory_type, 30)
    return days * (0.5 + durability)


class MemoryBank:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else data_directory() / "memory.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    title TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, run_id TEXT NOT NULL,
                    content TEXT NOT NULL, payload TEXT NOT NULL, source_title TEXT NOT NULL,
                    state TEXT NOT NULL, valid INTEGER NOT NULL, origin TEXT NOT NULL,
                    base_score REAL NOT NULL, anchor_strength REAL NOT NULL, anchor_at TEXT NOT NULL,
                    half_life_days REAL NOT NULL, pinned INTEGER NOT NULL DEFAULT 0,
                    recall_count INTEGER NOT NULL DEFAULT 0, last_recalled_at TEXT,
                    created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS turns (
                    turn_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    query TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT NOT NULL, memory_id TEXT NOT NULL, kind TEXT NOT NULL,
                    created_at TEXT NOT NULL, reinforced INTEGER NOT NULL,
                    PRIMARY KEY(event_id, memory_id));
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS turns_session ON turns(session_id,created_at);
                PRAGMA user_version=1;
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def import_artifact(self, artifact) -> int:
        invalid = invalid_memory_indices(artifact.validation)
        decisions = {d.memory_unit_index: d for d in artifact.admission}
        inserted = 0
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?,?)",
                (
                    artifact.run_id,
                    artifact.document.document_id,
                    artifact.created_at,
                    artifact.document.title,
                    json.dumps(artifact.to_dict(), ensure_ascii=False),
                ),
            )
            for index, unit in enumerate(artifact.output.memory_units):
                normalized = " ".join(unit.content.casefold().split())
                digest = hashlib.sha256(
                    (artifact.document.document_id + normalized).encode()
                ).hexdigest()[:20]
                memory_id = f"mp_{digest}"
                llm = unit.assessment.get("method") == "llm"
                valid = index not in invalid and unit.scores.evidence_strength >= 0.6
                state = "active" if valid and llm and decisions[index].admitted else "held"
                score = information_value(unit)
                cursor = db.execute(
                    """INSERT OR IGNORE INTO memories
                    (memory_id,document_id,run_id,content,payload,source_title,state,valid,origin,
                     base_score,anchor_strength,anchor_at,half_life_days,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        memory_id,
                        artifact.document.document_id,
                        artifact.run_id,
                        unit.content,
                        json.dumps(asdict(unit), ensure_ascii=False),
                        artifact.document.title,
                        state,
                        int(valid),
                        "llm" if llm else "preview",
                        score,
                        score,
                        artifact.created_at,
                        initial_half_life(unit.memory_type, unit.assessment.get("durability", 0.5)),
                        artifact.created_at,
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def memories(self, active_only: bool = False) -> list[dict]:
        with self.connect() as db:
            where = "WHERE state='active' AND valid=1 AND origin='llm'" if active_only else ""
            rows = db.execute(
                f"SELECT * FROM memories {where} ORDER BY created_at,memory_id"
            ).fetchall()
        return [dict(row) | {"unit": json.loads(row["payload"])} for row in rows]

    def artifacts(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM artifacts ORDER BY created_at DESC").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def set_state(self, memory_id: str, state: str) -> None:
        if state not in {"active", "held", "forgotten"}:
            raise ValueError("Invalid memory state.")
        with self.connect() as db:
            row = db.execute(
                "SELECT valid,origin FROM memories WHERE memory_id=?", (memory_id,)
            ).fetchone()
            if not row or (state == "active" and (not row["valid"] or row["origin"] != "llm")):
                raise ValueError("Only evidence-checked, model-scored memories can be activated.")
            db.execute("UPDATE memories SET state=? WHERE memory_id=?", (state, memory_id))

    def pin(self, memory_id: str, pinned: bool, now: datetime | None = None):
        now = now or now_utc()
        with self.connect() as db:
            row = db.execute("SELECT * FROM memories WHERE memory_id=?", (memory_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown memory.")
            # Freeze/unfreeze current strength, never retroactively undo elapsed decay.
            strength = current_strength(dict(row), now)
            db.execute(
                "UPDATE memories SET pinned=?,anchor_at=?,anchor_strength=? WHERE memory_id=?",
                (int(pinned), now.isoformat(), strength, memory_id),
            )

    def setting(self, key: str, value: str | None = None) -> str:
        with self.connect() as db:
            if value is not None:
                db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, value))
                return value
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row[0] if row else ""

    def new_session(self, title: str = "新对话") -> str:
        session_id = uuid4().hex
        with self.connect() as db:
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?)", (session_id, title, now_utc().isoformat())
            )
        return session_id

    def sessions(self) -> list[dict]:
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM sessions ORDER BY created_at DESC")]

    def turns(self, session_id: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT payload FROM turns WHERE session_id=? ORDER BY created_at,rowid",
                (session_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_turn(self, turn_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM turns WHERE turn_id=?", (turn_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_turn(self, turn: dict, used_ids: list[str], now: datetime | None = None):
        now = now or now_utc()
        with self.connect() as db:
            # Serialize read-modify-write, and make one response + all events atomic.
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM turns WHERE turn_id=?", (turn["turn_id"],)).fetchone():
                return
            if not db.execute(
                "SELECT 1 FROM sessions WHERE session_id=?", (turn["session_id"],)
            ).fetchone():
                raise ValueError("Unknown conversation.")
            for memory_id in set(used_ids):
                row = db.execute(
                    "SELECT * FROM memories WHERE memory_id=?", (memory_id,)
                ).fetchone()
                if (
                    not row
                    or row["state"] != "active"
                    or not row["valid"]
                    or row["origin"] != "llm"
                ):
                    raise ValueError("A cited memory was deactivated; regenerate this answer.")
                last = row["last_recalled_at"]
                reinforce = (
                    not last or (now - datetime.fromisoformat(last)).total_seconds() >= 86400
                )
                db.execute(
                    "INSERT INTO events VALUES(?,?,?,?,?)",
                    (turn["turn_id"], memory_id, "used_in_answer", now.isoformat(), int(reinforce)),
                )
                if reinforce:
                    strength = current_strength(dict(row), now)
                    # Saturating boost; it too decays. One boost/day prevents chat feedback loops.
                    strength += 0.18 * (1 - strength)
                    half_life = min(365.0, row["half_life_days"] * 1.15)
                    db.execute(
                        """UPDATE memories SET anchor_strength=?,anchor_at=?,half_life_days=?,
                        recall_count=recall_count+1,last_recalled_at=? WHERE memory_id=?""",
                        (strength, now.isoformat(), half_life, now.isoformat(), memory_id),
                    )
            db.execute(
                "INSERT INTO turns VALUES(?,?,?,?,?)",
                (
                    turn["turn_id"],
                    turn["session_id"],
                    now.isoformat(),
                    turn["query"],
                    json.dumps(turn, ensure_ascii=False, allow_nan=False),
                ),
            )
            db.execute(
                "UPDATE sessions SET title=? WHERE session_id=? AND title='新对话'",
                (turn["query"][:40], turn["session_id"]),
            )

    def events(self, memory_id: str) -> list[dict]:
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM events WHERE memory_id=? ORDER BY created_at DESC", (memory_id,)
                )
            ]
