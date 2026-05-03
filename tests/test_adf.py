from jira_mcp.adf import text_to_adf


def test_single_paragraph():
    doc = text_to_adf("hello world")
    assert doc["type"] == "doc"
    assert doc["version"] == 1
    assert doc["content"] == [
        {"type": "paragraph", "content": [{"type": "text", "text": "hello world"}]}
    ]


def test_blank_line_splits_paragraphs():
    doc = text_to_adf("first\n\nsecond")
    assert len(doc["content"]) == 2
    assert doc["content"][0]["content"][0]["text"] == "first"
    assert doc["content"][1]["content"][0]["text"] == "second"


def test_single_newline_is_hard_break():
    doc = text_to_adf("line1\nline2")
    types = [c["type"] for c in doc["content"][0]["content"]]
    assert "hardBreak" in types


def test_empty_string_returns_one_paragraph():
    doc = text_to_adf("")
    assert doc["content"] == [{"type": "paragraph", "content": []}]
