"""AI provider abstraction — Protocol and error types.

Defines the contract that all AI providers must implement (AiProvider Protocol)
and the standardized error type (ProviderError) for wrapping provider-specific
exceptions.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class ProviderError(Exception):
    """Standardized error for AI provider failures.

    Wraps provider-specific exceptions into a uniform type so that consumers
    (SoapGenerator, etc.) do not depend on any particular SDK's exception
    hierarchy.

    Args:
        message: Human-readable error description.
        original_exception: The underlying SDK exception, if any.
        status_code: HTTP status code associated with the failure, if known.

    """

    def __init__(
        self,
        message: str,
        *,
        original_exception: BaseException | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize ProviderError.

        Args:
            message: Human-readable error description.
            original_exception: The underlying SDK exception, if any.
            status_code: HTTP status code associated with the failure, if known.

        """
        self.original_exception = original_exception
        self.status_code = status_code
        super().__init__(message)


@runtime_checkable
class AiProvider(Protocol):
    """Contract for AI chat-completion providers.

    Every concrete provider (GroqProvider, etc.) must satisfy this protocol.
    The single method ``chat_completion`` accepts the standard messages list,
    a model identifier, and a temperature parameter, returning the response
    content as a plain string.

    Implementations MUST raise ``ProviderError`` on any API or network failure.
    """

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.1,
    ) -> str:
        """Send a chat completion request and return the response text.

        Args:
            messages: List of message dicts, each with ``role`` and ``content``
                keys (standard OpenAI/ Groq format).
            model: Model identifier to use for completion (e.g.
                ``"llama-3.1-8b-instant"``).
            temperature: Sampling temperature (0.0 — 2.0).  Defaults to 0.1.

        Returns:
            The response content as a plain string.

        Raises:
            ProviderError: On any API or network failure.

        """
        ...
