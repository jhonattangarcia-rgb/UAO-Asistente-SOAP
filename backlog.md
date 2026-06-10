# Backlog Técnico — UAO Asistente SOAP

> Backlog generado el 2026-06-05. Última revisión: 2026-06-10.
> Pendientes priorizados por impacto. Cada item debe convertirse en
> un issue/feature branch siguiendo el flujo SpecKit.

---

## P0 — Prioridad Crítica (Bloqueantes de calidad)

### [INFRA-001] Configurar herramientas de calidad en `pyproject.toml` ✅ DONE
- **Problema**: No existe configuración de Ruff, mypy ni pytest.
- **Acción**: Agregar `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`
  y dev-dependencies (`pytest`, `ruff`, `mypy`, `pytest-cov`).
- **Verificación**: `make lint && make typecheck && make test` pasan.

### [INFRA-002] Poblar `Makefile` con comandos útiles ✅ DONE
- **Problema**: `Makefile` vacío.
- **Acción**: Implementar targets: `test`, `lint`, `format`, `typecheck`,
  `check`, `run`.
- **Verificación**: `make check` ejecuta lint + typecheck + test en secuencia.

### [MODEL-001] Leer `OPENROUTER_MODEL` desde `.env` en `transcriber.py` ✅ DONE
- **Problema**: `services/transcriber.py:24` hardcodea
  `model: str = "openai/whisper-large-v3-turbo"` como default en vez de leer
  `os.getenv("OPENROUTER_MODEL")`.
- **Acción**: Cambiar default a `os.getenv("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")`.
- **Verificación**: Test unitario que mocke `os.getenv` y verifique el valor.

### [ARCH-001] Extraer lógica SOAP de `app.py` a servicio independiente ✅ DONE
- **Problema**: `app.py` (312 lines) contiene lógica SOAP, PDF, prompts y UI
  todo mezclado. Viola Single Responsibility y la constitución (Principio II).
- **Acción**: Crear `services/soap_generator.py`, `services/pdf_generator.py`,
  `services/prompt_builder.py`. `app.py` solo llama a estos servicios.
- **Verificación**: Tests unitarios para cada nuevo servicio. `app.py` sin
  lógica de negocio (solo Streamlit).

### [ARCH-002] Crear abstracción de proveedores IA ✅ DONE
- **Problema**: Groq se instancia directamente en `app.py` via
  `Groq(api_key=...)`. Viola Dependency Inversion.
- **Acción**: Crear `services/providers/base.py` con Protocol/ABC,
  `services/providers/groq_provider.py`, `services/providers/registry.py`.
- **Verificación**: `app.py` solo conoce la abstracción, no la implementación
  concreta.

---

## P1 — Prioridad Alta

### [TEST-001] Tests unitarios para `services/transcriber.py` ⚠️ PARCIAL
- **Problema**: 0 tests para el transcriber (167 líneas).
- **Acción**: Mockear `requests.post` y `subprocess.run`. Tests para:
  constructor, `_get_duration_ms`, `_extract_mp3_chunk`, `_call_api` (éxito,
  retry, 401, timeout), `transcribe_file`.
- **Cobertura esperada**: >90%.
- **Estado actual**: Solo existe `test_transcriber_model.py` (3 tests para el modelo). Faltan tests para el core del transcriber.

### [TEST-002] Tests unitarios para `services/audio_utils.py` ❌ PENDIENTE
- **Problema**: 0 tests para `audio_utils.py` (24 líneas).
- **Acción**: Tests para `ensure_tmp_dir`, `save_webm_bytes`, `clear_tmp_recording`.
- **Cobertura esperada**: 100%.

### [TEST-003] Tests unitarios para servicios SOAP (por crear) ✅ DONE
- **Problema**: No existen servicios SOAP ni PDF todavía (ver ARCH-001).
- **Acción**: Una vez creados, escribir tests unitarios para cada servicio
  siguiendo TDD (prueba primero, implementación después).
- **Estado actual**: `test_soap_generator.py`, `test_pdf_generator.py`, `test_prompt_builder.py` existen y pasan.

### [TEST-004] Crear `tests/conftest.py` ❌ PENDIENTE
- **Problema**: No hay fixtures compartidos entre tests.
- **Acción**: Crear `conftest.py` con `tmp_path`, mocks de API keys,
  muestras de audio/soap para reutilizar.

### [TYPE-001] Agregar type hints faltantes en `app.py` ✅ DONE
- **Problema**: `generar_pdf_validacion` y `limpiar_texto` no tienen type hints.
- **Acción**: Agregar tipos a todas las funciones en `app.py`.
- **Verificación**: `mypy --strict app.py` pasa.

---

## P2 — Prioridad Media

### [DOC-001] Actualizar `.env.example` con `SOAP_MODEL` ✅ DONE
- **Problema**: `.env.example` no incluye `SOAP_MODEL` pero `app.py` lo usa.
- **Acción**: Agregar `SOAP_MODEL="llama-3.1-8b-instant"` a `.env.example`.

### [DOC-002] Agregar docstrings faltantes ⚠️ PARCIAL
- **Problema**: Varias funciones sin docstrings (ver Principio V).
- **Acción**: Revisar y agregar docstrings Google-style en funciones públicas
  de todos los módulos.
- **Estado actual**: `base.py`, `prompt_builder.py`, `soap_generator.py`, `pdf_generator.py` tienen docstrings. `transcriber.py` y `audio_utils.py` carecen de ellos.

### [CLN-001] Eliminar duplicación de manejo temporal de audio ✅ DONE
- **Problema**: `app.py` tiene lógica `_save_webm_b64` que duplica
  responsabilidades de `services/audio_utils.py`.
- **Acción**: Refactorizar `app.py` para usar solo `audio_utils.save_webm_bytes()`.

### [CLN-002] Separar prompts de la UI ✅ DONE
- **Problema**: `PROMPT_ESTRUCTURA_FIJA` y `PROMPT_REGLAS_VARIABLES` son
  globales en `app.py`.
- **Acción**: Mover a `services/prompt_builder.py` o archivo de configuración.

---

## P3 — Prioridad Baja (Mejora continua)

### [TMPL-001] Alinear templates SpecKit con la constitución ❌ PENDIENTE
- **Problema**: `plan-template.md`, `spec-template.md`, `tasks-template.md`
  pueden no reflejar los nuevos principios.
- **Acción**: Revisar y actualizar referencias.

### [CI-001] Configurar GitHub Actions para CI ❌ PENDIENTE
- **Problema**: No hay pipeline CI.
- **Acción**: Crear `.github/workflows/ci.yml` con `make check` en PRs y pushes.

### [COV-001] Alcanzar 100% de cobertura en tests ❌ PENDIENTE
- **Problema**: Sin métrica actual.
- **Acción**: Una vez implementados todos los tests de P0/P1, monitorear
  cobertura con `pytest-cov` y llevarla a 100%.
- **Cobertura actual**: ~60% global (servicios nuevos al 100%, transcriber y audio_utils pendientes).

---

## Resumen

| Prioridad | Cantidad | ✅ Done | ⚠️ Parcial | ❌ Pendiente |
|-----------|----------|---------|-------------|--------------|
| P0 (Crítica) | 5 | 5 | 0 | 0 |
| P1 (Alta) | 5 | 2 | 1 | 2 |
| P2 (Media) | 4 | 3 | 1 | 0 |
| P3 (Baja) | 3 | 0 | 0 | 3 |
| **Total** | **17** | **10** | **2** | **5** |
