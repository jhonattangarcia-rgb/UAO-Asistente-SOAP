"""PDF generation service for clinical validation reports.

Provides the generate_pdf function that creates a PDF document using fpdf2,
containing patient input data and the model-generated SOAP results.
"""

from __future__ import annotations

from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto_sin_markdown = texto.replace("**", "")
    return texto_sin_markdown.encode("latin-1", "replace").decode("latin-1")


def generate_pdf(evolucion_anterior: str, cambios: str, nueva_evo: str, justificacion: str) -> bytes:
    """Generate a clinical validation PDF report.

    Creates a PDF document using fpdf2 containing the input data (previous
    evolution and today's changes) and the generated model results (new SOAP
    evolution and clinical justification).

    Args:
        evolucion_anterior: The previous day's clinical evolution text.
        cambios: Today's reported changes or free-text clinical notes.
        nueva_evo: The generated SOAP evolution text from the model.
        justificacion: The clinical justification text from the model.

    Returns:
        bytes: The generated PDF document as a byte string, suitable for
            download or streaming.

    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Validacion - Asistente Clinico IA", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, "1. DATOS DE ENTRADA (INPUTS)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Evolucion del Dia Anterior:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _limpiar_texto(evolucion_anterior))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Cambios Reportados Hoy:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _limpiar_texto(cambios))
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(220, 235, 252)
    pdf.cell(0, 8, "2. RESULTADOS GENERADOS POR EL MODELO", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Nueva Evolucion SOAP Sugerida:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _limpiar_texto(nueva_evo))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Justificacion Clinica de los Cambios:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _limpiar_texto(justificacion))

    return bytes(pdf.output())
