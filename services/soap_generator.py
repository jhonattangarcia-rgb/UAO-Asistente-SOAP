"""SOAP generation service using the Groq API.

Provides SoapResult (dataclass) and SoapGenerator (class) to build prompts,
call the Groq chat completion endpoint, and parse the response into a
structured SOAP evolution with clinical justification.
"""

from __future__ import annotations

from dataclasses import dataclass

from groq import Groq

from services.prompt_builder import build_system_prompt, build_user_prompt


@dataclass
class SoapResult:
    """Represents the result of a SOAP generation via Groq.

    Attributes:
        nueva_evo: The generated clinical evolution text (before the
            clinical justification separator).
        justificacion: The clinical justification text (after the
            separator), or a fallback message if none was present.

    """

    nueva_evo: str
    justificacion: str


class SoapGenerator:
    """Coordinates SOAP note generation using the Groq API.

    Receives API credentials via dependency injection, builds prompts through
    PromptBuilder, calls the Groq chat completion endpoint, and parses the
    response into a SoapResult.

    Args:
        api_key: The Groq API key for authentication.
        model: The model identifier to use for chat completions
            (e.g. from the SOAP_MODEL environment variable).

    """

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize the SoapGenerator with Groq credentials.

        Args:
            api_key: The Groq API key for authentication.
            model: The model identifier to use for chat completions.

        """
        self._client = Groq(api_key=api_key)
        self._model = model

    def generate(self, evolucion_anterior: str, cambios: str) -> SoapResult:
        """Generate a SOAP evolution using the Groq API.

        Builds system and user prompts via PromptBuilder, sends them to the
        configured Groq model, splits the response at the clinical
        justification separator, and returns a structured SoapResult.

        Args:
            evolucion_anterior: The previous day's clinical evolution text.
            cambios: Today's reported changes or free-text clinical notes.

        Returns:
            SoapResult containing the new evolution text and the clinical
            justification.

        Raises:
            groq.APIError: If the Groq API call fails or returns an error.

        """
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(evolucion_anterior, cambios)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        content: str = response.choices[0].message.content or ""
        partes = content.split("### Justificación Clínica:")
        nueva_evo = partes[0].strip()
        justificacion = partes[1].strip() if len(partes) > 1 else "No se generó justificación."
        return SoapResult(nueva_evo=nueva_evo, justificacion=justificacion)
