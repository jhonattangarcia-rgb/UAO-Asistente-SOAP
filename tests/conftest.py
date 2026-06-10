from __future__ import annotations

from pathlib import Path

import pytest

from services.transcriber import OpenRouterTranscriber
from tests.providers.mock_provider import MockProvider


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider(response="test response")


@pytest.fixture
def mock_api_key() -> str:
    return "test-api-key-12345"


@pytest.fixture
def transcriber(mock_api_key: str) -> OpenRouterTranscriber:
    return OpenRouterTranscriber(api_key=mock_api_key)


@pytest.fixture
def tmp_audio_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    aud_dir = tmp_path / "tmp_audio"
    aud_file = aud_dir / "pending_recording.webm"
    monkeypatch.setattr("services.audio_utils.TMP_DIR", aud_dir)
    monkeypatch.setattr("services.audio_utils.TMP_WEBM", aud_file)
    return aud_dir
