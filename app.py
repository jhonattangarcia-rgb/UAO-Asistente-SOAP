import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from services import audio_utils
from services.pdf_generator import generate_pdf
from services.persistence.repository import RepositorioSupabase
from services.persistence.service import ServicioPersistenciaSOAP, ValidationError
from services.providers import GroqProvider, ProviderRegistry
from services.providers.openrouter_transcription import OpenRouterTranscriptionProvider
from services.soap_generator import SoapGenerator
from services.text_diff import compute_line_diff, line_diff_to_html
from services.transcriber import OpenRouterTranscriber
from services.ui import (
    APP_BADGE,
    APP_SUBTITLE,
    APP_TITLE,
    inject_global_styles,
    render_badge,
    render_header,
    render_status_badge,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Load .env located next to this file if present, but do NOT override existing
# environment variables. This ensures that container/CI provided ENV vars take
# precedence while allowing local development via a .env file.
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=False)

GROQ_API_KEY = os.getenv("API_SECRET_KEY")
SOAP_MODEL = os.environ.get("SOAP_MODEL")

# Provider registry — set up once at startup
_provider_registry = ProviderRegistry()
_provider_registry.register("groq", GroqProvider)

st.set_page_config(page_title="Asistente SOAP UCI V 1.0.0", layout="wide")
inject_global_styles()
st.markdown(render_header(APP_TITLE, APP_SUBTITLE, APP_BADGE), unsafe_allow_html=True)


# --- ACCESO CACHEADO A LA CAPA DE PERSISTENCIA (T003) ---
@st.cache_resource
def get_persistence_service() -> ServicioPersistenciaSOAP:
    """Build (once per session) the SOAP persistence service over Supabase."""
    return ServicioPersistenciaSOAP(RepositorioSupabase())


# --- INICIALIZACIÓN SEGURA DEL ESTADO DE SESIÓN (T004) ---
_DEFAULT_STATE: dict[str, Any] = {
    "patient_id": None,
    "historial_evoluciones": [],
    "historial_error": None,
    "justificacion": None,
    "nueva_evo": None,
    "evo_anterior_used": None,
    "pdf_bytes": None,
    "generation_error": None,
    "save_success": None,
    "save_error": None,
    "audio_duration_s": None,
}
for _key, _default in _DEFAULT_STATE.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# Nonce para las claves de los text_area de los bloques 1 y 2. Al reiniciar se
# incrementa, de modo que Streamlit instancia widgets NUEVOS y vacíos (resetear
# borrando la clave no es fiable cuando el valor también se setea por código).
_nonce = st.session_state.setdefault("form_nonce", 0)
EVO_KEY = f"evo_anterior_{_nonce}"
CAMBIOS_KEY = f"cambios_dia_{_nonce}"
PATIENT_KEY = f"patient_id_input_{_nonce}"
FECHA_KEY = f"fecha_idx_{_nonce}"


def _format_fecha(value: object) -> str:
    """Format a timestamptz value (str or datetime) as 'YYYY-MM-DD HH:MM'."""
    text = str(value).replace("T", " ")
    return text[:16]


# === MÓDULO 0: SELECCIÓN DE HISTORIAL CLÍNICO (US1) ===
with st.container(border=True):
    st.markdown("##### 0. Selección de historial clínico")
    _evos = st.session_state.get("historial_evoluciones", [])
    # Evitar un índice inválido (tipo incorrecto o fuera de rango) al cambiar
    # de paciente. Debe hacerse ANTES de instanciar el widget con key="fecha_idx".
    _stored_idx = st.session_state.get(FECHA_KEY)
    if _stored_idx is not None and (not isinstance(_stored_idx, int) or _stored_idx >= len(_evos)):
        st.session_state.pop(FECHA_KEY, None)
    col_pac, col_buscar, col_fecha, col_cargar = st.columns(
        [2.4, 1, 2.4, 1.6],
        vertical_alignment="bottom",
    )
    with col_pac:
        st.text_input("Paciente", key=PATIENT_KEY, placeholder="Ej: PAC-001")
    with col_buscar:
        buscar = st.button("🔍 Buscar", use_container_width=True)
    with col_fecha:
        st.selectbox(
            "Fecha de evolución a cargar",
            options=list(range(len(_evos))),
            format_func=lambda i: _format_fecha(_evos[i]["fecha_creacion"]),
            key=FECHA_KEY,
            disabled=not _evos,
            placeholder="Busque un paciente primero",
        )
    with col_cargar:
        cargar = st.button(
            "Cargar evolución anterior",
            use_container_width=True,
            disabled=not _evos,
        )
    if st.session_state.get("historial_error"):
        st.markdown(
            render_status_badge("error", detail=st.session_state["historial_error"]),
            unsafe_allow_html=True,
        )
    elif st.session_state.get("patient_id"):
        st.caption(
            f"Paciente {st.session_state['patient_id']} · "
            f"{len(_evos)} evolución(es) en historial. "
            "Al cargar, el campo 'Evolución del día anterior' se completará automáticamente."
        )

