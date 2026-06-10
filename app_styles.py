"""Visual theme helpers for the Streamlit presentation layer.

This module is purely presentational: it owns the CSS injected into the
page and small HTML-rendering helpers (header, badges, status indicators)
used by ``app.py``. It contains no business logic and no dependency on
``services/``.
"""

from __future__ import annotations

import streamlit as st

APP_BRAND = "⚡ FAST SOAP IA · Asistente Clínico"
APP_TITLE = "⚡ FAST SOAP IA · Asistente de Evoluciones Clínicas"
APP_SUBTITLE = "Ingrese la evolución anterior y los cambios del turno para generar la nota SOAP automáticamente"
APP_BADGE = "Prototipo académico v1.0"

GLOBAL_CSS = """
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
    background-color: #2f6fed;
    color: #ffffff;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

.app-header__brand {
    font-weight: 700;
    font-size: 1.1rem;
}

.app-title {
    margin-bottom: 0.1rem;
}

.app-subtitle {
    color: #5b6472;
    margin-top: 0;
    margin-bottom: 1rem;
}

.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    line-height: 1.4;
}

.badge-info {
    background-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
}

.badge-success {
    background-color: #e6f7ec;
    color: #1a7f3c;
}

.badge-warning {
    background-color: #fff4e5;
    color: #b15c00;
}

.badge-error {
    background-color: #fdecec;
    color: #c0292c;
}

.card {
    border: 1px solid #e1e6ef;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f8fafc;
    margin-bottom: 1rem;
}

.card h5 {
    color: #2f6fed;
    margin-top: 0;
    margin-bottom: 0.4rem;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.status-idle {
    background-color: #eef1f6;
    color: #5b6472;
}

.status-recording {
    background-color: #fdecec;
    color: #c0292c;
}

.status-transcribing {
    background-color: #fff4e5;
    color: #b15c00;
}

.status-generating {
    background-color: #e8eefd;
    color: #2f6fed;
}

.status-done {
    background-color: #e6f7ec;
    color: #1a7f3c;
}

.status-error {
    background-color: #fdecec;
    color: #c0292c;
}

div.stButton > button[kind="primary"] {
    width: 100%;
    background-color: #2f6fed;
    border-color: #2f6fed;
    font-weight: 700;
}

/* Make the two side-by-side input panels match in height on desktop */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {
    height: 100%;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    height: 100%;
}

/* Compact layout on phones: shorter text areas, tighter header */
@media (max-width: 640px) {
    div[data-testid="stTextArea"] textarea {
        height: 140px !important;
        min-height: 140px !important;
    }

    .app-header {
        padding: 0.6rem 0.85rem;
    }

    .app-header__brand {
        font-size: 0.95rem;
    }

    .app-title {
        font-size: 1.4rem;
    }
}
"""

_STATUS_LABELS: dict[str, str] = {
    "idle": "⚪ En espera",
    "recording": "🔴 Grabando",
    "transcribing": "🟠 Transcribiendo audio",
    "generating": "🔵 Generando evolución",
    "done": "🟢 Completado",
    "error": "⚠️ Error",
}


def inject_global_styles() -> None:
    """Inject the shared CSS for the redesigned UI into the page."""
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)


def render_header(title: str, subtitle: str, badge_text: str) -> str:
    """Render the brand header bar plus the page title/subtitle as HTML."""
    return (
        '<div class="app-header">'
        f'<span class="app-header__brand">{APP_BRAND}</span>'
        f'<span class="badge badge-info">{badge_text}</span>'
        "</div>"
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
