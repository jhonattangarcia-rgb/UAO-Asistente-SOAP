"""Tests unitarios puros para RepositorioSupabase.

Responsabilidad: validar exclusivamente la logica de construccion de
queries y manejo de respuestas de RepositorioSupabase, mockeando por
completo el cliente de Supabase (create_client). Ninguna llamada de
red real ni dependencia de un proyecto Supabase activo.

Alta cohesion: cada clase prueba un unico metodo publico del repositorio.
Bajo acoplamiento: el cliente Supabase se inyecta via monkeypatch sobre
create_client, sin acoplarse a la implementacion interna de PostgREST.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from services.persistence.repository import RepositorioSupabase

# --- Constantes de prueba ---------------------------------------------------

URL_VALIDA = "https://proyecto-fastsoap.supabase.co"
KEY_VALIDA = "service-role-key-de-prueba-123456"

FILA_EJEMPLO: dict[str, Any] = {
    "id": 1,
    "patient_id": "PAC-001",
    "fecha_creacion": "2026-06-15T10:00:00+00:00",
    "soap_result": "S: Estable. O: Normal. A: Bien. P: Continuar.",
}


# --- Factories ----------------------------------------------------------------


def _make_query_mock(execute_data: list[dict[str, Any]] | None) -> MagicMock:
    """Crear un mock de query encadenable que retorna execute_data al ejecutar.

    Replica la interfaz fluida de PostgREST: cada metodo (select, eq, order,
    limit, lt, or_) retorna el mismo mock para permitir encadenamiento, y
    solo execute() produce un resultado con el atributo .data.
    """
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.lt.return_value = query
    query.or_.return_value = query
    query.insert.return_value = query

    result = MagicMock()
    result.data = execute_data
    query.execute.return_value = result
    return query


def _make_repository(
    monkeypatch: pytest.MonkeyPatch,
    table_mock: MagicMock,
) -> RepositorioSupabase:
    """Construir un RepositorioSupabase con un cliente Supabase completamente mockeado.

    Args:
        monkeypatch: Fixture de pytest para parchear create_client.
        table_mock: Mock que sera retornado por client.table(...).

    Returns:
        Una instancia de RepositorioSupabase lista para probar, sin
        ninguna conexion de red real.

    """
    fake_client = MagicMock()
    fake_client.table.return_value = table_mock

    monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
    monkeypatch.setattr(
        "services.persistence.repository.create_client",
        lambda *_args, **_kwargs: fake_client,
    )
    return RepositorioSupabase()


# ==============================================================================
# 1. GUARDAR - casos exitosos (5 casos)
# ==============================================================================


class TestGuardarExitoso:
    """Verifica que guardar() inserta el registro y retorna el id generado."""

    def test_caso_01_retorna_id_entero_del_registro_insertado(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe retornar el id como entero, no como string."""
        query = _make_query_mock([{**FILA_EJEMPLO, "id": 42}])
        repo = _make_repository(monkeypatch, query)
        result = repo.guardar("PAC-001", "contenido soap valido")
        assert result == 42
        assert isinstance(result, int)

    def test_caso_02_llama_insert_con_patient_id_y_soap_result(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe construir el payload de insert con las claves correctas."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.guardar("PAC-001", "contenido soap valido")
        query.insert.assert_called_once_with(
            {"patient_id": "PAC-001", "soap_result": "contenido soap valido"},
        )

    def test_caso_03_llama_table_con_nombre_correcto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe operar sobre la tabla evoluciones_soap."""
        query = _make_query_mock([FILA_EJEMPLO])
        fake_client = MagicMock()
        fake_client.table.return_value = query
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        monkeypatch.setattr(
            "services.persistence.repository.create_client",
            lambda *_a, **_k: fake_client,
        )
        repo = RepositorioSupabase()
        repo.guardar("PAC-001", "contenido soap valido")
        fake_client.table.assert_called_with("evoluciones_soap")

    def test_caso_04_id_con_string_numerico_se_convierte_a_entero(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe convertir a int un id que llegue como string desde PostgREST."""
        query = _make_query_mock([{**FILA_EJEMPLO, "id": "7"}])
        repo = _make_repository(monkeypatch, query)
        result = repo.guardar("PAC-001", "contenido soap valido")
        assert result == 7
        assert isinstance(result, int)

    def test_caso_05_ejecuta_la_query_exactamente_una_vez(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe llamar execute() una sola vez por invocacion."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.guardar("PAC-001", "contenido soap valido")
        assert query.execute.call_count == 1


# ==============================================================================
# 2. GUARDAR - errores de infraestructura (3 casos)
# ==============================================================================


class TestGuardarErroresInfraestructura:
    """Verifica el manejo de respuestas vacias o invalidas de Supabase."""

    def test_caso_06_data_vacia_lanza_connection_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe lanzar ConnectionError si Supabase no retorna data."""
        query = _make_query_mock([])
        repo = _make_repository(monkeypatch, query)
        with pytest.raises(ConnectionError, match="no se recibió respuesta"):
            repo.guardar("PAC-001", "contenido soap valido")

    def test_caso_07_data_none_lanza_connection_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """guardar() debe lanzar ConnectionError si result.data es None."""
        query = _make_query_mock(None)
        repo = _make_repository(monkeypatch, query)
        with pytest.raises(ConnectionError):
            repo.guardar("PAC-001", "contenido soap valido")

    def test_caso_08_excepcion_del_cliente_se_propaga(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Una excepcion lanzada por el cliente Supabase debe propagarse sin alterarse."""
        query = _make_query_mock([FILA_EJEMPLO])
        query.execute.side_effect = ConnectionError("Supabase unreachable")
        repo = _make_repository(monkeypatch, query)
        with pytest.raises(ConnectionError, match="Supabase unreachable"):
            repo.guardar("PAC-001", "contenido soap valido")


# ==============================================================================
# 3. OBTENER POR PACIENTE - casos exitosos (8 casos)
# ==============================================================================


class TestObtenerPorPacienteExitoso:
    """Verifica que obtener_por_paciente() construye la query y mapea filas."""

    def test_caso_09_retorna_lista_de_evolucionsoap(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe retornar una lista de diccionarios EvolucionSOAP."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["patient_id"] == "PAC-001"

    def test_caso_10_sin_registros_retorna_lista_vacia(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe retornar una lista vacia cuando no hay coincidencias."""
        query = _make_query_mock([])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-999")
        assert result == []

    def test_caso_11_data_none_se_trata_como_lista_vacia(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe tratar result.data=None como una lista vacia."""
        query = _make_query_mock(None)
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert result == []

    def test_caso_12_filtra_por_eq_patient_id(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe filtrar la consulta por patient_id exacto."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_por_paciente("PAC-001")
        query.eq.assert_called_with("patient_id", "PAC-001")

    def test_caso_13_aplica_limit_por_defecto_de_50(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() sin limit explicito debe usar el valor por defecto 50."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_por_paciente("PAC-001")
        query.limit.assert_called_with(50)

    def test_caso_14_aplica_limit_personalizado(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe respetar un limit distinto al por defecto."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_por_paciente("PAC-001", limit=10)
        query.limit.assert_called_with(10)

    def test_caso_15_sin_cursor_no_llama_lt_ni_or(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sin cursor (primera pagina), no debe construirse la clausula de paginacion."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_por_paciente("PAC-001", cursor=None)
        query.lt.assert_not_called()
        query.or_.assert_not_called()

    def test_caso_16_evolucion_mapeada_conserva_soap_result_completo(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """El campo soap_result no debe truncarse ni alterarse al mapear la fila."""
        fila = {**FILA_EJEMPLO, "soap_result": "S: " + "x" * 5000}
        query = _make_query_mock([fila])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert len(result[0]["soap_result"]) == len(fila["soap_result"])


# ==============================================================================
# 4. OBTENER POR PACIENTE - paginacion con cursor (6 casos)
# ==============================================================================


class TestObtenerPorPacientePaginacion:
    """Verifica la logica de paginacion basada en cursor (id + fecha_creacion)."""

    def test_caso_17_con_cursor_busca_el_registro_de_referencia(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Con un cursor, debe consultarse primero el registro de referencia por id."""
        cursor_query = _make_query_mock([{"id": 5, "fecha_creacion": "2026-06-10T00:00:00+00:00"}])
        page_query = _make_query_mock([FILA_EJEMPLO])

        fake_client = MagicMock()
        fake_client.table.side_effect = [page_query, cursor_query]
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        monkeypatch.setattr(
            "services.persistence.repository.create_client",
            lambda *_a, **_k: fake_client,
        )
        repo = RepositorioSupabase()
        repo.obtener_por_paciente("PAC-001", cursor=5)
        assert fake_client.table.call_count == 2

    def test_caso_18_cursor_inexistente_ignora_paginacion_sin_fallar(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Si el cursor no existe en la base, la consulta debe continuar sin filtrar."""
        cursor_query = _make_query_mock([])
        page_query = _make_query_mock([FILA_EJEMPLO])

        fake_client = MagicMock()
        fake_client.table.side_effect = [page_query, cursor_query]
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        monkeypatch.setattr(
            "services.persistence.repository.create_client",
            lambda *_a, **_k: fake_client,
        )
        repo = RepositorioSupabase()
        result = repo.obtener_por_paciente("PAC-001", cursor=999)
        assert result[0]["id"] == 1

    def test_caso_19_fetch_cursor_record_retorna_diccionario_correcto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """_fetch_cursor_record() debe retornar fecha_creacion e id del registro buscado."""
        query = _make_query_mock([{"id": 5, "fecha_creacion": "2026-06-10T00:00:00+00:00"}])
        repo = _make_repository(monkeypatch, query)
        result = repo._fetch_cursor_record(5)
        assert result is not None
        assert result["id"] == 5
        assert result["fecha_creacion"] == "2026-06-10T00:00:00+00:00"

    def test_caso_20_fetch_cursor_record_sin_resultados_retorna_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """_fetch_cursor_record() debe retornar None cuando el id no existe."""
        query = _make_query_mock([])
        repo = _make_repository(monkeypatch, query)
        result = repo._fetch_cursor_record(999)
        assert result is None

    def test_caso_21_fetch_cursor_record_filtra_por_id_exacto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """_fetch_cursor_record() debe filtrar la consulta por el id exacto solicitado."""
        query = _make_query_mock([{"id": 5, "fecha_creacion": "2026-06-10T00:00:00+00:00"}])
        repo = _make_repository(monkeypatch, query)
        repo._fetch_cursor_record(5)
        query.eq.assert_called_with("id", 5)

    def test_caso_22_fetch_cursor_record_aplica_limit_uno(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """_fetch_cursor_record() debe limitar la busqueda a un unico registro."""
        query = _make_query_mock([{"id": 5, "fecha_creacion": "2026-06-10T00:00:00+00:00"}])
        repo = _make_repository(monkeypatch, query)
        repo._fetch_cursor_record(5)
        query.limit.assert_called_with(1)


# ==============================================================================
# 5. OBTENER ANTERIOR - casos exitosos (6 casos)
# ==============================================================================


class TestObtenerAnteriorExitoso:
    """Verifica que obtener_anterior() retorna el registro mas reciente o None."""

    def test_caso_23_con_registros_retorna_evolucionsoap(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() con registros existentes debe retornar un EvolucionSOAP."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_anterior("PAC-001")
        assert result is not None
        assert result["id"] == 1

    def test_caso_24_sin_registros_retorna_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() sin registros para el paciente debe retornar None."""
        query = _make_query_mock([])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_anterior("PAC-999")
        assert result is None

    def test_caso_25_data_none_retorna_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() con result.data=None debe retornar None sin lanzar error."""
        query = _make_query_mock(None)
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_anterior("PAC-001")
        assert result is None

    def test_caso_26_aplica_limit_uno(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() debe limitar la consulta a un unico registro."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_anterior("PAC-001")
        query.limit.assert_called_with(1)

    def test_caso_27_ordena_por_fecha_creacion_descendente(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() debe ordenar por fecha_creacion descendente."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_anterior("PAC-001")
        query.order.assert_any_call("fecha_creacion", desc=True)

    def test_caso_28_filtra_por_patient_id_exacto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() debe filtrar por el patient_id solicitado."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        repo.obtener_anterior("PAC-001")
        query.eq.assert_called_with("patient_id", "PAC-001")


# ==============================================================================
# 6. MAPEO DE TIPOS - conversion de filas crudas (5 casos)
# ==============================================================================


class TestMapeoDeTipos:
    """Verifica que las filas crudas de PostgREST se convierten a tipos correctos."""

    def test_caso_29_id_string_se_convierte_a_int_en_obtener_por_paciente(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_por_paciente() debe convertir id de string a int en cada fila."""
        fila = {**FILA_EJEMPLO, "id": "10"}
        query = _make_query_mock([fila])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert result[0]["id"] == 10
        assert isinstance(result[0]["id"], int)

    def test_caso_30_id_string_se_convierte_a_int_en_obtener_anterior(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """obtener_anterior() debe convertir id de string a int en el resultado."""
        fila = {**FILA_EJEMPLO, "id": "15"}
        query = _make_query_mock([fila])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_anterior("PAC-001")
        assert result is not None
        assert result["id"] == 15
        assert isinstance(result["id"], int)

    def test_caso_31_patient_id_se_convierte_a_str(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """patient_id debe normalizarse explicitamente a str en el resultado mapeado."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert isinstance(result[0]["patient_id"], str)

    def test_caso_32_soap_result_se_convierte_a_str(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """soap_result debe normalizarse explicitamente a str en el resultado mapeado."""
        query = _make_query_mock([FILA_EJEMPLO])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert isinstance(result[0]["soap_result"], str)

    def test_caso_33_multiples_filas_se_mapean_en_el_orden_recibido(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Varias filas retornadas por Supabase deben mapearse preservando su orden."""
        fila_1 = {**FILA_EJEMPLO, "id": 1}
        fila_2 = {**FILA_EJEMPLO, "id": 2}
        query = _make_query_mock([fila_1, fila_2])
        repo = _make_repository(monkeypatch, query)
        result = repo.obtener_por_paciente("PAC-001")
        assert [r["id"] for r in result] == [1, 2]


# ==============================================================================
# 7. INICIALIZACION DEL CLIENTE (3 casos)
# ==============================================================================


class TestInicializacionCliente:
    """Verifica que RepositorioSupabase construye el cliente correctamente."""

    def test_caso_34_usa_credenciales_explicitas_si_se_proveen(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Si se pasan url/key explicitos, deben tener prioridad sobre Config."""
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)

        llamados: dict[str, str] = {}

        def fake_create_client(url: str, key: str) -> MagicMock:
            llamados["url"] = url
            llamados["key"] = key
            return MagicMock()

        monkeypatch.setattr(
            "services.persistence.repository.create_client",
            fake_create_client,
        )
        RepositorioSupabase(url="https://override.supabase.co", key="override-key")
        assert llamados["url"] == "https://override.supabase.co"
        assert llamados["key"] == "override-key"

    def test_caso_35_usa_config_cuando_no_se_proveen_credenciales(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sin url/key explicitos, deben usarse los valores leidos por Config."""
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)

        llamados: dict[str, str] = {}

        def fake_create_client(url: str, key: str) -> MagicMock:
            llamados["url"] = url
            llamados["key"] = key
            return MagicMock()

        monkeypatch.setattr(
            "services.persistence.repository.create_client",
            fake_create_client,
        )
        RepositorioSupabase()
        assert llamados["url"] == URL_VALIDA
        assert llamados["key"] == KEY_VALIDA

    def test_caso_36_sin_variables_de_entorno_propaga_config_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sin configuracion valida ni credenciales explicitas, debe fallar al construirse."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        with pytest.raises(Exception):  # noqa: B017 - ConfigError, validado por test_config.py
            RepositorioSupabase()
