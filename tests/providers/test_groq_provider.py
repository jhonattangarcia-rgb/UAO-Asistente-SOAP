"""Tests for GroqProvider implementation."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from groq import APIError
from services.providers.base import ProviderError
from services.providers.groq_provider import GroqProvider


@pytest.fixture
def mock_groq_client() -> MagicMock:
    """Return a MagicMock that simulates a groq.Groq client."""
    client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    client.chat.completions.create.return_value = mock_response
    return client


class TestGroqProvider:
    """GroqProvider chat_completion behaviour."""

    def test_chat_completion_success(self, mock_groq_client: MagicMock) -> None:
        """Must return the model's content and forward the expected call arguments."""
        provider = GroqProvider(api_key="test-key", client=mock_groq_client)
        result = provider.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-8b-instant",
        )
        assert result == "Mocked response"
        mock_groq_client.chat.completions.create.assert_called_once_with(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.1,
        )

    def test_chat_completion_empty_content(self, mock_groq_client: MagicMock) -> None:
        """Must return an empty string when the model responds with no content."""
        mock_groq_client.chat.completions.create.return_value.choices[0].message.content = ""
        provider = GroqProvider(api_key="test-key", client=mock_groq_client)
        result = provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama-3.1-8b-instant",
        )
        assert result == ""

    def test_chat_completion_api_error(self, mock_groq_client: MagicMock) -> None:
        """Must wrap a Groq APIError in ProviderError, preserving the status code."""
        request = httpx.Request("POST", "https://api.groq.com/v1/chat/completions")
        api_error = APIError("Rate limit exceeded", request=request, body={})
        api_error.status_code = 429  # type: ignore[attr-defined]
        mock_groq_client.chat.completions.create.side_effect = api_error

        provider = GroqProvider(api_key="test-key", client=mock_groq_client)
        with pytest.raises(ProviderError) as exc_info:
            provider.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama-3.1-8b-instant",
            )
        assert exc_info.value.status_code == 429
        assert exc_info.value.original_exception is api_error

    def test_chat_completion_network_error(self, mock_groq_client: MagicMock) -> None:
        """Must wrap a low-level ConnectionError in ProviderError without a status code."""
        mock_groq_client.chat.completions.create.side_effect = ConnectionError("DNS failure")

        provider = GroqProvider(api_key="test-key", client=mock_groq_client)
        with pytest.raises(ProviderError) as exc_info:
            provider.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama-3.1-8b-instant",
            )
        assert exc_info.value.status_code is None
        assert exc_info.value.original_exception is not None
