"""Tests unitarios puros para Config y ConfigError.

Responsabilidad: validar exclusivamente la lectura y validacion de
variables de entorno requeridas por la capa de persistencia, sin
ninguna dependencia de Supabase real.

Alta cohesion: cada clase prueba una unica responsabilidad de Config.
Bajo acoplamiento: usa monkeypatch sobre os.environ, sin tocar el
sistema de archivos ni servicios externos.
"""

from __future__ import annotations

import pytest

from services.persistence.config import Config, ConfigError

# --- Constantes de prueba ---------------------------------------------------

URL_VALIDA = "https://proyecto-fastsoap.supabase.co"
KEY_VALIDA = "service-role-key-de-prueba-123456"


# --- Factories ----------------------------------------------------------------


def _set_valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configurar ambas variables de entorno requeridas con valores validos."""
    monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)


# ==============================================================================
# 1. CONFIG - construccion exitosa (6 casos)
# ==============================================================================


class TestConfigConstruccionExitosa:
    """Verifica que Config se construye correctamente con variables validas."""

    def test_caso_01_construye_sin_lanzar_excepcion(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Con ambas variables presentes, Config() no debe lanzar excepcion."""
        _set_valid_env(monkeypatch)
        Config()

    def test_caso_02_expone_supabase_url_correcto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """El atributo supabase_url debe coincidir exactamente con el env var."""
        _set_valid_env(monkeypatch)
        config = Config()
        assert config.supabase_url == URL_VALIDA

    def test_caso_03_expone_supabase_service_key_correcto(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """El atributo supabase_service_key debe coincidir exactamente con el env var."""
        _set_valid_env(monkeypatch)
        config = Config()
        assert config.supabase_service_key == KEY_VALIDA

    def test_caso_04_url_con_caracteres_especiales_se_acepta(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Una URL con query params o puertos debe aceptarse sin validacion de formato."""
        monkeypatch.setenv("SUPABASE_URL", "https://proyecto.supabase.co:443/v1?x=1")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        config = Config()
        assert "proyecto.supabase.co" in config.supabase_url

    def test_caso_05_key_larga_tipo_jwt_se_acepta(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Una service key larga (formato JWT real) debe aceptarse sin truncar."""
        key_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." + "x" * 200
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", key_jwt)
        config = Config()
        assert config.supabase_service_key == key_jwt

    def test_caso_06_dos_instancias_leen_el_mismo_entorno_independientemente(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Dos instancias de Config creadas en el mismo entorno deben ser consistentes."""
        _set_valid_env(monkeypatch)
        config_a = Config()
        config_b = Config()
        assert config_a.supabase_url == config_b.supabase_url
        assert config_a.supabase_service_key == config_b.supabase_service_key


# ==============================================================================
# 2. CONFIG - variables faltantes (5 casos)
# ==============================================================================


class TestConfigVariablesFaltantes:
    """Verifica que Config falla rapido (fail-fast) ante configuracion incompleta."""

    def test_caso_07_sin_supabase_url_lanza_config_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sin SUPABASE_URL definida, Config() debe lanzar ConfigError."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        with pytest.raises(ConfigError, match="SUPABASE_URL"):
            Config()

    def test_caso_08_sin_supabase_service_key_lanza_config_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sin SUPABASE_SERVICE_KEY definida, Config() debe lanzar ConfigError."""
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        with pytest.raises(ConfigError, match="SUPABASE_SERVICE_KEY"):
            Config()

    def test_caso_09_url_vacia_se_trata_como_faltante(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Un SUPABASE_URL vacio (cadena vacia) debe tratarse como no definido."""
        monkeypatch.setenv("SUPABASE_URL", "")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        with pytest.raises(ConfigError, match="SUPABASE_URL"):
            Config()

    def test_caso_10_service_key_vacia_se_trata_como_faltante(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Un SUPABASE_SERVICE_KEY vacio (cadena vacia) debe tratarse como no definido."""
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "")
        with pytest.raises(ConfigError, match="SUPABASE_SERVICE_KEY"):
            Config()

    def test_caso_11_ambas_variables_faltantes_reporta_la_primera(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Si ambas variables faltan, debe reportarse la primera validada (SUPABASE_URL)."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        with pytest.raises(ConfigError, match="SUPABASE_URL"):
            Config()


# ==============================================================================
# 3. CONFIG - mensaje de error y tipo de excepcion (3 casos)
# ==============================================================================


class TestConfigMensajesDeError:
    """Verifica que ConfigError sea informativo y del tipo correcto."""

    def test_caso_12_config_error_es_subclase_de_exception(self) -> None:
        """ConfigError debe heredar de Exception para ser capturable genericamente."""
        assert issubclass(ConfigError, Exception)

    def test_caso_13_mensaje_menciona_archivo_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """El mensaje de error debe orientar al usuario hacia el archivo .env."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY_VALIDA)
        with pytest.raises(ConfigError, match=".env"):
            Config()

    def test_caso_14_mensaje_incluye_nombre_exacto_de_la_variable(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """El mensaje debe incluir el nombre exacto de la variable de entorno faltante."""
        monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        with pytest.raises(ConfigError) as exc_info:
            Config()
        assert "SUPABASE_SERVICE_KEY" in str(exc_info.value)
