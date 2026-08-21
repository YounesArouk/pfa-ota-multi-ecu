import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT
    / "config"
    / "timing-model.json"
)


class TimingModelConfigurationTests(
    unittest.TestCase
):

    def setUp(self):
        with MODEL_PATH.open(
            encoding="utf-8"
        ) as file:
            self.model = json.load(file)

        self.durations = self.model[
            "state_durations_s"
        ]

    def test_model_metadata(self):
        self.assertEqual(
            self.model["schema_version"],
            "1.0",
        )
        self.assertEqual(
            self.model["model_id"],
            "PFE_OTA_TIMING_V1",
        )
        self.assertEqual(
            self.model["source_type"],
            "SIMULATED",
        )
        self.assertEqual(
            self.model["execution_policy"],
            "PARALLEL_WITHIN_WAVE",
        )

    def test_all_ecu_states_are_covered(self):
        expected_states = {
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "CONFIRMED",
            "REJECTED",
            "BLOCKED",
            "ROLLBACK",
            "ROLLED_BACK",
            "ROLLBACK_LOCKOUT",
            "RECOVERY_BOOT",
            "RECOVERY_LOCKOUT",
        }

        self.assertEqual(
            set(self.durations),
            expected_states,
        )

    def test_durations_are_non_negative(self):
        for state, duration in (
            self.durations.items()
        ):
            with self.subTest(state=state):
                self.assertIsInstance(
                    duration,
                    int,
                )
                self.assertGreaterEqual(
                    duration,
                    0,
                )

    def test_nominal_campaign_respects_budget(
        self,
    ):
        nominal_sequence = [
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "CONFIRMED",
        ]

        nominal_ecu_duration = sum(
            self.durations[state]
            for state in nominal_sequence
        )

        nominal_campaign_duration = (
            nominal_ecu_duration * 5
        )

        self.assertEqual(
            nominal_ecu_duration,
            15,
        )
        self.assertEqual(
            nominal_campaign_duration,
            75,
        )
        self.assertLessEqual(
            nominal_campaign_duration,
            self.model[
                "nominal_time_budget_s"
            ],
        )

    def test_rollback_duration_matches_ecu(
        self,
    ):
        self.assertEqual(
            self.durations["ROLLBACK"],
            3,
        )


if __name__ == "__main__":
    unittest.main()
