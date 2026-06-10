"""Groq AI provider implementation."""

from __future__ import annotations

import os
from typing import Any

from groq import Groq

from services.providers.base import ProviderError


class GroqProvider:
    """Concrete AI provider that wraps the Groq SDK.

    Reads the API key from the constructor parameter and delegates chat
    completion requests to ``groq.Groq.chat.completions.create()``.

    Args:
        api_key: The Groq API key.  If not provided, falls back to the
            ``API_SECRET_KEY`` environment variable.
        client: Optional pre-configured ``groq.Groq`` instance (used for
            dependency injection in tests).

    """

    def __init__(
        self,
        api_key: str | None = None,
        client: Groq | None = None,
    ) -> None:
        """Initialize GroqProvider.

        Args:
            api_key: Groq API key. Falls back to ``API_SECRET_KEY`` env var.
            client: Optional pre-configured Groq client (used for DI in tests).

        """
        self._api_key = api_key or os.getenv("API_SECRET_KEY", "")
        self._client = client if client is not None else Groq(api_key=self._api_key)

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.1,
    ) -> str:
        """Send a chat completion request to the Groq API.

        Args:
            messages: List of message dicts with ``role`` and ``content``.
            model: Groq model identifier.
            temperature: Sampling temperature.

        Returns:
            The response text content.

        Raises:
            ProviderError: On any Groq API or network failure.

        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
            )
        except Exception as exc:
            status_code: int | None = None
            if hasattr(exc, "status_code"):
                status_code = exc.status_code
            raise ProviderError(
                str(exc),
                original_exception=exc,
                status_code=status_code,
            ) from exc
        return response.choices[0].message.content or ""
