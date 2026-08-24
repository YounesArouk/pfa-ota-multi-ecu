#!/usr/bin/env bash

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

RUNTIME_DIR=${PFE_QEMU_RUNTIME_DIR:-/home/pfaota/pfe-ota-tests/dashboard-connector-live-20260824}
DEPLOY_DIR=${PFE_QEMU_DEPLOY_DIR:-/home/pfaota/poky/build-qemux86-64/tmp/deploy/images/qemux86-64}
BASE_IMAGE=${PFE_QEMU_BASE_IMAGE:-${DEPLOY_DIR}/pfe-ota-dashboard-image-qemux86-64.rootfs.wic}
OVMF_CODE=${PFE_QEMU_OVMF_CODE:-/usr/share/OVMF/OVMF_CODE_4M.fd}
OVMF_VARS_TEMPLATE=${PFE_QEMU_OVMF_VARS_TEMPLATE:-/usr/share/OVMF/OVMF_VARS_4M.fd}
SSH_PORT=${PFE_QEMU_SSH_PORT:-2222}

OVMF_VARS=${RUNTIME_DIR}/OVMF_VARS_4M.fd
OVERLAY=${RUNTIME_DIR}/qemu-dashboard-overlay.qcow2
SERIAL_LOG=${RUNTIME_DIR}/qemu-serial.log
PID_FILE=${RUNTIME_DIR}/qemu.pid

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERREUR : commande absente : $1" >&2
        exit 1
    fi
}

require_file() {
    if [ ! -f "$1" ]; then
        echo "ERREUR : fichier absent : $1" >&2
        exit 1
    fi
}

require_command qemu-system-x86_64
require_command qemu-img
require_command ssh
require_command ss

require_file "$BASE_IMAGE"
require_file "$OVMF_CODE"
require_file "$OVMF_VARS_TEMPLATE"

mkdir -p "$RUNTIME_DIR"

if [ -f "$PID_FILE" ]; then
    existing_pid=$(cat "$PID_FILE" 2>/dev/null || true)

    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
        echo "QEMU est déjà actif (PID ${existing_pid})."
        "$PROJECT_ROOT/scripts/status-qemu-rauc.sh"
        exit 0
    fi

    rm -f "$PID_FILE"
fi

if ss -ltn | grep -q "127.0.0.1:${SSH_PORT}"; then
    echo "ERREUR : le port ${SSH_PORT} est déjà utilisé." >&2
    exit 1
fi

if [ ! -f "$OVMF_VARS" ]; then
    cp "$OVMF_VARS_TEMPLATE" "$OVMF_VARS"
    echo "Variables OVMF créées : $OVMF_VARS"
fi

if [ ! -f "$OVERLAY" ]; then
    qemu-img create \
        -f qcow2 \
        -F raw \
        -b "$BASE_IMAGE" \
        "$OVERLAY"

    echo "Overlay QCOW2 créé : $OVERLAY"
fi

if [ -f "$SERIAL_LOG" ]; then
    log_backup="${SERIAL_LOG}.$(date +%Y%m%d-%H%M%S).bak"
    mv "$SERIAL_LOG" "$log_backup"
    echo "Ancien journal conservé : $log_backup"
fi

echo "Démarrage de QEMU/RAUC..."

qemu-system-x86_64 \
    -machine q35 \
    -accel tcg,thread=multi \
    -cpu max \
    -m 2048 \
    -smp 2 \
    -drive "if=pflash,format=raw,readonly=on,file=${OVMF_CODE}" \
    -drive "if=pflash,format=raw,file=${OVMF_VARS}" \
    -drive "file=${OVERLAY},format=qcow2,if=ide" \
    -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22" \
    -device e1000,netdev=net0 \
    -display none \
    -serial "file:${SERIAL_LOG}" \
    -monitor none \
    -pidfile "$PID_FILE" \
    -daemonize

echo "QEMU lancé. Attente du port SSH ${SSH_PORT}..."

port_ready=false

for attempt in $(seq 1 120); do
    if ss -ltn | grep -q "127.0.0.1:${SSH_PORT}"; then
        port_ready=true
        break
    fi

    sleep 1
done

if [ "$port_ready" != "true" ]; then
    echo "ERREUR : le port SSH n'est pas disponible après 120 secondes." >&2
    exit 1
fi

echo "Port SSH disponible. Attente de la cible Yocto..."

ssh_ready=false

for attempt in $(seq 1 120); do
    if ssh \
        -p "$SSH_PORT" \
        -o BatchMode=yes \
        -o ConnectTimeout=3 \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o LogLevel=ERROR \
        root@127.0.0.1 \
        true >/dev/null 2>&1; then
        ssh_ready=true
        break
    fi

    sleep 1
done

if [ "$ssh_ready" != "true" ]; then
    echo "ERREUR : Yocto n'est pas accessible par SSH après 120 secondes." >&2
    echo "Consultez : $SERIAL_LOG" >&2
    exit 1
fi

echo "SSH disponible. Attente du health check RAUC..."

health_ready=false

for attempt in $(seq 1 180); do
    if grep -q \
        "Le slot courant est marque good." \
        "$SERIAL_LOG" 2>/dev/null; then
        health_ready=true
        break
    fi

    sleep 1
done

if [ "$health_ready" != "true" ]; then
    echo "ERREUR : le health check RAUC n'est pas validé après 180 secondes." >&2
    echo "Consultez : $SERIAL_LOG" >&2
    exit 1
fi

echo "Health check RAUC validé."
echo "QEMU/RAUC est prêt."
"$PROJECT_ROOT/scripts/status-qemu-rauc.sh"
