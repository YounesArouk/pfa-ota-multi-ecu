import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_json(filename):
    path = CONFIG_DIR / filename
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class DataContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ecu = load_json("ecu-state.example.json")
        cls.campaign = load_json("campaign-state.example.json")
        cls.event = load_json("event.example.json")

    def test_ecu_contract(self):
        self.assertIn(
            self.ecu["source_type"],
            {"SIMULATED", "REAL_QEMU"},
        )
        self.assertIn(
            self.ecu["active_partition"],
            {"A", "B", "RECOVERY"},
        )
        self.assertGreaterEqual(self.ecu["progress_pct"], 0)
        self.assertLessEqual(self.ecu["progress_pct"], 100)
        self.assertTrue(
            self.ecu["partitions"]["RECOVERY"]["read_only"]
        )

    def test_campaign_contract(self):
        self.assertEqual(self.campaign["total_ecus"], 28)
        self.assertEqual(self.campaign["time_budget_s"], 90)
        self.assertIn(
            self.campaign["source_mode"],
            {"SIMULATION", "REAL_QEMU", "HYBRID"},
        )
        self.assertIn(
            self.campaign["rollback_policy"],
            {"LOCAL", "GLOBAL"},
        )

    def test_campaign_counters(self):
        counted_ecus = (
            self.campaign["queued_ecus"]
            + self.campaign["active_ecus"]
            + self.campaign["confirmed_ecus"]
            + self.campaign["rolled_back_ecus"]
            + self.campaign["rejected_ecus"]
            + self.campaign["offline_ecus"]
        )
        self.assertEqual(
            counted_ecus,
            self.campaign["total_ecus"],
        )

    def test_event_contract(self):
        self.assertEqual(
            self.event["campaign_id"],
            self.campaign["campaign_id"],
        )
        self.assertEqual(
            self.event["ecu_id"],
            self.ecu["ecu_id"],
        )
        self.assertIn(
            self.event["level"],
            {"DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"},
        )
        self.assertGreaterEqual(self.event["progress_pct"], 0)
        self.assertLessEqual(self.event["progress_pct"], 100)


if __name__ == "__main__":
    unittest.main()
