import unittest

from simulator.orchestrator import (
    CampaignOrchestrator,
)
from simulator.timing import (
    build_timing_summary,
    calculate_state_history_duration,
    load_timing_model,
)


class TimingModelTests(unittest.TestCase):

    def test_model_loads(self):
        model = load_timing_model()

        self.assertEqual(
            model["model_id"],
            "PFE_OTA_TIMING_V1",
        )

    def test_nominal_state_history_is_15_seconds(
        self,
    ):
        model = load_timing_model()

        history = [
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "CONFIRMED",
        ]

        duration = (
            calculate_state_history_duration(
                history,
                model["state_durations_s"],
            )
        )

        self.assertEqual(duration, 15.0)

    def test_unknown_state_is_rejected(self):
        model = load_timing_model()

        with self.assertRaises(ValueError):
            calculate_state_history_duration(
                ["IDLE", "UNKNOWN_STATE"],
                model["state_durations_s"],
            )

    def test_nominal_campaign_is_within_budget(
        self,
    ):
        orchestrator = CampaignOrchestrator()
        manifest = (
            orchestrator.build_manifest(
                campaign_id=(
                    "CMP-TIMING-NOMINAL"
                ),
                release_id=(
                    "release-timing-nominal"
                ),
            )
        )

        orchestrator.run_campaign(manifest)

        timing = build_timing_summary(
            orchestrator.ecus,
            orchestrator.executed_waves,
        )

        self.assertEqual(
            timing["elapsed_s"],
            75.0,
        )
        self.assertEqual(
            timing["fleet_processing_s"],
            420.0,
        )
        self.assertEqual(
            timing["average_ecu_duration_s"],
            15.0,
        )
        self.assertEqual(
            timing["budget_status"],
            "WITHIN_BUDGET",
        )
        self.assertEqual(
            timing["budget_margin_s"],
            15.0,
        )
        self.assertEqual(
            [
                wave["elapsed_s"]
                for wave in timing[
                    "wave_durations"
                ]
            ],
            [
                15.0,
                15.0,
                15.0,
                15.0,
                15.0,
            ],
        )

    def test_mixed_campaign_timing(self):
        orchestrator = CampaignOrchestrator()

        manifest = (
            orchestrator.build_manifest(
                campaign_id=(
                    "CMP-TIMING-MIXED"
                ),
                release_id=(
                    "release-timing-mixed"
                ),
                fault_injections={
                    "ECU-05": "RB-01",
                    "ECU-11": "RB-04",
                    "ECU-17": "RB-18",
                    "ECU-02": (
                        "PFE-RECOVERY"
                    ),
                },
            )
        )

        orchestrator.run_campaign(manifest)

        timing = build_timing_summary(
            orchestrator.ecus,
            orchestrator.executed_waves,
        )

        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-03"
            ],
            15.0,
        )
        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-05"
            ],
            6.0,
        )
        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-06"
            ],
            0.0,
        )
        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-11"
            ],
            18.0,
        )
        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-17"
            ],
            36.0,
        )
        self.assertEqual(
            timing["ecu_durations_s"][
                "ECU-02"
            ],
            18.0,
        )

        self.assertEqual(
            [
                wave["elapsed_s"]
                for wave in timing[
                    "wave_durations"
                ]
            ],
            [
                15.0,
                15.0,
                36.0,
                15.0,
                18.0,
            ],
        )

        self.assertEqual(
            timing["elapsed_s"],
            99.0,
        )
        self.assertEqual(
            timing["fleet_processing_s"],
            378.0,
        )
        self.assertEqual(
            timing["average_ecu_duration_s"],
            13.5,
        )
        self.assertEqual(
            timing["max_ecu_duration_s"],
            36.0,
        )
        self.assertEqual(
            timing["min_ecu_duration_s"],
            0.0,
        )
        self.assertEqual(
            timing["budget_status"],
            "EXCEEDED",
        )
        self.assertEqual(
            timing["budget_overrun_s"],
            9.0,
        )


if __name__ == "__main__":
    unittest.main()
