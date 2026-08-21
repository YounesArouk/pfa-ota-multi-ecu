from __future__ import annotations

from typing import Any, Iterable

from simulator.ecu import VirtualECU, utc_now
from simulator.fleet_inventory import (
    build_prerequisites,
    load_dependencies,
    load_inventory,
    validate_inventory,
)


class CampaignOrchestrator:
    """Représente la logique du Central Gateway OTA Master."""

    def __init__(self) -> None:
        self.inventory = load_inventory()
        self.dependencies = load_dependencies()

        self.update_waves = validate_inventory(
            self.inventory,
            self.dependencies,
        )

        prerequisites = build_prerequisites(
            self.inventory,
            self.dependencies,
        )

        self.ecus: dict[str, VirtualECU] = {}

        for ecu_id, data in self.inventory.items():
            self.ecus[ecu_id] = VirtualECU(
                ecu_id=ecu_id,
                name=data["name"],
                domain=data["domain"],
                current_version=data["current_version"],
                active_partition=data["active_partition"],
                dependencies=sorted(
                    prerequisites[ecu_id]
                ),
            )

        self.status = "IDLE"
        self.manifest_signature_status = "NOT_CHECKED"
        self.events: list[dict[str, Any]] = []
        self.executed_waves: list[list[str]] = []
        self._event_counter = 0

    def _log(
        self,
        level: str,
        event_code: str,
        message: str,
        ecu_id: str | None = None,
        ota_status: str | None = None,
        progress_pct: int = 0,
        rollback_trigger: str | None = None,
    ) -> None:
        """Ajoute un événement destiné au futur dashboard."""

        self._event_counter += 1

        self.events.append(
            {
                "schema_version": "1.0",
                "event_id": (
                    f"EVT-{self._event_counter:06d}"
                ),
                "timestamp": utc_now(),
                "campaign_id": None,
                "ecu_id": ecu_id,
                "source_type": "SIMULATED",
                "level": level,
                "event_code": event_code,
                "ota_status": ota_status,
                "progress_pct": progress_pct,
                "message": message,
                "rollback_trigger": rollback_trigger,
            }
        )

    def build_manifest(
        self,
        target_ecu_ids: Iterable[str] | None = None,
        campaign_id: str = "CMP-VEHICLE-V3",
        release_id: str = (
            "pfe-ota-vehicle-v3-release-001"
        ),
        vehicle_release: str = "3.0.0",
        signature_valid: bool = True,
        fault_injections: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Construit un manifeste signé de simulation.

        Si target_ecu_ids est absent, les 28 ECU sont ciblés.
        """

        if target_ecu_ids is None:
            selected_ids = list(self.inventory)
        else:
            selected_ids = list(target_ecu_ids)

        unknown_ecus = sorted(
            set(selected_ids) - set(self.inventory)
        )

        if unknown_ecus:
            raise ValueError(
                "ECU inconnus dans le manifeste : "
                + ", ".join(unknown_ecus)
            )

        if not selected_ids:
            raise ValueError(
                "Le manifeste ne cible aucun ECU"
            )

        fault_injections = dict(
            fault_injections or {}
        )
        supported_faults = {
            "RB-01",
            "RB-04",
            "RB-18",
            "PFE-RECOVERY",
        }

        unknown_fault_ecus = sorted(
            set(fault_injections) - set(self.inventory)
        )

        if unknown_fault_ecus:
            raise ValueError(
                "Injection sur ECU inconnu : "
                + ", ".join(unknown_fault_ecus)
            )

        unselected_fault_ecus = sorted(
            set(fault_injections) - set(selected_ids)
        )

        if unselected_fault_ecus:
            raise ValueError(
                "Injection sur ECU non ciblé : "
                + ", ".join(unselected_fault_ecus)
            )

        unsupported_faults = sorted(
            {
                str(fault)
                for fault in fault_injections.values()
                if fault not in supported_faults
            }
        )

        if unsupported_faults:
            raise ValueError(
                "Scénario de défaut inconnu : "
                + ", ".join(unsupported_faults)
            )

        targets = []

        for ecu_id in sorted(selected_ids):
            ecu_data = self.inventory[ecu_id]
            target_version = ecu_data["target_version"]

            fault_scenario = fault_injections.get(
                ecu_id
            )

            targets.append(
                {
                    "ecu_id": ecu_id,
                    "target_version": target_version,
                    "package": (
                        f"{ecu_id.lower()}-"
                        f"{target_version}.img"
                    ),
                    "checksum_valid": (
                        fault_scenario != "RB-01"
                    ),
                    "self_test_valid": (
                        fault_scenario
                        not in {
                            "RB-04",
                            "RB-18",
                            "PFE-RECOVERY",
                        }
                    ),
                    "dual_bank_failure": (
                        fault_scenario
                        == "PFE-RECOVERY"
                    ),
                    "repeat_failure_count": (
                        2
                        if fault_scenario == "RB-18"
                        else 1
                    ),
                    "fault_scenario": fault_scenario,
                }
            )

        return {
            "schema_version": "1.0",
            "campaign_id": campaign_id,
            "release_id": release_id,
            "vehicle_release": vehicle_release,
            "signature_valid": signature_valid,
            "targets": targets,
        }

    def _validate_manifest(
        self,
        manifest: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """
        Vérifie le manifeste avant de toucher un ECU.

        Cette méthode respecte la règle RB-09.
        """

        required_fields = {
            "campaign_id",
            "release_id",
            "vehicle_release",
            "signature_valid",
            "targets",
        }

        missing_fields = required_fields - set(manifest)

        if missing_fields:
            self.status = "REJECTED"

            raise ValueError(
                "Champs du manifeste manquants : "
                + ", ".join(sorted(missing_fields))
            )

        self.status = "VALIDATING"

        if manifest["signature_valid"] is not True:
            self.manifest_signature_status = "INVALID"
            self.status = "REJECTED"

            self._log(
                level="ERROR",
                event_code="RB-09",
                message=(
                    "Manifest rejected: "
                    "invalid signature"
                ),
            )

            raise ValueError(
                "Signature du manifeste invalide"
            )

        self.manifest_signature_status = "VALID"

        self._log(
            level="SUCCESS",
            event_code="MANIFEST_SIGNATURE_VALID",
            message=(
                "Signature globale vérifiée avant "
                "toute modification d'ECU"
            ),
        )

        targets = manifest["targets"]

        if not isinstance(targets, list) or not targets:
            self.status = "REJECTED"

            raise ValueError(
                "Liste des cibles invalide"
            )

        target_map: dict[str, dict[str, Any]] = {}

        for target in targets:
            ecu_id = target.get("ecu_id")
            target_version = target.get(
                "target_version"
            )

            if ecu_id not in self.ecus:
                self.status = "REJECTED"

                raise ValueError(
                    f"ECU cible inconnu : {ecu_id}"
                )

            if ecu_id in target_map:
                self.status = "REJECTED"

                raise ValueError(
                    f"ECU cible dupliqué : {ecu_id}"
                )

            if not target_version:
                self.status = "REJECTED"

                raise ValueError(
                    f"Version cible absente : {ecu_id}"
                )

            target_map[ecu_id] = target

        return target_map

    def run_campaign(
        self,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        """Exécute une campagne nominale par vagues."""

        self.events = []
        self.executed_waves = []
        self._event_counter = 0

        target_map = self._validate_manifest(
            manifest
        )

        campaign_id = manifest["campaign_id"]

        for event in self.events:
            event["campaign_id"] = campaign_id

        self.status = "RUNNING"

        self._log(
            level="INFO",
            event_code="CAMPAIGN_STARTED",
            message=(
                f"Campagne {campaign_id} démarrée "
                f"pour {len(target_map)} ECU"
            ),
        )
        self.events[-1]["campaign_id"] = campaign_id

        confirmed_ecus = 0
        rejected_ecus = 0
        rolled_back_ecus = 0
        blocked_ecus = 0
        locked_out_ecus = 0
        recovery_ecus = 0
        processed_ecus = 0
        planned_wave_number = 0

        for inventory_wave in self.update_waves:
            selected_wave = [
                ecu_id
                for ecu_id in inventory_wave
                if ecu_id in target_map
            ]

            if not selected_wave:
                continue

            planned_wave_number += 1
            self.executed_waves.append(
                selected_wave
            )

            self._log(
                level="INFO",
                event_code="WAVE_STARTED",
                message=(
                    f"Vague {planned_wave_number} : "
                    + ", ".join(selected_wave)
                ),
            )
            self.events[-1]["campaign_id"] = campaign_id

            for ecu_id in selected_wave:
                ecu = self.ecus[ecu_id]
                target = target_map[ecu_id]

                failed_dependencies = [
                    dependency_id
                    for dependency_id in ecu.dependencies
                    if (
                        dependency_id in target_map
                        and self.ecus[
                            dependency_id
                        ].ota_status != "CONFIRMED"
                    )
                ]

                if failed_dependencies:
                    reason = (
                        "Prérequis non confirmés : "
                        + ", ".join(
                            failed_dependencies
                        )
                    )

                    ecu.mark_blocked(reason)
                    blocked_ecus += 1
                    processed_ecus += 1

                    progress_pct = round(
                        processed_ecus
                        / len(target_map)
                        * 100
                    )

                    self._log(
                        level="WARNING",
                        event_code=(
                            "ECU_BLOCKED_DEPENDENCY"
                        ),
                        ecu_id=ecu_id,
                        ota_status="BLOCKED",
                        progress_pct=progress_pct,
                        message=reason,
                    )
                    self.events[-1][
                        "campaign_id"
                    ] = campaign_id
                    continue

                if ecu_id == "ECU-01":
                    self._log(
                        level="INFO",
                        event_code=(
                            "CAMPAIGN_STATE_PERSISTED"
                        ),
                        ecu_id=ecu_id,
                        message=(
                            "État de campagne sauvegardé "
                            "avant la mise à jour du "
                            "Central Gateway"
                        ),
                    )
                    self.events[-1][
                        "campaign_id"
                    ] = campaign_id

                self._log(
                    level="INFO",
                    event_code="ECU_UPDATE_STARTED",
                    ecu_id=ecu_id,
                    ota_status="DOWNLOADING",
                    message=(
                        f"Mise à jour de {ecu.name} "
                        f"vers "
                        f"{target['target_version']}"
                    ),
                )
                self.events[-1][
                    "campaign_id"
                ] = campaign_id

                fault_scenario = target.get(
                    "fault_scenario"
                )

                if fault_scenario:
                    self._log(
                        level="WARNING",
                        event_code="FAULT_INJECTED",
                        ecu_id=ecu_id,
                        ota_status=(
                            "FAULT_INJECTION"
                        ),
                        message=(
                            f"Injection {fault_scenario} "
                            f"dans {ecu.name}"
                        ),
                        rollback_trigger=(
                            fault_scenario
                        ),
                    )
                    self.events[-1][
                        "campaign_id"
                    ] = campaign_id

                if fault_scenario == "RB-18":
                    repeat_count = target.get(
                        "repeat_failure_count",
                        2,
                    )

                    for attempt in range(
                        1,
                        repeat_count + 1,
                    ):
                        ecu.run_update(
                            target_version=(
                                target[
                                    "target_version"
                                ]
                            ),
                            release_id=(
                                f"{manifest['release_id']}-"
                                f"{ecu_id.lower()}-"
                                f"attempt-{attempt}"
                            ),
                            checksum_valid=True,
                            self_test_valid=False,
                        )
                else:
                    ecu.run_update(
                        target_version=(
                            target["target_version"]
                        ),
                        release_id=(
                            manifest["release_id"]
                        ),
                        checksum_valid=target.get(
                            "checksum_valid",
                            True,
                        ),
                        self_test_valid=target.get(
                            "self_test_valid",
                            True,
                        ),
                        dual_bank_failure=target.get(
                            "dual_bank_failure",
                            False,
                        ),
                    )
                processed_ecus += 1

                progress_pct = round(
                    processed_ecus
                    / len(target_map)
                    * 100
                )

                if ecu.ota_status == "CONFIRMED":
                    confirmed_ecus += 1

                    self._log(
                        level="SUCCESS",
                        event_code="ECU_CONFIRMED",
                        ecu_id=ecu_id,
                        ota_status=ecu.ota_status,
                        progress_pct=progress_pct,
                        message=(
                            f"{ecu.name} confirmé sur "
                            f"le banc "
                            f"{ecu.active_partition}"
                        ),
                    )

                elif ecu.ota_status == "REJECTED":
                    rejected_ecus += 1

                    self._log(
                        level="ERROR",
                        event_code=(
                            ecu.rollback_trigger
                            or "ECU_REJECTED"
                        ),
                        ecu_id=ecu_id,
                        ota_status=ecu.ota_status,
                        progress_pct=progress_pct,
                        message=(
                            ecu.last_error
                            or "Mise à jour rejetée"
                        ),
                        rollback_trigger=(
                            ecu.rollback_trigger
                        ),
                    )

                elif ecu.ota_status == "ROLLED_BACK":

                    rolled_back_ecus += 1

                    self._log(
                        level="WARNING",
                        event_code=(
                            ecu.rollback_trigger
                            or "ECU_ROLLED_BACK"
                        ),
                        ecu_id=ecu_id,
                        ota_status=ecu.ota_status,
                        progress_pct=progress_pct,
                        message=(
                            ecu.last_error
                            or "Rollback exécuté"
                        ),
                        rollback_trigger=(
                            ecu.rollback_trigger
                        ),
                    )

                elif (
                    ecu.ota_status
                    == "ROLLBACK_LOCKOUT"
                ):
                    locked_out_ecus += 1

                    self._log(
                        level="ERROR",
                        event_code=(
                            ecu.rollback_trigger
                            or "RB-18"
                        ),
                        ecu_id=ecu_id,
                        ota_status=ecu.ota_status,
                        progress_pct=progress_pct,
                        message=(
                            ecu.last_error
                            or (
                                "ECU verrouillé après "
                                "des rollbacks répétés"
                            )
                        ),
                        rollback_trigger=(
                            ecu.rollback_trigger
                            or "RB-18"
                        ),
                    )

                elif (
                    ecu.ota_status
                    == "RECOVERY_BOOT"
                ):
                    recovery_ecus += 1

                    self._log(
                        level="ERROR",
                        event_code=(
                            ecu.rollback_trigger
                            or "PFE-RECOVERY"
                        ),
                        ecu_id=ecu_id,
                        ota_status=ecu.ota_status,
                        progress_pct=progress_pct,
                        message=(
                            ecu.last_error
                            or (
                                "Démarrage sur la "
                                "partition Recovery"
                            )
                        ),
                        rollback_trigger=(
                            ecu.rollback_trigger
                            or "PFE-RECOVERY"
                        ),
                    )

                else:
                    raise RuntimeError(
                        "État OTA final inattendu pour "
                        f"{ecu_id}: {ecu.ota_status}"
                    )

                self.events[-1][
                    "campaign_id"
                ] = campaign_id

        failure_count = (
            rejected_ecus
            + rolled_back_ecus
            + blocked_ecus
            + locked_out_ecus
            + recovery_ecus
        )
        if failure_count:
            self.status = "COMPLETED_WITH_FAILURES"
            final_level = "WARNING"
            final_event = (
                "CAMPAIGN_COMPLETED_WITH_FAILURES"
            )
        else:
            self.status = "COMPLETED"
            final_level = "SUCCESS"
            final_event = "CAMPAIGN_COMPLETED"

        self._log(
            level=final_level,
            event_code=final_event,
            progress_pct=100,
            message=(
                f"Campagne terminée : "
                f"{confirmed_ecus} confirmés, "
                f"{rejected_ecus} rejetés, "
                f"{rolled_back_ecus} restaurés, "
                f"{blocked_ecus} bloqués, "
                f"{locked_out_ecus} verrouillés, "
                f"{recovery_ecus} en Recovery"
            ),
        )
        self.events[-1]["campaign_id"] = campaign_id

        return self.build_summary(
            manifest=manifest,
            confirmed_ecus=confirmed_ecus,
            rejected_ecus=rejected_ecus,
            rolled_back_ecus=rolled_back_ecus,
            blocked_ecus=blocked_ecus,
            locked_out_ecus=locked_out_ecus,
            recovery_ecus=recovery_ecus,
        )

    def build_summary(
        self,
        manifest: dict[str, Any],
        confirmed_ecus: int,
        rejected_ecus: int = 0,
        rolled_back_ecus: int = 0,
        blocked_ecus: int = 0,
        locked_out_ecus: int = 0,
        recovery_ecus: int = 0,
    ) -> dict[str, Any]:
        """Construit le résumé destiné à l'API."""

        targeted_ids = {
            target["ecu_id"]
            for target in manifest["targets"]
        }

        targeted_ecus = [
            self.ecus[ecu_id].to_dict()
            for ecu_id in sorted(targeted_ids)
        ]

        return {
            "schema_version": "1.0",
            "campaign_id": manifest["campaign_id"],
            "release_id": manifest["release_id"],
            "target_version": (
                manifest["vehicle_release"]
            ),
            "source_mode": "SIMULATION",
            "rollback_policy": "LOCAL",
            "status": self.status,
            "manifest_signature_status": (
                self.manifest_signature_status
            ),
            "dependency_graph_status": "VALID",
            "fleet_total_ecus": len(self.ecus),
            "total_ecus": len(targeted_ecus),
            "confirmed_ecus": confirmed_ecus,
            "rolled_back_ecus": rolled_back_ecus,
            "rejected_ecus": rejected_ecus,
            "blocked_ecus": blocked_ecus,
            "locked_out_ecus": locked_out_ecus,
            "recovery_ecus": recovery_ecus,
            "offline_ecus": 0,
            "progress_pct": (
                round(
                    (
                        confirmed_ecus
                        + rejected_ecus
                        + rolled_back_ecus
                        + blocked_ecus
                        + locked_out_ecus
                        + recovery_ecus
                    )
                    / len(targeted_ecus)
                    * 100
                )
                if targeted_ecus
                else 0
            ),
            "executed_waves": list(
                self.executed_waves
            ),
            "ecus": targeted_ecus,
            "events": list(self.events),
        }


def main() -> None:
    """Lance la première campagne des 28 ECU."""

    orchestrator = CampaignOrchestrator()
    manifest = orchestrator.build_manifest()
    summary = orchestrator.run_campaign(
        manifest
    )

    gateway = orchestrator.ecus["ECU-01"]
    ep150 = orchestrator.ecus["ECU-02"]

    installed_versions = {
        ecu.current_version
        for ecu in orchestrator.ecus.values()
    }

    print(
        f"Campagne : {summary['campaign_id']}"
    )
    print(f"Statut : {summary['status']}")
    print(
        "Signature : "
        f"{summary['manifest_signature_status']}"
    )
    print(
        "ECU confirmés : "
        f"{summary['confirmed_ecus']}/"
        f"{summary['total_ecus']}"
    )
    print(
        "Vagues exécutées : "
        f"{len(summary['executed_waves'])}"
    )
    print(
        "Central Gateway : "
        f"{gateway.current_version} "
        f"slot {gateway.active_partition}"
    )
    print(
        "Aptiv EP-150 : "
        f"{ep150.current_version} "
        f"slot {ep150.active_partition}"
    )
    print(
        "Versions finales distinctes : "
        f"{len(installed_versions)}"
    )


if __name__ == "__main__":
    main()