# Handler: búsqueda de paciente (US1 / T006)
if buscar:
    pid = (st.session_state.get(PATIENT_KEY) or "").strip()
    st.session_state["save_success"] = None
    st.session_state["save_error"] = None
    if not pid:
        st.session_state["historial_error"] = "Ingrese un ID de paciente antes de buscar."
        st.session_state["historial_evoluciones"] = []
        st.session_state["patient_id"] = None
    else:
        try:
            respuesta = get_persistence_service().obtener_por_paciente(pid)
            evoluciones = respuesta["evoluciones"]
            if not evoluciones:
                st.session_state["historial_error"] = (
                    f"El paciente '{pid}' no está registrado o no tiene historia previa. "
                    "No es posible generar una evolución sin una historia registrada."
                )
                st.session_state["historial_evoluciones"] = []
                st.session_state["patient_id"] = None
            else:
                st.session_state["historial_evoluciones"] = evoluciones
                st.session_state["patient_id"] = pid.upper()
                st.session_state["historial_error"] = None
        except ValidationError as exc:
            st.session_state["historial_error"] = f"Identificador inválido: {exc}"
            st.session_state["historial_evoluciones"] = []
            st.session_state["patient_id"] = None
        except Exception as exc:  # noqa: BLE001 — conexión/PostgREST: degradar con mensaje
            logger.exception("Error consultando historial del paciente")
            st.session_state["historial_error"] = f"Error al consultar la base de datos: {exc}"
            st.session_state["historial_evoluciones"] = []
            st.session_state["patient_id"] = None
    st.rerun()

# Handler: cargar evolución anterior seleccionada (US1 / T008)
if cargar and st.session_state.get("historial_evoluciones"):
    idx = st.session_state.get(FECHA_KEY) or 0
    evoluciones = st.session_state["historial_evoluciones"]
    if 0 <= idx < len(evoluciones):
        # Poblar el campo del bloque 1 ANTES de instanciar el widget (siguiente run).
        st.session_state[EVO_KEY] = evoluciones[idx]["soap_result"]
        st.rerun()

# --- FORMULARIO DE ENTRADA (bloques 1 y 2 — sin cambios de comportamiento, FR-009) ---
col1, col2 = st.columns(2)
with col1, st.container(border=True):
    evo_anterior = st.text_area(
        "1. Pegue la evolución del DÍA ANTERIOR:",
        height=200,
        key=EVO_KEY,
    )
with col2, st.container(border=True):
    # If a transcription just arrived, move it into the session_state key that
    # the widget will bind to BEFORE creating the widget. This avoids modifying
    # a widget-bound session_state after instantiation (which raises errors).
    last_transcript = st.session_state.get("last_transcript")
    consumed = st.session_state.get("last_transcript_consumed", True)
    if last_transcript and not consumed:
        # populate the widget-backed session key and mark consumed
        st.session_state[CAMBIOS_KEY] = last_transcript
        st.session_state["last_transcript_consumed"] = True
        logger.info("col2: applied last_transcript (len=%d) into cambios_dia", len(last_transcript))

    # Create the text area bound to the nonce-based key so it reflects the
    # transcription if we populated it above.
    cambios_dia = st.text_area(
        "2. Escriba los CAMBIOS DEL DÍA (Texto libre):",
        height=200,
        key=CAMBIOS_KEY,
        placeholder=(
            "Ej: Signos vitales estables, sin cambios neurológicos, "
            "se ajusta dosis de antibiótico, otros cambios del turno..."
        ),
    )

# --- GRABADOR DE AUDIO Y TRANSCRIPCIÓN (reubicado debajo de bloques 1 y 2 — US4 / T018) ---
RECORDER_COMPONENT = None
try:
    RECORDER_COMPONENT = components.declare_component(
        "webm_recorder",
        path=str(Path(__file__).resolve().parent / "components" / "webm_recorder" / "frontend" / "dist"),
    )
except Exception:
    RECORDER_COMPONENT = None

captured_b64 = None
if RECORDER_COMPONENT:
    with st.container(border=True):
        st.markdown("##### 🎙️ Grabar y transcribir cambios del turno")
        try:
            captured_b64 = RECORDER_COMPONENT()
        except Exception:
            captured_b64 = None
        # Feedback persistente de transcripción: verde + segundos del audio (US4 / T019)
        if st.session_state.get("last_transcript"):
            secs = st.session_state.get("audio_duration_s")
            detail = "Transcripción completada"
            if secs is not None:
                detail += f" · {secs:.0f} s"
            st.markdown(render_badge(detail, variant="success"), unsafe_allow_html=True)

