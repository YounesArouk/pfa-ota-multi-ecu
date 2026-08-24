#!/usr/bin/env bash

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

RUNTIME_DIR=${PFE_QEMU_RUNTIME_DIR:-/home/pfaota/pfe-ota-tests/dashboard-connector-live-20260824}
SSH_PORT=${PFE_QEMU_SSH_PORT:-2222}
PID_FILE=${RUNTIME_DIR}/qemu.pid
SERIAL_LOG=${RUNTIME_DIR}/qemu-serial.log

if [ -f "$PID_FILE" ]; then
    qemu_pid=$(cat "$PID_FILE" 2>/dev/null || true)
else
    qemu_pid=""
fi

if [ -n "$qemu_pid" ] && kill -0 "$qemu_pid" 2>/dev/null; then
    echo "Processus QEMU : ACTIF (PID ${qemu_pid})"
else
    echo "Processus QEMU : ARRÊTÉ"
fi

if ss -ltn | grep -q "127.0.0.1:${SSH_PORT}"; then
    echo "Port SSH ${SSH_PORT} : OUVERT"
else
    echo "Port SSH ${SSH_PORT} : FERMÉ"
fi

if [ -f "$SERIAL_LOG" ]; then
    echo "Journal série : $SERIAL_LOG"
else
    echo "Journal série : ABSENT"
fi

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN=$PROJECT_ROOT/.venv/bin/python
else
    PYTHON_BIN=python3
fi

echo
echo "État retourné par le connecteur :"

cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m api.qemu_rauc_connector
