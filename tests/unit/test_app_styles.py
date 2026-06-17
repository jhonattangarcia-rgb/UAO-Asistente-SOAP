"""Unit tests for the presentation-layer helpers in services.ui."""

from __future__ import annotations

from services import ui


def test_global_css_defines_expected_classes() -> None:
    """GLOBAL_CSS must define the core CSS classes used across the app."""
    css = ui.GLOBAL_CSS
    assert ".app-header" in css
    assert ".badge" in css
    assert ".card" in css


def test_render_header_includes_title_subtitle_and_badge() -> None:
    """render_header() must embed the title, subtitle, and badge text in its HTML."""
    html = ui.render_header("My Title", "My subtitle", "My Badge")
    assert "My Title" in html
    assert "My subtitle" in html
    assert "My Badge" in html
    assert "app-header" in html


def test_render_badge_includes_text_and_variant_class() -> None:
    """render_badge() must embed the label text and the variant-specific CSS class."""
    html = ui.render_badge("Hello", variant="success")
    assert "Hello" in html
    assert "badge" in html
    assert "badge-success" in html


def test_render_status_badge_known_states() -> None:
    """render_status_badge() must produce a state-specific class for every known state."""
    for state in ("idle", "recording", "transcribing", "generating", "done", "error"):
        html = ui.render_status_badge(state, detail="detalle")
        assert "detalle" in html
        assert f"status-{state}" in html


def test_render_status_badge_unknown_state_falls_back_to_idle() -> None:
    """render_status_badge() must fall back to the 'idle' class for unknown states."""
    html = ui.render_status_badge("not-a-real-state", detail="x")
    assert "status-idle" in html
