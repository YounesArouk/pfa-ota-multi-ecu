import unittest

from simulator.orchestrator import (
    CampaignOrchestrator,
)


class AdditionalFaultOrchestrationTests(
    unittest.TestCase
):

    def test_rb18_campaign_locks_ecu(self):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            target_ecu_ids=["ECU-05"],
            campaign_id="CMP-TEST-RB18",
            release_id="release-test-rb18",
            fault_injections={
                "ECU-05": "RB-18",
            },
        )

        summary = orchestrator.run_campaign(
            manifest
        )
        ecu = orchestrator.ecus["ECU-05"]

        self.assertEqual(
            summary["status"],
            "COMPLETED_WITH_FAILURES",
        )
        self.assertEqual(
            summary["locked_out_ecus"],
            1,
        )
        self.assertEqual(
            summary["recovery_ecus"],
            0,
        )
        self.assertEqual(
            summary["progress_pct"],
            100,
        )
        self.assertEqual(
            ecu.ota_status,
            "ROLLBACK_LOCKOUT",
        )
        self.assertEqual(
            ecu.rollback_trigger,
            "RB-18",
        )
        self.assertEqual(
            ecu.rollback_counter,
            2,
        )
        self.assertTrue(
            ecu.rollback_lockout
        )

    def test_recovery_campaign_boots_recovery(self):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            target_ecu_ids=["ECU-02"],
            campaign_id="CMP-TEST-RECOVERY",
            release_id="release-test-recovery",
            fault_injections={
                "ECU-02": "PFE-RECOVERY",
            },
        )

        summary = orchestrator.run_campaign(
            manifest
        )
        ecu = orchestrator.ecus["ECU-02"]

        self.assertEqual(
            summary["status"],
            "COMPLETED_WITH_FAILURES",
        )
        self.assertEqual(
            summary["locked_out_ecus"],
            0,
        )
        self.assertEqual(
            summary["recovery_ecus"],
            1,
        )
        self.assertEqual(
            summary["progress_pct"],
            100,
        )
        self.assertEqual(
            ecu.ota_status,
            "RECOVERY_BOOT",
        )
        self.assertEqual(
            ecu.rollback_trigger,
            "PFE-RECOVERY",
        )
        self.assertEqual(
            ecu.active_partition,
            "RECOVERY",
        )
        self.assertEqual(
            ecu.partitions["A"].status,
            "BAD",
        )
        self.assertEqual(
            ecu.partitions["B"].status,
            "BAD",
        )
        self.assertTrue(
            ecu.partitions["RECOVERY"].read_only
        )


if __name__ == "__main__":
    unittest.main()
