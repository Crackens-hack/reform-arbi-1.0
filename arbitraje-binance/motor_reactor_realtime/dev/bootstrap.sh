#!/usr/bin/env bash
set -euo pipefail

# Bootstrap de entorno de desarrollo (por ahora solo bash/)
# Objetivo: portable e inteligente para Alpine, Debian y Ubuntu.
# No instala nada por defecto; puede instalar si DEV_AUTO_INSTALL=1.

# Directorios base
DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASH_DIR="$DEV_DIR/bash"
REPO_DIR="$(dirname "$DEV_DIR")"

# Detección de SO/container
OS_ID="unknown"
PKG="none"
if [ -r /etc/os-release ]; then
  . /etc/os-release || true
  OS_ID="${ID:-unknown}"
fi
if command -v apk >/dev/null 2>&1; then
  PKG="apk"
elif command -v apt-get >/dev/null 2>&1; then
  PKG="apt-get"
fi

echo "[dev/bootstrap] OS=${OS_ID} PKG=${PKG} DEV_DIR=${DEV_DIR}"

# Requisitos mínimos (runtime): bash real, git (opcional pero recomendado), bash-completion (opcional)
need_cmd() { command -v "$1" >/dev/null 2>&1; }

MISSING=()
need_cmd bash || MISSING+=(bash)
need_cmd git  || MISSING+=(git)

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "[dev/bootstrap] Faltan herramientas: ${MISSING[*]}" >&2
  if [ "${DEV_AUTO_INSTALL:-0}" = "1" ]; then
    echo "[dev/bootstrap] DEV_AUTO_INSTALL=1 → intentar instalar (requiere red y permisos)" >&2
    case "$PKG" in
      apk)
        apk add --no-cache bash git bash-completion ca-certificates || true
        ;;
      apt-get)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y && apt-get install -y --no-install-recommends \
          bash git bash-completion ca-certificates && \
          rm -rf /var/lib/apt/lists/* || true
        ;;
      *)
        echo "[dev/bootstrap] No se reconoce gestor de paquetes. Instalar manualmente: ${MISSING[*]}" >&2
        ;;
    esac
  else
    echo "[dev/bootstrap] Sugerencia Alpine: apk add --no-cache bash git bash-completion ca-certificates" >&2
    echo "[dev/bootstrap] Sugerencia Debian/Ubuntu: apt-get update && apt-get install -y bash git bash-completion ca-certificates" >&2
  fi
fi

# Asegurar que exista el subdirectorio bash/
if [ ! -d "$BASH_DIR" ]; then
  echo "[dev/bootstrap] No existe $BASH_DIR. Nada que configurar." >&2
  exit 0
fi

# Construir rutas de destino para alinear root y $HOME
DESTS=()
DESTS+=("/root")
if [ -n "${HOME:-}" ] && [ "$HOME" != "/root" ]; then
  DESTS+=("$HOME")
fi

write_rc_for() {
  local home_dir="$1"
  mkdir -p "$home_dir"

  # Usar ruta absoluta real al .bashrc_custom del repo para evitar depender de /app
  local RC_CUSTOM="$BASH_DIR/.bashrc_custom"

  # .bash_profile → puente a .bashrc
  cat >"$home_dir/.bash_profile" <<'EOF'
export SHELL=/bin/bash
[[ -r ~/.bashrc ]] && . ~/.bashrc
EOF

  # .bashrc → orquesta desde dev/bash/.bashrc_custom si existe
  cat >"$home_dir/.bashrc" <<EOF
if [[ -r "$RC_CUSTOM" ]]; then
  . "$RC_CUSTOM"
else
  echo "[warn] $RC_CUSTOM no encontrado (¿montaje del repo?)" >&2
fi
EOF
}

for d in "${DESTS[@]}"; do
  write_rc_for "$d"
  echo "[dev/bootstrap] Shell RC actualizado en $d"
done

# Permitir que otros pasos del pipeline sepan dónde vive el stack bash
export DEV_BASH_DIR="$BASH_DIR"

echo "[dev/bootstrap] Listo. Abrí una shell de login: bash -l"

