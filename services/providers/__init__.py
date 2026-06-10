"""Provider abstraction package — public API exports.

Usage:

    from services.providers import AiProvider, ProviderRegistry, ProviderError

    registry = ProviderRegistry()
    registry.register("groq", GroqProvider)
    provider = registry.resolve()          # reads SOAP_PROVIDER env var
    response = provider.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        model="llama-3.1-8b-instant",
    )

To add a new provider, create a file ``services/providers/<name>_provider.py``
that implements the ``AiProvider`` protocol, then register it:

.. code-block:: python

    from services.providers import ProviderRegistry
    from services.providers.my_provider import MyProvider

    registry.register("my", MyProvider)
    # Set SOAP_PROVIDER=my in .env
"""

from __future__ import annotations

from services.providers.base import AiProvider, ProviderError
from services.providers.groq_provider import GroqProvider
from services.providers.registry import ProviderRegistry

__all__ = [
    "AiProvider",
    "GroqProvider",
    "ProviderError",
    "ProviderRegistry",
]
