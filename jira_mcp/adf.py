"""Plain-text -> Atlassian Document Format (ADF) helper.

The Jira Cloud v3 API requires comment/description bodies to be ADF JSON.
We support a minimal subset: paragraphs separated by blank lines.
"""

from __future__ import annotations

from typing import Any


def text_to_adf(text: str) -> dict[str, Any]:
    """Wrap plain text into a minimal valid ADF document.

    Blank lines split paragraphs; single newlines become hard breaks within a paragraph.
    """
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b for b in text.split("\n\n") if b.strip() != ""] or [""]
    paragraphs: list[dict[str, Any]] = []
    for block in blocks:
        lines = block.split("\n")
        content: list[dict[str, Any]] = []
        for i, line in enumerate(lines):
            if i > 0:
                content.append({"type": "hardBreak"})
            if line:
                content.append({"type": "text", "text": line})
        paragraphs.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": paragraphs}
