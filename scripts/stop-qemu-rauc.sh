#!/usr/bin/env bash

set -eu

RUNTIME_DIR=${PFE_QEMU_RUNTIME_DIR:-/home/pfaota/pfe-ota-tests/dashboard-connector-live-20260824}
SSH_PORT=${PFE_QEMU_SSH_PORT:-2222}
PID_FILE=${RUNTIME_DIR}/qemu.pid

if [ ! -f "$PID_FILE" ]; then
    echo "QEMU est déjà arrêté : aucun fichier PID."
    exit 0
fi

qemu_pid=$(cat "$PID_FILE" 2>/dev/null || true)

if [ -z "$qemu_pid" ] || ! kill -0 "$qemu_pid" 2>/dev/null; then
    echo "QEMU est déjà arrêté : PID inactif."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Demande d'arrêt propre de QEMU (PID ${qemu_pid})..."

timeout 8 ssh \
    -p "$SSH_PORT" \
    -o BatchMode=yes \
    -o ConnectTimeout=3 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR \
    root@127.0.0.1 \
    poweroff >/dev/null 2>&1 || true

for attempt in $(seq 1 60); do
    if ! kill -0 "$qemu_pid" 2>/dev/null; then
        rm -f "$PID_FILE"
        echo "QEMU arrêté proprement."
        exit 0
    fi

    sleep 1
done

echo "L'arrêt invité n'a pas terminé QEMU. Envoi de SIGTERM..."
kill "$qemu_pid"

for attempt in $(seq 1 20); do
    if ! kill -0 "$qemu_pid" 2>/dev/null; then
        rm -f "$PID_FILE"
        echo "QEMU arrêté par SIGTERM."
        exit 0
    fi

    sleep 1
done

echo "ERREUR : QEMU est toujours actif. Aucune suppression de disque n'a été effectuée." >&2
exit 1
