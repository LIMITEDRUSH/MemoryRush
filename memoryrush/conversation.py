"""Attach a reading to a persistent conversation without changing memory policy."""

from __future__ import annotations

from uuid import uuid4

from memoryrush.bank import MemoryBank, now_utc
from memoryrush.chat import answer
from memoryrush.parsing import parse_document
from memoryrush.pipeline import process_document


def read_in_conversation(
    bank: MemoryBank,
    provider,
    session_id: str,
    source_name: str,
    text: str,
    *,
    question: str = "",
    memory_budget: int = 5,
    highlighted_ids: tuple[str, ...] = (),
    turn_id: str | None = None,
    on_progress=None,
) -> dict:
    """An attachment yields a reading receipt or a grounded answer to its accompanying question.

    If question generation fails after a successful import, retain an honest reading receipt;
    do not tell the user their already-saved article was lost. Reading itself never reinforces.
    """
    turn_id = turn_id or uuid4().hex
    existing = bank.get_turn(turn_id)
    document = parse_document(source_name, text)
    if existing:
        if (
            existing["session_id"] != session_id
            or existing.get("reading", {}).get("document_id") != document.document_id
            or existing.get("reading", {}).get("question", "") != question.strip()
        ):
            raise ValueError("This reading request ID belongs to another submission.")
        return existing
    if session_id not in {session["session_id"] for session in bank.sessions()}:
        raise ValueError("Unknown conversation.")
    if len(question.strip()) > 1500:
        raise ValueError("附带问题请控制在 1500 字以内；正文放在文章附件中。")
    progress = on_progress or (lambda message: None)
    progress("正在提取记忆，并由所选模型逐项评分…")
    artifact = process_document(
        document,
        provider,
        memory_budget,
        profile=bank.setting("profile"),
        highlighted_ids=highlighted_ids,
        prior_memories=bank.memories(active_only=True),
    )
    progress("正在保存原文、评分和记忆…")
    count = bank.import_artifact(artifact)
    active = sum(m["document_id"] == document.document_id for m in bank.memories(True))
    reading = {
        "run_id": artifact.run_id,
        "document_id": document.document_id,
        "title": document.title,
        "source_name": source_name,
        "inserted": count,
        "active_count": active,
        "question": question.strip(),
        "validation_errors": artifact.validation.error_count,
        "preview": provider.name == "deterministic-preview",
    }
    answer_error = None
    if question.strip() and not reading["preview"]:
        progress("文章已保存，正在结合这篇文章回答你的问题…")
        try:
            return answer(
                bank,
                provider,
                session_id,
                question.strip(),
                turn_id=turn_id,
                document_id=document.document_id,
                reading=reading,
            )
        except (RuntimeError, ValueError, OSError) as exc:
            answer_error = str(exc)
    turn = {
        "kind": "reading",
        "turn_id": turn_id,
        "session_id": session_id,
        "query": question.strip() or f"阅读《{document.title}》",
        "answer": artifact.output.summary,
        "paragraphs": [{"text": artifact.output.summary, "citations": []}],
        "reading": reading,
        "answer_error": answer_error,
        "insufficient_evidence": False,
        "used_memory_ids": [],
        "retrieval": [],
        "created_at": now_utc().isoformat(),
        "model": provider.model_name,
        "provider": provider.name,
        "document_id": document.document_id,
    }
    bank.save_turn(turn, [])
    return turn
