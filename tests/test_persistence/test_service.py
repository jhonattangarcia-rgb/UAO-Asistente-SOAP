"""Tests for ServicioPersistenciaSOAP validation and orchestration."""

from __future__ import annotations

import pytest

from services.persistence.service import (
    ServicioPersistenciaSOAP,
    ValidationError,
)
from tests.test_persistence.conftest import MockRepositorioEvoluciones


class TestServicioPersistenciaSOAPGuardar:
    """US1 — Guardar una evolución SOAP exitosamente."""

    @pytest.fixture
    def repo(self) -> MockRepositorioEvoluciones:
        return MockRepositorioEvoluciones()

    @pytest.fixture
    def service(self, repo: MockRepositorioEvoluciones) -> ServicioPersistenciaSOAP:
        return ServicioPersistenciaSOAP(repo)

    def test_guardar_exitoso_retorna_id_y_mensaje(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        soap = (
            "S: Paciente refiere dolor lumbar progresivo.\n"
            "O: Contractura paravertebral. EVA 6/8.\n"
            "A: Lumbalgia mecánica.\n"
            "P: AINE por 7 días, fisioterapia."
        )
        result = service.guardar(patient_id="pac-001", soap=soap)
        assert result["id"] == 1
        assert result["mensaje"] == "Evolución guardada exitosamente"

    def test_guardar_con_patient_id_vacio_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.guardar(patient_id="", soap="S: Dolor de cabeza.\nP: Reposo.")
        assert "no puede estar vacío" in str(exc.value)

    def test_guardar_con_soap_corto_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.guardar(patient_id="pac-001", soap="Corto")
        assert "10 caracteres" in str(exc.value)

    def test_guardar_con_patient_id_invalido_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.guardar(
                patient_id="pac-001@malo!",
                soap="S: Válido.\nO: Normal.\nA: Estable.\nP: Continuar.",
            )
        assert "solo puede contener" in str(exc.value)

    def test_guardar_con_soap_demasiado_largo_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.guardar(patient_id="pac-001", soap="X" * 100_001)
        assert "100.000" in str(exc.value) or "100000" in str(exc.value)

    def test_guardar_con_bd_no_disponible_lanza_error(
        self,
        repo: MockRepositorioEvoluciones,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        repo.fail_next_call()
        soap = "S: Test.\nO: Normal.\nA: Bueno.\nP: Esperar."
        with pytest.raises(ConnectionError) as exc:
            service.guardar(patient_id="pac-001", soap=soap)
        assert "disponible" in str(exc.value)


class TestServicioPersistenciaSOAPObtenerPorPaciente:
    """US2 — Consultar historial de evoluciones de un paciente."""

    @pytest.fixture
    def repo(self) -> MockRepositorioEvoluciones:
        return MockRepositorioEvoluciones()

    @pytest.fixture
    def service(
        self,
        repo: MockRepositorioEvoluciones,
    ) -> ServicioPersistenciaSOAP:
        svc = ServicioPersistenciaSOAP(repo)
        svc.guardar(patient_id="pac-001", soap="S: Primera.\nO: OK.\nA: Bien.\nP: Seguir.")
        svc.guardar(patient_id="pac-001", soap="S: Segunda.\nO: OK.\nA: Bien.\nP: Seguir.")
        return svc

    def test_obtener_por_paciente_retorna_todas(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        result = service.obtener_por_paciente(patient_id="pac-001")
        assert len(result["evoluciones"]) == 2

    def test_obtener_por_paciente_orden_descendente(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        result = service.obtener_por_paciente(patient_id="pac-001")
        evoluciones = result["evoluciones"]
        assert evoluciones[0]["id"] == 2  # más reciente
        assert evoluciones[1]["id"] == 1

    def test_obtener_por_paciente_sin_evoluciones_retorna_vacio(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        result = service.obtener_por_paciente(patient_id="pac-999")
        assert result["evoluciones"] == []
        assert result["cursor"] is None

    def test_obtener_por_paciente_con_cursor_retorna_siguiente_pagina(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        result = service.obtener_por_paciente(patient_id="pac-001", limit=1)
        assert len(result["evoluciones"]) == 1
        assert result["cursor"] == 2  # última id en la página 1
        page2 = service.obtener_por_paciente(
            patient_id="pac-001",
            cursor=result["cursor"],
            limit=1,
        )
        assert len(page2["evoluciones"]) == 1
        assert page2["evoluciones"][0]["id"] == 1  # la primera, ahora en página 2


class TestServicioPersistenciaSOAPObtenerAnterior:
    """US2 (ext) — Consultar evolución anterior de un paciente."""

    @pytest.fixture
    def repo(self) -> MockRepositorioEvoluciones:
        return MockRepositorioEvoluciones()

    @pytest.fixture
    def service(
        self,
        repo: MockRepositorioEvoluciones,
    ) -> ServicioPersistenciaSOAP:
        return ServicioPersistenciaSOAP(repo)

    def test_con_dos_evoluciones_retorna_mas_reciente(
        self,
        repo: MockRepositorioEvoluciones,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        repo.guardar(patient_id="pac-001", soap="S: Primera.\nO: Normal.\nA: Bien.\nP: Seguir.")
        repo.guardar(patient_id="pac-001", soap="S: Segunda.\nO: Normal.\nA: Bien.\nP: Seguir.")
        result = service.obtener_evolucion_anterior(patient_id="pac-001")
        assert result["evolucion"] is not None
        assert result["evolucion"]["id"] == 2  # la más reciente
        assert "encontrada" in result["mensaje"].lower()

    def test_con_una_evolucion_retorna_la_unica(
        self,
        repo: MockRepositorioEvoluciones,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        repo.guardar(patient_id="pac-001", soap="S: Unica.\nO: Normal.\nA: Bien.\nP: Seguir.")
        result = service.obtener_evolucion_anterior(patient_id="pac-001")
        assert result["evolucion"] is not None
        assert result["evolucion"]["id"] == 1
        assert "encontrada" in result["mensaje"].lower()

    def test_sin_evoluciones_retorna_none(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        result = service.obtener_evolucion_anterior(patient_id="pac-999")
        assert result["evolucion"] is None
        assert "no hay" in result["mensaje"].lower()

    def test_patient_id_vacio_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.obtener_evolucion_anterior(patient_id="")
        assert "vacío" in str(exc.value)

    def test_patient_id_invalido_rechaza(
        self,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            service.obtener_evolucion_anterior(patient_id="invalid@#$")
        assert "solo puede contener" in str(exc.value)

    def test_conexion_bd_falla_lanza_error(
        self,
        repo: MockRepositorioEvoluciones,
        service: ServicioPersistenciaSOAP,
    ) -> None:
        repo.fail_next_call()
        with pytest.raises(ConnectionError):
            service.obtener_evolucion_anterior(patient_id="pac-001")
