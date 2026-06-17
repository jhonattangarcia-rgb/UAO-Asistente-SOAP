"""TDD tests for the word-level text diff used in the change-tracking view."""

from __future__ import annotations

from services.text_diff import (
    DiffLine,
    DiffSegment,
    compute_diff,
    compute_line_diff,
    line_diff_to_html,
    segments_to_html,
)


def test_identical_texts_are_all_equal() -> None:
    """compute_diff() must mark every segment as 'equal' for identical texts."""
    text = "Paciente estable sin cambios"
    segments = compute_diff(text, text)
    assert all(seg.op == "equal" for seg in segments)
    assert "".join(seg.text for seg in segments) == text


def test_empty_anterior_yields_single_insert() -> None:
    """compute_diff() must yield a single insert segment when 'anterior' is empty."""
    segments = compute_diff("", "Texto nuevo")
    assert segments == [DiffSegment(op="insert", text="Texto nuevo")]


def test_empty_nueva_yields_single_delete() -> None:
    """compute_diff() must yield a single delete segment when 'nueva' is empty."""
    segments = compute_diff("Texto viejo", "")
    assert segments == [DiffSegment(op="delete", text="Texto viejo")]


def test_both_empty_yields_empty_list() -> None:
    """compute_diff() must return an empty list when both texts are empty."""
    assert compute_diff("", "") == []


def test_mixed_change_is_reconstructible() -> None:
    """compute_diff() segments must allow rebuilding both original texts."""
    anterior = "TA 120 80 sin dolor"
    nueva = "TA 130 90 sin dolor"
    segments = compute_diff(anterior, nueva)
    reconstructed_anterior = "".join(s.text for s in segments if s.op in ("equal", "delete"))
    reconstructed_nueva = "".join(s.text for s in segments if s.op in ("equal", "insert"))
    assert reconstructed_anterior == anterior
    assert reconstructed_nueva == nueva
    assert any(s.op == "insert" for s in segments)
    assert any(s.op == "delete" for s in segments)


def test_consecutive_same_op_segments_are_merged() -> None:
    """compute_diff() must merge consecutive segments sharing the same operation."""
    segments = compute_diff("", "una dos tres")
    inserts = [s for s in segments if s.op == "insert"]
    assert len(inserts) == 1


def test_segments_to_html_escapes_and_wraps() -> None:
    """segments_to_html() must escape HTML and wrap insert/delete in styled spans."""
    segments = [
        DiffSegment(op="equal", text="A & B "),
        DiffSegment(op="delete", text="<viejo>"),
        DiffSegment(op="insert", text="<nuevo>"),
    ]
    html = segments_to_html(segments)
    assert "&amp;" in html
    assert "&lt;viejo&gt;" in html
    assert "&lt;nuevo&gt;" in html
    assert 'class="diff-del"' in html
    assert 'class="diff-ins"' in html
    assert "<span" not in html.split("A &amp; B ")[0]


def test_segments_to_html_empty_list_is_empty_string() -> None:
    """segments_to_html() must return an empty string for an empty segment list."""
    assert segments_to_html([]) == ""


def test_compute_line_diff_marks_whole_changed_lines() -> None:
    """compute_line_diff() must classify each line as equal, insert, or delete."""
    anterior = "linea uno\nlinea dos\nlinea tres"
    nueva = "linea uno\nlinea DOS modificada\nlinea tres"
    lines = compute_line_diff(anterior, nueva)
    assert DiffLine(op="equal", text="linea uno") in lines
    assert DiffLine(op="delete", text="linea dos") in lines
    assert DiffLine(op="insert", text="linea DOS modificada") in lines
    assert DiffLine(op="equal", text="linea tres") in lines


def test_compute_line_diff_replace_groups_deletes_before_inserts() -> None:
    """compute_line_diff() must emit all deletes before inserts for a replace."""
    lines = compute_line_diff("vieja", "nueva")
    ops = [dl.op for dl in lines]
    assert ops == ["delete", "insert"]


def test_compute_line_diff_identical_is_all_equal() -> None:
    """compute_line_diff() must classify every line as equal for identical texts."""
    text = "a\nb\nc"
    assert all(dl.op == "equal" for dl in compute_line_diff(text, text))


def test_line_diff_to_html_uses_block_classes_and_collapses_blank_equals() -> None:
    """line_diff_to_html() must use block classes and collapse blank equal lines."""
    lines = [
        DiffLine(op="equal", text="S (Subjetivo)"),
        DiffLine(op="equal", text="   "),
        DiffLine(op="delete", text="dolor <torácico>"),
        DiffLine(op="insert", text="sin dolor"),
    ]
    html = line_diff_to_html(lines)
    assert 'class="diff-line diff-line-del"' in html
    assert 'class="diff-line diff-line-ins"' in html
    assert "&lt;torácico&gt;" in html
    assert html.count('class="diff-line"') == 1


def test_line_diff_to_html_empty_is_empty_string() -> None:
    """line_diff_to_html() must return an empty string for an empty line list."""
    assert line_diff_to_html([]) == ""
