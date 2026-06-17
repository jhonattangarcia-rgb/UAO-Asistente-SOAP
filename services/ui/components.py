"""HTML-rendering helpers for the presentation layer.

Small pure functions that build HTML snippets (header, badges, status
indicators) consumed by ``app.py`` via ``st.markdown(..., unsafe_allow_html=True)``.
They depend only on brand constants and the CSS classes defined in
:mod:`services.ui.theme` — no business logic, no Streamlit calls.
"""

from __future__ import annotations

from services.ui.branding import APP_BRAND

_STATUS_LABELS: dict[str, str] = {
    "idle": "⚪ En espera",
    "recording": "🔴 Grabando",
    "transcribing": "🟠 Transcribiendo audio",
    "generating": "🔵 Generando evolución",
    "done": "🟢 Completado",
    "error": "⚠️ Error",
}


def render_header(title: str, subtitle: str, badge_text: str) -> str:
    """Render the brand header bar plus the page title/subtitle as HTML."""
    return (
        '<div class="app-header">'
        f'<span class="app-header__brand">{APP_BRAND}</span>'
        f'<span class="badge badge-info">{badge_text}</span>'
        "</div>"
        '<div class="app-header-spacer"></div>'
        f'<h1 class="app-title">{title}</h1>'
        f'<p class="app-subtitle">{subtitle}</p>'
    )


def render_badge(text: str, variant: str = "info") -> str:
    """Render a small rounded badge as HTML."""
    return f'<span class="badge badge-{variant}">{text}</span>'


def render_status_badge(state: str, detail: str = "") -> str:
    """Render a status badge for the given UI state.

    Falls back to the ``idle`` state for unknown values of ``state``.
    """
    label = _STATUS_LABELS.get(state)
    css_state = state if label is not None else "idle"
    label = label or _STATUS_LABELS["idle"]
    text = f"{label} · {detail}" if detail else label
    return f'<span class="status-badge status-{css_state}">{text}</span>'
