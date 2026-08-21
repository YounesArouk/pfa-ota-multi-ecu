import unittest

from simulator.orchestrator import (
    CampaignOrchestrator,
)


class OrchestratorTimingIntegrationTests(
    unittest.TestCase
):

    def test_nominal_summary_contains_timing(
        self,
    ):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            campaign_id=(
                "CMP-ORCHESTRATOR-TIMING-NOMINAL"
            ),
            release_id=(
                "release-orchestrator-timing-nominal"
            ),
        )

        summary = orchestrator.run_campaign(
            manifest
        )

        self.assertEqual(
            summary["elapsed_s"],
            75.0,
        )
        self.assertEqual(
            summary["time_budget_s"],
            90.0,
        )
        self.assertEqual(
            summary["timing"]["budget_status"],
            "WITHIN_BUDGET",
        )
        self.assertEqual(
            summary["timing"][
                "budget_margin_s"
            ],
            15.0,
        )

        for ecu_state in summary["ecus"]:
            self.assertEqual(
                ecu_state["elapsed_s"],
                15.0,
            )

    def test_mixed_summary_exposes_overrun(
        self,
    ):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            campaign_id=(
                "CMP-ORCHESTRATOR-TIMING-MIXED"
            ),
            release_id=(
                "release-orchestrator-timing-mixed"
            ),
            fault_injections={
                "ECU-05": "RB-01",
                "ECU-11": "RB-04",
                "ECU-17": "RB-18",
                "ECU-02": "PFE-RECOVERY",
            },
        )

        summary = orchestrator.run_campaign(
            manifest
        )

        self.assertEqual(
            summary["elapsed_s"],
            99.0,
        )
        self.assertEqual(
            summary["timing"]["budget_status"],
            "EXCEEDED",
        )
        self.assertEqual(
            summary["timing"][
                "budget_overrun_s"
            ],
            9.0,
        )
        self.assertEqual(
            summary["timing"][
                "fleet_processing_s"
            ],
            378.0,
        )

        ecu_states = {
            state["ecu_id"]: state
            for state in summary["ecus"]
        }

        self.assertEqual(
            ecu_states["ECU-17"]["elapsed_s"],
            36.0,
        )
        self.assertEqual(
            ecu_states["ECU-06"]["elapsed_s"],
            0.0,
        )
        self.assertEqual(
            ecu_states["ECU-02"]["elapsed_s"],
            18.0,
        )


if __name__ == "__main__":
    unittest.main()
