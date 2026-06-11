from datetime import UTC, datetime

from services.persistence.schemas import EvolucionSOAP


class MockRepositorioEvoluciones:
    """In-memory repository for testing ServicioPersistenciaSOAP.

    Implements the RepositorioEvoluciones Protocol using a simple list.
    """

    def __init__(self) -> None:
        self._store: list[EvolucionSOAP] = []
        self._next_id: int = 1
        self._should_fail: bool = False

    def fail_next_call(self) -> None:
        self._should_fail = True

    def guardar(self, patient_id: str, soap: str) -> int:
        if self._should_fail:
            self._should_fail = False
            msg = "Base de datos no disponible."
            raise ConnectionError(msg)
        record = EvolucionSOAP(
            id=self._next_id,
            patient_id=patient_id,
            fecha_creacion=datetime.now(UTC),
            soap_result=soap,
        )
        self._store.insert(0, record)
        self._next_id += 1
        return record["id"]

    def obtener_por_paciente(
        self,
        patient_id: str,
        *,
        cursor: int | None = None,
        limit: int = 50,
    ) -> list[EvolucionSOAP]:
        filtered = [r for r in self._store if r["patient_id"] == patient_id]
        if cursor is not None:
            cursor_idx = next(
                (i for i, r in enumerate(filtered) if r["id"] == cursor),
                None,
            )
            if cursor_idx is not None:
                filtered = filtered[cursor_idx + 1 :]
        return filtered[:limit]
