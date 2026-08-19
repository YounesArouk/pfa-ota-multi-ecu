from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = PROJECT_ROOT / "data" / "ecu_inventory.csv"
DEFAULT_DEPENDENCIES_PATH = PROJECT_ROOT / "data" / "dependencies.csv"

DATASET_ID = "SYNTHETIC_PFE_V1"
EXPECTED_ECU_COUNT = 28


def parse_yes_no(value: str) -> bool:
    """Convertit Yes/No en booléen Python."""

    normalized = value.strip().lower()

    if normalized == "yes":
        return True

    if normalized == "no":
        return False

    raise ValueError(f"Valeur Yes/No invalide : {value}")


def load_inventory(
    path: Path = DEFAULT_INVENTORY_PATH,
) -> dict[str, dict[str, Any]]:
    """Charge les 28 ECU depuis le fichier CSV."""

    required_columns = {
        "dataset_id",
        "ecu_id",
        "name",
        "domain",
        "role",
        "current_version",
        "target_version",
        "partition_scheme",
        "active_partition",
        "image_size_mb",
        "priority",
        "supports_live_rollback",
        "has_recovery_partition",
        "bus_type",
    }

    inventory: dict[str, dict[str, Any]] = {}

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as stream:
        reader = csv.DictReader(stream)

        missing_columns = required_columns - set(
            reader.fieldnames or []
        )

        if missing_columns:
            raise ValueError(
                "Colonnes manquantes dans l'inventaire : "
                + ", ".join(sorted(missing_columns))
            )

        for raw_row in reader:
            row = {
                key: (value or "").strip()
                for key, value in raw_row.items()
            }

            ecu_id = row["ecu_id"]

            if not ecu_id:
                raise ValueError("Identifiant ECU absent")

            if ecu_id in inventory:
                raise ValueError(
                    f"Identifiant ECU dupliqué : {ecu_id}"
                )

            row["image_size_mb"] = int(
                row["image_size_mb"]
            )
            row["priority"] = int(row["priority"])
            row["supports_live_rollback"] = parse_yes_no(
                row["supports_live_rollback"]
            )
            row["has_recovery_partition"] = parse_yes_no(
                row["has_recovery_partition"]
            )

            inventory[ecu_id] = row

    return inventory


def load_dependencies(
    path: Path = DEFAULT_DEPENDENCIES_PATH,
) -> list[dict[str, str]]:
    """Charge les relations de dépendance."""

    required_columns = {
        "dataset_id",
        "ecu_id",
        "depends_on",
        "dependency_type",
        "reason",
    }

    dependencies: list[dict[str, str]] = []

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as stream:
        reader = csv.DictReader(stream)

        missing_columns = required_columns - set(
            reader.fieldnames or []
        )

        if missing_columns:
            raise ValueError(
                "Colonnes manquantes dans les dépendances : "
                + ", ".join(sorted(missing_columns))
            )

        for raw_row in reader:
            row = {
                key: (value or "").strip()
                for key, value in raw_row.items()
            }
            dependencies.append(row)

    return dependencies


def build_prerequisites(
    inventory: dict[str, dict[str, Any]],
    dependencies: list[dict[str, str]],
) -> dict[str, set[str]]:
    """Construit la liste des prérequis de chaque ECU."""

    prerequisites = {
        ecu_id: set()
        for ecu_id in inventory
    }

    for dependency in dependencies:
        ecu_id = dependency["ecu_id"]
        depends_on = dependency["depends_on"]

        if ecu_id not in inventory:
            raise ValueError(
                f"ECU dépendant inconnu : {ecu_id}"
            )

        if depends_on not in inventory:
            raise ValueError(
                f"Prérequis inconnu : {depends_on}"
            )

        if ecu_id == depends_on:
            raise ValueError(
                f"Auto-dépendance interdite : {ecu_id}"
            )

        prerequisites[ecu_id].add(depends_on)

    return prerequisites


