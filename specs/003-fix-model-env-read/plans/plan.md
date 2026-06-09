# Implementation Plan: MODEL-001 — fix-model-env-read

**Spec**: `specs/003-fix-model-env-read/spec.md`

**Created**: 2026-06-08

**Status**: Draft

## Technical Context

### Problem
`services/transcriber.py:23` hardcodea `model: str = "openai/whisper-large-v3-turbo"` como default
en el constructor de `OpenRouterTranscriber`, en vez de leer la variable de entorno
`OPENROUTER_MODEL`. Esto viola el Principio IV de la constitucion del proyecto.

### Solution
Cambiar el default del parametro `model` a `None` y usar `os.environ.get("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")` como valor efectivo cuando no se pasa un modelo explicito.

### Scope
- Un solo archivo de codigo modificado: `services/transcriber.py` (1 linea del constructor)
- Un nuevo archivo de test: `tests/unit/test_transcriber_model.py` (3 tests)
- Sin cambios en `app.py`, `services/audio_utils.py`, ni otros modulos.

### Dependencies
- Ninguna. La funcionalidad de `dotenv` ya carga las variables antes de usar el transcriber.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. TDD** | ✅ Tests cubren los 3 escenarios antes/durante el fix | FR-004 del spec |
| **II. SOLID** | ✅ Sin impacto en separacion de responsabilidades | Cambio localizado |
| **III. Typing** | ✅ `str \| None` es compatible con mypy strict | No breaking changes |
| **IV. AI Abstraction** | ✅ **Objetivo principal del fix** — modelo via `.env` | Alinea con la constitucion |
| **V. Clean Code** | ✅ Codigo legible, sin duplicacion | |

## Gates

- [x] Spec completado y validado (checklist items todos ✔️)
- [x] Sin NEEDS CLARIFICATION
- [x] Constitucion: cumple Principio IV
- [x] Sin breaking changes en API publica
- [ ] Pendiente: `make check` pasa tras implementacion

## Implementation Steps

### Step 1: Modify `services/transcriber.py`

**File**: `services/transcriber.py`

**Change 1** — Parametro `__init__` (linea 23):
```python
# Antes:
model: str = "openai/whisper-large-v3-turbo",
# Despues:
model: str | None = None,
```

**Change 2** — Cuerpo del `__init__` (linea 28):
```python
# Antes:
self.model = model
# Despues:
self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/whisper-large-v3-turbo")
```

**Rationale**: Si `model=None` (default), evalua `os.environ.get("OPENROUTER_MODEL")`. Si esa variable no existe o esta vacia, cae al fallback `"openai/whisper-large-v3-turbo"`. Si el caller pasa un modelo explicito, `model or ...` lo preserva.

### Step 2: Create `tests/unit/test_transcriber_model.py`

```python
from __future__ import annotations

from typing import Any

from services.transcriber import OpenRouterTranscriber


def test_model_reads_from_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model-from-env")
    transcriber = OpenRouterTranscriber(api_key="test-key")
    assert transcriber.model == "test-model-from-env"


def test_model_fallback_when_env_missing(monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    transcriber = OpenRouterTranscriber(api_key="test-key")
    assert transcriber.model == "openai/whisper-large-v3-turbo"


def test_explicit_model_ignores_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "should-be-ignored")
    transcriber = OpenRouterTranscriber(api_key="test-key", model="explicit-model")
    assert transcriber.model == "explicit-model"
```

### Step 3: Run verification

```bash
make check
```

Expected: lint ✅, typecheck ✅, test ✅ (3 tests pass).

### Step 4: Update agent context

Actualizar `AGENTS.md` para reflejar el plan completado.

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Spec | `specs/003-fix-model-env-read/spec.md` | ✅ Created |
| Plan | `specs/003-fix-model-env-read/plans/plan.md` | ✅ This file |
| Checklist | `specs/003-fix-model-env-read/checklists/requirements.md` | ✅ Created |

## Next Steps

Una vez aprobado este plan, ejecutar:
1. Modificar `services/transcriber.py` (2 cambios)
2. Crear `tests/unit/test_transcriber_model.py` (3 tests)
3. `make check` para verificar
4. Commit via `/speckit.git.commit`
