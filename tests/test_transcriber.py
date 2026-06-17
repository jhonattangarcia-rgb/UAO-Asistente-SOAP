"""Tests for OpenRouterTranscriber: ffprobe/ffmpeg helpers and API calls."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
import requests
from services.transcriber import OpenRouterTranscriber


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


class TestCallApi:
    """_call_api() — OpenRouter HTTP transcription endpoint."""

    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        """Must return the transcribed text on a successful 200 response."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"text": "transcribed text"}
        mock_resp.text = '{"text": "transcribed text"}'
        with patch("services.transcriber.requests.post", return_value=mock_resp):
            result = transcriber._call_api(b"audio data")
        assert result == "transcribed text"

    def test_401_unauthorized(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError mentioning 'Unauthorized' on a 401 response."""
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="Unauthorized"),
        ):
            transcriber._call_api(b"audio data")

    def test_429_retry_then_fail(self, transcriber: OpenRouterTranscriber) -> None:
        """Must retry on 429 and finally raise RuntimeError after exhausting retries."""
        mock_resp = Mock()
        mock_resp.status_code = 429
        mock_resp.text = "Too Many Requests"
        with (
            patch("services.transcriber.time.sleep"),
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="after retries"),
        ):
            transcriber._call_api(b"audio data")

    def test_timeout_retry_then_fail(self, transcriber: OpenRouterTranscriber) -> None:
        """Must retry on request timeout and finally raise RuntimeError."""
        with (
            patch("services.transcriber.time.sleep"),
            patch(
                "services.transcriber.requests.post",
                side_effect=requests.Timeout("timeout"),
            ),
            pytest.raises(RuntimeError, match="after retries"),
        ):
            transcriber._call_api(b"audio data")

    def test_403_with_json(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError mentioning '403' when the body is valid JSON."""
        mock_resp = Mock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {"error": "forbidden"}
        mock_resp.text = '{"error": "forbidden"}'
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="403"),
        ):
            transcriber._call_api(b"audio data")

    def test_403_non_json(self, transcriber: OpenRouterTranscriber) -> None:
        """Must fall back to the raw response text when the 403 body is not JSON."""
        mock_resp = Mock()
        mock_resp.status_code = 403
        mock_resp.json.side_effect = ValueError("bad json")
        mock_resp.text = "forbidden plain text"
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="forbidden plain text"),
        ):
            transcriber._call_api(b"audio data")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""})
    def test_no_api_key(self) -> None:
        """Must raise RuntimeError when no API key is provided or configured."""
        t = OpenRouterTranscriber(api_key=None)
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY not provided"):
            t._call_api(b"audio data")

    def test_non_json_response(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError mentioning 'non-JSON' for an unparseable 200 body."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("no json")
        mock_resp.text = "not json"
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="non-JSON"),
        ):
            transcriber._call_api(b"audio data")

    def test_missing_text_field(self, transcriber: OpenRouterTranscriber) -> None:
        """Must raise RuntimeError when the JSON body lacks a 'text' field."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"other": "data"}
        mock_resp.text = '{"other": "data"}'
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="missing transcription text"),
        ):
            transcriber._call_api(b"audio data")


class TestTranscribeFile:
    """transcribe_file() — full pipeline orchestration across audio chunks."""

    def test_single_chunk(self, transcriber: OpenRouterTranscriber) -> None:
        """Must return the single chunk's transcription for a short audio file."""
        with (
            patch.object(transcriber, "_get_duration_ms", return_value=5000),
            patch.object(transcriber, "_extract_mp3_chunk", return_value=b"mp3"),
            patch.object(transcriber, "_call_api", return_value="transcribed chunk"),
        ):
            result = transcriber.transcribe_file("test.mp3")
        assert result == "transcribed chunk"

    def test_multiple_chunks(self, transcriber: OpenRouterTranscriber) -> None:
        """Must join the transcriptions of all chunks for a longer audio file."""
        with (
            patch.object(transcriber, "_get_duration_ms", return_value=45000),
            patch.object(transcriber, "_extract_mp3_chunk", return_value=b"mp3"),
            patch.object(transcriber, "_call_api", return_value="chunk"),
        ):
            result = transcriber.transcribe_file("test.mp3")
        assert result == "chunk chunk chunk"
