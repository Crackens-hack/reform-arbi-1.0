#!/usr/bin/env bash
set -euo pipefail

# === Entrypoint específico para motor_reactor_real_time ===
BOOTSTRAP_PATH="/workspace/motor_reactor_realtime/dev/bootstrap.sh"

if [ -f "$BOOTSTRAP_PATH" ]; then
  chmod +x "$BOOTSTRAP_PATH" || true
  # Permite auto-instalación opcional si se define DEV_AUTO_INSTALL=1
  DEV_AUTO_INSTALL=${DEV_AUTO_INSTALL:-0} "$BOOTSTRAP_PATH"
else
  echo "[warn] $BOOTSTRAP_PATH no encontrado; saltando configuración dev." >&2
fi

# Ejecuta el comando final del contenedor
exec "$@"

# Señales (SIGTERM) llegan al proceso final; ideal para shells/daemons
