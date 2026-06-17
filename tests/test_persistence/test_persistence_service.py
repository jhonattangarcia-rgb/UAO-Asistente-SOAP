"""Tests unitarios puros para ServicioPersistenciaSOAP.

Responsabilidad: validar EXCLUSIVAMENTE las reglas de negocio y
validación del servicio, usando ``MagicMock`` como repositorio. Sin
dependencia de implementaciones concretas de repositorio.

Alta cohesion: cada clase prueba una unica responsabilidad del servicio.
Bajo acoplamiento: usa MagicMock, sin importar MockRepositorioEvoluciones.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, call

import pytest

from services.persistence.schemas import EvolucionSOAP
from services.persistence.service import ServicioPersistenciaSOAP, ValidationError

# --- Constantes de prueba ---------------------------------------------------

SOAP_VALIDO = (
    "S: Paciente refiere dolor lumbar progresivo desde hace 3 semanas.\n"
    "O: Contractura paravertebral lumbar. EVA 6/8.\n"
    "A: Lumbalgia mecanica por contractura muscular.\n"
    "P: AINE 7 dias, fisioterapia 2x semana, retorno en 10 dias."
)

SOAP_MINIMO = "S:ok O:ok."  # exactamente 10 caracteres


# --- Factories ----------------------------------------------------------------


def _mock_repo(guardar_id: int = 1, evoluciones: list[EvolucionSOAP] | None = None) -> MagicMock:
    """Crear un mock que satisface el protocolo RepositorioEvoluciones."""
    repo = MagicMock()
    repo.guardar.return_value = guardar_id
    repo.obtener_por_paciente.return_value = evoluciones or []
    return repo


def _make_evolucion(id: int = 1, patient_id: str = "pac-001") -> EvolucionSOAP:
    """Construir una EvolucionSOAP de prueba con valores por defecto."""
    return EvolucionSOAP(
        id=id,
        patient_id=patient_id,
        fecha_creacion=datetime(2026, 6, 10, 12, 0, 0),
        soap_result=SOAP_VALIDO,
    )


def _make_service(repo: MagicMock | None = None) -> ServicioPersistenciaSOAP:
    """Construir un ServicioPersistenciaSOAP con un repositorio mock."""
    return ServicioPersistenciaSOAP(repo or _mock_repo())


# ==============================================================================
# 1. GUARDAR - casos exitosos (6 casos)
# ==============================================================================


class TestGuardarExitoso:
    """Verifica que guardar() retorna GuardarResponse correcto y delega al repo."""

    def test_caso_01_retorna_id_del_repositorio(self) -> None:
        """El id retornado debe coincidir con el generado por el repositorio."""
        repo = _mock_repo(guardar_id=42)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        assert result["id"] == 42

    def test_caso_02_retorna_mensaje_exitoso(self) -> None:
        """El mensaje de respuesta debe confirmar el guardado exitoso."""
        result = _make_service().guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        assert "exitosamente" in result["mensaje"].lower()

    def test_caso_03_delega_patient_id_y_soap_exactos_al_repo(self) -> None:
        """El servicio debe pasar patient_id y soap sin transformarlos."""
        repo = _mock_repo()
        _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        repo.guardar.assert_called_once_with("pac-001", SOAP_VALIDO)

    def test_caso_04_patient_id_alfanumerico_con_guiones_es_valido(self) -> None:
        """Un patient_id alfanumerico con guiones debe ser aceptado."""
        repo = _mock_repo(guardar_id=5)
        result = _make_service(repo).guardar(patient_id="pac-001-UAO", soap=SOAP_VALIDO)
        assert result["id"] == 5

    def test_caso_05_soap_exactamente_en_el_limite_minimo(self) -> None:
        """Un SOAP de exactamente 10 caracteres debe ser aceptado."""
        repo = _mock_repo(guardar_id=2)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_MINIMO)
        assert result["id"] == 2

    def test_caso_06_soap_exactamente_en_el_limite_maximo(self) -> None:
        """Un SOAP de exactamente 100.000 caracteres debe ser aceptado."""
        repo = _mock_repo(guardar_id=3)
        soap_maximo = "S: " + "x" * (100_000 - 3)
        result = _make_service(repo).guardar(patient_id="pac-001", soap=soap_maximo)
        assert result["id"] == 3


# ==============================================================================
# 2. GUARDAR - validacion de patient_id (8 casos)
# ==============================================================================


class TestGuardarValidacionPatientId:
    """Verifica todas las reglas de validacion sobre patient_id en guardar()."""

    def test_caso_07_patient_id_vacio_lanza_error(self) -> None:
        """Un patient_id vacio debe rechazarse con ValidationError."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().guardar(patient_id="", soap=SOAP_VALIDO)

    def test_caso_08_patient_id_solo_espacios_lanza_error(self) -> None:
        """Un patient_id compuesto solo de espacios debe rechazarse."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().guardar(patient_id="   ", soap=SOAP_VALIDO)

    def test_caso_09_patient_id_con_arroba_lanza_error(self) -> None:
        """Un patient_id con caracter @ debe rechazarse."""
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac@001", soap=SOAP_VALIDO)

    def test_caso_10_patient_id_con_punto_lanza_error(self) -> None:
        """Un patient_id con punto debe rechazarse."""
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac.001", soap=SOAP_VALIDO)

    def test_caso_11_patient_id_con_espacio_interno_lanza_error(self) -> None:
        """Un patient_id con espacio interno debe rechazarse."""
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac 001", soap=SOAP_VALIDO)

    def test_caso_12_patient_id_con_slash_lanza_error(self) -> None:
        """Un patient_id con caracter / debe rechazarse."""
        with pytest.raises(ValidationError, match="solo puede contener"):
            _make_service().guardar(patient_id="pac/001", soap=SOAP_VALIDO)

    def test_caso_13_patient_id_solo_numeros_es_valido(self) -> None:
        """Un patient_id compuesto solo de digitos debe ser aceptado."""
        repo = _mock_repo(guardar_id=10)
        result = _make_service(repo).guardar(patient_id="12345", soap=SOAP_VALIDO)
        assert result["id"] == 10

    def test_caso_14_no_llama_repo_si_patient_id_invalido(self) -> None:
        """Si patient_id es invalido, el repositorio no debe invocarse."""
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="", soap=SOAP_VALIDO)
        repo.guardar.assert_not_called()


# ==============================================================================
# 3. GUARDAR - validacion de contenido SOAP (7 casos)
# ==============================================================================


class TestGuardarValidacionSoap:
    """Verifica todas las reglas de validacion sobre el contenido SOAP."""

    def test_caso_15_soap_vacio_lanza_error(self) -> None:
        """Un SOAP vacio debe rechazarse por longitud minima."""
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="")

    def test_caso_16_soap_de_9_chars_lanza_error(self) -> None:
        """Un SOAP de 9 caracteres (uno menos del minimo) debe rechazarse."""
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="123456789")

    def test_caso_17_soap_de_100001_chars_lanza_error(self) -> None:
        """Un SOAP de 100.001 caracteres (uno mas del maximo) debe rechazarse."""
        with pytest.raises(ValidationError, match="no puede exceder"):
            _make_service().guardar(patient_id="pac-001", soap="x" * 100_001)

    def test_caso_18_soap_solo_espacios_lanza_error(self) -> None:
        """Un SOAP compuesto solo de espacios debe rechazarse tras strip()."""
        with pytest.raises(ValidationError, match="al menos"):
            _make_service().guardar(patient_id="pac-001", soap="   ")

    def test_caso_19_soap_con_espacios_extremos_se_acepta_si_contenido_valido(self) -> None:
        """Espacios al inicio/fin no deben afectar la validacion de longitud."""
        repo = _mock_repo(guardar_id=4)
        result = _make_service(repo).guardar(
            patient_id="pac-001",
            soap=f"  {SOAP_VALIDO}  ",
        )
        assert result["id"] == 4

    def test_caso_20_no_llama_repo_si_soap_invalido(self) -> None:
        """Si el SOAP es invalido, el repositorio no debe invocarse."""
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="pac-001", soap="")
        repo.guardar.assert_not_called()

    def test_caso_21_errores_de_patient_id_y_soap_se_acumulan_en_un_mensaje(self) -> None:
        """Errores simultaneos de patient_id y soap deben reportarse juntos."""
        with pytest.raises(ValidationError) as exc_info:
            _make_service().guardar(patient_id="", soap="")
        mensaje = str(exc_info.value)
        assert "paciente" in mensaje
        assert "SOAP" in mensaje
        assert ";" in mensaje


# ==============================================================================
# 4. GUARDAR - propagacion de errores de infraestructura (3 casos)
# ==============================================================================


class TestGuardarErroresInfraestructura:
    """Verifica que guardar() propaga errores del repositorio sin alterarlos."""

    def test_caso_22_connection_error_del_repo_se_propaga_intacto(self) -> None:
        """Un ConnectionError del repositorio debe llegar intacto al llamador."""
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("BD no disponible")
        with pytest.raises(ConnectionError, match="BD no disponible"):
            _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)

    def test_caso_23_connection_error_no_se_convierte_en_otro_tipo(self) -> None:
        """El servicio no debe envolver ConnectionError en otra excepcion."""
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            _make_service(repo).guardar(patient_id="pac-001", soap=SOAP_VALIDO)

    def test_caso_24_validation_error_previo_impide_llamar_al_repo(self) -> None:
        """Una validacion fallida debe evitar cualquier llamada al repositorio."""
        repo = _mock_repo()
        repo.guardar.side_effect = ConnectionError("no deberia llamarse")
        with pytest.raises(ValidationError):
            _make_service(repo).guardar(patient_id="", soap=SOAP_VALIDO)
        repo.guardar.assert_not_called()


# ==============================================================================
# 5. OBTENER POR PACIENTE - casos exitosos (8 casos)
# ==============================================================================


class TestObtenerPorPacienteExitoso:
    """Verifica que obtener_por_paciente() retorna ConsultaResponse correcto."""

    def test_caso_25_retorna_response_con_claves_requeridas(self) -> None:
        """La respuesta debe incluir las claves evoluciones y cursor."""
        repo = _mock_repo(evoluciones=[_make_evolucion()])
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        assert "evoluciones" in result
        assert "cursor" in result

    def test_caso_26_paciente_sin_evoluciones_retorna_lista_vacia(self) -> None:
        """Un paciente sin registros debe retornar una lista vacia."""
        result = _make_service().obtener_por_paciente(patient_id="pac-999")
        assert result["evoluciones"] == []

    def test_caso_27_cursor_es_none_cuando_no_hay_registros(self) -> None:
        """Sin registros, el cursor de paginacion debe ser None."""
        result = _make_service().obtener_por_paciente(patient_id="pac-999")
        assert result["cursor"] is None

    def test_caso_28_cursor_es_none_cuando_hay_menos_registros_que_limit(self) -> None:
        """Si hay menos registros que el limite, no debe existir pagina siguiente."""
        evoluciones = [_make_evolucion(id=i + 1) for i in range(3)]
        repo = _mock_repo(evoluciones=evoluciones)
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001", limit=10)
        assert result["cursor"] is None

    def test_caso_29_cursor_apunta_al_id_del_ultimo_registro_con_limit_exacto(self) -> None:
        """Si el numero de registros iguala al limite, el cursor debe apuntar al ultimo id."""
        evoluciones = [_make_evolucion(id=i + 1) for i in range(5)]
        repo = _mock_repo(evoluciones=evoluciones)
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001", limit=5)
        assert result["cursor"] == evoluciones[-1]["id"]

    def test_caso_30_delega_parametros_correctos_al_repositorio(self) -> None:
        """Los parametros cursor y limit deben pasarse sin modificar al repositorio."""
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(patient_id="pac-001", cursor=10, limit=25)
        repo.obtener_por_paciente.assert_called_once_with("pac-001", cursor=10, limit=25)

    def test_caso_31_primera_pagina_llama_repo_sin_cursor(self) -> None:
        """La primera pagina debe consultarse con cursor None y el limit por defecto."""
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        repo.obtener_por_paciente.assert_called_once_with("pac-001", cursor=None, limit=50)

    def test_caso_32_evoluciones_contienen_todos_los_campos_del_schema(self) -> None:
        """Cada evolucion retornada debe conservar todos los campos del schema."""
        evolucion = _make_evolucion(id=99, patient_id="pac-001")
        repo = _mock_repo(evoluciones=[evolucion])
        result = _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        evo = result["evoluciones"][0]
        assert evo["id"] == 99
        assert evo["patient_id"] == "pac-001"
        assert evo["soap_result"] == SOAP_VALIDO
        assert "fecha_creacion" in evo


# ==============================================================================
# 6. OBTENER POR PACIENTE - validacion (4 casos)
# ==============================================================================


class TestObtenerPorPacienteValidacion:
    """Verifica validaciones de patient_id en obtener_por_paciente()."""

    def test_caso_33_patient_id_vacio_lanza_validation_error(self) -> None:
        """Un patient_id vacio en consulta debe rechazarse."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().obtener_por_paciente(patient_id="")

    def test_caso_34_patient_id_solo_espacios_lanza_validation_error(self) -> None:
        """Un patient_id de solo espacios en consulta debe rechazarse."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            _make_service().obtener_por_paciente(patient_id="   ")

    def test_caso_35_no_llama_repo_si_patient_id_invalido(self) -> None:
        """Si la validacion falla, el repositorio no debe consultarse."""
        repo = _mock_repo()
        with pytest.raises(ValidationError):
            _make_service(repo).obtener_por_paciente(patient_id="")
        repo.obtener_por_paciente.assert_not_called()

    def test_caso_36_patient_id_valido_llama_al_repositorio(self) -> None:
        """Un patient_id valido debe disparar la consulta al repositorio."""
        repo = _mock_repo()
        _make_service(repo).obtener_por_paciente(patient_id="pac-001")
        repo.obtener_por_paciente.assert_called_once()


# ==============================================================================
# 7. OBTENER POR PACIENTE - errores de infraestructura (2 casos)
# ==============================================================================


class TestObtenerPorPacienteErroresInfraestructura:
    """Verifica que obtener_por_paciente() propaga errores del repositorio."""

    def test_caso_37_connection_error_del_repo_se_propaga(self) -> None:
        """Un ConnectionError en consulta debe propagarse sin alterarse."""
        repo = _mock_repo()
        repo.obtener_por_paciente.side_effect = ConnectionError("Supabase offline")
        with pytest.raises(ConnectionError, match="Supabase offline"):
            _make_service(repo).obtener_por_paciente(patient_id="pac-001")

    def test_caso_38_validation_error_impide_llamar_repo_en_consulta(self) -> None:
        """Una validacion fallida debe evitar la consulta al repositorio."""
        repo = _mock_repo()
        repo.obtener_por_paciente.side_effect = ConnectionError("no deberia llamarse")
        with pytest.raises(ValidationError):
            _make_service(repo).obtener_por_paciente(patient_id="")
        repo.obtener_por_paciente.assert_not_called()


# ==============================================================================
# 8. _VALIDAR_ENTRADA - metodo estatico puro (8 casos)
# ==============================================================================


class TestValidarEntrada:
    """Tests unitarios directos del metodo estatico _validar_entrada().

    Alta cohesion: prueba exclusivamente la logica de validacion sin
    instanciar el servicio completo ni el repositorio.
    """

    def test_caso_39_entrada_completamente_valida_no_lanza_excepcion(self) -> None:
        """Una entrada valida no debe lanzar ninguna excepcion."""
        ServicioPersistenciaSOAP._validar_entrada("pac-001", SOAP_VALIDO)

    def test_caso_40_patient_id_solo_letras_es_valido(self) -> None:
        """Un patient_id compuesto solo de letras debe ser aceptado."""
        ServicioPersistenciaSOAP._validar_entrada("PacienteUno", SOAP_VALIDO)

    def test_caso_41_patient_id_solo_numeros_es_valido(self) -> None:
        """Un patient_id compuesto solo de numeros debe ser aceptado."""
        ServicioPersistenciaSOAP._validar_entrada("123456", SOAP_VALIDO)

    def test_caso_42_patient_id_con_guiones_compuestos_es_valido(self) -> None:
        """Un patient_id con multiples guiones debe ser aceptado."""
        ServicioPersistenciaSOAP._validar_entrada("pac-001-UAO-2026", SOAP_VALIDO)

    def test_caso_43_soap_exactamente_10_chars_es_valido(self) -> None:
        """Un SOAP de exactamente 10 caracteres debe ser aceptado."""
        ServicioPersistenciaSOAP._validar_entrada("pac-001", SOAP_MINIMO)

    def test_caso_44_ambos_invalidos_genera_mensaje_con_separador(self) -> None:
        """Errores combinados deben separarse con punto y coma en el mensaje."""
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("", "")
        assert ";" in str(exc_info.value)

    def test_caso_45_error_acumulado_menciona_patient_id_y_soap(self) -> None:
        """El mensaje acumulado debe mencionar tanto paciente como SOAP."""
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("", "corto")
        mensaje = str(exc_info.value)
        assert "paciente" in mensaje
        assert "SOAP" in mensaje

    def test_caso_46_patient_id_valido_y_soap_invalido_menciona_solo_soap(self) -> None:
        """Si solo el SOAP es invalido, el mensaje no debe mencionar al paciente."""
        with pytest.raises(ValidationError) as exc_info:
            ServicioPersistenciaSOAP._validar_entrada("pac-001", "")
        mensaje = str(exc_info.value)
        assert "SOAP" in mensaje
        assert "paciente" not in mensaje


# ==============================================================================
# 9. PROTOCOLO Y CONTRATO (4 casos)
# ==============================================================================


class TestProtocoloRepositorio:
    """Verifica que el servicio respeta el principio de bajo acoplamiento.

    El servicio no debe depender de RepositorioSupabase directamente,
    sino de cualquier objeto que cumpla el protocolo RepositorioEvoluciones.
    """

    def test_caso_47_servicio_acepta_cualquier_objeto_como_repositorio(self) -> None:
        """El constructor debe aceptar cualquier mock que cumpla el protocolo."""
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        assert service is not None

    def test_caso_48_guardar_llama_repo_exactamente_una_vez_por_invocacion(self) -> None:
        """Cada llamada a guardar() debe traducirse en una sola llamada al repo."""
        repo = _mock_repo(guardar_id=1)
        service = ServicioPersistenciaSOAP(repo)
        service.guardar(patient_id="pac-001", soap=SOAP_VALIDO)
        service.guardar(patient_id="pac-002", soap=SOAP_VALIDO)
        assert repo.guardar.call_count == 2

    def test_caso_49_obtener_llama_repo_exactamente_una_vez_por_invocacion(self) -> None:
        """Cada llamada a obtener_por_paciente() debe traducirse en una sola llamada al repo."""
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        service.obtener_por_paciente(patient_id="pac-001")
        service.obtener_por_paciente(patient_id="pac-002")
        assert repo.obtener_por_paciente.call_count == 2

    def test_caso_50_multiples_pacientes_no_se_mezclan_en_las_llamadas(self) -> None:
        """Las llamadas para distintos pacientes no deben mezclar sus argumentos."""
        repo = _mock_repo()
        service = ServicioPersistenciaSOAP(repo)
        service.obtener_por_paciente(patient_id="pac-001")
        service.obtener_por_paciente(patient_id="pac-002")
        calls = repo.obtener_por_paciente.call_args_list
        assert calls[0] == call("pac-001", cursor=None, limit=50)
        assert calls[1] == call("pac-002", cursor=None, limit=50)