# Transcription flow: if the recorder produced a NEW base64 payload (different
# from the last one we already processed), save it and call the transcriber.
is_new_recording = (
    captured_b64 and isinstance(captured_b64, str) and captured_b64 != st.session_state.get("last_processed_b64")
)

if is_new_recording and RECORDER_COMPONENT:
    st.session_state["last_processed_b64"] = captured_b64
    st.markdown(render_status_badge("transcribing", detail="Audio recibido"), unsafe_allow_html=True)
    try:
        raw = base64.b64decode(captured_b64)
    except Exception:
        raw = None

    if raw:
        try:
            audio_path = audio_utils.save_webm_bytes(raw)
        except OSError as exc:
            st.markdown(
                render_status_badge("error", detail=f"Error guardando el audio: {exc}"),
                unsafe_allow_html=True,
            )
        else:
            # Duración del audio para el feedback (antes de borrar el temporal).
            st.session_state["audio_duration_s"] = audio_utils.get_audio_duration_seconds(audio_path)

            provider = OpenRouterTranscriptionProvider(api_key=os.getenv("OPENROUTER_API_KEY"))
            tr = OpenRouterTranscriber(provider=provider)
            try:
                transcript = tr.transcribe_file(str(audio_path))
            except Exception as e:
                st.markdown(
                    render_status_badge("error", detail=f"Error en la transcripción: {e}"),
                    unsafe_allow_html=True,
                )
                transcript = None

            audio_utils.clear_recording(audio_path)

            if not transcript:
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.warning(
                    "Transcripción completada pero sin texto. "
                    "Verifica OPENROUTER_API_KEY, el servicio de "
                    "OpenRouter y revisa los logs del servidor."
                )
            else:
                st.session_state["last_transcript"] = transcript
                st.session_state["last_transcript_consumed"] = False
                st.session_state["last_transcript_time"] = __import__("time").time()
    else:
        st.markdown(
            render_status_badge("error", detail="No se pudo decodificar audio de la grabación."),
            unsafe_allow_html=True,
        )

    st.rerun()

# --- ACCIÓN DEL BOTÓN ---
if st.button("⚡ Generar evolución y justificación", type="primary", use_container_width=True):
    if not evo_anterior or not cambios_dia:
        st.markdown(
            render_status_badge("error", detail="Por favor, llena ambos campos de texto."),
            unsafe_allow_html=True,
        )
    elif not GROQ_API_KEY or GROQ_API_KEY == "TU_API_KEY_DE_GROQ_AQUI":
        st.markdown(
            render_status_badge("error", detail="Configura API_SECRET_KEY en tu archivo .env."),
            unsafe_allow_html=True,
        )
    elif not SOAP_MODEL:
        st.markdown(
            render_status_badge("error", detail="Configura SOAP_MODEL en tu archivo .env."),
            unsafe_allow_html=True,
        )
    else:
        st.session_state["generation_error"] = None
        st.session_state["save_success"] = None
        st.session_state["save_error"] = None
        try:
            # Animación de procesamiento (US4 / T020)
            with st.status(
                "Generando evolución SOAP con justificación clínica…",
                expanded=True,
            ) as status:
                st.write("Analizando cambios del turno…")
                provider = _provider_registry.resolve()
                generator = SoapGenerator(provider=provider, model=SOAP_MODEL)
                st.write("Estructurando formato SOAP…")
                result = generator.generate(evo_anterior, cambios_dia)
                st.write("Justificando decisiones terapéuticas…")

                st.session_state["justificacion"] = result.justificacion
                st.session_state["nueva_evo"] = result.nueva_evo
                st.session_state["evo_anterior_used"] = evo_anterior
                st.session_state["pdf_bytes"] = generate_pdf(
                    evo_anterior, cambios_dia, result.nueva_evo, result.justificacion
                )
                status.update(label="Evolución generada", state="complete", expanded=False)

        except Exception as e:
            st.session_state["generation_error"] = str(e)

# --- MOSTRAR ERRORES PERSISTENTES ---
if st.session_state["generation_error"]:
    st.markdown(
        render_status_badge("error", detail=f"Error de generación: {st.session_state['generation_error']}"),
        unsafe_allow_html=True,
    )
    if st.button("Descartar error y reintentar"):
        st.session_state["generation_error"] = None
        st.session_state["justificacion"] = None
        st.session_state["nueva_evo"] = None
        st.session_state["pdf_bytes"] = None
        st.rerun()


