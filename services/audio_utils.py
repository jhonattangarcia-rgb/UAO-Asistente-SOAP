from __future__ import annotations

from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent.parent / "tmp_audio"
TMP_WEBM = TMP_DIR / "pending_recording.webm"


def ensure_tmp_dir() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def save_webm_bytes(raw_bytes: bytes) -> None:
    ensure_tmp_dir()
    TMP_WEBM.write_bytes(raw_bytes)


def clear_tmp_recording() -> None:
    try:
        if TMP_WEBM.exists():
            TMP_WEBM.unlink()
    except Exception:
        pass
