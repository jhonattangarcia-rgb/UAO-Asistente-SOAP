from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from services.transcriber import OpenRouterTranscriber


class TestGetDurationMs:
    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = "12.5\n"
        with patch("services.transcriber.subprocess.run", return_value=mock_proc):
            result = transcriber._get_duration_ms("test.mp3")
        assert result == 12500

    def test_ffprobe_failure(self, transcriber: OpenRouterTranscriber) -> None:
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
    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = b"mp3 data here"
        with patch("services.transcriber.subprocess.run", return_value=mock_proc):
            result = transcriber._extract_mp3_chunk("test.mp3", 0, 10000)
        assert result == b"mp3 data here"

    def test_ffmpeg_failure(self, transcriber: OpenRouterTranscriber) -> None:
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
    def test_success(self, transcriber: OpenRouterTranscriber) -> None:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"text": "transcribed text"}
        mock_resp.text = '{"text": "transcribed text"}'
        with patch("services.transcriber.requests.post", return_value=mock_resp):
            result = transcriber._call_api(b"audio data")
        assert result == "transcribed text"

    def test_401_unauthorized(self, transcriber: OpenRouterTranscriber) -> None:
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="Unauthorized"),
        ):
            transcriber._call_api(b"audio data")

    def test_429_retry_then_fail(self, transcriber: OpenRouterTranscriber) -> None:
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
        mock_resp = Mock()
        mock_resp.status_code = 403
        mock_resp.json.side_effect = ValueError("bad json")
        mock_resp.text = "forbidden plain text"
        with (
            patch("services.transcriber.requests.post", return_value=mock_resp),
            pytest.raises(RuntimeError, match="forbidden plain text"),
        ):
            transcriber._call_api(b"audio data")

    def test_no_api_key(self) -> None:
        t = OpenRouterTranscriber(api_key=None)
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY not provided"):
            t._call_api(b"audio data")

    def test_non_json_response(self, transcriber: OpenRouterTranscriber) -> None:
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
    def test_single_chunk(self, transcriber: OpenRouterTranscriber) -> None:
        with (
            patch.object(transcriber, "_get_duration_ms", return_value=5000),
            patch.object(transcriber, "_extract_mp3_chunk", return_value=b"mp3"),
            patch.object(transcriber, "_call_api", return_value="transcribed chunk"),
        ):
            result = transcriber.transcribe_file("test.mp3")
        assert result == "transcribed chunk"

    def test_multiple_chunks(self, transcriber: OpenRouterTranscriber) -> None:
        with (
            patch.object(transcriber, "_get_duration_ms", return_value=45000),
            patch.object(transcriber, "_extract_mp3_chunk", return_value=b"mp3"),
            patch.object(transcriber, "_call_api", return_value="chunk"),
        ):
            result = transcriber.transcribe_file("test.mp3")
        assert result == "chunk chunk chunk"
