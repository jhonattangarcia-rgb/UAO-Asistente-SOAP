"""Tests for OpenRouterTranscriber: ffprobe/ffmpeg helpers and orchestration."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from services.transcriber import OpenRouterTranscriber
from tests.providers.mock_transcription import MockTranscriptionProvider


class TestGetDurationMs:
    """_get_duration_ms() — ffprobe-based duration parsing."""

    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        """Must parse a valid ffprobe stdout value into milliseconds."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = "12.5\n"
        with patch("services.transcriber.subprocess.run", return_value=mock_proc):
            result = transcriber._get_duration_ms("test.mp3")
        assert result == 12500

    def test_ffprobe_failure(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError when ffprobe exits with a non-zero code."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = b"file not found"
        with (
            patch("services.transcriber.subprocess.run", return_value=mock_proc),
            pytest.raises(RuntimeError, match="ffprobe failed"),
        ):
            transcriber._get_duration_ms("nonexistent.mp3")

    def test_invalid_duration_output(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError when ffprobe stdout is not a valid number."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = "not-a-number\n"
        mock_proc.stderr = b""
        with (
            patch("services.transcriber.subprocess.run", return_value=mock_proc),
            pytest.raises(RuntimeError, match="Unable to parse duration"),
        ):
            transcriber._get_duration_ms("test.mp3")


class TestExtractMp3Chunk:
    """_extract_mp3_chunk() — ffmpeg-based audio chunk extraction."""

    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        """Must return the raw mp3 bytes produced by ffmpeg on success."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = b"mp3 data here"
        with patch("services.transcriber.subprocess.run", return_value=mock_proc):
            result = transcriber._extract_mp3_chunk("test.mp3", 0, 10000)
        assert result == b"mp3 data here"

    def test_ffmpeg_failure(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError when ffmpeg exits with a non-zero code."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = b""
        mock_proc.stderr = b"invalid input"
        with (
            patch("services.transcriber.subprocess.run", return_value=mock_proc),
            pytest.raises(RuntimeError, match="ffmpeg chunk extraction failed"),
        ):
            transcriber._extract_mp3_chunk("test.mp3", 0, 10000)


class TestTranscribeFile:
    """transcribe_file() — full pipeline orchestration across audio chunks."""

    def test_single_chunk(self) -> None:
        """Must return the single chunk's transcription for a short audio file."""
        provider = MockTranscriptionProvider(response="transcribed chunk")
        tr = OpenRouterTranscriber(provider=provider)
        with (
            patch.object(tr, "_get_duration_ms", return_value=5000),
            patch.object(tr, "_extract_mp3_chunk", return_value=b"mp3"),
        ):
            result = tr.transcribe_file("test.mp3")
        assert result == "transcribed chunk"

    def test_multiple_chunks(self) -> None:
        """Must join the transcriptions of all chunks for a longer audio file."""
        provider = MockTranscriptionProvider(response="chunk")
        tr = OpenRouterTranscriber(provider=provider)
        with (
            patch.object(tr, "_get_duration_ms", return_value=45000),
            patch.object(tr, "_extract_mp3_chunk", return_value=b"mp3"),
        ):
            result = tr.transcribe_file("test.mp3")
        assert result == "chunk chunk chunk"
