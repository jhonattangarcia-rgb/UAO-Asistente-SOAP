from __future__ import annotations

from services.prompt_builder import build_system_prompt, build_user_prompt


def test_build_system_prompt_returns_string() -> None:
    result = build_system_prompt()
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_system_prompt_contains_soap_keywords() -> None:
    result = build_system_prompt()
    assert "SOAP" in result
    assert "### Justificación Clínica:" in result


def test_build_user_prompt_returns_string() -> None:
    result = build_user_prompt(evolucion_anterior="paciente estable", cambios="fiebre")
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_user_prompt_interpolates_parameters() -> None:
    result = build_user_prompt(evolucion_anterior="test_anterior", cambios="test_cambios")
    assert "test_anterior" in result
    assert "test_cambios" in result


def test_build_user_prompt_handles_empty_parameters() -> None:
    result = build_user_prompt(evolucion_anterior="", cambios="")
    assert isinstance(result, str)
    assert len(result) > 0
