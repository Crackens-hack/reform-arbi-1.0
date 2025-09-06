# Repository Guidelines

## Estructura del Proyecto y Módulos
- `Dockerfile`: Imagen de desarrollo con utilidades Bash preparadas.
- `entrypoint.sh`: Delegado; ejecuta `dev/bootstrap.sh` para configurar el entorno.
- `dev/`: Entorno Bash portable (lógica principal).
  - `dev/bootstrap.sh`: Setup idempotente para Alpine/Debian/Ubuntu.
  - `dev/bash/`: Variables, aliases, prompt y completados (`.bash_*`).
- `.vscode/`: Preferencias del editor.
- `main.py`: Placeholder para código Python futuro.

## Comandos de Build, Test y Desarrollo
- Construir imagen: `docker build -t repo-dev .`
- Iniciar contenedor: `docker run --rm -it -v "$PWD:/app" repo-dev bash -l`
- Mantener sesión viva: `bash -l -c "tail -f /dev/null"`
- Auto‑instalación opcional: `DEV_AUTO_INSTALL=1 /app/dev/bootstrap.sh`

## Estilo y Convenciones de Nombres
- Python: PEP 8, indentación 4 espacios, `snake_case` para funciones/módulos y `PascalCase` para clases. Ej.: `src/util/date_utils.py`.
- Bash: `set -euo pipefail`; preferir funciones a pipelines largos; archivos en `lower_snake`. Ej.: `scripts/db_dump.sh`.
- Formateo/Lint (recomendado): `black` y `ruff` (Python), `shellcheck` (Bash). Añadir config al incorporarlos.

## Guía de Pruebas
- Aún no hay pruebas. Al añadir código:
  - Framework: `pytest` con árbol `tests/` que refleje los paquetes.
  - Nombres: `test_<unidad>.py`, funciones `test_<comportamiento>()`.
  - Ejecución: `pytest -q` (dentro del contenedor) una vez configuradas dependencias.

## Commits y Pull Requests
- Commits imperativos, acotados y claros. Preferir Conventional Commits.
  - Ej.: `feat(dev): mejorar idempotencia de bootstrap`, `fix(entrypoint): manejar ausencia de script`.
- PRs con: propósito, cambios clave, notas de prueba y issues vinculados. Adjuntar capturas/logs para cambios de experiencia en shell.

## Seguridad y Configuración
- Instalaciones controladas: activar sólo con `DEV_AUTO_INSTALL=1`. Evitarlo en CI salvo necesidad.
- Volúmenes: montar el repo en `/app` para que `entrypoint.sh` encuentre `dev/bootstrap.sh`.
- Base mínima: documentar en el `Dockerfile` cualquier nueva dependencia de sistema.

## Instrucciones para Agentes
- Usar `bash -l` para cargar el entorno personalizado.
- Priorizar `dev/bootstrap.sh` en lugar de cambios ad‑hoc del sistema.
- Si agregás app code, agrupar bajo `src/` y conservar `main.py` como entrypoint o wrapper de CLI.
