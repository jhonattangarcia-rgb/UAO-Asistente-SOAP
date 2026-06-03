import streamlit as st
import streamlit.components.v1 as components
from services import audio_utils
from services.transcriber import OpenRouterTranscriber
from groq import Groq
import difflib
from fpdf import FPDF
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env located next to this file if present, but do NOT override existing
# environment variables. This ensures that container/CI provided ENV vars take
# precedence while allowing local development via a .env file.
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=False)

# Accede a las claves de forma segura
api_key = os.getenv("API_SECRET_KEY")

# ==============================================================================
# CONFIGURACIÓN DE IA Y MODELO
# ==============================================================================
GROQ_API_KEY = os.getenv("API_SECRET_KEY")

# VARIABLE 1: LO QUE SE DEBE CONSERVAR (Estructura técnica fija de la aplicación)
# ¡No modifiques el título '### Justificación Clínica:' para que no se rompa el PDF!
PROMPT_ESTRUCTURA_FIJA = (
    "Eres un asistente médico experto en formato SOAP para UCI y hospitalización. "
    "Tu tarea es generar la nueva evolución del día de forma redactada e integrada en formato SOAP strico "
    "(Subjetivo, Objetivo, Análisis, Plan). Al final del texto, añade obligatoriamente una sección "
    "que empiece exactamente con el título '### Justificación Clínica:' seguido de viñetas explicativas."
)

# VARIABLE 2: LO QUE PUEDE CAMBIAR (Reglas de negocio, tono, estilo y contexto clínico)
# Aquí puedes experimentar libremente con el comportamiento y ajustar el "tuning" del modelo.
PROMPT_REGLAS_VARIABLES = (
    "Toma los datos de entrada y estructúralos estrictamente en formato SOAP:\n"
    "- S (Subjetivo): Síntomas referidos por el paciente.\n"
    "- O (Objetivo): Signos vitales, examen físico, resultados de laboratorio/imágenes.\n"
    "- A (Assessment/Análisis/Diagnóstico): Impresión diagnóstica, análisis de evolución, códigos CIE-10 sugeridos.\n"
    "- P (Plan): Tratamiento, medicamentos, indicaciones, ventilación, metas y seguimiento.\n\n"
    "REGLAS CLÍNICAS DE AUDITORÍA:\n"
    "1. No inventes ni alucines datos que no hayan sido explícitamente mencionados.\n"
    "2. Si algún dato del texto libre es ambiguo, colócalo en la sección del SOAP más lógica.\n"
    "3. Mantén terminología médica precisa y formal (español hospitalario de Colombia).\n"
    "4. Responde siempre en el mismo idioma del dictado.\n"
    "5. Compara activamente la nota del día anterior con los cambios de hoy. En la sección final obligatoria "
    "('### Justificación Clínica:'), responde detalladamente a estos tres puntos de control:\n"
    "   - ¿Había datos en la sección incorrecta el día anterior que se corrigieron hoy?\n"
    "   - ¿Faltaba alguna sección obligatoria o parámetro crítico?\n"
    "   - Justifica clínicamente el porqué de cada cambio (ej: variaciones de medicamentos, FiO2, laboratorios) "
    "y verifica que el diagnóstico principal cuente con su respectiva orientación CIE-10."
)
# ==============================================================================

st.set_page_config(page_title="Asistente SOAP UCI", layout="wide")
st.title(" 🩺 Asistente de Evoluciones Clínicas (SOAP)")
st.caption("Prototipo de Validación Académica - Versión Estable Modular")


# --- FUNCIÓN DEL PDF (Anti-Errores y Sin Asteriscos) ---
def generar_pdf_validacion(anterior, cambios, nueva, just):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def limpiar_texto(t):
        if not t:
            return ""
        texto_sin_markdown = t.replace("**", "")
        return texto_sin_markdown.encode("latin-1", "replace").decode("latin-1")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Validacion - Asistente Clinico IA", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, "1. DATOS DE ENTRADA (INPUTS)", ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Evolucion del Dia Anterior:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, limpiar_texto(anterior))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Cambios Reportados Hoy:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, limpiar_texto(cambios))
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(220, 235, 252)
    pdf.cell(0, 8, "2. RESULTADOS GENERADOS POR EL MODELO", ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Nueva Evolucion SOAP Sugerida:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, limpiar_texto(nueva))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Justificacion Clinica de los Cambios:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, limpiar_texto(just))

    return bytes(pdf.output())


# --- FORMULARIO DE ENTRADA ---
col1, col2 = st.columns(2)
with col1:
    evo_anterior = st.text_area("1. Pegue la evolución del DÍA ANTERIOR:", height=200)
with col2:
    # If a transcription just arrived, move it into the session_state key that
    # the widget will bind to BEFORE creating the widget. This avoids modifying
    # a widget-bound session_state after instantiation (which raises errors).
    last_transcript = st.session_state.get("last_transcript")
    consumed = st.session_state.get("last_transcript_consumed", True)
    if last_transcript and not consumed:
        # populate the widget-backed session key and mark consumed
        st.session_state["cambios_dia"] = last_transcript
        st.session_state["last_transcript_consumed"] = True

    # Create the text area bound to session_state['cambios_dia'] so it reflects
    # the transcription if we populated it above.
    cambios_dia = st.text_area(
        "2. Escriba los CAMBIOS DEL DÍA (Texto libre):", height=200, key="cambios_dia"
    )

# Recorder component (from Whisper Feature)
RECORDER_COMPONENT = None
try:
    RECORDER_COMPONENT = components.declare_component(
        "webm_recorder",
        path=str((__import__("pathlib").Path(__file__).resolve().parent.parent / "Whisper Feature" / "components" / "webm_recorder" / "frontend" / "dist")),
    )
