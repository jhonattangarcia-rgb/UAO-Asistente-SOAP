"""Tests for SoapGenerator refactored to use AiProvider."""

from __future__ import annotations

import pytest
from services.providers.base import ProviderError
from services.soap_generator import SoapGenerator, SoapResult

from tests.providers.mock_provider import MockProvider

SOAP_RESPONSE = (
    "S: Patient stable.\n"
    "O: Vitals normal.\n"
    "A: Improving.\n"
    "P: Continue current management.\n"
    "### Justificación Clínica:\n"
    "- Reason for changes."
)


class TestSoapGeneratorWithMockProvider:
    """SoapGenerator delegates to the injected provider."""

    def test_generate_returns_soap_result(self) -> None:
        """generate() must return a SoapResult containing the SOAP note and justification."""
        provider = MockProvider(response=SOAP_RESPONSE)
        generator = SoapGenerator(provider=provider, model="test-model")
        result = generator.generate(
            evolucion_anterior="Previous evolution.",
            cambios="Patient stable, no changes.",
        )
        assert isinstance(result, SoapResult)
        assert "S: Patient stable." in result.nueva_evo
        assert "Reason for changes." in result.justificacion

    def test_generate_delegates_to_provider(self) -> None:
        """generate() must return the SOAP body exactly as produced by the provider."""
        provider = MockProvider(response=SOAP_RESPONSE)
        generator = SoapGenerator(provider=provider, model="test-model")
        result = generator.generate("Previous", "Changes")
        assert result.nueva_evo == (
            "S: Patient stable.\nO: Vitals normal.\nA: Improving.\nP: Continue current management."
        )

    def test_generate_handles_missing_justification(self) -> None:
        """generate() must supply a default message when no justification block exists."""
        provider = MockProvider(response="Just S and O.")
        generator = SoapGenerator(provider=provider, model="test-model")
        result = generator.generate("Previous", "Changes")
        assert result.nueva_evo == "Just S and O."
        assert "No se generó" in result.justificacion

    def test_generate_propagates_provider_error(self) -> None:
        """generate() must propagate ProviderError raised by the underlying provider."""
        provider = MockProvider(side_effect=ConnectionError("API unavailable"))
        generator = SoapGenerator(provider=provider, model="test-model")
        with pytest.raises(ProviderError) as exc_info:
            generator.generate("Previous", "Changes")
        assert "API unavailable" in str(exc_info.value)
