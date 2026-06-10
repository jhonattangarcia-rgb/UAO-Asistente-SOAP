"""Utility functions for temporary audio file management."""

from __future__ import annotations

from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent.parent / "tmp_audio"
TMP_WEBM = TMP_DIR / "pending_recording.webm"


def ensure_tmp_dir() -> None:
    """Create the temporary audio directory if it doesn't exist."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def save_webm_bytes(raw_bytes: bytes) -> None:
    """Write raw WebM bytes to the pending recording file.

    Args:
        raw_bytes: The audio data to save.

    """
    ensure_tmp_dir()
    TMP_WEBM.write_bytes(raw_bytes)


def clear_tmp_recording() -> None:
    """Remove the pending recording file if it exists.

    Silently ignores any errors during removal (e.g. permission
    denied) to avoid crashing the UI.

    """
    try:
        if TMP_WEBM.exists():
            TMP_WEBM.unlink()
    except Exception:
        pass
