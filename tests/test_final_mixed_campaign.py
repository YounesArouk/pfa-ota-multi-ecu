import unittest

from simulator.orchestrator import (
    CampaignOrchestrator,
)


class FinalMixedCampaignTests(unittest.TestCase):

    def setUp(self):
        self.orchestrator = (
            CampaignOrchestrator()
        )

        self.manifest = (
            self.orchestrator.build_manifest(
                campaign_id=(
                    "CMP-TEST-FINAL-MIXED"
                ),
                release_id=(
                    "release-test-final-mixed"
                ),
                vehicle_release="3.0.0",
                fault_injections={
                    "ECU-05": "RB-01",
                    "ECU-11": "RB-04",
                    "ECU-17": "RB-18",
                    "ECU-02": "PFE-RECOVERY",
                },
            )
        )

        self.summary = (
            self.orchestrator.run_campaign(
                self.manifest
            )
        )

    def test_final_campaign_counters(self):
        expected = {
            "total_ecus": 28,
            "confirmed_ecus": 20,
            "rejected_ecus": 1,
            "rolled_back_ecus": 1,
            "blocked_ecus": 4,
            "locked_out_ecus": 1,
            "recovery_ecus": 1,
            "progress_pct": 100,
        }

        for field, expected_value in (
            expected.items()
        ):
            self.assertEqual(
                self.summary[field],
                expected_value,
                field,
            )

        self.assertEqual(
            self.summary["status"],
            "COMPLETED_WITH_FAILURES",
        )

        final_total = sum(
            self.summary[field]
            for field in {
                "confirmed_ecus",
                "rejected_ecus",
                "rolled_back_ecus",
                "blocked_ecus",
                "locked_out_ecus",
                "recovery_ecus",
            }
        )

        self.assertEqual(final_total, 28)
        self.assertEqual(
            len(
                self.summary[
                    "executed_waves"
                ]
            ),
            5,
        )

    def test_faults_and_blocked_dependencies(
        self,
    ):
        ecus = self.orchestrator.ecus

        self.assertEqual(
            ecus["ECU-05"].ota_status,
            "REJECTED",
        )
        self.assertEqual(
            ecus["ECU-05"].rollback_trigger,
            "RB-01",
        )

        self.assertEqual(
            ecus["ECU-11"].ota_status,
            "ROLLED_BACK",
        )
        self.assertEqual(
            ecus["ECU-11"].rollback_trigger,
            "RB-04",
        )

        self.assertEqual(
            ecus["ECU-17"].ota_status,
            "ROLLBACK_LOCKOUT",
        )
        self.assertEqual(
            ecus["ECU-17"].rollback_trigger,
            "RB-18",
        )

        self.assertEqual(
            ecus["ECU-02"].ota_status,
            "RECOVERY_BOOT",
        )
        self.assertEqual(
            ecus["ECU-02"].active_partition,
            "RECOVERY",
        )

        blocked_ids = sorted(
            ecu_id
            for ecu_id, ecu in ecus.items()
            if ecu.ota_status == "BLOCKED"
        )

        self.assertEqual(
            blocked_ids,
            [
                "ECU-06",
                "ECU-07",
                "ECU-08",
                "ECU-09",
            ],
        )


if __name__ == "__main__":
    unittest.main()
