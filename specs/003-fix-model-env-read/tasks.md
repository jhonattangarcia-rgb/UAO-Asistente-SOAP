# Tasks: MODEL-001 — fix-model-env-read

**Feature**: Fix Model Env Read

**Spec**: `specs/003-fix-model-env-read/spec.md`

**Plan**: `specs/003-fix-model-env-read/plans/plan.md`

**Created**: 2026-06-08

## Phase 1: Setup

- [X] T001 Crear directorio `tests/unit/` si no existe
- [X] T002 Verificar que `services/transcriber.py` existe y es accesible

## Phase 2: Implementation [US1]

- [X] T003 [P] [US1] Modificar constructor de `OpenRouterTranscriber` en `services/transcriber.py` — cambiar default `model: str` a `model: str | None = None` y asignar `self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")`
- [X] T004 [US1] Crear `tests/unit/test_transcriber_model.py` con 3 tests: `test_model_reads_from_env`, `test_model_fallback_when_env_missing`, `test_explicit_model_ignores_env`

## Phase 3: Verification

- [X] T005 Ejecutar `make check` (lint → typecheck → test) y confirmar que pasa

## Dependency Graph

```
T001 → T002 → T003 ─┐
                    ├→ T005
               T004 ─┘
```

## Parallel Execution

- **T003 y T004**: Pueden ejecutarse en paralelo (distintos archivos, sin dependencias mutuas).
- **T005**: Bloqueante — requiere T003 y T004 completados.

## Implementation Strategy

Por ser una sola User Story con solo 2 cambios (1 linea de codigo + archivo de tests), se entrega en un unico incremento. T003 y T004 son paralelizables. T005 es la verificacion final con `make check`.

## Independent Test Criteria

**US1**: Ejecutar `uv run pytest tests/unit/test_transcriber_model.py -v` — debe pasar 3/3 tests.

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 5 |
| Tasks per US | 2 (T003, T004) |
| Parallel opportunities | 1 (T003 ⟂ T004) |
| Independent test criteria | 3 tests con monkeypatch |
| MVP scope | US1 completa (unica historia) |
