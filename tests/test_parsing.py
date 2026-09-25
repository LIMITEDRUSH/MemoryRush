from memoryrush.parsing import parse_document


def test_markdown_parser_creates_stable_ids_and_removes_title() -> None:
    text = "# Reading Memory\r\n\r\nFirst paragraph.\r\ncontinued.\r\n\r\nSecond paragraph."

    first = parse_document("notes.md", text)
    second = parse_document("notes.md", text)

    assert first.document_id == second.document_id
    assert first.title == "Reading Memory"
    assert [paragraph.paragraph_id for paragraph in first.paragraphs] == ["p_001", "p_002"]
    assert first.paragraphs[0].text == "First paragraph. continued."
    assert parse_document("renamed.md", text).document_id == first.document_id


def test_parser_rejects_empty_text() -> None:
    try:
        parse_document("empty.txt", " \n\n ")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected empty text to be rejected")
