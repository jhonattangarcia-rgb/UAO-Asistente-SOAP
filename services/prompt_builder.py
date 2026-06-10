"""Prompt construction service for Groq-based SOAP generation.

Provides functions to build the fixed system prompt (medical assistant role)
and the variable user prompt (clinical rules + patient data input).
"""

from __future__ import annotations

_PROMPT_ESTRUCTURA_FIJA = (
    "Eres un asistente médico experto en formato SOAP para UCI y hospitalización. "
    "Tu tarea es generar la nueva evolución del día de forma redactada e integrada en formato SOAP strico "
    "(Subjetivo, Objetivo, Análisis, Plan). Al final del texto, añade obligatoriamente una sección "
    "que empiece exactamente con el título '### Justificación Clínica:' seguido de viñetas explicativas."
)

_PROMPT_REGLAS_VARIABLES = (
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


def build_system_prompt() -> str:
    """Build the fixed system prompt defining the medical assistant's role.

    Returns the prompt that establishes the SOAP format structure, the
    assistant's expertise in ICU/hospitalization context, and the mandatory
    clinical justification section header.

    Returns:
        str: The system prompt string.

    """
    return _PROMPT_ESTRUCTURA_FIJA


def build_user_prompt(evolucion_anterior: str, cambios: str) -> str:
    """Build the user prompt with clinical rules and patient data.

    Interpolates the previous evolution text and today's changes into the
    variable business rules template (audit rules, SOAP structure, Colombian
    medical Spanish guidelines).

    Args:
        evolucion_anterior: The previous day's clinical evolution text.
        cambios: Today's reported changes or free-text clinical notes.

    Returns:
        str: The complete user prompt combining input data and business rules.

    """
    prompt = f"EVOLUCIÓN ANTERIOR:\n{evolucion_anterior}\n\nCAMBIOS DEL DÍA:\n{cambios}\n\n{_PROMPT_REGLAS_VARIABLES}"
    return prompt
