import base64
import contextlib
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from services import audio_utils
from services.pdf_generator import generate_pdf
from services.soap_generator import SoapGenerator
from services.transcriber import OpenRouterTranscriber

# Load .env located next to this file if present, but do NOT override existing
# environment variables. This ensures that container/CI provided ENV vars take
# precedence while allowing local development via a .env file.
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=False)

GROQ_API_KEY = os.getenv("API_SECRET_KEY")
SOAP_MODEL = os.environ.get("SOAP_MODEL")

st.set_page_config(page_title="Asistente SOAP UCI", layout="wide")
st.title(" 🩺 Asistente de Evoluciones Clínicas (SOAP)")
st.caption("Prototipo de Validación Académica - Versión Estable Modular")

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
    cambios_dia = st.text_area("2. Escriba los CAMBIOS DEL DÍA (Texto libre):", height=200, key="cambios_dia")

# Recorder component (from repo-local frontend)
RECORDER_COMPONENT = None
try:
    RECORDER_COMPONENT = components.declare_component(
        "webm_recorder",
        path=str(Path(__file__).resolve().parent / "components" / "webm_recorder" / "frontend" / "dist"),
    )
except Exception:
    RECORDER_COMPONENT = None

if "recording_size" not in st.session_state:
    st.session_state["recording_size"] = 0
if "last_recording_b64" not in st.session_state:
    st.session_state["last_recording_b64"] = None


# Render recorder if available
captured_b64 = None
if RECORDER_COMPONENT:
    try:
        captured_b64 = RECORDER_COMPONENT()
    except Exception:
        captured_b64 = None

# Inicializar estados vacíos de forma segura
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
                generator = SoapGenerator(api_key=GROQ_API_KEY, model=SOAP_MODEL)
                result = generator.generate(evo_anterior, cambios_dia)

                st.session_state["justificacion"] = result.justificacion
                st.session_state["pdf_bytes"] = generate_pdf(
                    evo_anterior, cambios_dia, result.nueva_evo, result.justificacion
                )

            except Exception as e:
                st.error(f"Error de API: {str(e)}")

# --- MOSTRAR RESULTADOS ---
if st.session_state["justificacion"]:
    st.success("¡Evolución procesada con éxito!")

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
        try:
            raw = base64.b64decode(captured_b64)
        except Exception:
            raw = None
        if raw:
            audio_utils.save_webm_bytes(raw)
            tr = OpenRouterTranscriber(api_key=os.getenv("OPENROUTER_API_KEY"))
            try:
                transcript = tr.transcribe_file(str(audio_utils.TMP_WEBM))
            except Exception as e:
                # Bubble up transcriber errors to the UI for clarity
                st.error(f"Error en la transcripción: {e}")
                transcript = None

            with contextlib.suppress(Exception):
                audio_utils.TMP_WEBM.unlink()

            # Handle transcription results
            if not transcript:
                # Explicitly inform the user that transcription returned no text
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.warning(
                    "Transcripción completada pero sin texto. "
                    "Verifica OPENROUTER_API_KEY, el servicio de "
                    "OpenRouter y revisa los logs del servidor."
                )
            else:
                # Insert transcript automatically (Q1=B)
                # Store as last_transcript and mark as not consumed so the
                # text_area initial value will be populated on the next rerun.
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.session_state["last_transcript_time"] = __import__("time").time()
                st.success("Transcripción completada e insertada en 'Cambios del día'.")

            if hasattr(st, "experimental_rerun"):
                with contextlib.suppress(Exception):
                    st.experimental_rerun()
        else:
            st.error("No se pudo decodificar audio de la grabación.")
    except Exception as exc:
        st.error(f"Error en la transcripción: {exc}")
