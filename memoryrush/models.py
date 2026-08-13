"""Backward-compatible model exports.

New code should import domain models from `memoryrush.domain`.
"""

from memoryrush.domain.models import Document, Paragraph, SourceDocument, SourceParagraph

__all__ = ["Document", "Paragraph", "SourceDocument", "SourceParagraph"]
