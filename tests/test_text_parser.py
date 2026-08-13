from pathlib import Path

from memoryrush.domain import Document, Paragraph, SourceDocument, SourceParagraph
from memoryrush.ingestion.text_parser import parse_document, parse_directory


def test_parse_markdown_document_extracts_title_and_paragraphs(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("# My Title\n\nFirst paragraph.\n\nSecond paragraph.", encoding="utf-8")

    document = parse_document(source)

    assert isinstance(document, SourceDocument)
    assert document.title == "My Title"
    assert document.document_type == "md"
    assert len(document.paragraphs) == 2
    assert isinstance(document.paragraphs[0], SourceParagraph)
    assert document.paragraphs[0].paragraph_id == "p_001"
    assert document.paragraphs[0].document_id == document.document_id
    assert document.paragraphs[0].text == "First paragraph."


def test_parse_text_document_uses_filename_title(tmp_path: Path) -> None:
    source = tmp_path / "reading_memory.txt"
    source.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")

    document = parse_document(source)

    assert document.title == "Reading Memory"
    assert document.document_type == "txt"
    assert [p.position for p in document.paragraphs] == [1, 2]


def test_paragraph_ids_are_stable_for_unchanged_content(tmp_path: Path) -> None:
    source = tmp_path / "stable.md"
    source.write_text("# Stable\n\nFirst paragraph.\n\nSecond paragraph.", encoding="utf-8")

    first = parse_document(source)
    second = parse_document(source)

    assert first.document_id == second.document_id
    assert [p.paragraph_id for p in first.paragraphs] == [p.paragraph_id for p in second.paragraphs]


def test_parse_document_rejects_unsupported_file_type(tmp_path: Path) -> None:
    source = tmp_path / "paper.pdf"
    source.write_text("not supported yet", encoding="utf-8")

    try:
        parse_document(source)
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)
        assert ".md" in str(exc)
        assert ".txt" in str(exc)
    else:
        raise AssertionError("Expected unsupported file type to raise ValueError")


def test_parse_directory_finds_supported_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B", encoding="utf-8")
    (tmp_path / "ignore.pdf").write_text("no", encoding="utf-8")

    documents = parse_directory(tmp_path)

    assert len(documents) == 2


def test_domain_models_serialize_to_dict() -> None:
    paragraph = Paragraph(
        paragraph_id="p_001",
        document_id="doc_001",
        text="Memory is selective.",
        position=1,
        source_path="sample.txt",
    )
    document = Document(
        document_id="doc_001",
        title="Sample",
        source_path="sample.txt",
        document_type="txt",
        paragraphs=[paragraph],
    )

    assert document.to_dict() == {
        "document_id": "doc_001",
        "title": "Sample",
        "source_path": "sample.txt",
        "document_type": "txt",
        "paragraphs": [
            {
                "paragraph_id": "p_001",
                "document_id": "doc_001",
                "text": "Memory is selective.",
                "position": 1,
                "source_path": "sample.txt",
            }
        ],
    }
