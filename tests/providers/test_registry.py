"""Tests for ProviderRegistry."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from services.providers.registry import ProviderRegistry


class FakeProvider:
    """Minimal AiProvider implementation for registry tests."""

    def __init__(self, api_key: str = "") -> None:
        """Store the api_key, ignoring its value for test purposes."""
        self._api_key = api_key

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.1,
    ) -> str:
        """Return a fixed response string identifying the requested model."""
        return f"Fake response for {model}"


class BrokenProvider:
    """Non-AiProvider class used to test registration validation."""

    def __init__(self, api_key: str = "") -> None:
        """Store the api_key without implementing chat_completion()."""
        self._api_key = api_key


class TestProviderRegistry:
    """ProviderRegistry registration and resolution."""

    def setup_method(self) -> None:
        """Create a fresh, empty ProviderRegistry before each test."""
        self.registry = ProviderRegistry()

    def test_register_and_resolve_by_name(self) -> None:
        """resolve() must return an instance of the provider registered by name."""
        self.registry.register("fake", FakeProvider)
        provider = self.registry.resolve("fake")
        assert isinstance(provider, FakeProvider)

    def test_resolve_default_from_env(self) -> None:
        """resolve() with no name must use the SOAP_PROVIDER environment variable."""
        self.registry.register("custom", FakeProvider)
        with patch.dict(os.environ, {"SOAP_PROVIDER": "custom"}, clear=False):
            provider = self.registry.resolve()
        assert isinstance(provider, FakeProvider)

    def test_resolve_default_fallback_to_groq(self) -> None:
        """resolve() with no name and no env var must default to the 'groq' provider."""
        self.registry.register("groq", FakeProvider)
        with patch.dict(os.environ, {}, clear=True):
            provider = self.registry.resolve()
        assert isinstance(provider, FakeProvider)

    def test_resolve_unknown_provider_raises_error(self) -> None:
        """resolve() with an unregistered name must raise KeyError listing available names."""
        self.registry.register("fake", FakeProvider)
        with pytest.raises(KeyError) as exc_info:
            self.registry.resolve("nonexistent")
        assert "fake" in str(exc_info.value)

    def test_registered_providers_property(self) -> None:
        """registered_providers must list every name registered, in order."""
        self.registry.register("a", FakeProvider)
        self.registry.register("b", FakeProvider)
        providers = self.registry.registered_providers
        assert providers == ["a", "b"]

    def test_register_overwrites_existing(self) -> None:
        """register() must allow re-registering the same name without raising."""
        self.registry.register("dup", FakeProvider)
        self.registry.register("dup", FakeProvider)
        assert self.registry.registered_providers == ["dup"]


class TestNewProviderRegistration:
    """Verify that a new provider can be added without changing existing code."""

    def test_new_provider_works_without_modifying_existing_code(self) -> None:
        """Registering two new providers must not require touching registry internals."""
        registry = ProviderRegistry()
        registry.register("fake", FakeProvider)
        registry.register("custom", FakeProvider)

        provider = registry.resolve("custom")
        result = provider.chat_completion(
            messages=[{"role": "user", "content": "test"}],
            model="any-model",
        )
        assert "Fake response" in result
        assert registry.registered_providers == ["custom", "fake"]
