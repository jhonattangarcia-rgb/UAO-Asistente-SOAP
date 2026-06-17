"""Shared pytest fixtures for the test suite.

Provides reusable doubles and configuration shared across multiple
test modules: a mock AI provider, a transcriber with a fake API key,
and an isolated temporary directory for audio file tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from services.transcriber import OpenRouterTranscriber

from tests.providers.mock_provider import MockProvider


@pytest.fixture
def mock_provider() -> MockProvider:
    """Return a MockProvider configured with a fixed response string."""
    return MockProvider(response="test response")


@pytest.fixture
def mock_api_key() -> str:
    """Return a fake API key for tests that do not call a real service."""
    return "test-api-key-12345"


@pytest.fixture
def transcriber(mock_api_key: str) -> OpenRouterTranscriber:
    """Return an OpenRouterTranscriber initialized with a fake API key."""
    return OpenRouterTranscriber(api_key=mock_api_key)


@pytest.fixture
def tmp_audio_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect audio_utils.TMP_DIR to an isolated temporary directory."""
    aud_dir = tmp_path / "tmp_audio"
    monkeypatch.setattr("services.audio_utils.TMP_DIR", aud_dir)
    return aud_dir
