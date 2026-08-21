import json
import unittest
from pathlib import Path

from simulator.ecu import VirtualECU


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RB18ContractTests(unittest.TestCase):

    def test_example_contains_rb18_fields(self):
        path = (
            PROJECT_ROOT
            / "config"
            / "ecu-state.example.json"
        )

        with path.open(encoding="utf-8") as file:
            state = json.load(file)

        self.assertEqual(
            state["consecutive_rollback_counter"],
            0,
        )
        self.assertFalse(
            state["rollback_lockout"]
        )

    def test_virtual_ecu_exports_rb18_fields(self):
        ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

        state = ecu.to_dict()

        self.assertEqual(
            state["consecutive_rollback_counter"],
            0,
        )
        self.assertFalse(
            state["rollback_lockout"]
        )


if __name__ == "__main__":
    unittest.main()
