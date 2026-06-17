"""Mock transcription provider for tests — returns fixed text without network calls.

Usage:
    provider = MockTranscriptionProvider(response="texto simulado")
    result = provider.transcribe(b"audio bytes")
"""

from __future__ import annotations

from services.providers.base import ProviderError


class MockTranscriptionProvider:
    """Test double that returns deterministic text without calling any API.

    Args:
        response: Text returned by ``transcribe()``.
        side_effect: If set, raised instead of returning ``response``.
            Useful for testing error handling in the orchestrator.

    """

    def __init__(
        self,
        response: str = "",
        *,
        side_effect: Exception | None = None,
    ) -> None:
        """Initialize the mock with a fixed response or optional error."""
        self._response = response
        self._side_effect = side_effect

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str = "es",
        audio_format: str = "mp3",
    ) -> str:
        """Return the configured response or raise the configured error.

        Args:
            audio_bytes: Ignored — the mock does not process audio.
            language: Ignored.
            audio_format: Ignored.

        Returns:
            The ``response`` string provided at construction.

        Raises:
            ProviderError: If ``side_effect`` was set at construction.

        """
        if self._side_effect is not None:
            raise ProviderError(str(self._side_effect))
        return self._response
