"""Supabase-backed repository for SOAP evolution persistence.

Implements the RepositorioEvoluciones Protocol using the Supabase
PostgREST client. Configuration is read from environment variables
via Config.
"""

from __future__ import annotations

from typing import Any, cast

from supabase import Client as SupabaseClient
from supabase import create_client

from services.persistence.config import Config
from services.persistence.schemas import EvolucionSOAP


class RepositorioSupabase:
    """Concrete repository using Supabase/PostgREST.

    Uses the service-role key for authenticated backend access (bypasses RLS).
    """

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        """Initialize Supabase client from Config or explicit credentials.

        Args:
            url: Supabase project URL (overrides env var).
            key: Supabase service-role key (overrides env var).

        """
        self._config = Config()
        self._client: SupabaseClient = create_client(
            url or self._config.supabase_url,
            key or self._config.supabase_service_key,
        )

    def guardar(self, patient_id: str, soap: str) -> int:
        """Insert a new SOAP evolution record.

        Args:
            patient_id: Unique patient identifier.
            soap: Full SOAP evolution content.

        Returns:
            The auto-generated id of the inserted record.

        Raises:
            ConnectionError: If the insert fails or DB is unavailable.

        """
        data: dict[str, str] = {
            "patient_id": patient_id,
            "soap_result": soap,
        }
        result = self._client.table("evoluciones_soap").insert(data).execute()
        if not result.data:
            msg = "Error al guardar la evolución: no se recibió respuesta de la base de datos."
            raise ConnectionError(msg)
        row: dict[str, Any] = cast("dict[str, Any]", result.data[0])
        return int(row["id"])

    def obtener_por_paciente(
        self,
        patient_id: str,
        *,
        cursor: int | None = None,
        limit: int = 50,
    ) -> list[EvolucionSOAP]:
        """Query a patient's evolutions with cursor-based pagination.

        Args:
            patient_id: Unique patient identifier.
            cursor: ID of the last record from the previous page.
                    None = first page.
            limit: Maximum records per page (default 50).

        Returns:
            List of EvolucionSOAP ordered by fecha_creacion descending.

        """
        query = (
            self._client.table("evoluciones_soap")
            .select("id, patient_id, fecha_creacion, soap_result")
            .eq("patient_id", patient_id)
            .order("fecha_creacion", desc=True)
            .order("id", desc=True)
            .limit(limit)
        )
        if cursor is not None:
            cursor_data = self._fetch_cursor_record(cursor)
            if cursor_data:
                query = query.lt("fecha_creacion", cursor_data["fecha_creacion"]).or_(
                    f"fecha_creacion.eq.{cursor_data['fecha_creacion']},id.lt.{cursor_data['id']}",
                )
        result = query.execute()
        rows: list[dict[str, Any]] = cast("list[dict[str, Any]]", result.data or [])
        return [
            EvolucionSOAP(
                id=int(row["id"]),
                patient_id=str(row["patient_id"]),
                fecha_creacion=row["fecha_creacion"],
                soap_result=str(row["soap_result"]),
            )
            for row in rows
        ]

    def obtener_anterior(self, patient_id: str) -> EvolucionSOAP | None:
        """Return the immediately previous (second-to-last) evolution.

        Uses OFFSET 1 LIMIT 1 via PostgREST's Range header to skip
        the most recent record and return the penultimate one.

        Args:
            patient_id: Unique patient identifier.

        Returns:
            The penultimate evolution, or None if fewer than 2 records.

        """
        query = (
            self._client.table("evoluciones_soap")
            .select("id, patient_id, fecha_creacion, soap_result")
            .eq("patient_id", patient_id)
            .order("fecha_creacion", desc=True)
            .order("id", desc=True)
            .limit(1)
        )
        result = query.execute()
        if not result.data:
            return None
        row: dict[str, Any] = cast("dict[str, Any]", result.data[0])
        return EvolucionSOAP(
            id=int(row["id"]),
            patient_id=str(row["patient_id"]),
            fecha_creacion=row["fecha_creacion"],
            soap_result=str(row["soap_result"]),
        )

    def _fetch_cursor_record(self, cursor: int) -> dict[str, Any] | None:
        """Retrieve the fecha_creacion and id for a given cursor record.

        Args:
            cursor: Record id to look up.

        Returns:
            A dict with "fecha_creacion" and "id" keys, or None if not found.

        """
        record_result = (
            self._client.table("evoluciones_soap").select("fecha_creacion, id").eq("id", cursor).limit(1).execute()
        )
        if record_result.data:
            return cast("dict[str, Any]", record_result.data[0])
        return None
