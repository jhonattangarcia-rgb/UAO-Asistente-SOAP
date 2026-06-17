"""Audio transcription orchestrator.

Splits audio into chunks and delegates transcription to an injected
``TranscriptionProvider``.
"""

from __future__ import annotations

import logging
import subprocess

from services.providers.base import TranscriptionProvider

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class OpenRouterTranscriber:
    """Transcribe audio files by splitting into chunks and delegating to a provider.

    Splits long audio into chunks, transcodes each chunk to MP3 via
    ffmpeg, and sends each chunk to the injected ``TranscriptionProvider``.

    Args:
        provider: An implementation of ``TranscriptionProvider`` (e.g.
            ``OpenRouterTranscriptionProvider`` for production or
            ``MockTranscriptionProvider`` for tests).
        max_chunk_ms: Maximum chunk duration in milliseconds (default 20_000).

    """

    def __init__(
        self,
        provider: TranscriptionProvider,
        max_chunk_ms: int = 20_000,
    ) -> None:
        """Initialize the orchestrator with a provider and chunking parameters."""
        self.provider = provider
        self.max_chunk_ms = max_chunk_ms

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

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file by splitting it into chunks.

        Determines the total duration, splits the audio into
        ``max_chunk_ms``-sized segments, transcodes each to MP3, and
        sends them sequentially to the injected provider.  Results are
        joined with spaces.

        Args:
            file_path: Path to the audio file.

        Returns:
            Full transcription text.

        """
        duration_ms = self._get_duration_ms(file_path)
        chunks: list[tuple[int, int]] = []
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
            text = self.provider.transcribe(audio_bytes=mp3_bytes, audio_format="mp3")
            texts.append(text.strip())

        return " ".join(t for t in texts if t)
