import unittest

from simulator.orchestrator import CampaignOrchestrator


class FaultCampaignTests(unittest.TestCase):

    def setUp(self):
        self.orchestrator = CampaignOrchestrator()

    def _dependency_link(self):
        return next(
            item
            for item in self.orchestrator.dependencies
            if item["depends_on"] != "ECU-01"
        )

    def _leaf_ecu(self):
        providers = {
            item["depends_on"]
            for item in self.orchestrator.dependencies
        }

        return sorted(
            set(self.orchestrator.inventory)
            - providers
        )[0]

    def test_manifest_encodes_fault_injections(self):
        manifest = self.orchestrator.build_manifest(
            fault_injections={
                "ECU-05": "RB-01",
                "ECU-02": "RB-04",
            }
        )

        targets = {
            target["ecu_id"]: target
            for target in manifest["targets"]
        }

        self.assertFalse(
            targets["ECU-05"]["checksum_valid"]
        )
        self.assertTrue(
            targets["ECU-05"]["self_test_valid"]
        )
        self.assertEqual(
            targets["ECU-05"]["fault_scenario"],
            "RB-01",
        )

        self.assertTrue(
            targets["ECU-02"]["checksum_valid"]
        )
        self.assertFalse(
            targets["ECU-02"]["self_test_valid"]
        )
        self.assertEqual(
            targets["ECU-02"]["fault_scenario"],
            "RB-04",
        )

    def test_unknown_fault_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "Scénario de défaut inconnu",
        ):
            self.orchestrator.build_manifest(
                fault_injections={
                    "ECU-05": "RB-99",
                }
            )

    def test_fault_on_unselected_ecu_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "ECU non ciblé",
        ):
            self.orchestrator.build_manifest(
                target_ecu_ids=["ECU-01"],
                fault_injections={
                    "ECU-02": "RB-04",
                },
            )

    def test_rb01_blocks_dependent_ecus(self):
        link = self._dependency_link()
        failed = link["depends_on"]
        dependent = link["ecu_id"]

        manifest = self.orchestrator.build_manifest(
            campaign_id="TEST-RB01",
            release_id="test-rb01-release",
            fault_injections={
                failed: "RB-01",
            },
        )

        summary = self.orchestrator.run_campaign(
            manifest
        )

        self.assertEqual(
            self.orchestrator.ecus[
                failed
            ].ota_status,
            "REJECTED",
        )
        self.assertEqual(
            self.orchestrator.ecus[
                dependent
            ].ota_status,
            "BLOCKED",
        )
        self.assertEqual(
            summary["rejected_ecus"],
            1,
        )
        self.assertGreaterEqual(
            summary["blocked_ecus"],
            1,
        )
        self.assertEqual(
            summary["status"],
            "COMPLETED_WITH_FAILURES",
        )

        processed = (
            summary["confirmed_ecus"]
            + summary["rejected_ecus"]
            + summary["rolled_back_ecus"]
            + summary["blocked_ecus"]
        )

        self.assertEqual(
            processed,
            summary["total_ecus"],
        )

    def test_rb04_rolls_back_and_continues(self):
        leaf = self._leaf_ecu()

        manifest = self.orchestrator.build_manifest(
            campaign_id="TEST-RB04",
            release_id="test-rb04-release",
            fault_injections={
                leaf: "RB-04",
            },
        )

        summary = self.orchestrator.run_campaign(
            manifest
        )
        ecu = self.orchestrator.ecus[leaf]

        self.assertEqual(
            ecu.ota_status,
            "ROLLED_BACK",
        )
        self.assertEqual(
            ecu.active_partition,
            "A",
        )
        self.assertEqual(
            ecu.current_version,
            self.orchestrator.inventory[
                leaf
            ]["current_version"],
        )
        self.assertLess(
            ecu.last_rollback_duration_s,
            5.0,
        )
        self.assertEqual(
            summary["confirmed_ecus"],
            27,
        )
        self.assertEqual(
            summary["rolled_back_ecus"],
            1,
        )
        self.assertEqual(
            summary["rejected_ecus"],
            0,
        )
        self.assertEqual(
            summary["blocked_ecus"],
            0,
        )

    def test_fault_events_expose_trigger(self):
        leaf = self._leaf_ecu()

        manifest = self.orchestrator.build_manifest(
            campaign_id="TEST-RB04-EVENTS",
            release_id="test-rb04-events",
            fault_injections={
                leaf: "RB-04",
            },
        )

        summary = self.orchestrator.run_campaign(
            manifest
        )

        fault_event = next(
            event
            for event in summary["events"]
            if (
                event["event_code"]
                == "FAULT_INJECTED"
                and event["ecu_id"] == leaf
            )
        )

        rollback_event = next(
            event
            for event in summary["events"]
            if (
                event["event_code"] == "RB-04"
                and event["ecu_id"] == leaf
            )
        )

        self.assertEqual(
            fault_event["rollback_trigger"],
            "RB-04",
        )
        self.assertEqual(
            rollback_event["rollback_trigger"],
            "RB-04",
        )
        self.assertEqual(
            rollback_event["campaign_id"],
            manifest["campaign_id"],
        )


if __name__ == "__main__":
    unittest.main()
