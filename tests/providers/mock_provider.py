"""Mock provider for testing — test double implementing AiProvider."""

from __future__ import annotations

from services.providers.base import AiProvider, ProviderError


class MockProvider:
    """Test double implementing the ``AiProvider`` protocol.

    Returns a fixed response string or raises a ``ProviderError`` when a
    ``side_effect`` is configured.  Used to test ``SoapGenerator`` and other
    consumers without calling a real AI API.

    Args:
        response: The fixed string to return from ``chat_completion``.
        side_effect: An optional exception to raise instead of returning
            the response.  Wrapped in ``ProviderError`` automatically.

    """

    def __init__(
        self,
        response: str = "",
        side_effect: BaseException | None = None,
    ) -> None:
        self._response = response
        self._side_effect = side_effect

    def chat_completion(
        self,
        messages: list[dict],  # noqa: ARG002
        model: str,  # noqa: ARG002
        temperature: float = 0.1,  # noqa: ARG002
    ) -> str:
        """Return the configured response or raise the configured error.

        Args:
            messages: Ignored by the mock.
            model: Ignored by the mock.
            temperature: Ignored by the mock.

        Returns:
            The fixed ``response`` string passed at construction.

        Raises:
            ProviderError: If a ``side_effect`` was configured at construction.

        """
        if self._side_effect is not None:
            raise ProviderError(
                str(self._side_effect),
                original_exception=self._side_effect,
            )
        return self._response


def _assert_is_ai_provider(instance: object) -> None:
    """Verify at runtime that an object satisfies the AiProvider protocol.

    This helper can be used in tests or registry validation to check that a
    candidate implements the required interface without forcing nominal
    subtyping.

    Args:
        instance: The object to check.

    Raises:
        AssertionError: If the object does not satisfy the protocol.

    """

    assert isinstance(instance, AiProvider), f"{type(instance).__name__} does not satisfy the AiProvider protocol"
