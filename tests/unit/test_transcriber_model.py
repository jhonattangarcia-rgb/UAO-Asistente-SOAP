from __future__ import annotations

from typing import Any

from services.transcriber import OpenRouterTranscriber


def test_model_reads_from_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model-from-env")
    transcriber = OpenRouterTranscriber(api_key="test-key")
    assert transcriber.model == "test-model-from-env"


def test_model_fallback_when_env_missing(monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    transcriber = OpenRouterTranscriber(api_key="test-key")
    assert transcriber.model == "openai/whisper-large-v3-turbo"


def test_explicit_model_ignores_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "should-be-ignored")
    transcriber = OpenRouterTranscriber(api_key="test-key", model="explicit-model")
    assert transcriber.model == "explicit-model"
