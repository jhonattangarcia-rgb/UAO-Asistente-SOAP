"""Presentation layer for the Streamlit UI.

Public API aggregating the brand constants, the global CSS theme and the
HTML-rendering helpers. ``app.py`` imports everything it needs from here:

    from services.ui import inject_global_styles, render_header, APP_TITLE

The submodules keep concerns separated (high cohesion, low coupling):
- ``branding``   — brand strings (data only)
- ``theme``      — CSS blob + ``inject_global_styles``
- ``components`` — HTML render helpers (header, badges, status)
"""

from services.ui.branding import APP_BADGE, APP_BRAND, APP_SUBTITLE, APP_TITLE
from services.ui.components import (
    render_badge,
    render_header,
    render_status_badge,
)
from services.ui.theme import GLOBAL_CSS, inject_global_styles

__all__ = [
    "APP_BADGE",
    "APP_BRAND",
    "APP_SUBTITLE",
    "APP_TITLE",
    "GLOBAL_CSS",
    "inject_global_styles",
    "render_badge",
    "render_header",
    "render_status_badge",
]
