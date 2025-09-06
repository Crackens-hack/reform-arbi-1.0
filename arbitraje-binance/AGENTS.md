AGENTS.md — Guía rápida para Codex CLI (stack Binance)

Eres Codex (sesión nueva o continua). Sigue estos pasos mínimos para operar dentro del contenedor con simbiosis y trazabilidad.

1) Lee las reglas base
- Dentro del contenedor, abre: `/workspace/codex-rules/rules`.
- Ahí están tu alcance de escritura, ritual de inicio, Action-ID y cómo documentar cada acción.

2) Entiende tu workspace
- Estás en `/workspace`.
- Monorepo global (solo lectura): `/workspace/1-repo-global-solo-lectura`.
- Tu ámbito de escritura es estrictamente tu motor y su volumen custom:
  - Código del motor: `/workspace/<motor>/` (ej. `motor_sentinel`, `motor_reactor_realtime`, `motor_data_refinery`).
  - Continuidad: `/workspace/custom-codex-<motor>/` (ej. `custom-codex-sentinel`).

3) Ritual de inicio (resumen práctico)
- Define un propósito conciso de sesión y genera un Action-ID `YYYYMMDD-HHMMSS-<rand4>`.
- Guarda ese propósito en `/workspace/custom-codex-<motor>/purpose_current.md` usando el Action-ID en el encabezado.
- Trabaja solo dentro de tu ámbito. No escribas en `/workspace/1-repo-global-solo-lectura`.

4) Commits con trazabilidad
- Incluye el Action-ID en los mensajes de commit.
- Registra cada commit en `/workspace/custom-codex-<motor>/history_commits.txt` con la línea:
  `[Action-ID] <fecha ISO8601> <branch> <scope/motor> <resumen>`
- Documenta fundamentos/decisiones en `/workspace/custom-codex-<motor>/fundaments-git.txt` con la plantilla del archivo de reglas.

5) Dudas o cambios fuera de alcance
- Detente y consulta a Dominus. No modifiques otros motores ni infra global sin autorización.

Referencias útiles
- Reglas (obligatorio): `/workspace/codex-rules/rules`
- Repo global RO: `/workspace/1-repo-global-solo-lectura`
- Maestro (opcional): `/workspace/1-repo-global-solo-lectura/CODEX-MAESTRO/README.md`

