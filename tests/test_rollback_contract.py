import json
import unittest
from pathlib import Path

from simulator.ecu import VirtualECU


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RollbackContractTests(unittest.TestCase):

    def test_example_contains_rollback_fields(self):
        path = (
            PROJECT_ROOT
            / "config"
            / "ecu-state.example.json"
        )

        with path.open(encoding="utf-8") as file:
            state = json.load(file)

        self.assertIn("rollback_trigger", state)
        self.assertIn("last_rollback_duration_s", state)
        self.assertIsNone(state["rollback_trigger"])
        self.assertIsNone(state["last_rollback_duration_s"])

    def test_virtual_ecu_exports_rollback_fields(self):
        ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

        state = ecu.to_dict()

        self.assertIn("rollback_trigger", state)
        self.assertIn("last_rollback_duration_s", state)

        ecu.run_update(
            target_version="3.0.0",
            release_id="contract-rb04",
            self_test_valid=False,
        )

        state = ecu.to_dict()

        self.assertEqual(
            state["rollback_trigger"],
            "RB-04",
        )
        self.assertLess(
            state["last_rollback_duration_s"],
            5.0,
        )


if __name__ == "__main__":
    unittest.main()
