"""Abstract repository contract (Protocol) for SOAP evolution persistence.

Defines the RepositorioEvoluciones protocol that all concrete
implementations must satisfy, enabling database-agnostic service code.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from services.persistence.schemas import EvolucionSOAP


@runtime_checkable
class RepositorioEvoluciones(Protocol):
    """Contract for persisting and querying SOAP evolutions.

    Usage:
        repo: RepositorioEvoluciones = RepositorioSupabase()
        service = ServicioPersistenciaSOAP(repo)
    """

    def guardar(self, patient_id: str, soap: str) -> int:
        """Persist a new SOAP evolution record.

        Args:
            patient_id: Unique patient identifier.
            soap: Full SOAP evolution content.

        Returns:
            The auto-generated id of the created record.

        Raises:
            ConnectionError: If the database is unavailable.
            ValueError: If data fails database-level validation.

        """

    def obtener_anterior(self, patient_id: str) -> EvolucionSOAP | None:
        """Return the immediately previous (second-to-last) evolution.

        The previous evolution is the second most recent record in
        descending chronological order. Returns None if the patient
        has fewer than 2 evolutions.

        Args:
            patient_id: Unique patient identifier.

        Returns:
            The penultimate evolution, or None if not enough history.

        Raises:
            ConnectionError: If the database is unavailable.

        """

    def obtener_por_paciente(
        self,
        patient_id: str,
        *,
        cursor: int | None = None,
        limit: int = 50,
    ) -> list[EvolucionSOAP]:
        """Return a patient's evolutions ordered by creation date descending.

        Args:
            patient_id: Unique patient identifier.
            cursor: ID of the last record from the previous page
                    (cursor-based pagination). None = first page.
            limit: Maximum number of records to return (default 50).

        Returns:
            List of SOAP evolutions for the patient, ordered by
            fecha_creacion descending. Empty if no records.

        Raises:
            ConnectionError: If the database is unavailable.

        """
