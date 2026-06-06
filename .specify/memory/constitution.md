<!-- Sync Impact Report
  Version change: 0.0.0 (template) → 1.0.0
  Bump rationale: Primera versión activa con principios específicos del proyecto
  Modified principles: Todos nuevos (template → personalizados)
  Added sections: 5 principios, 2 constraint sections, governance
  Removed sections: N/A
  Templates pending update: plan-template.md, spec-template.md, tasks-template.md
  Follow-up TODOs: Ninguno
-->
# UAO Asistente SOAP Constitution

## Core Principles

### I. Test-First Development (TDD)

Ninguna función de servicio se escribe sin su respectiva prueba unitaria en
`tests/`. El ciclo Red-Green-Refactor es obligatorio:
- **Red**: Escribir la prueba que falla primero.
- **Green**: Implementar el código mínimo para que pase.
- **Refactor**: Mejorar sin romper la prueba.

Los defectos reproducibles deben convertirse en casos de prueba antes de
corregirlos. Las pruebas deben ejecutarse localmente (`make test`) antes de
realizar push. No se aceptan PRs sin cobertura de pruebas asociada.

### II. Separation of Concerns & SOLID

- **Streamlit** actúa únicamente como capa de presentación. Ninguna lógica de
  negocio (generación SOAP, PDF, transcripción) reside en `app.py`.
- La generación SOAP debe implementarse en servicios independientes dentro de
  `services/`, con alta cohesión y bajo acoplamiento.
- Los servicios no dependen directamente de la UI ni de la base de datos: usan
  abstracciones (Protocol, ABC) para invertir dependencias.
- Refactorizar cuando la complejidad aumente. Evitar duplicación de código
  (DRY).

### III. Static Typing & Linting

- Tipado estricto con `typing` de Python (Type Hints) en **todos** los
  parámetros, retornos y variables de función. Sin excepciones.
- El proyecto debe pasar `mypy --strict` sin errores.
- Cumplimiento riguroso de las reglas de Ruff para linter y formatter.
  Ejecutar `make lint` y `make format` antes de cada commit.

### IV. AI Provider Abstraction

- Los proveedores de IA (Groq, OpenRouter, OpenAI) NO deben estar acoplados
  directamente a la aplicación. Se accede a ellos mediante abstracciones
  (Protocol/ABC) definidas en `services/providers/base.py`.
- El modelo concreto a usar se define EXCLUSIVAMENTE en `.env` mediante las
  variables `SOAP_MODEL` y `OPENROUTER_MODEL`. No se permite hardcodear nombres
  de modelo en el código fuente.
- Si se requiere un modelo diferente, se cambia `.env`, no el código.

### V. Clean Code & Documentation

- **Docstrings obligatorios** en toda función, clase y método público. Formato
  Google-style o reStructuredText.
- No almacenar credenciales en el repositorio. El archivo `.env` está en
  `.gitignore`. Los secretos se gestionan exclusivamente mediante variables de
  entorno.
- Código legible, nombres descriptivos, funciones pequeñas (una
  responsabilidad). Seguir las guías del skill SOLID disponible en el proyecto.

## Technical Constraints

- **Python** >= 3.12, gestionado con `uv` (lockfile: `uv.lock`).
- **Dependencias principales**: streamlit (UI), groq + openai (IA),
  python-dotenv (config), fpdf2 (PDF), requests (HTTP).
- **Frontend**: TypeScript + Vite para el grabador de audio webm (aislado en
  `components/webm_recorder/`).
- **Infraestructura**: Docker con imagen `python:3.12-slim-bookworm`, ffmpeg
  requerido para transcripción.
- **Variables de entorno obligatorias**: `API_SECRET_KEY`, `OPENROUTER_API_KEY`,
  `OPENROUTER_MODEL`, `SOAP_MODEL`. Ver `.env.example`.
- **Calidad**: Ruff (linter + formatter), mypy (strict), pytest + pytest-cov.

## Development Workflow

1. **Plan/Spec**: Usar el flujo SpecKit (`/speckit.specify` → `/speckit.plan` →
   `/speckit.tasks`).
2. **Implementación**: Seguir TDD (Fase Red → Fase Green → Refactor).
3. **Verificación local** antes de commit:
   ```bash
   make check   # Ejecuta lint + typecheck + test en secuencia
   ```
4. **Makefile**: Debe mantener comandos actualizados:
   - `make test` — Ejecuta pytest con cobertura.
   - `make lint` — Ejecuta ruff check.
   - `make format` — Ejecuta ruff format.
   - `make typecheck` — Ejecuta mypy.
   - `make check` — Todo en uno.
   - `make run` — Inicia streamlit.
5. **Commit**: Usar `/speckit.git.commit` con mensajes descriptivos siguiendo
   conventional commits.
6. **Push**: Solo después de que `make check` pase exitosamente.

## Governance

- Esta constitución reemplaza y unifica todas las prácticas anteriores del
  proyecto.
- Las enmiendas requieren: (1) documento de propuesta, (2) revisión de
  impacto en templates y tests, (3) plan de migración, (4) aprobación del
  equipo.
- El versionado sigue SEMVER: MAJOR (cambios incompatibles en principios),
  MINOR (nuevos principios/secciones), PATCH (aclaraciones, correcciones).
- Toda PR debe verificar cumplimiento con esta constitución como parte del
  checklist.

**Version**: 1.0.0 | **Ratified**: 2026-06-05 | **Last Amended**: 2026-06-05
