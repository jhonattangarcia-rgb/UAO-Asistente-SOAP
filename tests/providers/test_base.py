"""Tests for AiProvider Protocol and ProviderError."""

from __future__ import annotations

from services.providers.base import AiProvider, ProviderError


class TestProviderError:
    """ProviderError wrapping and attribute access."""

    def test_basic_exception(self) -> None:
        """A bare ProviderError must expose None for optional fields."""
        error = ProviderError("something went wrong")
        assert str(error) == "something went wrong"
        assert error.original_exception is None
        assert error.status_code is None

    def test_with_original_exception(self) -> None:
        """ProviderError must preserve a reference to the wrapped exception."""
        original = ValueError("bad value")
        error = ProviderError("wrapped", original_exception=original)
        assert error.original_exception is original
        assert error.status_code is None

    def test_with_status_code(self) -> None:
        """ProviderError must expose the HTTP status code when provided."""
        error = ProviderError("HTTP error", status_code=429)
        assert error.status_code == 429

    def test_with_all_fields(self) -> None:
        """ProviderError must preserve both original_exception and status_code together."""
        original = ConnectionError("timeout")
        error = ProviderError("API timeout", original_exception=original, status_code=504)
        assert error.original_exception is original
        assert error.status_code == 504


class TestAiProviderProtocol:
    """Verify that the Protocol is correctly defined and runtime-checkable."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """A class implementing chat_completion() must satisfy isinstance checks."""

        class ValidProvider:
            """Minimal class implementing the AiProvider protocol."""

            def chat_completion(
                self,
                messages: list[dict[str, str]],
                model: str,
                temperature: float = 0.1,
            ) -> str:
                """Return a fixed response, ignoring all arguments."""
                return "ok"

        assert isinstance(ValidProvider(), AiProvider)

    def test_protocol_rejects_missing_method(self) -> None:
        """A class with no methods must not satisfy the AiProvider protocol."""

        class InvalidProvider:
            """Empty class used to verify protocol rejection."""

        assert not isinstance(InvalidProvider(), AiProvider)

    def test_protocol_rejects_missing_method_name(self) -> None:
        """A class with a differently named method must not satisfy the protocol."""

        class WrongName:
            """Class exposing an unrelated method name."""

            def other_method(self) -> str:
                """Return a fixed string unrelated to the protocol."""
                return "ok"

        assert not isinstance(WrongName(), AiProvider)
