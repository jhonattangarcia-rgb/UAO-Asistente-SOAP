"""OpenRouter transcription provider — HTTP-based implementation of TranscriptionProvider.

Responsibility: encapsulate the HTTP call to OpenRouter's /v1/audio/transcriptions
endpoint, including authentication, retry logic, and response parsing.
"""

from __future__ import annotations

import base64
import logging
import os
import time

import requests

from services.providers.base import ProviderError

logger = logging.getLogger(__name__)


class OpenRouterTranscriptionProvider:
    """Transcribe audio chunks via the OpenRouter API.

    Args:
        api_key: OpenRouter API key. Falls back to ``OPENROUTER_API_KEY`` env var.
        model: Model name. Falls back to ``OPENROUTER_MODEL`` env var, then
            ``openai/whisper-large-v3-turbo``.
        max_retries: Maximum retry attempts on transient errors (default 3).
        timeout: HTTP request timeout in seconds (default 120).

    Raises:
        ProviderError: On any API or network failure.

    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: int = 120,
    ) -> None:
        """Initialize the provider with API key, model, and retry parameters."""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")
        self.max_retries = max_retries
        self.timeout = timeout
        self.endpoint = "https://openrouter.ai/api/v1/audio/transcriptions"

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str = "es",  # noqa: ARG002
        audio_format: str = "mp3",
    ) -> str:
        """Send an audio chunk to the OpenRouter transcription API.

        Implements automatic retries with exponential backoff for
        transient errors (429, 5xx, network timeouts).  Raises
        immediately on 401 or other 4xx errors.

        Args:
            audio_bytes: Raw audio data to transcribe.
            language: Expected language code (default ``"es"``).
            audio_format: MIME format of the audio (default ``"mp3"``).

        Returns:
            Transcribed text.

        Raises:
            ProviderError: On authentication failure, API errors, or if all
                retries are exhausted.

        """
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload: dict[str, object] = {
            "model": self.model,
            "input_audio": {"data": b64, "format": audio_format},
        }

        backoff = 1.0
        last_err: str | None = None
        for attempt in range(self.max_retries):
            if not self.api_key:
                raise ProviderError(
                    "OPENROUTER_API_KEY not provided. Set OPENROUTER_API_KEY in your environment.",
                    status_code=401,
                )
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            logger.info(
                "OpenRouter JSON attempt %d/%d, audio_format=%s, raw_bytes=%d, b64_len=%d",
                attempt + 1,
                self.max_retries,
                audio_format,
                len(audio_bytes),
                len(b64),
            )
            try:
                r = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)  # type: ignore[arg-type]
            except requests.RequestException as exc:
                last_err = str(exc)
                logger.warning("OpenRouter request failed on attempt %d: %s", attempt + 1, exc)
                time.sleep(backoff)
                backoff *= 2
                continue

            logger.info(
                "OpenRouter response status=%d, text_len=%d",
                r.status_code,
                len(r.text or ""),
            )

            if r.status_code == 401:  # noqa: PLR2004
                raise ProviderError(
                    f"Unauthorized (401). Check OPENROUTER_API_KEY. Response: {r.text}",
                    status_code=401,
                )
            if r.status_code == 429 or r.status_code >= 500:  # noqa: PLR2004
                last_err = f"{r.status_code}: {r.text}"
                logger.warning(
                    "OpenRouter transient error %d, retrying after %ss",
                    r.status_code,
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2
                continue
            if r.status_code >= 400:  # noqa: PLR2004
                try:
                    err_data = r.json()
                except Exception:
                    err_data = r.text
                raise ProviderError(
                    f"OpenRouter returned {r.status_code}: {err_data}",
                    status_code=r.status_code,
                )

            try:
                resp = r.json()
            except Exception as exc:
                raise ProviderError(
                    f"OpenRouter returned non-JSON response: {r.text}",
                ) from exc

            text: str | None = resp.get("text")
            if text is None:
                logger.warning("OpenRouter response JSON missing 'text' field: %s", resp)
                raise ProviderError(
                    f"OpenRouter response missing transcription text. Response: {resp}",
                )

            return text

        raise ProviderError(
            f"OpenRouter transcription failed after retries. Last error: {last_err}",
        )
