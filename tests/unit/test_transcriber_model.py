"""Tests for OpenRouterTranscriptionProvider model resolution precedence."""

from __future__ import annotations

from typing import Any

from services.providers.openrouter_transcription import OpenRouterTranscriptionProvider


def test_model_reads_from_env(monkeypatch: Any) -> None:
    """The provider must use OPENROUTER_MODEL from the environment when set."""
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model-from-env")
    provider = OpenRouterTranscriptionProvider(api_key="test-key")
    assert provider.model == "test-model-from-env"


def test_model_fallback_when_env_missing(monkeypatch: Any) -> None:
    """The provider must fall back to the default model when the env var is unset."""
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    provider = OpenRouterTranscriptionProvider(api_key="test-key")
    assert provider.model == "openai/whisper-large-v3-turbo"


def test_explicit_model_ignores_env(monkeypatch: Any) -> None:
    """An explicit model argument must take precedence over the environment variable."""
    monkeypatch.setenv("OPENROUTER_MODEL", "should-be-ignored")
    provider = OpenRouterTranscriptionProvider(api_key="test-key", model="explicit-model")
    assert provider.model == "explicit-model"
