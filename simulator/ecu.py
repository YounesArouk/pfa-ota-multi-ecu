from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    """Retourne une date UTC compatible avec JSON."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Partition:
    """Représente une partition logicielle d'un ECU."""

    version: str | None
    status: str
    read_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "read_only": self.read_only,
        }


@dataclass
class VirtualECU:
    """Modèle d'un ECU OTA Python simulé avec partitions A/B."""

    ecu_id: str
    name: str
    domain: str
    current_version: str = "2.0.0"
    target_version: str | None = None
    source_type: str = "SIMULATED"
    connected: bool = True
    active_partition: str = "A"
    supports_live_rollback: bool = True
    ota_status: str = "IDLE"
    health_status: str = "GOOD"
    progress_pct: int = 0
    dependencies: list[str] = field(default_factory=list)
    rollback_counter: int = 0
    accepted_releases: list[str] = field(default_factory=list)
    last_error: str | None = None
    rollback_trigger: str | None = None
    last_rollback_duration_s: float | None = None
    updated_at: str | None = None

    partitions: dict[str, Partition] = field(init=False)
    state_history: list[str] = field(init=False)
    previous_partition: str = field(init=False)
    previous_version: str = field(init=False)

    def __post_init__(self) -> None:
        self.partitions = {
            "A": Partition(
                version=self.current_version,
                status="GOOD",
                read_only=False,
            ),
            "B": Partition(
                version=None,
                status="EMPTY",
                read_only=False,
            ),
            "RECOVERY": Partition(
                version="1.0.0",
                status="GOOD",
                read_only=True,
            ),
        }

        self.previous_partition = self.active_partition
        self.previous_version = self.current_version
        self.updated_at = utc_now()
        self.state_history = [self.ota_status]

    def _set_state(self, status: str, progress: int) -> None:
        """Modifie l'état OTA et mémorise la transition."""

        self.ota_status = status
        self.progress_pct = progress
        self.updated_at = utc_now()
        self.state_history.append(status)

    def get_inactive_partition(self) -> str:
        """Retourne le banc inactif qui recevra la mise à jour."""

        if self.active_partition == "A":
            return "B"

        if self.active_partition == "B":
            return "A"

        raise RuntimeError(
            "Une mise à jour ne peut pas commencer depuis RECOVERY"
        )

    def mark_blocked(
        self,
        reason: str,
    ) -> dict[str, Any]:
        """Bloque la mise à jour pour une dépendance invalide."""

        if not reason:
            raise ValueError("Raison du blocage absente")

        self.last_error = reason
        self.rollback_trigger = None
        self.last_rollback_duration_s = None
        self._set_state("BLOCKED", 0)

        return self.to_dict()

    def run_update(
        self,
        target_version: str,
        release_id: str,
        *,
        checksum_valid: bool = True,
        self_test_valid: bool = True,
    ) -> dict[str, Any]:
        """Exécute une mise à jour avec injection facultative de défaut."""

        if not self.connected:
            raise RuntimeError("ECU non joignable")

        if not target_version:
            raise ValueError("Version cible absente")

        if not release_id:
            raise ValueError("Release ID absent")

        if release_id in self.accepted_releases:
            raise ValueError("Release déjà acceptée")

        self.target_version = target_version
        self.previous_partition = self.active_partition
        self.previous_version = self.current_version
        self.last_error = None
        self.rollback_trigger = None
        self.last_rollback_duration_s = None

        self._set_state("DOWNLOADING", 15)
        self._set_state("VERIFYING_SIGNATURE", 30)
        self._set_state("VERIFYING_CHECKSUM", 45)

        # RB-01 : le défaut est détecté avant toute écriture.
        if not checksum_valid:
            self.last_error = "RB-01: checksum mismatch"
            self.rollback_trigger = "RB-01"
            self._set_state("REJECTED", 45)
            return self.to_dict()

        target_partition = self.get_inactive_partition()
        self.partitions[target_partition].status = "WRITING"
        self._set_state("INSTALLING", 65)

        self.partitions[target_partition].version = target_version
        self.partitions[target_partition].status = "GOOD"

        self._set_state("REBOOTING", 80)
        self.active_partition = target_partition

        self._set_state("SELF_TEST", 90)

        # RB-04 : l'échec arrive après installation et redémarrage.
        if not self_test_valid:
            self.health_status = "FAILED"
            self.partitions[target_partition].status = "BAD"
            self.last_error = "RB-04: self-test failure"
            self.rollback_trigger = "RB-04"

            self._set_state("ROLLBACK", 95)

            self.active_partition = self.previous_partition
            self.current_version = self.previous_version
            self.partitions[self.previous_partition].status = "GOOD"

            self.rollback_counter += 1
            self.last_rollback_duration_s = 3.0
            self.health_status = "GOOD"

            self._set_state("ROLLED_BACK", 100)
            return self.to_dict()

        self.health_status = "GOOD"
        self.current_version = target_version
        self.accepted_releases.append(release_id)
        self._set_state("CONFIRMED", 100)

        return self.to_dict()

    def run_nominal_update(
        self,
        target_version: str,
        release_id: str,
    ) -> dict[str, Any]:
        """Conserve l'interface nominale utilisée par l'orchestrateur."""

        return self.run_update(
            target_version=target_version,
            release_id=release_id,
            checksum_valid=True,
            self_test_valid=True,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'état interne dans le contrat JSON commun."""

        return {
            "schema_version": "1.0",
            "ecu_id": self.ecu_id,
            "name": self.name,
            "domain": self.domain,
            "source_type": self.source_type,
            "connected": self.connected,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "active_partition": self.active_partition,
            "partitions": {
                name: partition.to_dict()
                for name, partition in self.partitions.items()
            },
            "supports_live_rollback": self.supports_live_rollback,
            "ota_status": self.ota_status,
            "health_status": self.health_status,
            "progress_pct": self.progress_pct,
            "dependencies": list(self.dependencies),
            "rollback_counter": self.rollback_counter,
            "accepted_releases": list(self.accepted_releases),
            "last_error": self.last_error,
            "rollback_trigger": self.rollback_trigger,
            "last_rollback_duration_s": self.last_rollback_duration_s,
            "updated_at": self.updated_at,
        }
