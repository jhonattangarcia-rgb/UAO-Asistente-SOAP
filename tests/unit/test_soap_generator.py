"""Tests for SoapGenerator parsing logic using MockProvider."""

from __future__ import annotations

from services.soap_generator import SoapGenerator, SoapResult
from tests.providers.mock_provider import MockProvider


def test_generate_returns_soap_result() -> None:
    """generate() must split the provider response into nueva_evo and justificacion."""
    provider = MockProvider(
        response="Paciente en observación.\n### Justificación Clínica:\n- Mejora reportada.",
    )
    generator = SoapGenerator(provider=provider, model="test-model")
    result = generator.generate(evolucion_anterior="estable", cambios="fiebre")

    assert isinstance(result, SoapResult)
    assert result.nueva_evo == "Paciente en observación."
    assert result.justificacion == "- Mejora reportada."


def test_generate_handles_missing_separator() -> None:
    """generate() must use the full response as nueva_evo when no separator is present."""
    provider = MockProvider(response="Texto completo sin separador.")
    generator = SoapGenerator(provider=provider, model="test-model")
    result = generator.generate(evolucion_anterior="", cambios="")

    assert result.nueva_evo == "Texto completo sin separador."
    assert result.justificacion == "No se generó justificación."


def test_generate_calls_provider_with_correct_params() -> None:
    """generate() must invoke the provider and successfully parse its raw response."""
    provider = MockProvider(response="test\n### Justificación Clínica:\ntest")
    generator = SoapGenerator(provider=provider, model="custom-model")
    generator.generate(evolucion_anterior="a", cambios="b")

    assert provider._response == "test\n### Justificación Clínica:\ntest"
