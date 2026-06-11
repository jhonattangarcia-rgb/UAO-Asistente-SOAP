"""Data schemas (TypedDicts) for the SOAP persistence service.

Defines the shape of domain objects and API responses used across
the service layer and repository.
"""

from datetime import datetime
from typing import TypedDict


class EvolucionSOAP(TypedDict):
    """A single SOAP evolution record.

    Attributes:
        id: Auto-generated unique identifier from the database.
        patient_id: Identifier of the patient.
        fecha_creacion: Creation timestamp (timezone-aware).
        soap_result: Full SOAP evolution text content.

    """

    id: int
    patient_id: str
    fecha_creacion: datetime
    soap_result: str


class ErrorResponse(TypedDict):
    """Standard error response body."""

    error: str


class GuardarResponse(TypedDict):
    """Successful save response body."""

    id: int
    mensaje: str


class ConsultaResponse(TypedDict):
    """Successful query response body."""

    evoluciones: list[EvolucionSOAP]
    cursor: int | None
