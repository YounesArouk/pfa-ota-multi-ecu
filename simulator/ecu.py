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
    """Premier modèle d'un ECU OTA Python simulé."""

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
            "Une mise à jour nominale ne peut pas commencer depuis RECOVERY"
        )

    def run_nominal_update(
        self,
        target_version: str,
        release_id: str,
    ) -> dict[str, Any]:
        """Exécute une mise à jour nominale sans panne."""

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

        self._set_state("DOWNLOADING", 15)
        self._set_state("VERIFYING_SIGNATURE", 30)
        self._set_state("VERIFYING_CHECKSUM", 45)

        target_partition = self.get_inactive_partition()
        self.partitions[target_partition].status = "WRITING"
        self._set_state("INSTALLING", 65)

        self.partitions[target_partition].version = target_version
        self.partitions[target_partition].status = "GOOD"

        self._set_state("REBOOTING", 80)
        self.active_partition = target_partition

        self._set_state("SELF_TEST", 90)
        self.health_status = "GOOD"

        self.current_version = target_version
        self.accepted_releases.append(release_id)
        self._set_state("CONFIRMED", 100)

        return self.to_dict()

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
            "updated_at": self.updated_at,
        }
