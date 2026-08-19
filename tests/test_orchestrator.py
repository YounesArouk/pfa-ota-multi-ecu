import unittest

from simulator.orchestrator import CampaignOrchestrator


class CampaignOrchestratorTests(unittest.TestCase):

    def setUp(self):
        self.orchestrator = CampaignOrchestrator()

    def test_orchestrator_loads_28_ecus(self):
        self.assertEqual(
            len(self.orchestrator.ecus),
            28,
        )
        self.assertEqual(
            self.orchestrator.inventory["ECU-01"]["role"],
            "OTA_MASTER",
        )

    def test_full_campaign_updates_all_ecus(self):
        manifest = self.orchestrator.build_manifest()
        summary = self.orchestrator.run_campaign(
            manifest
        )

        self.assertEqual(
            summary["status"],
            "COMPLETED",
        )
        self.assertEqual(
            summary["confirmed_ecus"],
            28,
        )
        self.assertEqual(
            summary["total_ecus"],
            28,
        )
        self.assertEqual(
            len(summary["executed_waves"]),
            5,
        )

        for ecu in self.orchestrator.ecus.values():
            self.assertEqual(
                ecu.ota_status,
                "CONFIRMED",
            )
            self.assertEqual(
                ecu.active_partition,
                "B",
            )

    def test_each_ecu_receives_specific_target_version(self):
        manifest = self.orchestrator.build_manifest()

        self.orchestrator.run_campaign(
            manifest
        )

        installed_versions = set()

        for ecu_id, ecu in self.orchestrator.ecus.items():
            expected_version = (
                self.orchestrator
                .inventory[ecu_id]["target_version"]
            )

            self.assertEqual(
                ecu.current_version,
                expected_version,
            )

            installed_versions.add(
                ecu.current_version
            )

        self.assertGreater(
            len(installed_versions),
            10,
        )

    def test_invalid_signature_rejects_before_touching_ecus(self):
        manifest = self.orchestrator.build_manifest(
            signature_valid=False
        )

        with self.assertRaisesRegex(
            ValueError,
            "Signature",
        ):
            self.orchestrator.run_campaign(
                manifest
            )

        self.assertEqual(
            self.orchestrator.status,
            "REJECTED",
        )
        self.assertEqual(
            self.orchestrator.manifest_signature_status,
            "INVALID",
        )

        for ecu_id, ecu in self.orchestrator.ecus.items():
            self.assertEqual(
                ecu.ota_status,
                "IDLE",
            )
            self.assertEqual(
                ecu.active_partition,
                "A",
            )
            self.assertEqual(
                ecu.current_version,
                self.orchestrator
                .inventory[ecu_id]["current_version"],
            )

        self.assertEqual(
            self.orchestrator.events[0]["event_code"],
            "RB-09",
        )

    def test_partial_manifest_updates_only_selected_ecus(self):
        selected_ecus = {
            "ECU-01",
            "ECU-20",
            "ECU-21",
            "ECU-23",
        }

        manifest = self.orchestrator.build_manifest(
            target_ecu_ids=selected_ecus,
            campaign_id="CMP-PARTIAL-001",
            release_id="partial-release-001",
        )

        summary = self.orchestrator.run_campaign(
            manifest
        )

        self.assertEqual(
            summary["total_ecus"],
            4,
        )
        self.assertEqual(
            summary["confirmed_ecus"],
            4,
        )
        self.assertEqual(
            len(summary["executed_waves"]),
            4,
        )

        for ecu_id, ecu in self.orchestrator.ecus.items():
            if ecu_id in selected_ecus:
                self.assertEqual(
                    ecu.ota_status,
                    "CONFIRMED",
                )
                self.assertEqual(
                    ecu.active_partition,
                    "B",
                )
            else:
                self.assertEqual(
                    ecu.ota_status,
                    "IDLE",
                )
                self.assertEqual(
                    ecu.active_partition,
                    "A",
                )

    def test_unknown_ecu_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "ECU inconnus",
        ):
            self.orchestrator.build_manifest(
                target_ecu_ids=[
                    "ECU-01",
                    "ECU-99",
                ]
            )

    def test_duplicate_target_is_rejected(self):
        manifest = self.orchestrator.build_manifest(
            target_ecu_ids=[
                "ECU-01",
                "ECU-01",
            ],
            campaign_id="CMP-DUPLICATE",
            release_id="duplicate-release",
        )

        with self.assertRaisesRegex(
            ValueError,
            "dupliqué",
        ):
            self.orchestrator.run_campaign(
                manifest
            )

        for ecu in self.orchestrator.ecus.values():
            self.assertEqual(
                ecu.ota_status,
                "IDLE",
            )

    def test_signature_event_precedes_first_ecu_update(self):
        manifest = self.orchestrator.build_manifest()
        summary = self.orchestrator.run_campaign(
            manifest
        )

        event_codes = [
            event["event_code"]
            for event in summary["events"]
        ]

        signature_position = event_codes.index(
            "MANIFEST_SIGNATURE_VALID"
        )
        update_position = event_codes.index(
            "ECU_UPDATE_STARTED"
        )

        self.assertLess(
            signature_position,
            update_position,
        )

    def test_gateway_state_is_persisted_before_self_update(self):
        manifest = self.orchestrator.build_manifest()
        summary = self.orchestrator.run_campaign(
            manifest
        )

        persistence_position = None
        gateway_update_position = None

        for position, event in enumerate(
            summary["events"]
        ):
            if (
                event["event_code"]
                == "CAMPAIGN_STATE_PERSISTED"
                and event["ecu_id"] == "ECU-01"
            ):
                persistence_position = position

            if (
                event["event_code"]
                == "ECU_UPDATE_STARTED"
                and event["ecu_id"] == "ECU-01"
            ):
                gateway_update_position = position

        self.assertIsNotNone(
            persistence_position
        )
        self.assertIsNotNone(
            gateway_update_position
        )
        self.assertLess(
            persistence_position,
            gateway_update_position,
        )

    def test_dependencies_are_respected_in_executed_waves(self):
        manifest = self.orchestrator.build_manifest()
        summary = self.orchestrator.run_campaign(
            manifest
        )

        wave_by_ecu = {
            ecu_id: wave_number
            for wave_number, wave in enumerate(
                summary["executed_waves"],
                start=1,
            )
            for ecu_id in wave
        }

        for dependency in (
            self.orchestrator.dependencies
        ):
            self.assertLess(
                wave_by_ecu[
                    dependency["depends_on"]
                ],
                wave_by_ecu[
                    dependency["ecu_id"]
                ],
            )

    def test_events_use_common_campaign_and_source(self):
        manifest = self.orchestrator.build_manifest()
        summary = self.orchestrator.run_campaign(
            manifest
        )

        for event in summary["events"]:
            self.assertEqual(
                event["campaign_id"],
                manifest["campaign_id"],
            )
            self.assertEqual(
                event["source_type"],
                "SIMULATED",
            )


if __name__ == "__main__":
    unittest.main()
