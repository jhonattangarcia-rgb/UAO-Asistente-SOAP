"""Orchestration service for SOAP evolution persistence.

Validates inputs and delegates all storage operations to an injected
repository, keeping the service database-agnostic.
"""

from __future__ import annotations

import logging
import re

from services.persistence.interfaces import RepositorioEvoluciones
from services.persistence.schemas import ConsultaResponse, GuardarResponse

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Raised when input data fails validation rules."""


class ServicioPersistenciaSOAP:
    """Orchestrator for SOAP persistence operations.

    Validates inputs and delegates to the injected repository.
    The repository dependency follows the RepositorioEvoluciones Protocol,
    making this service database-agnostic.
    """

    _PATIENT_ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9-]+$")
    _SOAP_MIN_LENGTH: int = 10
    _SOAP_MAX_LENGTH: int = 100_000

    def __init__(self, repositorio: RepositorioEvoluciones) -> None:
        """Initialize the service with a repository.

        Args:
            repositorio: Any object satisfying the RepositorioEvoluciones Protocol.

        """
        self._repositorio = repositorio

    def guardar(self, patient_id: str, soap: str) -> GuardarResponse:
        """Validate and persist a new SOAP evolution.

        Args:
            patient_id: Unique patient identifier.
            soap: Full SOAP evolution content (min 10 chars, max 100k).

        Returns:
            A GuardarResponse with the new record id and success message.

        Raises:
            ValidationError: If input fails validation rules.
            ConnectionError: If the database is unavailable.

        """
        logger.info("Guardando evolución para paciente: %s", patient_id)
        self._validar_entrada(patient_id, soap)
        try:
            record_id = self._repositorio.guardar(patient_id, soap)
        except ConnectionError:
            logger.exception(
                "Error de conexión al guardar evolución para paciente: %s",
                patient_id,
            )
            raise
        logger.info(
            "Evolución guardada exitosamente para paciente: %s (id=%d)",
            patient_id,
            record_id,
        )
        return GuardarResponse(
            id=record_id,
            mensaje="Evolución guardada exitosamente",
        )

    def obtener_por_paciente(
        self,
        patient_id: str,
        *,
        cursor: int | None = None,
        limit: int = 50,
    ) -> ConsultaResponse:
        """Retrieve a patient's evolutions with cursor-based pagination.

        Args:
            patient_id: Unique patient identifier.
            cursor: ID of the last record from the previous page.
                    None = first page.
            limit: Maximum records per page (default 50).

        Returns:
            A ConsultaResponse with the evolution list and next cursor.

        Raises:
            ValidationError: If patient_id is empty.
            ConnectionError: If the database is unavailable.

        """
        logger.info(
            "Consultando evoluciones para paciente: %s (cursor=%s, limit=%d)",
            patient_id,
            cursor,
            limit,
        )
        if not patient_id or not patient_id.strip():
            raise ValidationError("El identificador del paciente no puede estar vacío.")
        try:
            evoluciones = self._repositorio.obtener_por_paciente(
                patient_id,
                cursor=cursor,
                limit=limit,
            )
        except ConnectionError:
            logger.exception(
                "Error de conexión al consultar evoluciones para paciente: %s",
                patient_id,
            )
            raise

        next_cursor: int | None = None
        if len(evoluciones) == limit:
            last = evoluciones[-1]
            next_cursor = last["id"]

        logger.info(
            "Consulta completada para paciente: %s — %d registros, cursor_siguiente=%s",
            patient_id,
            len(evoluciones),
            next_cursor,
        )
        return ConsultaResponse(
            evoluciones=evoluciones,
            cursor=next_cursor,
        )

    @staticmethod
    def _validar_entrada(patient_id: str, soap: str) -> None:
        """Validate patient_id and soap content against business rules.

        Args:
            patient_id: Patient identifier to validate.
            soap: SOAP content to validate.

        Raises:
            ValidationError: Aggregated message of all validation failures.

        """
        errors: list[str] = []

        if not patient_id or not patient_id.strip():
            errors.append("El identificador del paciente no puede estar vacío.")
        elif not ServicioPersistenciaSOAP._PATIENT_ID_PATTERN.match(patient_id):
            errors.append(
                "El identificador del paciente solo puede contener "
                "letras, números y guiones.",
            )

        soap_stripped = soap.strip() if soap else ""
        if len(soap_stripped) < ServicioPersistenciaSOAP._SOAP_MIN_LENGTH:
            errors.append(
                f"El contenido SOAP debe tener al menos "
                f"{ServicioPersistenciaSOAP._SOAP_MIN_LENGTH} caracteres.",
            )
        if len(soap_stripped) > ServicioPersistenciaSOAP._SOAP_MAX_LENGTH:
            errors.append(
                f"El contenido SOAP no puede exceder "
                f"{ServicioPersistenciaSOAP._SOAP_MAX_LENGTH} caracteres.",
            )

        if errors:
            logger.warning("Error de validación: %s", "; ".join(errors))
            raise ValidationError("; ".join(errors))
