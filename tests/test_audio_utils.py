from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from services import audio_utils


def test_ensure_tmp_dir_creates_directory(tmp_audio_dir: Path) -> None:
    assert not tmp_audio_dir.exists()
    audio_utils.ensure_tmp_dir()
    assert tmp_audio_dir.is_dir()


def test_save_webm_bytes_writes_file(tmp_audio_dir: Path) -> None:
    path = audio_utils.save_webm_bytes(b"test audio data")
    assert path.exists()
    assert path.parent == tmp_audio_dir
    assert path.read_bytes() == b"test audio data"


def test_save_webm_bytes_empty(tmp_audio_dir: Path) -> None:
    path = audio_utils.save_webm_bytes(b"")
    assert path.exists()
    assert path.read_bytes() == b""


def test_save_webm_bytes_unique_paths(tmp_audio_dir: Path) -> None:
    path_a = audio_utils.save_webm_bytes(b"a")
    path_b = audio_utils.save_webm_bytes(b"b")
    assert path_a != path_b
    assert path_a.read_bytes() == b"a"
    assert path_b.read_bytes() == b"b"


def test_clear_recording_removes_file(tmp_audio_dir: Path) -> None:
    path = audio_utils.save_webm_bytes(b"data")
    assert path.exists()
    audio_utils.clear_recording(path)
    assert not path.exists()


def test_clear_recording_no_file(tmp_audio_dir: Path) -> None:
    path = tmp_audio_dir / "nonexistent.webm"
    audio_utils.clear_recording(path)
    assert not path.exists()


def test_clear_recording_swallows_oserror() -> None:
    class _RaisesOnUnlink:
        @staticmethod
        def unlink() -> None:
            raise PermissionError("access denied")

    audio_utils.clear_recording(_RaisesOnUnlink())  # type: ignore[arg-type]


def test_get_audio_duration_seconds_parses_ffprobe_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="12.34\n", stderr="")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) == pytest.approx(12.34)


def test_get_audio_duration_seconds_returns_none_on_invalid_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="N/A\n", stderr="")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) is None


def test_get_audio_duration_seconds_returns_none_on_ffprobe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("ffprobe not found")

    monkeypatch.setattr("services.audio_utils.subprocess.run", fake_run)
    assert audio_utils.get_audio_duration_seconds(Path("any.webm")) is None
