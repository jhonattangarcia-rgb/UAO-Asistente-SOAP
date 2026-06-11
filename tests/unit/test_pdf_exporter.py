import os
from services.pdf_exporter import generar_pdf, _limpiar_markdown


def test_limpiar_markdown_asteriscos_dobles():
    texto = "**Subjetivo:** paciente con fiebre"
    resultado = _limpiar_markdown(texto)
    assert "**" not in resultado
    assert "Subjetivo:" in resultado


def test_limpiar_markdown_asteriscos_simples():
    texto = "*Objetivo:* temperatura 38.5"
    resultado = _limpiar_markdown(texto)
    assert "*" not in resultado
    assert "Objetivo:" in resultado


def test_generar_pdf_crea_archivo(tmp_path):
    ruta = str(tmp_path / "test_soap.pdf")
    nota = "Subjetivo: fiebre de 3 dias\nObjetivo: T 38.5\nAnalisis: infeccion\nPlan: antibiotico"
    resultado = generar_pdf(nota, ruta)
    assert os.path.exists(resultado)
    assert resultado.endswith(".pdf")


def test_generar_pdf_con_tildes(tmp_path):
    ruta = str(tmp_path / "test_tildes.pdf")
    nota = "Evaluacion: paciente con diagnostico de neumonia adquirida en la comunidad"
    resultado = generar_pdf(nota, ruta)
    assert os.path.exists(resultado)


def test_generar_pdf_con_caracteres_especiales(tmp_path):
    ruta = str(tmp_path / "test_especiales.pdf")
    nota = "Signos vitales: TA 120/80 mmHg, FC 90 lpm, FR 18 rpm, SatO2 95%"