# --- DIÁLOGO DE CONFIRMACIÓN DE GUARDADO (US2 / T010) ---
@st.dialog("Confirmar guardado en historial")
def _confirm_save_dialog() -> None:
    """Modal that warns the note is AI-generated before persisting it."""
    st.warning(
        "⚠️ Documento generado por IA. Debe ser revisado y validado por el "
        "médico tratante antes de ser registrado en la historia clínica.\n\n"
        f"Se guardará la nueva evolución del paciente "
        f"**{st.session_state.get('patient_id')}** en la base de datos."
    )
    col_ok, col_cancel = st.columns(2)
    if col_ok.button("✅ Confirmar y guardar", type="primary", use_container_width=True):
        try:
            respuesta = get_persistence_service().guardar(
                st.session_state["patient_id"],
                st.session_state["nueva_evo"],
            )
            st.session_state["save_success"] = f"{respuesta['mensaje']} (id={respuesta['id']})."
            st.session_state["save_error"] = None
            st.session_state["save_toast"] = True
        except (ValidationError, ConnectionError) as exc:
            st.session_state["save_error"] = f"No se pudo guardar: {exc}"
        except Exception as exc:  # noqa: BLE001 — degradar con mensaje, conservar contenido
            logger.exception("Error guardando evolución en historial")
            st.session_state["save_error"] = f"Error al guardar en la base de datos: {exc}"
        st.rerun()
    if col_cancel.button("Cancelar", use_container_width=True):
        st.rerun()


def _reset_evolucion() -> None:
    """Clear all flow state so the UI returns to the initial empty form (US5).

    NOTE: ``last_processed_b64`` is intentionally NOT cleared. The audio
    recorder component keeps returning its last base64 payload on every
    rerun; keeping ``last_processed_b64`` marks that residual audio as
    "already processed" so the reset does not trigger a re-transcription
    that would refill the "Cambios del día" field. A genuinely new
    recording produces a different payload and is processed normally.
    """
    nonce = st.session_state.get("form_nonce", 0)
    for key in (
        "patient_id",
        "historial_evoluciones",
        "historial_error",
        f"patient_id_input_{nonce}",
        f"fecha_idx_{nonce}",
        f"evo_anterior_{nonce}",
        f"cambios_dia_{nonce}",
        "nueva_evo",
        "justificacion",
        "evo_anterior_used",
        "pdf_bytes",
        "generation_error",
        "save_success",
        "save_error",
        "save_toast",
        "audio_duration_s",
        "last_transcript",
        "last_transcript_consumed",
        "last_transcript_time",
    ):
        st.session_state.pop(key, None)
    # Forzar text_area nuevos y vacíos en el siguiente run.
    st.session_state["form_nonce"] = nonce + 1


# --- MOSTRAR RESULTADOS (vista de control de cambios — US3) ---
if st.session_state["justificacion"] and st.session_state["nueva_evo"]:
    with st.container(border=True):
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.markdown(f"### ✅ Evolución generada · {fecha_actual}")

        # Barra de acciones: Exportar PDF · Guardar en historial · Nueva evolución
        act_pdf, act_save, act_new = st.columns(3)
        with act_pdf:
            st.download_button(
                label="📄 Exportar PDF",
                data=st.session_state["pdf_bytes"],
                file_name="reporte_caso_clinico_soap.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with act_save:
            if st.button("💾 Guardar en historial", use_container_width=True):
                if not st.session_state.get("patient_id"):
                    st.session_state["save_error"] = (
                        "Seleccione y cargue un paciente en 'Selección de historial clínico' antes de guardar."
                    )
                else:
                    _confirm_save_dialog()
        with act_new:
            # Reset en callback on_click: corre ANTES de instanciar los widgets
            # en el rerun, de modo que limpiar las claves de los text_area
            # (bloques 1 y 2) realmente vacía los campos.
            st.button(
                "↩ Nueva evolución",
                use_container_width=True,
                on_click=_reset_evolucion,
            )

        if st.session_state.get("save_success"):
            st.success(
                f"✅ Evolución guardada en el historial del paciente "
                f"{st.session_state.get('patient_id')}. {st.session_state['save_success']}",
                icon="✅",
            )
            # Notificación emergente, solo una vez por guardado.
            if st.session_state.pop("save_toast", False):
                st.toast("Guardado en historial", icon="✅")
        if st.session_state.get("save_error"):
            st.error(st.session_state["save_error"], icon="⚠️")

        tab_evo, tab_just = st.tabs(["📝 Nueva Evolución (control de cambios)", "💡 Justificación clínica"])
        with tab_evo:
            st.caption(
                "🟥 Líneas en rojo: eliminadas respecto al día anterior · 🟩 Líneas en verde: nuevas en esta evolución"
            )
            diff_lines = compute_line_diff(
                st.session_state.get("evo_anterior_used") or "",
                st.session_state["nueva_evo"],
            )
            st.markdown(
                f'<div class="diff-view">{line_diff_to_html(diff_lines)}</div>',
                unsafe_allow_html=True,
            )
        with tab_just:
            st.info(st.session_state["justificacion"])
