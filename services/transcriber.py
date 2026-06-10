"""Audio transcription via the OpenRouter API with chunking and retry logic."""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import time

import requests

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class OpenRouterTranscriber:
    """Transcribe audio files using the OpenRouter API.

    Splits long audio into chunks, transcodes each chunk to MP3 via
    ffmpeg, and sends it to the OpenRouter /v1/audio/transcriptions
    endpoint with automatic retries on transient errors.

    Args:
        api_key: OpenRouter API key. Falls back to ``OPENROUTER_API_KEY`` env var.
        model: Model name. Falls back to ``OPENROUTER_MODEL`` env var, then
            ``openai/whisper-large-v3-turbo``.
        batch_size: Number of concurrent chunks (reserved for future use).
        language: Expected language code (default ``es``).

    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        batch_size: int = 4,
        language: str = "es",
    ) -> None:
        """Initialize the transcriber with API key, model, and chunking parameters."""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")
        self.batch_size = int(batch_size)
        self.language = language
        self.endpoint = "https://openrouter.ai/api/v1/audio/transcriptions"
        self.max_chunk_ms = 20_000

    def _get_duration_ms(self, file_path: str) -> int:
        """Return the total duration of an audio file in milliseconds.

        Uses ``ffprobe`` to read the file's duration metadata.

        Args:
            file_path: Path to the audio file.

        Returns:
            Duration in milliseconds.

        Raises:
            RuntimeError: If ffprobe fails or its output cannot be parsed.

        """
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()}")
        try:
            duration = float(proc.stdout.strip())
        except ValueError as exc:
            raise RuntimeError(f"Unable to parse duration from ffprobe output: {proc.stdout}") from exc
        return int(duration * 1000)

    def _extract_mp3_chunk(self, file_path: str, start_ms: int, duration_ms: int) -> bytes:
        """Extract a segment of audio as MP3 bytes.

        Uses ``ffmpeg`` to seek to ``start_ms`` and capture ``duration_ms``
        of audio, transcoded to mono 16 kHz MP3.

        Args:
            file_path: Path to the source audio file.
            start_ms: Start offset in milliseconds.
            duration_ms: Length of the segment in milliseconds.

        Returns:
            Raw MP3 bytes.

        Raises:
            RuntimeError: If ffmpeg fails.

        """
        start = start_ms / 1000.0
        duration = duration_ms / 1000.0
        command = [
            "ffmpeg",
            "-nostdin",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-i",
            file_path,
            "-t",
            str(duration),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "32k",
            "-f",
            "mp3",
            "pipe:1",
        ]
        proc = subprocess.run(command, capture_output=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg chunk extraction failed: {proc.stderr.decode('utf-8', 'ignore')}")
        return proc.stdout

    def _call_api(self, audio_bytes: bytes, audio_format: str = "mp3") -> str:
        """Send an audio chunk to the OpenRouter transcription API.

        Implements automatic retries with exponential backoff for
        transient errors (429, 5xx, network timeouts).  Raises
        immediately on 401 or other 4xx errors.

        Args:
            audio_bytes: Raw audio data to transcribe.
            audio_format: MIME format of the audio (default ``mp3``).

        Returns:
            Transcribed text.

        Raises:
            RuntimeError: On authentication failure, API errors, or if all
                retries are exhausted.

        """
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload: dict[str, object] = {
            "model": self.model,
            "input_audio": {"data": b64, "format": audio_format},
        }

        backoff = 1.0
        last_err: str | None = None
        for attempt in range(3):
            if not self.api_key:
                raise RuntimeError("OPENROUTER_API_KEY not provided. Set OPENROUTER_API_KEY in your environment.")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            logger.info(
                "OpenRouter JSON attempt %d/3, audio_format=%s, raw_bytes=%d, b64_len=%d",
                attempt + 1,
                audio_format,
                len(audio_bytes),
                len(b64),
            )
            try:
                r = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)  # type: ignore[arg-type]
            except requests.RequestException as exc:
                last_err = str(exc)
                logger.warning("OpenRouter request failed on attempt %d: %s", attempt + 1, exc)
                time.sleep(backoff)
                backoff *= 2
                continue

            # Log the basic response for diagnostics
            logger.info(
                "OpenRouter response status=%d, text_len=%d",
                r.status_code,
                len(r.text or ""),
            )

            if r.status_code == 401:  # noqa: PLR2004
                raise RuntimeError(f"Unauthorized (401). Check OPENROUTER_API_KEY. Response: {r.text}")
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
                raise RuntimeError(f"OpenRouter returned {r.status_code}: {err_data}")

            try:
                resp = r.json()
            except Exception as exc:
                raise RuntimeError(f"OpenRouter returned non-JSON response: {r.text}") from exc

            text: str | None = resp.get("text")
            if text is None:
                logger.warning("OpenRouter response JSON missing 'text' field: %s", resp)
                raise RuntimeError(f"OpenRouter response missing transcription text. Response: {resp}")

            return text

        raise RuntimeError(f"OpenRouter transcription failed after retries. Last error: {last_err}")

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file by splitting it into chunks.

        Determines the total duration, splits the audio into
        ``max_chunk_ms``-sized segments, transcodes each to MP3, and
        sends them sequentially to the OpenRouter API.  Results are
        joined with spaces.

        Args:
            file_path: Path to the audio file.

        Returns:
            Full transcription text.

        """
        duration_ms = self._get_duration_ms(file_path)
        chunks = []
        start_ms = 0
        while start_ms < duration_ms:
            chunk_duration = min(self.max_chunk_ms, duration_ms - start_ms)
            chunks.append((start_ms, chunk_duration))
            start_ms += chunk_duration

        logger.info(
            "Audio duration_ms=%d → %d chunk(s) of %ds each",
            duration_ms,
            len(chunks),
            self.max_chunk_ms // 1000,
        )

        texts: list[str] = []
        for index, (start_ms, length_ms) in enumerate(chunks, start=1):
            mp3_bytes = self._extract_mp3_chunk(file_path, start_ms, length_ms)
            logger.info(
                "Chunk %d/%d: start_ms=%d, duration_ms=%d, mp3_bytes=%d",
                index,
                len(chunks),
                start_ms,
                length_ms,
                len(mp3_bytes),
            )
            text = self._call_api(audio_bytes=mp3_bytes, audio_format="mp3")
            texts.append(text.strip())

        return " ".join(t for t in texts if t)
