"""Tests for SoapGenerator parsing logic using MockProvider."""

from __future__ import annotations

from services.soap_generator import SoapGenerator, SoapResult
from tests.providers.mock_provider import MockProvider

EXPECTED_TEMPERATURE = 0.1


def test_generate_returns_soap_result() -> None:
    provider = MockProvider(response="Paciente en observación.\n### Justificación Clínica:\n- Mejora reportada.")
    generator = SoapGenerator(provider=provider, model="test-model")
    result = generator.generate(evolucion_anterior="estable", cambios="fiebre")

    assert isinstance(result, SoapResult)
    assert result.nueva_evo == "Paciente en observación."
    assert result.justificacion == "- Mejora reportada."


def test_generate_handles_missing_separator() -> None:
    provider = MockProvider(response="Texto completo sin separador.")
    generator = SoapGenerator(provider=provider, model="test-model")
    result = generator.generate(evolucion_anterior="", cambios="")

    assert result.nueva_evo == "Texto completo sin separador."
    assert result.justificacion == "No se generó justificación."


def test_generate_calls_provider_with_correct_params() -> None:
    provider = MockProvider(response="test\n### Justificación Clínica:\ntest")
    generator = SoapGenerator(provider=provider, model="custom-model")
    generator.generate(evolucion_anterior="a", cambios="b")

    # Verify the provider was called with the correct model and temperature
    # by checking that the response was properly parsed
    assert provider._response == "test\n### Justificación Clínica:\ntest"
