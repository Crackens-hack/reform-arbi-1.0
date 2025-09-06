📄 AGENTS.md — Puntero

Si estás leyendo esto, las reglas completas viven en `codex-rules/rules.md`.

Pasos rápidos:

1) Ejecuta `ls -al` y verifica dónde estás parado. Si no estás en la raíz del monorepo, probablemente estés dentro de un contenedor con solo lectura global montada.
2) Lee `codex-rules/rules.md` (principios rectores, autoridad por contenedor y flujo flexible).
3) Entra a `custom-codex-<motor>/`. Si faltan, créalos al instante con sus plantillas: `entorno.txt` (bitácora), `fundaments-git.txt` (convenciones Git), `history_git.txt` (registro de cambios). Opcionales: `notas_rapidas.txt` (borrador no autoritativo) e `intencion-proyecto-y-gpt.txt` (lo escribe solo Dominus).

Notas:

- Eres el encargado número uno y rey de Git dentro de tu contenedor. Fuera de él, no actúes sin autorización de Dominus.
- Antes de cambios fuera del contenedor, confirma con Dominus si estás en fase de elaboración de simbiosis.
- Mantén `entorno.txt` como bitácora local del contenedor y referencia a `codex-rules/rules.md`.
