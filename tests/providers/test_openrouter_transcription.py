"""Tests for OpenRouterTranscriptionProvider — HTTP boundary only.

Responsibility: verify that the provider handles success, authentication
errors, transient failures, retries, and malformed responses correctly.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from services.providers.base import ProviderError
from services.providers.openrouter_transcription import OpenRouterTranscriptionProvider


@pytest.fixture
def provider() -> OpenRouterTranscriptionProvider:
    """Return an OpenRouterTranscriptionProvider with a fake API key."""
    return OpenRouterTranscriptionProvider(api_key="test-api-key-12345")


class TestTranscribe:
    """transcribe() — HTTP communication with OpenRouter."""

    def test_success(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must return the transcribed text on a successful 200 response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "transcribed text"}
        mock_response.text = ""

        with patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response):
            result = provider.transcribe(b"audio data")

        assert result == "transcribed text"

    def test_401_unauthorized(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must raise ProviderError on 401."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            pytest.raises(ProviderError, match="Unauthorized"),
        ):
            provider.transcribe(b"audio data")

    def test_403_with_json(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must raise ProviderError with parsed JSON on 403."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "forbidden"}
        mock_response.text = ""

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            pytest.raises(ProviderError, match="403"),
        ):
            provider.transcribe(b"audio data")

    def test_403_non_json(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must raise ProviderError with plain text on 403 when response is not JSON."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.side_effect = ValueError("not json")
        mock_response.text = "forbidden plain text"

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            pytest.raises(ProviderError, match="forbidden plain text"),
        ):
            provider.transcribe(b"audio data")

    def test_429_retry_then_fail(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must retry on 429 up to max_retries and then raise ProviderError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            patch("services.providers.openrouter_transcription.time.sleep"),
            pytest.raises(ProviderError, match="after retries"),
        ):
            provider.transcribe(b"audio data")

    def test_timeout_retry_then_fail(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must retry on network timeout and then raise ProviderError."""
        timeout_err = requests.Timeout("Connection timed out")
        with (
            patch("services.providers.openrouter_transcription.requests.post", side_effect=timeout_err),
            patch("services.providers.openrouter_transcription.time.sleep"),
            pytest.raises(ProviderError, match="after retries"),
        ):
            provider.transcribe(b"audio data")

    def test_non_json_response(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must raise ProviderError when the 200 response is not valid JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("not json")
        mock_response.text = "not json at all"

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            pytest.raises(ProviderError, match="non-JSON"),
        ):
            provider.transcribe(b"audio data")

    def test_missing_text_field(self, provider: OpenRouterTranscriptionProvider) -> None:
        """Must raise ProviderError when the 200 JSON lacks 'text'."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"other": "data"}
        mock_response.text = ""

        with (
            patch("services.providers.openrouter_transcription.requests.post", return_value=mock_response),
            pytest.raises(ProviderError, match="missing transcription text"),
        ):
            provider.transcribe(b"audio data")

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}, clear=True)
    def test_no_api_key(self) -> None:
        """Must raise ProviderError when API key is not configured."""
        p = OpenRouterTranscriptionProvider(api_key=None)

        with (
            patch("services.providers.openrouter_transcription.requests.post"),
            patch("services.providers.openrouter_transcription.time.sleep"),
            pytest.raises(ProviderError, match="OPENROUTER_API_KEY not provided"),
        ):
            p.transcribe(b"audio data")
