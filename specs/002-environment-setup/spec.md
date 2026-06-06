# Feature Specification: Environment Setup (Dev Tooling)

**Feature Branch**: `002-environment-setup`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Resolver INFRA-001 y INFRA-002 del backlog: configurar herramientas de calidad en pyproject.toml y poblar Makefile con comandos utiles"

## User Scenarios & Testing

### User Story 1 - Developer configura entorno de calidad (Priority: P1)

Como desarrollador del proyecto, quiero que las herramientas de calidad
(ruff, mypy, pytest) esten configuradas en pyproject.toml para que
pueda ejecutar linting, type-checking y tests con un solo comando.

**Why this priority**: Sin esta configuracion no se puede verificar
ninguna contribucion de codigo. Es el prerrequisito para todos los
demas items del backlog.

**Independent Test**: Ejecutar `uv sync` y verificar que ruff, mypy,
pytest estan disponibles. Luego `make check` falla limpiamente (sin
errores de comando no encontrado) porque aun no hay codigo que verificar.

**Acceptance Scenarios**:

1. **Given** el proyecto clonado, **When** ejecuto `uv sync`,
   **Then** ruff, mypy, pytest y pytest-cov estan instalados en el
   entorno virtual.
2. **Given** ruff instalado, **When** ejecuto `ruff check .`,
   **Then** se ejecuta el linter sin errores de configuracion.

---

### User Story 2 - Developer usa Makefile para tareas comunes (Priority: P1)

Como desarrollador, quiero un Makefile con targets `test`, `lint`,
`format`, `typecheck`, `check`, `run` para no tener que recordar los
comandos exactos de cada herramienta.

**Why this priority**: El Makefile unifica la interfaz de comandos y
es el estandar definido en la constitucion (v1.0.0, Development Workflow).

**Independent Test**: Ejecutar `make test`, `make lint`, `make format`,
`make typecheck`, `make run` - cada uno debe ejecutarse sin error de
comando no encontrado.

**Acceptance Scenarios**:

1. **Given** Makefile poblado, **When** ejecuto `make lint`,
   **Then** se ejecuta `ruff check .` y retorna 0.
2. **Given** Makefile poblado, **When** ejecuto `make test`,
   **Then** se ejecuta `pytest` con cobertura y retorna 0.
3. **Given** Makefile poblado, **When** ejecuto `make check`,
   **Then** ejecuta lint - typecheck - test en secuencia y retorna 0.

### Edge Cases

- Que pasa si `uv` no esta instalado? - `make install` falla con
  mensaje claro de error.
- Que pasa si no hay tests todavia? - `make test` debe reportar
  "no tests collected" pero no fallar.
- Que pasa si hay errores de lint? - `make lint` retorna != 0,
  `make check` debe detenerse y reportar el error.

## Requirements

### Functional Requirements

- **FR-001**: pyproject.toml MUST incluir `[tool.ruff]` con reglas
  de linter y formatter.
- **FR-002**: pyproject.toml MUST incluir `[tool.mypy]` con
  configuracion estricta.
- **FR-003**: pyproject.toml MUST incluir `[tool.pytest.ini_options]`
  con configuracion basica.
- **FR-004**: pyproject.toml MUST incluir dev-dependencies:
  `pytest>=8`, `pytest-cov>=5`, `ruff>=0.6`, `mypy>=1.11`.
- **FR-005**: Makefile MUST tener targets: `test`, `lint`, `format`,
  `typecheck`, `check`, `run`, `install`, `clean`, `help`.
- **FR-006**: `make test` MUST ejecutar `pytest` con coverage.
- **FR-007**: `make lint` MUST ejecutar `ruff check .`
- **FR-008**: `make format` MUST ejecutar `ruff format .`
- **FR-009**: `make typecheck` MUST ejecutar `mypy .`
- **FR-010**: `make check` MUST ejecutar lint - typecheck - test
  secuencialmente, deteniendose si alguna falla.
- **FR-011**: `make run` MUST ejecutar `streamlit run app.py`
- **FR-012**: Todos los targets MUST usar `uv run` para ejecutar
  herramientas dentro del entorno virtual.
- **FR-013**: Makefile MUST incluir target `docker-build` que ejecute
  `docker build -t uao-asistente-soap:local .`
- **FR-014**: Makefile MUST incluir target `docker-run` que ejecute
  `docker run` con `--env-file .env` y puerto 8501.
- **FR-015**: Makefile MUST incluir targets `docker-stop`, `docker-rm`,
  `docker-logs`, `docker-rebuild`.
- **FR-016**: Makefile MUST incluir target `help` que liste y describa
  todos los targets disponibles agrupados por categoria.

### Key Entities

N/A - Esta tarea no involucra entidades de datos. Es infraestructura
de desarrollo.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make check` se ejecuta de principio a fin sin errores
  de comando no encontrado.
- **SC-002**: `ruff check .` reporta cero errores en el codigo existente.
- **SC-003**: `mypy .` se ejecuta sin errores de configuracion
  (puede reportar type errors del codigo existente, pero no errores
  de configuracion).
- **SC-004**: `pytest` descubre y ejecuta los tests existentes en
  `tests/unit/`.
- **SC-005**: `make help` muestra todos los targets disponibles con
  descripcion.

## Assumptions

- El proyecto usa `uv` como gestor de paquetes (lockfile `uv.lock`
  presente).
- Python >= 3.12 esta disponible en el entorno de desarrollo.
- Las herramientas (ruff, mypy, pytest) no existian previamente
  como dependencias.
- El Makefile se usara en Windows (PowerShell) y Linux/Mac (bash)
  - los comandos deben ser cross-platform.
- Docker esta instalado para los comandos `docker-*`.
