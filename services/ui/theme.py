"""Global CSS theme for the Streamlit presentation layer.

Owns the single CSS blob injected into the page and the helper that
injects it. No business logic and no dependency on the rest of
``services/`` beyond Streamlit itself.
"""

from __future__ import annotations

import streamlit as st

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
    margin: 0;
    /* Fixed just below Streamlit's own header bar (3.75rem tall) so the
       app's branded header stays visible while scrolling. The
       .app-header-spacer below reserves the matching vertical space so
       content doesn't slide underneath it. */
    position: fixed;
    top: 3.75rem;
    left: 0;
    right: 0;
    z-index: 999991;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.app-header-spacer {
    height: 3.5rem;
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

/* Change-tracking (diff) view: red = deleted, green = inserted */
.diff-view {
    border: 1px solid #e1e6ef;
    border-radius: 0.5rem;
    padding: 1rem 1.15rem;
    background-color: #ffffff;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.95rem;
}

.diff-ins {
    background-color: #e6f7ec;
    color: #1a7f3c;
    text-decoration: none;
    border-radius: 3px;
    padding: 0 1px;
}

.diff-del {
    background-color: #fdecec;
    color: #c0292c;
    text-decoration: line-through;
    border-radius: 3px;
    padding: 0 1px;
}

/* Git-style line-level diff: stacked red/green blocks, easy to validate */
.diff-line {
    padding: 0.2rem 0.65rem;
    margin: 1px 0;
    border-left: 3px solid transparent;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.45;
}

.diff-line-ins {
    background-color: #e6f7ec;
    border-left-color: #1a7f3c;
    color: #14532d;
}

.diff-line-ins::before {
    content: "+ ";
    color: #1a7f3c;
    font-weight: 700;
}

.diff-line-del {
    background-color: #fdecec;
    border-left-color: #c0292c;
    color: #9b2c2c;
    text-decoration: line-through;
}

.diff-line-del::before {
    content: "− ";
    color: #c0292c;
    font-weight: 700;
    text-decoration: none;
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

    .app-header-spacer {
        /* Brand and badge wrap to two lines on narrow screens, so the
           fixed header is taller here than on desktop. */
        height: 4.75rem;
    }

    .app-header__brand {
        font-size: 0.95rem;
    }

    .app-title {
        font-size: 1.4rem;
    }

    /* Keep the main action reachable with the thumb: pin it to the
       bottom of the screen and reserve space so it never covers the
       results below it. */
    div[data-testid="stMainBlockContainer"] {
        padding-bottom: 4.5rem;
    }

    div.stButton:has(> button[kind="primary"]) {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        margin: 0;
        padding: 0.5rem 0.85rem;
        background-color: #ffffff;
        box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.08);
        z-index: 999991;
    }

    div.stButton > button[kind="primary"] {
        border-radius: 999px;
    }
}
"""


def inject_global_styles() -> None:
    """Inject the shared CSS for the redesigned UI into the page."""
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)
