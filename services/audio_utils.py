"""Utility functions for temporary audio file management."""

from __future__ import annotations

import contextlib
import subprocess
import uuid
from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent.parent / "tmp_audio"


def ensure_tmp_dir() -> None:
    """Create the temporary audio directory if it doesn't exist."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def save_webm_bytes(raw_bytes: bytes) -> Path:
    """Write raw WebM bytes to a uniquely-named temporary file.

    Args:
        raw_bytes: The audio data to save.

    Returns:
        Path to the newly written file. Each call creates a distinct
        file so concurrent sessions don't overwrite each other's audio.

    """
    ensure_tmp_dir()
    path = TMP_DIR / f"recording_{uuid.uuid4().hex}.webm"
    path.write_bytes(raw_bytes)
    return path


def clear_recording(path: Path) -> None:
    """Remove a recording file if it exists.

    Silently ignores any errors during removal (e.g. permission
    denied) to avoid crashing the UI.

    Args:
        path: Path to the recording file to remove.

    """
    with contextlib.suppress(OSError):
        path.unlink()


def get_audio_duration_seconds(path: Path) -> float | None:
    """Return the duration of an audio file in seconds, or None on failure.

    Uses ``ffprobe`` (part of ffmpeg, already required by the project) to
    read the container duration. Any failure — ffprobe missing, non-zero
    exit, or unparseable output — degrades gracefully to ``None`` so the
    UI can omit the duration without breaking.

    Args:
        path: Path to the audio file (e.g. a WebM recording).

    Returns:
        The duration in seconds as a float, or ``None`` if it cannot be
        determined.

    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return None

    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except (TypeError, ValueError):
        return None
