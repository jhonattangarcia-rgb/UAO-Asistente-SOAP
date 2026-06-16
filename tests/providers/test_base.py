"""Tests for AiProvider Protocol and ProviderError."""

from __future__ import annotations

from services.providers.base import AiProvider, ProviderError


class TestProviderError:
    """ProviderError wrapping and attribute access."""

    def test_basic_exception(self) -> None:
        error = ProviderError("something went wrong")
        assert str(error) == "something went wrong"
        assert error.original_exception is None
        assert error.status_code is None

    def test_with_original_exception(self) -> None:
        original = ValueError("bad value")
        error = ProviderError("wrapped", original_exception=original)
        assert error.original_exception is original
        assert error.status_code is None

    def test_with_status_code(self) -> None:
        error = ProviderError("HTTP error", status_code=429)
        assert error.status_code == 429

    def test_with_all_fields(self) -> None:
        original = ConnectionError("timeout")
        error = ProviderError("API timeout", original_exception=original, status_code=504)
        assert error.original_exception is original
        assert error.status_code == 504


class TestAiProviderProtocol:
    """Verify that the Protocol is correctly defined and runtime-checkable."""

    def test_protocol_is_runtime_checkable(self) -> None:
        # isinstance should work because of @runtime_checkable
        class ValidProvider:
            def chat_completion(
                self,
                messages: list[dict[str, str]],
                model: str,
                temperature: float = 0.1,
            ) -> str:
                return "ok"

        assert isinstance(ValidProvider(), AiProvider)

    def test_protocol_rejects_missing_method(self) -> None:
        class InvalidProvider:
            pass

        assert not isinstance(InvalidProvider(), AiProvider)

    def test_protocol_rejects_missing_method_name(self) -> None:
        class WrongName:
            def other_method(self) -> str:
                return "ok"

        assert not isinstance(WrongName(), AiProvider)
