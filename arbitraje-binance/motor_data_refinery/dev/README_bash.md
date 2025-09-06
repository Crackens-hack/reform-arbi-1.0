# Entorno Bash Portable (Alpine / Debian / Ubuntu)

Este `dev/` organiza un entorno Bash de desarrollo portable dentro del contenedor, por ahora centrado en `dev/bash/`.

Objetivo: mantener un entrypoint estándar y mínimo que sólo delegue la configuración a un script dentro de `dev/` (este repositorio). Así la “inteligencia” queda versionada y reutilizable.

## Qué hace `dev/bootstrap.sh`

- Detecta el entorno (Alpine, Debian, Ubuntu) y valida herramientas mínimas.
- Opcionalmente instala dependencias base si `DEV_AUTO_INSTALL=1`.
- Reemplaza/crea `~/.bash_profile` y `~/.bashrc` tanto en `/root` como en `$HOME` para que ambos perfiles queden alineados.
- Orquesta la configuración desde `dev/bash/.bashrc_custom` usando la ruta absoluta del repo (no depende de `/app`).

> Por diseño, el entrypoint se mantiene simple: hace `chmod +x` del bootstrap y lo ejecuta. Toda la lógica vive en `dev/bootstrap.sh` y en los archivos de `dev/bash/`.

## Requisitos mínimos (runtime)

- Bash real (`/bin/bash` o accesible como `bash`).
- Git (recomendado para prompt y utilidades), `bash-completion` (opcional).
- Distribuciones soportadas: Alpine, Debian y Ubuntu.

Si faltan, el bootstrap te muestra los comandos para instalarlos. Para instalar automáticamente, exportá `DEV_AUTO_INSTALL=1` (requiere red y permisos de root):

- Alpine: `apk add --no-cache bash git bash-completion ca-certificates`
- Debian/Ubuntu: `apt-get update && apt-get install -y bash git bash-completion ca-certificates`

## Uso recomendado en Dockerfile

1) Copiá el entrypoint estándar y dale permisos (ejemplo):

```dockerfile
# ... tu base (alpine|debian|ubuntu)
# 1) Copiá la carpeta dev/ donde el entrypoint la espera (/app/dev)
COPY motor_reactor_realtime/dev/ /app/dev/

# 2) Copiá el entrypoint estándar y dale permisos
COPY motor_reactor_realtime/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /app/dev/bootstrap.sh || true
```

2) El entrypoint debe delegar al bootstrap del repo (montado en `/app` o ruta equivalente). Un patrón típico:

```bash
#!/usr/bin/env bash
set -e

# Asegurar permisos del bootstrap (dentro del repo)
if [ -f /app/dev/bootstrap.sh ]; then
  chmod +x /app/dev/bootstrap.sh || true
  DEV_AUTO_INSTALL=${DEV_AUTO_INSTALL:-0} /app/dev/bootstrap.sh
else
  echo "[warn] /app/dev/bootstrap.sh no encontrado; saltando configuración dev." >&2
fi

exec "$@"
```

> Nota: si tu repo no está en `/app`, ajustá la ruta. El bootstrap usa rutas absolutas para sourcear `dev/bash/.bashrc_custom`, por lo que no depende de `/app` internamente.

## Uso con docker-compose

Ejemplo mínimo que deja la shell viva y monta el repo en `/app`:

```yaml
services:
  dev:
    build: .
    working_dir: /app
    command: bash -l -c "tail -f /dev/null"
    volumes:
      - ./:/app
      # Asegurate de que /app/dev exista (copiado en build y/o montado desde el host)
    environment:
      - CONTAINER=true
      - NAME=dev
      # - DEV_AUTO_INSTALL=1   # si querés que bootstrap instale dependencias
```

Abrí una shell dentro del contenedor con `docker exec -it dev bash -l` y ya tendrías el prompt/aliases/funciones.

## Estructura de `dev/bash/`

- `.bash_env`: entorno general (history, EDITOR, ls color, etc.).
- `.bash_aliases`: aliases (docker, git, go, etc.).
- `.bash_functions`: utilidades (git helpers, etc.).
- `.bash_gitprompt`: flags para `__git_ps1`.
- `.bash_prompt`: prompt de 2 líneas; usa `git-prompt.sh` si existe, o fallback.
- `.bash_completion_extras`: carga completados si están disponibles en el sistema.
- `.bashrc_custom`: orquestador que sourcea todo lo anterior y refresca el prompt.

## Filosofía

- EntryPoint mínimo y reusable; la lógica vive en el repo (`dev/`).
- Operación idempotente: el bootstrap reescribe `~/.bashrc`/`~/.bash_profile` en cada arranque del contenedor.
- Portabilidad enfocada: Alpine, Debian, Ubuntu. Otros sistemas no son objetivo de este `dev/` por ahora.

## Troubleshooting

- No se ve el prompt “pro”: asegurate de tener `git` y (si querés) `bash-completion` instalados.
- Mensaje de warning sobre `.bashrc_custom`: verificá que el volumen del repo esté montado donde el entrypoint espera.
- Tu usuario no es root: el bootstrap también escribe en `$HOME` además de `/root` para alinear perfiles.
- Dockerfile no encuentra `dev/`: en build, copiá `motor_reactor_realtime/dev/` a `/app/dev/` como en el ejemplo.
- Usuarios sin el repo completo: opciones de consumo del `dev/`:
  - git subdir: `git clone https://…/tu-dev.git dev/` dentro de tu proyecto.
  - copiar carpeta: empaquetar y copiar `dev/` al contenedor (como arriba).
  - paquete del sistema: posible a futuro (deb/apk), no cubierto aún.

