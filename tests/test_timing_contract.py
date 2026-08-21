import json
import unittest
from pathlib import Path

from simulator.orchestrator import (
    CampaignOrchestrator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TimingContractTests(unittest.TestCase):

    def test_campaign_example_contains_timing(
        self,
    ):
        path = (
            PROJECT_ROOT
            / "config"
            / "campaign-state.example.json"
        )

        with path.open(
            encoding="utf-8"
        ) as file:
            campaign = json.load(file)

        self.assertEqual(
            campaign["elapsed_s"],
            0,
        )
        self.assertEqual(
            campaign["time_budget_s"],
            90,
        )
        self.assertEqual(
            campaign["locked_out_ecus"],
            0,
        )
        self.assertEqual(
            campaign["recovery_ecus"],
            0,
        )

        timing = campaign["timing"]

        self.assertEqual(
            timing["timing_model_id"],
            "PFE_OTA_TIMING_V1",
        )
        self.assertEqual(
            timing["execution_policy"],
            "PARALLEL_WITHIN_WAVE",
        )
        self.assertEqual(
            timing["budget_status"],
            "NOT_EVALUATED",
        )
        self.assertEqual(
            timing["wave_durations"],
            [],
        )

    def test_ecu_example_contains_elapsed_time(
        self,
    ):
        path = (
            PROJECT_ROOT
            / "config"
            / "ecu-state.example.json"
        )

        with path.open(
            encoding="utf-8"
        ) as file:
            ecu = json.load(file)

        self.assertEqual(
            ecu["elapsed_s"],
            0,
        )

    def test_orchestrator_exports_timing_contract(
        self,
    ):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            campaign_id=(
                "CMP-TIMING-CONTRACT"
            ),
            release_id=(
                "release-timing-contract"
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
            summary["timing"][
                "timing_model_id"
            ],
            "PFE_OTA_TIMING_V1",
        )
        self.assertEqual(
            summary["timing"][
                "execution_policy"
            ],
            "PARALLEL_WITHIN_WAVE",
        )

        self.assertTrue(
            all(
                "elapsed_s" in ecu
                for ecu in summary["ecus"]
            )
        )


if __name__ == "__main__":
    unittest.main()
