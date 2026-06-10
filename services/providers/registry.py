"""Provider registry — central catalog of AI provider implementations."""

from __future__ import annotations

import os
from typing import cast

from services.providers.base import AiProvider


class ProviderRegistry:
    """Registry of available AI provider implementations.

    Providers are registered by name and resolved either by explicit name or
    from the ``SOAP_PROVIDER`` environment variable (default ``"groq"``).

    Usage::

        registry = ProviderRegistry()
        registry.register("groq", GroqProvider)
        provider = registry.resolve()          # reads SOAP_PROVIDER env var
        response = provider.chat_completion(...)

    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._providers: dict[str, type] = {}

    def register(self, name: str, provider_cls: type) -> None:
        """Register a provider class under the given name.

        Args:
            name: Short identifier (e.g. ``"groq"``, ``"openai"``).
            provider_cls: A class that satisfies the ``AiProvider`` protocol.

        """
        self._providers[name] = provider_cls

    def resolve(self, name: str | None = None) -> AiProvider:
        """Return an instance of the named provider.

        If ``name`` is ``None`` the value of the ``SOAP_PROVIDER`` environment
        variable is used, falling back to ``"groq"``.

        Args:
            name: Provider name, or ``None`` to use the environment default.

        Returns:
            An instantiated provider.

        Raises:
            KeyError: If the name is not registered.

        """
        provider_name: str = name if name is not None else os.getenv("SOAP_PROVIDER", "groq")
        try:
            provider_cls = self._providers[provider_name]
        except KeyError:
            available = ", ".join(sorted(self._providers))
            msg = f"Unknown provider '{provider_name}'. Available providers: {available}"
            raise KeyError(msg) from None
        return cast(AiProvider, provider_cls())

    @property
    def registered_providers(self) -> list[str]:
        """Return sorted list of registered provider names."""
        return sorted(self._providers)
