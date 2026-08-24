from __future__ import annotations

import json
import re
import subprocess
from typing import Any


SSH_HOST = "127.0.0.1"
SSH_PORT = "2222"
SSH_USER = "root"

ECU_ID = "QEMU-ECU-01"
SSH_COMMAND_TIMEOUT_S = 20

QEMU_SNAPSHOT_COMMAND = (
    "printf '__PFE_VERSION__\\n'; "
    "cat /etc/pfe-ota-version; "
    "printf '\\n__PFE_CMDLINE__\\n'; "
    "cat /proc/cmdline; "
    "printf '\\n__PFE_RAUC__\\n'; "
    "rauc status --output-format=json"
)
def run_ssh(command: str) -> str:
    result = subprocess.run(
        [
            "ssh",
            "-p",
            SSH_PORT,
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=3",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "LogLevel=ERROR",
            f"{SSH_USER}@{SSH_HOST}",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=SSH_COMMAND_TIMEOUT_S,
        check=False,
    )

    if result.returncode != 0:
        message = result.stderr.strip()
        raise RuntimeError(
            message or "Communication SSH avec QEMU impossible"
        )

    return result.stdout.strip()


def get_active_slot(cmdline: str) -> str:
    match = re.search(
        r"(?:^|\s)rauc\.slot=([AB])(?:\s|$)",
        cmdline,
    )

    if match is None:
        return "UNKNOWN"

    return match.group(1)


def get_boot_status(
    rauc_status: str,
    active_slot: str,
) -> str:
    pattern = (
        rf"bootname:\s*{re.escape(active_slot)}"
        rf".*?boot status:\s*(\w+)"
    )

    match = re.search(
        pattern,
        rauc_status,
        re.DOTALL | re.IGNORECASE,
    )

    if match is None:
        return "unknown"

    return match.group(1).lower()

def parse_qemu_snapshot(
    snapshot: str,
) -> tuple[str, str, str]:
    version_prefix = "__PFE_VERSION__\n"
    cmdline_marker = "\n__PFE_CMDLINE__\n"
    rauc_marker = "\n__PFE_RAUC__\n"

    if not snapshot.startswith(version_prefix):
        raise RuntimeError(
            "Réponse QEMU invalide : "
            "marqueur de version absent"
        )

    try:
        version_block, remaining = (
            snapshot.split(
                cmdline_marker,
                1,
            )
        )

        cmdline, rauc_json_text = (
            remaining.split(
                rauc_marker,
                1,
            )
        )
    except ValueError as error:
        raise RuntimeError(
            "Réponse QEMU incomplète"
        ) from error

    version = version_block[
        len(version_prefix):
    ].strip()

    cmdline = cmdline.strip()
    rauc_json_text = rauc_json_text.strip()

    if not version:
        raise RuntimeError(
            "Version QEMU absente"
        )

    if not cmdline:
        raise RuntimeError(
            "Ligne de démarrage QEMU absente"
        )

    if not rauc_json_text:
        raise RuntimeError(
            "État RAUC QEMU absent"
        )

    return (
        version,
        cmdline,
        rauc_json_text,
    )


def load_qemu_ecu() -> dict[str, Any]:
    try:
        snapshot = run_ssh(
            QEMU_SNAPSHOT_COMMAND
        )

        (
            version,
            cmdline,
            rauc_json_text,
        ) = parse_qemu_snapshot(
            snapshot
        )
        rauc_data = json.loads(
            rauc_json_text
        )

        active_slot = (
            rauc_data.get("booted")
            or get_active_slot(cmdline)
        )

        boot_status = "unknown"

        for slot_entry in rauc_data.get("slots", []):
            for slot_data in slot_entry.values():
                if slot_data.get("bootname") == active_slot:
                    boot_status = str(
                        slot_data.get(
                            "boot_status",
                            "unknown",
                        )
                    ).lower()
                    break

            if boot_status != "unknown":
                break

        healthy = boot_status == "good"

        return {
            "campaign_id": "CMP-QEMU-LIVE-001",
            "ecu_id": ECU_ID,
            "name": "QEMU_RAUC_ECU",
            "domain": "OTA_DEMONSTRATOR",
            "source_type": "QEMU_REAL",
            "current_version": version,
            "target_version": version,
            "active_partition": active_slot,
            "ota_status": (
                "CONFIRMED"
                if healthy
                else "REJECTED"
            ),
            "health_status": (
                "GOOD"
                if healthy
                else "BAD"
            ),
            "connected": True,
            "progress_pct": 100,
            "elapsed_s": 0.0,
            "rollback_trigger": None,
            "rollback_counter": 0,
            "consecutive_rollback_counter": 0,
            "rollback_lockout": False,
            "recovery_boot_counter": 0,
            "dependencies": [],
        }

    except (
        RuntimeError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ) as error:
        return {
            "campaign_id": "CMP-QEMU-LIVE-001",
            "ecu_id": ECU_ID,
            "name": "QEMU_RAUC_ECU",
            "domain": "OTA_DEMONSTRATOR",
            "source_type": "QEMU_REAL",
            "current_version": None,
            "target_version": None,
            "active_partition": "UNKNOWN",
            "ota_status": "BLOCKED",
            "health_status": "OFFLINE",
            "connected": False,
            "progress_pct": 0,
            "elapsed_s": 0.0,
            "rollback_trigger": None,
            "rollback_counter": 0,
            "consecutive_rollback_counter": 0,
            "rollback_lockout": False,
            "recovery_boot_counter": 0,
            "dependencies": [],
            "connector_error": str(error),
        }


if __name__ == "__main__":
    print(
        json.dumps(
            load_qemu_ecu(),
            indent=2,
        )
    )
