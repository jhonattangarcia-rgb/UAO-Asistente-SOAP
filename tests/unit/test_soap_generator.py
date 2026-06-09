from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.soap_generator import SoapGenerator, SoapResult

EXPECTED_TEMPERATURE = 0.1


def _make_mock_response(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [choice]
    return mock_response


@patch("services.soap_generator.Groq")
def test_generate_returns_soap_result(mock_groq: MagicMock) -> None:
    mock_response = _make_mock_response(
        "Paciente en observación.\n### Justificación Clínica:\n- Mejora reportada."
    )
    mock_groq.return_value.chat.completions.create.return_value = mock_response

    generator = SoapGenerator(api_key="test-key", model="test-model")
    result = generator.generate(evolucion_anterior="estable", cambios="fiebre")

    assert isinstance(result, SoapResult)
    assert result.nueva_evo == "Paciente en observación."
    assert result.justificacion == "- Mejora reportada."


@patch("services.soap_generator.Groq")
def test_generate_handles_missing_separator(mock_groq: MagicMock) -> None:
    mock_response = _make_mock_response("Texto completo sin separador.")
    mock_groq.return_value.chat.completions.create.return_value = mock_response

    generator = SoapGenerator(api_key="test-key", model="test-model")
    result = generator.generate(evolucion_anterior="", cambios="")

    assert result.nueva_evo == "Texto completo sin separador."
    assert result.justificacion == "No se generó justificación."


@patch("services.soap_generator.Groq")
def test_generate_calls_groq_with_correct_params(mock_groq: MagicMock) -> None:
    mock_response = _make_mock_response("test\n### Justificación Clínica:\ntest")
    mock_groq.return_value.chat.completions.create.return_value = mock_response

    generator = SoapGenerator(api_key="custom-key", model="custom-model")
    generator.generate(evolucion_anterior="a", cambios="b")

    mock_groq.assert_called_once_with(api_key="custom-key")
    mock_groq.return_value.chat.completions.create.assert_called_once()
    call_kwargs = mock_groq.return_value.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "custom-model"
    assert call_kwargs["temperature"] == EXPECTED_TEMPERATURE
