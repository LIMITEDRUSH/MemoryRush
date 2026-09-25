"""Stable TXT and Markdown parsing for the reading assistant."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from memoryrush.models import SourceDocument, SourceParagraph

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _default_title(source_name: str) -> str:
    stem = Path(source_name).stem.replace("_", " ").replace("-", " ").strip()
    return stem or "Untitled reading"


def parse_document(source_name: str, text: str) -> SourceDocument:
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("The document is empty.")

    lines = normalized.split("\n")
    title = _default_title(source_name)
    if lines and re.match(r"^#\s+\S", lines[0].strip()):
        title = re.sub(r"^#\s+", "", lines[0].strip()).strip()
        lines = lines[1:]

    body = "\n".join(lines).strip()
    raw_paragraphs = re.split(r"\n\s*\n+", body)
    paragraphs: list[SourceParagraph] = []
    for raw in raw_paragraphs:
        folded = re.sub(r"\s*\n\s*", " ", raw).strip()
        if not folded:
            continue
        paragraphs.append(
            SourceParagraph(
                paragraph_id=f"p_{len(paragraphs) + 1:03d}",
                position=len(paragraphs),
                text=folded,
            )
        )

    if not paragraphs:
        raise ValueError("The document does not contain any readable paragraphs.")

    # Renaming a file must not create a second bank of identical memories.
    digest_input = normalized.encode()
    document_id = f"doc_{hashlib.sha1(digest_input).hexdigest()[:12]}"
    return SourceDocument(
        document_id=document_id,
        title=title,
        source_name=source_name,
        paragraphs=paragraphs,
    )


def parse_document_file(path: str | Path) -> SourceDocument:
    source_path = Path(path)
    if source_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported file type. Use one of: {supported}")
    return parse_document(source_path.name, source_path.read_text(encoding="utf-8"))
