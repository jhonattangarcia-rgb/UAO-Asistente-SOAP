"""Word-level text diff for the change-tracking results view.

Pure module (no Streamlit dependency) that computes the differences
between the previous and the newly generated SOAP evolution and renders
them as HTML with red (deleted) / green (inserted) highlights.

Uses only the standard library (``difflib`` and ``html``) — no extra
dependencies, per the project constitution.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from html import escape
from typing import Literal, NamedTuple

DiffOp = Literal["equal", "insert", "delete"]

_TOKEN_PATTERN = re.compile(r"\S+|\s+")


class DiffSegment(NamedTuple):
    """A contiguous fragment of the diff.

    Attributes:
        op: Change type — ``"equal"`` (in both texts), ``"insert"`` (only
            in the new text) or ``"delete"`` (only in the previous text).
        text: The text fragment for this segment.

    """

    op: DiffOp
    text: str


def _tokenize(text: str) -> list[str]:
    """Split text into word and whitespace tokens, preserving spacing."""
    return _TOKEN_PATTERN.findall(text)


def compute_diff(anterior: str, nueva: str) -> list[DiffSegment]:
    """Compute the word-level diff between two texts.

    Tokenizes both texts (preserving whitespace) and classifies each
    fragment with ``difflib.SequenceMatcher``. Consecutive fragments with
    the same operation are merged into a single segment.

    Args:
        anterior: Text of the previous day's evolution.
        nueva: Text of the newly generated evolution.

    Returns:
        Ordered list of DiffSegment reconstructing ``nueva`` with insert
        marks and ``anterior`` with delete marks.

    """
    tokens_a = _tokenize(anterior)
    tokens_b = _tokenize(nueva)
    matcher = SequenceMatcher(a=tokens_a, b=tokens_b, autojunk=False)

    raw: list[DiffSegment] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            raw.append(DiffSegment(op="equal", text="".join(tokens_a[i1:i2])))
        elif tag == "delete":
            raw.append(DiffSegment(op="delete", text="".join(tokens_a[i1:i2])))
        elif tag == "insert":
            raw.append(DiffSegment(op="insert", text="".join(tokens_b[j1:j2])))
        elif tag == "replace":
            raw.append(DiffSegment(op="delete", text="".join(tokens_a[i1:i2])))
            raw.append(DiffSegment(op="insert", text="".join(tokens_b[j1:j2])))

    return _merge_adjacent(raw)


def _merge_adjacent(segments: list[DiffSegment]) -> list[DiffSegment]:
    """Merge consecutive segments sharing the same operation."""
    merged: list[DiffSegment] = []
    for seg in segments:
        if not seg.text:
            continue
        if merged and merged[-1].op == seg.op:
            merged[-1] = DiffSegment(op=seg.op, text=merged[-1].text + seg.text)
        else:
            merged.append(seg)
    return merged


def segments_to_html(segments: list[DiffSegment]) -> str:
    """Render diff segments as HTML safe for ``st.markdown``.

    Escapes the HTML special characters of each segment's text and wraps
    ``insert``/``delete`` segments in styled spans. ``equal`` segments are
    emitted as escaped text without a wrapping span.

    Args:
        segments: Output of :func:`compute_diff`.

    Returns:
        HTML string ready for ``st.markdown(html, unsafe_allow_html=True)``.

    """
    parts: list[str] = []
    for seg in segments:
        safe = escape(seg.text)
        if seg.op == "insert":
            parts.append(f'<span class="diff-ins">{safe}</span>')
        elif seg.op == "delete":
            parts.append(f'<span class="diff-del">{safe}</span>')
        else:
            parts.append(safe)
    return "".join(parts)


class DiffLine(NamedTuple):
    """A whole line classified for a Git-style unified line diff.

    Attributes:
        op: Change type — ``"equal"``, ``"insert"`` or ``"delete"``.
        text: The full text of the line (without trailing newline).

    """

    op: DiffOp
    text: str


def compute_line_diff(anterior: str, nueva: str) -> list[DiffLine]:
    """Compute a Git-style line-level diff between two texts.

    Splits both texts into lines and classifies each line as equal,
    inserted or deleted. Replaced regions are emitted as the old lines
    (delete) followed by the new lines (insert) — never interleaved word
    by word — which is far easier to read for clinical validation.

    Args:
        anterior: Text of the previous day's evolution.
        nueva: Text of the newly generated evolution.

    Returns:
        Ordered list of DiffLine reproducing the unified diff.

    """
    lines_a = anterior.splitlines()
    lines_b = nueva.splitlines()
    matcher = SequenceMatcher(a=lines_a, b=lines_b, autojunk=False)

    result: list[DiffLine] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("equal", "delete"):
            op: DiffOp = "equal" if tag == "equal" else "delete"
            result.extend(DiffLine(op=op, text=line) for line in lines_a[i1:i2])
        elif tag == "insert":
            result.extend(DiffLine(op="insert", text=line) for line in lines_b[j1:j2])
        elif tag == "replace":
            result.extend(DiffLine(op="delete", text=line) for line in lines_a[i1:i2])
            result.extend(DiffLine(op="insert", text=line) for line in lines_b[j1:j2])
    return result


def line_diff_to_html(lines: list[DiffLine]) -> str:
    """Render a line diff as stacked, color-coded blocks for ``st.markdown``.

    Each deleted line gets a red block (strikethrough), each inserted line a
    green block, and unchanged lines a plain block. Unchanged blank lines are
    collapsed to keep the view compact.

    Args:
        lines: Output of :func:`compute_line_diff`.

    Returns:
        HTML string ready for ``st.markdown(html, unsafe_allow_html=True)``.

    """
    rows: list[str] = []
    for dl in lines:
        # Collapse unchanged blank lines to reduce vertical noise.
        if dl.op == "equal" and not dl.text.strip():
            continue
        safe = escape(dl.text) or "&nbsp;"
        if dl.op == "insert":
            rows.append(f'<div class="diff-line diff-line-ins">{safe}</div>')
        elif dl.op == "delete":
            rows.append(f'<div class="diff-line diff-line-del">{safe}</div>')
        else:
            rows.append(f'<div class="diff-line">{safe}</div>')
    return "".join(rows)
