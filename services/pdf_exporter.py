import re
from fpdf import FPDF
from fpdf.enums import WrapMode


def _limpiar_markdown(texto: str) -> str:
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.*?)\*", r"\1", texto)
    return texto


class PDFExporter(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Evolucion Clinica SOAP", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")


def generar_pdf(nota_soap: str, ruta_salida: str = "evolucion_soap.pdf") -> str:
    pdf = PDFExporter()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)

    texto_limpio = _limpiar_markdown(nota_soap)

    for linea in texto_limpio.splitlines():
        linea_limpia = linea.encode("latin-1", errors="replace").decode("latin-1")
        if linea_limpia.strip() == "":
            pdf.ln(4)
        else:
            pdf.multi_cell(
                0,
                7,
                linea_limpia,
                new_x="LMARGIN",
                new_y="NEXT",
                wrapmode=WrapMode.CHAR,
            )

    pdf.output(ruta_salida)
    return ruta_salida