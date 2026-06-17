"""Tests for services.audio_utils: temp dir, save/clear, and ffprobe duration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from services import audio_utils


def test_ensure_tmp_dir_creates_directory(tmp_audio_dir: Path) -> None:
    """ensure_tmp_dir() must create the temp audio directory if missing."""
    assert not tmp_audio_dir.exists()
    audio_utils.ensure_tmp_dir()
    assert tmp_audio_dir.is_dir()


def test_save_webm_bytes_writes_file(tmp_audio_dir: Path) -> None:
    """save_webm_bytes() must write the exact bytes to a file in TMP_DIR."""
    path = audio_utils.save_webm_bytes(b"test audio data")
    assert path.exists()
    assert path.parent == tmp_audio_dir
    assert path.read_bytes() == b"test audio data"


def test_save_webm_bytes_empty(tmp_audio_dir: Path) -> None:
    """save_webm_bytes() must accept an empty payload without failing."""
    path = audio_utils.save_webm_bytes(b"")
    assert path.exists()
    assert path.read_bytes() == b""


def test_save_webm_bytes_unique_paths(tmp_audio_dir: Path) -> None:
    """Two consecutive calls must produce distinct file paths."""
    path_a = audio_utils.save_webm_bytes(b"a")
    path_b = audio_utils.save_webm_bytes(b"b")
    assert path_a != path_b
    assert path_a.read_bytes() == b"a"
    assert path_b.read_bytes() == b"b"


def test_clear_recording_removes_file(tmp_audio_dir: Path) -> None:
    """clear_recording() must delete an existing recording file."""
    path = audio_utils.save_webm_bytes(b"data")
    assert path.exists()
    audio_utils.clear_recording(path)
    assert not path.exists()


def test_clear_recording_no_file(tmp_audio_dir: Path) -> None:
    """clear_recording() must be a no-op when the file does not exist."""
    path = tmp_audio_dir / "nonexistent.webm"
    audio_utils.clear_recording(path)
    assert not path.exists()


def test_clear_recording_swallows_oserror() -> None:
    """clear_recording() must swallow OSError raised during unlink()."""

    class _RaisesOnUnlink:
        """Fake path whose unlink() always raises PermissionError."""

        @staticmethod
        def unlink() -> None:
            """Simulate a filesystem permission failure on delete."""
            raise PermissionError("access denied")

    audio_utils.clear_recording(_RaisesOnUnlink())  # type: ignore[arg-type]


def test_get_audio_duration_seconds_parses_ffprobe_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_audio_duration_seconds() must parse a valid ffprobe stdout value."""

    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Simulate ffprobe returning a valid duration string."""
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="12.34\n", stderr="")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) == pytest.approx(12.34)


def test_get_audio_duration_seconds_returns_none_on_invalid_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_audio_duration_seconds() must return None on non-numeric stdout."""

    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Simulate ffprobe returning a non-numeric duration string."""
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="N/A\n", stderr="")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) is None


def test_get_audio_duration_seconds_returns_none_on_ffprobe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_audio_duration_seconds() must return None if ffprobe is missing."""

    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Simulate ffprobe binary not being found on the system."""
        raise FileNotFoundError("ffprobe not found")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) is None
