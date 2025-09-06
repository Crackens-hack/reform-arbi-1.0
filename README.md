Reform‑Arbi — Motor de Arbitraje Triangular (Binance Lab)

Resumen
- Objetivo: motor de arbitraje triangular intra‑exchange (USDT → A → B → USDT; variantes con USDC) con ICI (Interés Compuesto Inmediato) para reinvertir ganancias y buscar ~1% diario sostenido.
- Estado: fase post‑simbiosis. La simbiosis definió reglas, volúmenes custom‑codex por motor y la coordinación Maestro ↔ Internos.
- Alcance actual: laboratorio en Binance, priorizando modularidad, claridad y trazabilidad.

Arquitectura (visión rápida)
- Monorepo único, organizado por servicios y motores.
- Stack Binance (directorio `arbitraje-binance/`):
  - Contenedores por motor: `motor_data_refinery`, `motor_reactor_realtime`, `motor_sentinel`.
  - Volúmenes de continuidad por motor: `custom-codex-<motor>/` (bitácoras y convenciones).
  - Compose y tooling local para desarrollo.
- Reglas y documentación:
  - Maestro: `CODEX-MAESTRO/rules.md` (dirección global post‑simbiosis).
  - Internos (contenedores): `codex-rules/rules.md` (constitución mínima montada RO).
  - Puntero interno por stack: `arbitraje-binance/AGENTS.md`.

Flujo de trabajo
- Codex Maestro (externo):
  1) Confirmar rol y leer `CODEX-MAESTRO/rules.md`.
  2) Limar y cerrar el objetivo junto a Dominus; registrar en `CODEX-MAESTRO/objetivo.md`.
  3) Derivar la intención a README por carpeta (mapa de “cómo y dónde está todo”).
- Codex internos (por contenedor):
  1) Leer `codex-rules/rules.md` montado en el contenedor.
  2) Trabajar solo dentro de `custom-codex-<motor>/` y `<motor>`.
  3) Mantener `entorno.txt`, `fundaments-git.txt`, `history_git.txt` al día (commits atómicos y frecuentes).

Arranque rápido (desarrollo local)
1) Requisitos: Docker + Docker Compose, archivo `.env` en `arbitraje-binance/` (ya existe un ejemplo base en repo).
2) Levantar servicios (desde `arbitraje-binance/`):
   - `docker-compose up -d`
3) Entrar a un motor (ejemplos):
   - `docker compose exec motor_data_refinery bash`
   - `docker compose exec motor_reactor_realtime bash`
   - `docker compose exec motor_sentinel bash`
4) Dentro del contenedor: seguir `AGENTS.md` (puntero) → `codex-rules/rules.md` y crear/verificar `custom-codex-<motor>/entorno.txt`.

Estructura esencial del repo
- `arbitraje-binance/`: compose, motores, volúmenes custom y soporte de entorno para Binance.
- `arbitraje-binance/motor_*`: código por motor (refinery, realtime, sentinel).
- `arbitraje-binance/custom-codex-*`: continuidad por motor (bitácoras y reglas locales de Git).
- `CODEX-MAESTRO/`: guías del Maestro y coordinación global.
- `codex-rules/`: reglas canónicas montadas en contenedores (solo lectura).

Privacidad y seguridad
- Todo el contenido es privado; no se comparte fuera del entorno controlado.
- Escritura únicamente dentro del ámbito permitido de cada motor/volumen.

Siguientes pasos sugeridos
- Maestro: crear/llenar `CODEX-MAESTRO/objetivo.md` con el objetivo cerrado y criterios de éxito.
- Internos: completar `entorno.txt` y mantener `history_git.txt` y `fundaments-git.txt` con cada cambio.
- Documentación: agregar README específicos en cada carpeta relevante siguiendo el mapa global.
