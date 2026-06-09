# Feature Specification: Fix Model Env Read

**Feature Branch**: `003-fix-model-env-read`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "Solucionar bug MODEL-001 del backlog: leer OPENROUTER_MODEL desde .env en transcriber.py en vez de hardcodear el modelo"

## User Scenarios & Testing

### User Story 1 - Developer configura modelo sin modificar codigo (Priority: P0)

Como desarrollador del proyecto, quiero que el transcriber use el modelo
definido en la variable de entorno `OPENROUTER_MODEL` para no tener que
modificar el codigo fuente cuando cambie de proveedor o version de modelo.

**Why this priority**: Es un bug P0 (critico) porque viola el Principio IV
de la constitucion (el modelo debe definirse exclusivamente en `.env`).
Ademas, bloquea el cambio de modelo sin editar codigo.

**Independent Test**: Ejecutar un test que mockee `os.getenv("OPENROUTER_MODEL")`
y verifique que el constructor de `OpenRouterTranscriber` usa el valor mockeado.

**Acceptance Scenarios**:

1. **Given** la variable `OPENROUTER_MODEL` definida en el entorno,
   **When** se crea una instancia de `OpenRouterTranscriber` sin pasar `model`,
   **Then** el valor de `self.model` es el de `OPENROUTER_MODEL`.

2. **Given** la variable `OPENROUTER_MODEL` NO definida en el entorno,
   **When** se crea una instancia de `OpenRouterTranscriber` sin pasar `model`,
   **Then** el valor de `self.model` es `"openai/whisper-large-v3-turbo"` (fallback).

3. **Given** un valor explicito de `model` pasado al constructor,
   **When** se crea la instancia,
   **Then** el valor de `self.model` es el valor explicito, ignorando `OPENROUTER_MODEL`.

### Edge Cases

- Que pasa si `OPENROUTER_MODEL` esta vacio (empty string)? — debe
  usar el fallback "openai/whisper-large-v3-turbo".
- Que pasa si `OPENROUTER_MODEL` no existe en el entorno? — debe
  usar el fallback sin lanzar error.

## Requirements

### Functional Requirements

- **FR-001**: El constructor de `OpenRouterTranscriber` DEBE leer
  `OPENROUTER_MODEL` del entorno cuando no se pasa `model` explicitamente.
- **FR-002**: Si `OPENROUTER_MODEL` no esta definida o esta vacia, DEBE
  usar `"openai/whisper-large-v3-turbo"` como fallback.
- **FR-003**: Si se pasa un `model` explicito al constructor, DEBE
  usarse ese valor sin consultar `OPENROUTER_MODEL`.
- **FR-004**: DEBE existir un test unitario que mockee `os.getenv` y
  verifique los tres escenarios de las acceptance scenarios.

### Key Entities

N/A — No involucra entidades de datos. Es una correccion de configuracion.

## Success Criteria

### Measurable Outcomes

- **SC-001**: El transcriber usa el modelo definido en `OPENROUTER_MODEL`
  cuando la variable existe, sin necesidad de modificar codigo.
- **SC-002**: El transcriber sigue funcionando con el modelo fallback
  cuando `OPENROUTER_MODEL` no esta definida.
- **SC-003**: Los tests unitarios cubren los 3 escenarios (env definida,
  env no definida, modelo explicito) y pasan correctamente.

## Assumptions

- `.env.example` ya documenta `OPENROUTER_MODEL` correctamente.
- La variable `OPENROUTER_MODEL` se carga via `python-dotenv` antes de
  importar el transcriber (existente en `app.py`).
- El unico cambio necesario esta en `services/transcriber.py` — no se
  requieren cambios en otros modulos.
