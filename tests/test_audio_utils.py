from __future__ import annotations

from pathlib import Path

import pytest

from services import audio_utils


def test_ensure_tmp_dir_creates_directory(tmp_audio_dir: Path) -> None:
    assert not tmp_audio_dir.exists()
    audio_utils.ensure_tmp_dir()
    assert tmp_audio_dir.is_dir()


def test_save_webm_bytes_writes_file(tmp_audio_dir: Path) -> None:
    audio_utils.save_webm_bytes(b"test audio data")
    assert audio_utils.TMP_WEBM.exists()
    assert audio_utils.TMP_WEBM.read_bytes() == b"test audio data"


def test_save_webm_bytes_empty(tmp_audio_dir: Path) -> None:
    audio_utils.save_webm_bytes(b"")
    assert audio_utils.TMP_WEBM.exists()
    assert audio_utils.TMP_WEBM.read_bytes() == b""


def test_clear_tmp_recording_removes_file(tmp_audio_dir: Path) -> None:
    audio_utils.save_webm_bytes(b"data")
    assert audio_utils.TMP_WEBM.exists()
    audio_utils.clear_tmp_recording()
    assert not audio_utils.TMP_WEBM.exists()


def test_clear_tmp_recording_no_file(tmp_audio_dir: Path) -> None:
    audio_utils.clear_tmp_recording()
    assert not audio_utils.TMP_WEBM.exists()


def test_clear_tmp_recording_swallows_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    class _RaisesOnExists:
        @staticmethod
        def exists() -> bool:
            raise PermissionError("access denied")

    monkeypatch.setattr("services.audio_utils.TMP_WEBM", _RaisesOnExists())
    audio_utils.clear_tmp_recording()
