"""In-memory test double for the persistence repository protocol."""

from __future__ import annotations

from datetime import UTC, datetime

from services.persistence.schemas import EvolucionSOAP


class MockRepositorioEvoluciones:
    """In-memory repository for testing ServicioPersistenciaSOAP.

    Implements the RepositorioEvoluciones Protocol using a simple list.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory store with no pending failure."""
        self._store: list[EvolucionSOAP] = []
        self._next_id: int = 1
        self._should_fail: bool = False

    def fail_next_call(self) -> None:
        """Arm the repository to raise ConnectionError on its next call."""
        self._should_fail = True

    def guardar(self, patient_id: str, soap: str) -> int:
        """Insert a new in-memory record, raising ConnectionError if armed.

        Args:
            patient_id: Unique patient identifier (stored uppercased).
            soap: Full SOAP evolution content.

        Returns:
            The auto-incremented id assigned to the new record.

        Raises:
            ConnectionError: If fail_next_call() was previously invoked.

        """
        if self._should_fail:
            self._should_fail = False
            msg = "Base de datos no disponible."
            raise ConnectionError(msg)
        record = EvolucionSOAP(
            id=self._next_id,
            patient_id=patient_id.upper(),
            fecha_creacion=datetime.now(UTC),
            soap_result=soap,
        )
        self._store.insert(0, record)
        self._next_id += 1
        return record["id"]

    def obtener_anterior(self, patient_id: str) -> EvolucionSOAP | None:
        """Return the most recent in-memory record for a patient, or None.

        Args:
            patient_id: Unique patient identifier (matched uppercased).

        Returns:
            The most recent EvolucionSOAP for the patient, or None if absent.

        Raises:
            ConnectionError: If fail_next_call() was previously invoked.

        """
        if self._should_fail:
            self._should_fail = False
            msg = "Base de datos no disponible."
            raise ConnectionError(msg)
        records = [r for r in self._store if r["patient_id"] == patient_id.upper()]
        if not records:
            return None
        return records[0]

    def obtener_por_paciente(
        self,
        patient_id: str,
        *,
        cursor: int | None = None,
        limit: int = 50,
    ) -> list[EvolucionSOAP]:
        """Return a page of in-memory records for a patient.

        Args:
            patient_id: Unique patient identifier (matched uppercased).
            cursor: Id of the last record from the previous page, or None.
            limit: Maximum number of records to return.

        Returns:
            A list of EvolucionSOAP records, most recent first.

        """
        filtered = [r for r in self._store if r["patient_id"] == patient_id.upper()]
        if cursor is not None:
            cursor_idx = next(
                (i for i, r in enumerate(filtered) if r["id"] == cursor),
                None,
            )
            if cursor_idx is not None:
                filtered = filtered[cursor_idx + 1 :]
        return filtered[:limit]
