from __future__ import annotations

from services.pdf_generator import generate_pdf


def test_generate_pdf_returns_bytes() -> None:
    result = generate_pdf(
        evolucion_anterior="anterior",
        cambios="cambios",
        nueva_evo="nueva",
        justificacion="justificacion",
    )
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_pdf_starts_with_pdf_header() -> None:
    result = generate_pdf(
        evolucion_anterior="test",
        cambios="test",
        nueva_evo="test",
        justificacion="test",
    )
    assert result.startswith(b"%PDF-")


def test_generate_pdf_with_empty_strings() -> None:
    result = generate_pdf(
        evolucion_anterior="",
        cambios="",
        nueva_evo="",
        justificacion="",
    )
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result.startswith(b"%PDF-")
