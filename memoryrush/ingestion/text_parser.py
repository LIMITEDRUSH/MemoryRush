"""TXT and Markdown parsing for Phase 1."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from memoryrush.domain import SourceDocument, SourceParagraph

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}


def parse_document(path: str | Path) -> SourceDocument:
    source_path = Path(path)
    if source_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported document type: {source_path.suffix}. Expected one of {supported}.")

    text = source_path.read_text(encoding="utf-8")
    normalized = _normalize_newlines(text)
    title = _extract_title(normalized, source_path)
    body = _drop_leading_markdown_title(normalized, source_path)
    paragraphs = _split_paragraphs(body)
    document_id = _stable_document_id(source_path, normalized)

    return SourceDocument(
        document_id=document_id,
        title=title,
        source_path=source_path.as_posix(),
        document_type=source_path.suffix.lower().lstrip("."),
        paragraphs=[
            SourceParagraph(
                paragraph_id=f"p_{index:03d}",
                document_id=document_id,
                text=paragraph,
                position=index,
                source_path=source_path.as_posix(),
            )
            for index, paragraph in enumerate(paragraphs, start=1)
        ],
    )


def parse_directory(path: str | Path) -> list[SourceDocument]:
    source_dir = Path(path)
    if not source_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {source_dir}")

    documents = []
    for file_path in sorted(source_dir.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_SUFFIXES:
            documents.append(parse_document(file_path))
    return documents


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _extract_title(text: str, source_path: Path) -> str:
    if source_path.suffix.lower() in {".md", ".markdown"}:
        for line in text.splitlines():
            match = re.match(r"^\s{0,3}#\s+(.+?)\s*$", line)
            if match:
                return match.group(1).strip()
    return source_path.stem.replace("_", " ").replace("-", " ").strip().title()


def _split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n+", text)
    paragraphs = []
    for block in blocks:
        paragraph = re.sub(r"[ \t]*\n[ \t]*", " ", block).strip()
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def _drop_leading_markdown_title(text: str, source_path: Path) -> str:
    if source_path.suffix.lower() not in {".md", ".markdown"}:
        return text

    lines = text.splitlines()
    if lines and re.match(r"^\s{0,3}#\s+.+?\s*$", lines[0]):
        return "\n".join(lines[1:]).strip()
    return text


def _stable_document_id(source_path: Path, text: str) -> str:
    digest = hashlib.sha1()
    digest.update(source_path.as_posix().encode("utf-8"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    return f"doc_{digest.hexdigest()[:12]}"