except Exception:
    RECORDER_COMPONENT = None

if "recording_size" not in st.session_state:
    st.session_state["recording_size"] = 0
if "last_recording_b64" not in st.session_state:
    st.session_state["last_recording_b64"] = None

def _save_webm_b64(encoded: str) -> bytes | None:
    import base64

    try:
        raw = base64.b64decode(encoded)
        return raw
    except Exception:
        return None

# Render recorder if available
captured_b64 = None
if RECORDER_COMPONENT:
    try:
        captured_b64 = RECORDER_COMPONENT()
    except Exception:
        captured_b64 = None

# Inicializar estados vacíos de forma segura
if "html_diff" not in st.session_state:
    st.session_state["html_diff"] = None
if "justificacion" not in st.session_state:
    st.session_state["justificacion"] = None
if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None

# --- ACCIÓN DEL BOTÓN ---
if st.button("Generar Evolución y Justificación", type="primary"):
    if not evo_anterior or not cambios_dia:
        st.error("Por favor, llena ambos campos de texto.")
    elif GROQ_API_KEY == "TU_API_KEY_DE_GROQ_AQUI":
        st.warning("Configura tu API Key de Groq en la línea 8.")
    else:
        with st.spinner("Procesando datos clínicos con Groq..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                prompt_usuario = f"EVOLUCIÓN ANTERIOR:\n{evo_anterior}\n\nCAMBIOS DEL DÍA:\n{cambios_dia}"

                # Unificamos ambas variables globales para enviárselas al modelo en el rol de sistema
                prompt_sistema_completo = f"{PROMPT_ESTRUCTURA_FIJA}\n\nREGLAS DE COMPORTAMIENTO:\n{PROMPT_REGLAS_VARIABLES}"

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": prompt_sistema_completo},
                        {"role": "user", "content": prompt_usuario},
                    ],
                    temperature=0.1,
                )

                resultado_ia = response.choices[0].message.content
                partes = resultado_ia.split("### Justificación Clínica:")
                nueva_evo = partes[0].strip()
                justificacion = (
                    partes[1].strip()
                    if len(partes) > 1
                    else "No se generó justificación."
                )

                # Calcular el Diff visual para la web
                diff = difflib.ndiff(evo_anterior.split(), nueva_evo.split())
                html_diff = []
                for word in diff:
                    if word.startswith("+ "):
                        html_diff.append(
                            f"<span style='background-color: #d4edda; color: #155724; padding: 2px; border-radius: 3px;'><b>{word[2:]}</b></span>"
                        )
                    elif word.startswith("- "):
                        html_diff.append(
                            f"<span style='background-color: #f8d7da; color: #721c24; text-decoration: line-through; padding: 2px; border-radius: 3px;'>{word[2:]}</span>"
                        )
                    elif word.startswith("  "):
                        html_diff.append(word[2:])

                st.session_state["html_diff"] = " ".join(html_diff)
                st.session_state["justificacion"] = justificacion
                st.session_state["pdf_bytes"] = generar_pdf_validacion(
                    evo_anterior, cambios_dia, nueva_evo, justificacion
                )

            except Exception as e:
                st.error(f"Error de API: {str(e)}")

# --- MOSTRAR RESULTADOS ---
if st.session_state["html_diff"]:
    st.success("¡Evolución procesada con éxito!")

    st.subheader("📋 Nueva Evolución SOAP (Cambios resaltados)")
    st.markdown(
        f"<div style='border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; background-color: #ffffff; line-height: 1.6;'>{st.session_state['html_diff']}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("💡 Justificación Clínica Automatizada")
    st.info(st.session_state["justificacion"])

    st.markdown("---")
    st.subheader("📥 Zona de Evidencia y Validación")
    st.download_button(
        label="Descargar Reporte Clínico (PDF)",
        data=st.session_state["pdf_bytes"],
        file_name="reporte_caso_clinico_soap.pdf",
        mime="application/pdf",
    )

# Transcription flow: if recorder produced base64, save it and call transcriber
if captured_b64 and isinstance(captured_b64, str) and RECORDER_COMPONENT:
    st.success("Audio recibido. Iniciando transcripción...")
    try:
        raw = _save_webm_b64(captured_b64)
        if raw:
            audio_utils.ensure_tmp_dir()
            audio_utils.TMP_WEBM.write_bytes(raw)
            tr = OpenRouterTranscriber(api_key=os.getenv("OPENROUTER_API_KEY"))
            try:
                transcript = tr.transcribe_file(str(audio_utils.TMP_WEBM))
            except Exception as e:
                # Bubble up transcriber errors to the UI for clarity
                st.error(f"Error en la transcripción: {e}")
                transcript = None

            # Remove temporary file
            try:
                audio_utils.TMP_WEBM.unlink()
            except Exception:
                pass

            # Handle transcription results
            if not transcript:
                # Explicitly inform the user that transcription returned no text
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.warning(
                    "Transcripción completada pero sin texto. Verifica OPENROUTER_API_KEY, el servicio de OpenRouter y revisa los logs del servidor."
                )
            else:
                # Insert transcript automatically (Q1=B)
                # Store as last_transcript and mark as not consumed so the
                # text_area initial value will be populated on the next rerun.
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.session_state["last_transcript_time"] = __import__("time").time()
                st.success("Transcripción completada e insertada en 'Cambios del día'.")

            # Try to trigger a rerun if supported; otherwise the widget key will
            # ensure the text area reflects session_state on the next interaction.
            if hasattr(st, "experimental_rerun"):
                try:
                    st.experimental_rerun()
                except Exception:
                    # Non-fatal: continue without crashing
                    pass
        else:
            st.error("No se pudo decodificar audio de la grabación.")
    except Exception as exc:
        st.error(f"Error en la transcripción: {exc}")
