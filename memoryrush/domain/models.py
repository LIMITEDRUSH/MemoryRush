"""Core domain models for parsed reading documents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceParagraph:
    paragraph_id: str
    document_id: str
    text: str
    position: int
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str
    source_path: str
    document_type: str
    paragraphs: list[SourceParagraph] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["paragraphs"] = [paragraph.to_dict() for paragraph in self.paragraphs]
        return data


# Backward-compatible aliases for the Phase 0 skeleton.
Paragraph = SourceParagraph
Document = SourceDocument
