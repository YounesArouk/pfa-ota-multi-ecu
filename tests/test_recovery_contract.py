import json
import unittest
from pathlib import Path

from simulator.ecu import VirtualECU


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecoveryContractTests(unittest.TestCase):

    def test_example_contains_recovery_counter(self):
        path = (
            PROJECT_ROOT
            / "config"
            / "ecu-state.example.json"
        )

        with path.open(encoding="utf-8") as file:
            state = json.load(file)

        self.assertEqual(
            state["recovery_boot_counter"],
            0,
        )

    def test_virtual_ecu_exports_recovery_counter(self):
        ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

        initial_state = ecu.to_dict()

        self.assertEqual(
            initial_state["recovery_boot_counter"],
            0,
        )

        recovery_state = ecu.run_update(
            target_version="3.0.0",
            release_id="recovery-contract-test",
            dual_bank_failure=True,
        )

        self.assertEqual(
            recovery_state["recovery_boot_counter"],
            1,
        )
        self.assertEqual(
            recovery_state["active_partition"],
            "RECOVERY",
        )


if __name__ == "__main__":
    unittest.main()