def calculate_update_waves(
    inventory: dict[str, dict[str, Any]],
    dependencies: list[dict[str, str]],
) -> list[list[str]]:
    """
    Calcule les vagues selon les dépendances et les priorités.

    Une priorité faible est traitée avant une priorité élevée.
    """

    prerequisites = build_prerequisites(
        inventory,
        dependencies,
    )

    remaining = set(inventory)
    completed: set[str] = set()
    waves: list[list[str]] = []

    while remaining:
        ready = [
            ecu_id
            for ecu_id in remaining
            if prerequisites[ecu_id].issubset(completed)
        ]

        if not ready:
            blocked = ", ".join(sorted(remaining))
            raise ValueError(
                "Dépendance circulaire détectée. "
                f"ECU bloqués : {blocked}"
            )

        current_priority = min(
            inventory[ecu_id]["priority"]
            for ecu_id in ready
        )

        wave = sorted(
            ecu_id
            for ecu_id in ready
            if inventory[ecu_id]["priority"]
            == current_priority
        )

        waves.append(wave)
        completed.update(wave)
        remaining.difference_update(wave)

    return waves


def validate_inventory(
    inventory: dict[str, dict[str, Any]],
    dependencies: list[dict[str, str]],
) -> list[list[str]]:
    """Contrôle complètement l'inventaire synthétique."""

    if len(inventory) != EXPECTED_ECU_COUNT:
        raise ValueError(
            f"Nombre d'ECU incorrect : {len(inventory)}"
        )

    expected_ids = {
        f"ECU-{index:02d}"
        for index in range(1, EXPECTED_ECU_COUNT + 1)
    }

    if set(inventory) != expected_ids:
        missing = expected_ids - set(inventory)
        unexpected = set(inventory) - expected_ids

        raise ValueError(
            "Identifiants ECU incorrects. "
            f"Manquants={sorted(missing)}, "
            f"Inattendus={sorted(unexpected)}"
        )

    for ecu_id, ecu in inventory.items():
        if ecu["dataset_id"] != DATASET_ID:
            raise ValueError(
                f"Dataset incorrect pour {ecu_id}"
            )

        if ecu["partition_scheme"] != "A/B":
            raise ValueError(
                f"Schéma A/B absent pour {ecu_id}"
            )

        if ecu["active_partition"] not in {"A", "B"}:
            raise ValueError(
                f"Partition active invalide pour {ecu_id}"
            )

        if not ecu["supports_live_rollback"]:
            raise ValueError(
                f"Rollback non supporté par {ecu_id}"
            )

        if not ecu["has_recovery_partition"]:
            raise ValueError(
                f"Recovery absente pour {ecu_id}"
            )

        if ecu["image_size_mb"] <= 0:
            raise ValueError(
                f"Taille d'image invalide pour {ecu_id}"
            )

        if not 1 <= ecu["priority"] <= 5:
            raise ValueError(
                f"Priorité invalide pour {ecu_id}"
            )

        if ecu["current_version"] == ecu["target_version"]:
            raise ValueError(
                f"Aucune nouvelle version pour {ecu_id}"
            )

    masters = [
        ecu_id
        for ecu_id, ecu in inventory.items()
        if ecu["role"] == "OTA_MASTER"
    ]

    if masters != ["ECU-01"]:
        raise ValueError(
            "ECU-01 doit être l'unique OTA Master"
        )

    for dependency in dependencies:
        if dependency["dataset_id"] != DATASET_ID:
            raise ValueError(
                "Dataset incorrect dans les dépendances"
            )

        if dependency["dependency_type"] != "HARD":
            raise ValueError(
                "Type de dépendance non supporté"
            )

    return calculate_update_waves(
        inventory,
        dependencies,
    )


def main() -> None:
    """Affiche le premier plan de campagne."""

    inventory = load_inventory()
    dependencies = load_dependencies()
    waves = validate_inventory(
        inventory,
        dependencies,
    )

    print(f"Dataset : {DATASET_ID}")
    print(f"Nombre d'ECU : {len(inventory)}")
    print(
        f"Nombre de dépendances : {len(dependencies)}"
    )
    print("Validation de l'inventaire : OK")
    print()

    for wave_number, wave in enumerate(waves, start=1):
        print(
            f"Vague {wave_number} "
            f"({len(wave)} ECU)"
        )

        for ecu_id in wave:
            ecu = inventory[ecu_id]
            print(
                f"  {ecu_id} | "
                f"{ecu['name']} | "
                f"{ecu['current_version']} -> "
                f"{ecu['target_version']} | "
                f"priorité {ecu['priority']}"
            )


if __name__ == "__main__":
    main()
