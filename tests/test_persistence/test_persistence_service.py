"""Tests unitarios puros para ServicioPersistenciaSOAP.

Responsabilidad: validar EXCLUSIVAMENTE las reglas de negocio y validación
del servicio, usando MagicMock como repositorio. Sin dependencia de
implementaciones concretas de repositorio.

Alta cohesión  → cada clase prueba una única responsabilidad del servicio.
Bajo acoplamiento → usa MagicMock, sin importar MockRepositorioEvoluciones.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, call

import pytest

from services.persistence.schemas import ConsultaResponse, EvolucionSOAP, GuardarResponse
from services.persistence.service import ServicioPersistenciaSOAP, ValidationError

# ─── Constantes de prueba ─────────────────────────────────────────────────────

SOAP_VALIDO = (
    "S: Paciente refiere dolor lumbar progresivo desde hace 3 semanas.\n"
    "O: Contractura paravertebral lumbar. EVA 6/8.\n"
    "A: Lumbalgia mecánica por contractura muscular.\n"
    "P: AINE 7 días, fisioterapia 2x semana, retorno en 10 días."
)

SOAP_MINIMO = "S:ok O:ok."  # exactamente 10 caracteres


# ─── Factories ────────────────────────────────────────────────────────────────

def _mock_repo(guardar_id: int = 1, evoluciones: list | None = None) -> MagicMock:
    """Crea un mock limpio que satisface el protocolo RepositorioEvoluciones."""
    repo = MagicMock()
    repo.guardar.return_value = guardar_id
    repo.obtener_por_paciente.return_value = evoluciones or []
    return repo


def _make_evolucion(id: int = 1, patient_id: str = "pac-001") -> EvolucionSOAP:
    return EvolucionSOAP(
        id=id,
        patient_id=patient_id,
        fecha_creacion=datetime(2026, 6, 10, 12, 0, 0),
        soap_result=SOAP_VALIDO,
    )


def _make_service(repo: MagicMock | None = None) -> ServicioPersistenciaSOAP:
    return ServicioPersistenciaSOAP(repo or _mock_repo())


# ══════════════════════════════════════════════════════════════════════════════
# 1. GUARDAR — casos exitosos (6 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarExitoso:
    """Verifica que guardar() retorna GuardarResponse correcto y delega al repo."""

    def test_TC01_retorna_id_del_repositorio(self) -> None:
        repo = _mock_repo(guardar_id=42)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        assert result["id"] == 42

    def test_TC02_retorna_mensaje_exitoso(self) -> None:
        result = _make_service().guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        assert "exitosamente" in result["mensaje"].lower()

    def test_TC03_delega_patient_id_y_soap_exactos_al_repo(self) -> None:
        repo = _mock_repo()
        _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        repo.guardar.assert_called_once_with("pac-001", SOAP_VALIDO)

    def test_TC04_patient_id_alfanumerico_con_guiones_es_valido(self) -> None:
        repo = _mock_repo(guardar_id=5)
        result = _make_service(repo).guardar(patient_id="pac-001-UAO", soap=SOAP_VALIDO)
        assert result["id"] == 5

    def test_TC05_soap_exactamente_en_el_limite_minimo(self) -> None:
        repo = _mock_repo(guardar_id=2)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_MINIMO)
        assert result["id"] == 2

    def test_TC06_soap_exactamente_en_el_limite_maximo(self) -> None:
        repo = _mock_repo(guardar_id=3)
        soap_maximo = "S: " + "x" * (100_000 - 3)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=soap_maximo)
        assert result["id"] == 3


# ══════════════════════════════════════════════════════════════════════════════
# 2. GUARDAR — validación de patient_id (8 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarValidacionPatientId:
    """Verifica todas las reglas de validación sobre patient_id en guardar()."""

    def test_TC07_patient_id_vacio_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().guardar(patient_id="", soap=SOAP_VALIDO)

    def test_TC08_patient_id_solo_espacios_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().guardar(patient_id="   ", soap=SOAP_VALIDO)

    def test_TC09_patient_id_con_arroba_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac@001", soap=SOAP_VALIDO)

    def test_TC10_patient_id_con_punto_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac.001", soap=SOAP_VALIDO)

    def test_TC11_patient_id_con_espacio_interno_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac 001", soap=SOAP_VALIDO)

    def test_TC12_patient_id_con_slash_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac/001", soap=SOAP_VALIDO)

    def test_TC13_patient_id_solo_numeros_es_valido(self) -> None:
        repo = _mock_repo(guardar_id=10)
        result = _make_service(repo).guardar(patient_id="12345", soap=SOAP_VALIDO)
        assert result["id"] == 10

    def test_TC14_no_llama_repo_si_patient_id_invalido(self) -> None:
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="", soap=SOAP_VALIDO)
        repo.guardar.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 3. GUARDAR — validación de contenido SOAP (7 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarValidacionSoap:
    """Verifica todas las reglas de validación sobre el contenido SOAP."""

    def test_TC15_soap_vacio_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="")

    def test_TC16_soap_de_9_chars_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="123456789")

    def test_TC17_soap_de_100001_chars_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="no puede exceder"):
            _make_service().guardar(patient_id="pac-001", soap="x" * 100_001)

    def test_TC18_soap_solo_espacios_lanza_error(self) -> None:
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="   ")

    def test_TC19_soap_con_espacios_inicio_fin_se_acepta_si_contenido_valido(self) -> None:
        repo = _mock_repo(guardar_id=4)
        result = _make_service(repo).guardar(
            patient_id="pac-001", soap=f"  {SOAP_VALIDO}  "
        )
        assert result["id"] == 4

    def test_TC20_no_llama_repo_si_soap_invalido(self) -> None:
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="pac-001", soap="")
        repo.guardar.assert_not_called()

    def test_TC21_errores_de_patient_id_y_soap_se_acumulan_en_un_mensaje(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _make_service().guardar(patient_id="", soap="")
        mensaje = str(exc_info.value)
        assert "paciente" in mensaje
        assert "SOAP" in mensaje
        assert ";" in mensaje


# ══════════════════════════════════════════════════════════════════════════════
# 4. GUARDAR — propagación de errores de infraestructura (3 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarErroresInfraestructura:
    """Verifica que guardar() propaga errores del repositorio sin alterarlos."""

    def test_TC22_connection_error_del_repo_se_propaga_intacto(self) -> None:
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("BD no disponible")
        with pytest.raises(ConnectionError, match="BD no disponible"):
            _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)

    def test_TC23_connection_error_no_se_convierte_en_otro_tipo(self) -> None:
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)

    def test_TC24_validation_error_previo_impide_llamar_al_repo(self) -> None:
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("no debería llamarse")
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="", soap=SOAP_VALIDO)
        repo.guardar.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 5. OBTENER POR PACIENTE — casos exitosos (8 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerPorPacienteExitoso:
    """Verifica que obtener_por_paciente() retorna ConsultaResponse correcto."""

    def test_TC25_retorna_response_con_claves_requeridas(self) -> None:
        repo = _mock_repo(evoluciones=[_make_evolucion()])
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        assert "evoluciones" in result
        assert "cursor" in result

    def test_TC26_paciente_sin_evoluciones_retorna_lista_vacia(self) -> None:
        result = _make_service().obtener_por_paciente(patient_id="pac-999")
        assert result["evoluciones"] == []

    def test_TC27_cursor_es_none_cuando_no_hay_registros(self) -> None:
        result = _make_service().obtener_por_paciente(patient_id="pac-999")
        assert result["cursor"] is None

    def test_TC28_cursor_es_none_cuando_hay_menos_registros_que_limit(self) -> None:
        evoluciones = [_make_evolucion(id=i+1) for i in range(3)]
        repo = _mock_repo(evoluciones=evoluciones)
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001", limit=10)
        assert result["cursor"] is None

    def test_TC29_cursor_apunta_al_id_del_ultimo_registro_con_limit_exacto(self) -> None:
        evoluciones = [_make_evolucion(id=i+1) for i in range(5)]
        repo = _mock_repo(evoluciones=evoluciones)
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001", limit=5)
        assert result["cursor"] == evoluciones[-1]["id"]

    def test_TC30_delega_parametros_correctos_al_repositorio(self) -> None:
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(
            patient_id="pac-001", cursor=10, limit=25
        )
        repo.obtener_por_paciente.assert_called_once_with(
            "pac-001", cursor=10, limit=25
        )

    def test_TC31_primera_pagina_llama_repo_sin_cursor(self) -> None:
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        repo.obtener_por_paciente.assert_called_once_with(
            "pac-001", cursor=None, limit=50
        )

    def test_TC32_evoluciones_contienen_todos_los_campos_del_schema(self) -> None:
        evolucion = _make_evolucion(id=99, patient_id="pac-001")
        repo = _mock_repo(evoluciones=[evolucion])
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        evo = result["evoluciones"][0]
        assert evo["id"] == 99
        assert evo["patient_id"] == "pac-001"
        assert evo["soap_result"] == SOAP_VALIDO
        assert "fecha_creacion" in evo


# ══════════════════════════════════════════════════════════════════════════════
# 6. OBTENER POR PACIENTE — validación (4 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerPorPacienteValidacion:
    """Verifica validaciones de patient_id en obtener_por_paciente()."""

    def test_TC33_patient_id_vacio_lanza_validation_error(self) -> None:
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().obtener_por_paciente(patient_id="")

    def test_TC34_patient_id_solo_espacios_lanza_validation_error(self) -> None:
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().obtener_por_paciente(patient_id="   ")

    def test_TC35_no_llama_repo_si_patient_id_invalido(self) -> None:
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).obtener_por_paciente(patient_id="")
        repo.obtener_por_paciente.assert_not_called()

    def test_TC36_patient_id_valido_llama_al_repositorio(self) -> None:
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        repo.obtener_por_paciente.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# 7. OBTENER POR PACIENTE — errores de infraestructura (2 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerPorPacienteErroresInfraestructura:
    """Verifica que obtener_por_paciente() propaga errores del repositorio."""

    def test_TC37_connection_error_del_repo_se_propaga(self) -> None:
        repo = _mock_repo()
        repo.obtener_por_paciente.side_effect = ConnectionError("Supabase offline")
        with pytest.raises(ConnectionError, match="Supabase offline"):
            _make_service(repo).obtener_por_paciente(patient_id="pac-001")

    def test_TC38_validation_error_impide_llamar_repo_en_consulta(self) -> None:
        repo = _mock_repo()
        repo.obtener_por_paciente.side_effect = ConnectionError("no debería llamarse")
        with pytest.raises(ValidationError):
            _make_service(repo).obtener_por_paciente(patient_id="")
        repo.obtener_por_paciente.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 8. _VALIDAR_ENTRADA — método estático puro (8 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestValidarEntrada:
    """Tests unitarios directos del método estático _validar_entrada().

    Alta cohesión: prueba exclusivamente la lógica de validación
    sin instanciar el servicio completo ni el repositorio.
    """

    def test_TC39_entrada_completamente_valida_no_lanza_excepcion(self) -> None:
        ServicioPersistenciaSOAP._validar_entrada("pac-001", SOAP_VALIDO)

    def test_TC40_patient_id_solo_letras_es_valido(self) -> None:
        ServicioPersistenciaSOAP._validar_entrada("PacienteUno", SOAP_VALIDO)

    def test_TC41_patient_id_solo_numeros_es_valido(self) -> None:
        ServicioPersistenciaSOAP._validar_entrada("123456", SOAP_VALIDO)

    def test_TC42_patient_id_con_guiones_compuestos_es_valido(self) -> None:
        ServicioPersistenciaSOAP._validar_entrada("pac-001-UAO-2026", SOAP_VALIDO)

    def test_TC43_soap_exactamente_10_chars_es_valido(self) -> None:
        ServicioPersistenciaSOAP._validar_entrada("pac-001", SOAP_MINIMO)

    def test_TC44_ambos_invalidos_genera_mensaje_con_separador(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("", "")
        assert ";" in str(exc_info.value)

    def test_TC45_error_acumulado_menciona_patient_id_y_soap(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("", "corto")
        mensaje = str(exc_info.value)
        assert "paciente" in mensaje
        assert "SOAP" in mensaje

    def test_TC46_patient_id_valido_y_soap_invalido_menciona_solo_soap(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("pac-001", "")
        mensaje = str(exc_info.value)
        assert "SOAP" in mensaje
        assert "paciente" not in mensaje


# ══════════════════════════════════════════════════════════════════════════════
# 9. PROTOCOLO Y CONTRATO (4 casos)
# ══════════════════════════════════════════════════════════════════════════════

class TestProtocoloRepositorio:
    """Verifica que el servicio respeta el principio de bajo acoplamiento.

    El servicio no debe depender de RepositorioSupabase directamente,
    sino de cualquier objeto que cumpla el protocolo RepositorioEvoluciones.
    """

    def test_TC47_servicio_acepta_cualquier_objeto_como_repositorio(self) -> None:
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        assert service is not None

    def test_TC48_guardar_llama_repo_exactamente_una_vez_por_invocacion(self) -> None:
        repo = _mock_repo(guardar_id=1)
        service = ServicioPersistenciaSOAP(repo)
        service.guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        service.guardar(patient_id="pac-002", soap=SOAP_VALIDO)
        assert repo.guardar.call_count == 2

    def test_TC49_obtener_llama_repo_exactamente_una_vez_por_invocacion(self) -> None:
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        service.obtener_por_paciente(patient_id="pac-001")
        service.obtener_por_paciente(patient_id="pac-002")
        assert repo.obtener_por_paciente.call_count == 2

    def test_TC50_multiples_pacientes_no_se_mezclan_en_las_llamadas(self) -> None:
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        service.obtener_por_paciente(patient_id="pac-001")
        service.obtener_por_paciente(patient_id="pac-002")
        calls = repo.obtener_por_paciente.call_args_list
        assert calls[0] == call("pac-001", cursor=None, limit=50)
        assert calls[1] == call("pac-002", cursor=None, limit=50)
