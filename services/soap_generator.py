"""SOAP generation service using an abstract AI provider.

Provides SoapResult (dataclass) and SoapGenerator (class) to build prompts,
call an injected AiProvider for chat completion, and parse the response into a
structured SOAP evolution with clinical justification.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.prompt_builder import build_system_prompt, build_user_prompt
from services.providers.base import AiProvider


@dataclass
class SoapResult:
    """Represents the result of a SOAP generation.

    Attributes:
        nueva_evo: The generated clinical evolution text (before the
            clinical justification separator).
        justificacion: The clinical justification text (after the
            separator), or a fallback message if none was present.

    """

    nueva_evo: str
    justificacion: str


class SoapGenerator:
    """Coordinates SOAP note generation using an injected AiProvider.

    Receives an abstract AI provider via dependency injection, builds prompts
    through PromptBuilder, calls the provider's chat completion, and parses
    the response into a SoapResult.

    Args:
        provider: An instance satisfying the ``AiProvider`` protocol.
        model: The model identifier to use for chat completions
            (e.g. from the ``SOAP_MODEL`` environment variable).

    """

    def __init__(self, provider: AiProvider, model: str) -> None:
        """Initialize the SoapGenerator.

        Args:
            provider: An abstract AI provider.
            model: The model identifier to use for chat completions.

        """
        self._provider = provider
        self._model = model

    def generate(self, evolucion_anterior: str, cambios: str) -> SoapResult:
        """Generate a SOAP evolution using the injected AiProvider.

        Builds system and user prompts via PromptBuilder, sends them to the
        configured provider, splits the response at the clinical justification
        separator, and returns a structured SoapResult.

        Args:
            evolucion_anterior: The previous day's clinical evolution text.
            cambios: Today's reported changes or free-text clinical notes.

        Returns:
            SoapResult containing the new evolution text and the clinical
            justification.

        Raises:
            ProviderError: If the AI provider call fails.

        """
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(evolucion_anterior, cambios)
        content = self._provider.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=self._model,
            temperature=0.1,
        )
        partes = content.split("### Justificación Clínica:")
        nueva_evo = partes[0].strip()
        justificacion = partes[1].strip() if len(partes) > 1 else "No se generó justificación."
        return SoapResult(nueva_evo=nueva_evo, justificacion=justificacion)
