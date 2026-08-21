import csv
import json
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "latest"


class ReferenceExportTests(unittest.TestCase):

    def test_reference_files_exist(self):
        expected_files = {
            "campaign-summary.json",
            "campaign-kpis.json",
            "ecu-results.csv",
            "wave-timing.csv",
            "events.csv",
        }

        actual_files = {
            path.name
            for path in DATA_DIR.iterdir()
            if path.is_file()
        }

        self.assertEqual(
            actual_files,
            expected_files,
        )

    def test_reference_counters_are_consistent(
        self,
    ):
        with (
            DATA_DIR / "campaign-summary.json"
        ).open(
            encoding="utf-8"
        ) as file:
            summary = json.load(file)

        with (
            DATA_DIR / "campaign-kpis.json"
        ).open(
            encoding="utf-8"
        ) as file:
            kpis = json.load(file)

        self.assertEqual(
            summary["campaign_id"],
            "CMP-FINAL-MIXED-001",
        )
        self.assertEqual(
            summary["total_ecus"],
            28,
        )
        self.assertEqual(
            kpis["terminal_ecus"],
            28,
        )
        self.assertEqual(
            kpis["confirmed_ecus"],
            20,
        )
        self.assertEqual(
            kpis["failed_ecus"],
            8,
        )
        self.assertEqual(
            kpis["elapsed_s"],
            99.0,
        )
        self.assertEqual(
            kpis["budget_utilization_pct"],
            110.0,
        )

    def test_reference_csv_files_are_consistent(
        self,
    ):
        with (
            DATA_DIR / "ecu-results.csv"
        ).open(
            encoding="utf-8",
            newline="",
        ) as file:
            ecus = list(csv.DictReader(file))

        with (
            DATA_DIR / "wave-timing.csv"
        ).open(
            encoding="utf-8",
            newline="",
        ) as file:
            waves = list(csv.DictReader(file))

        with (
            DATA_DIR / "events.csv"
        ).open(
            encoding="utf-8",
            newline="",
        ) as file:
            events = list(csv.DictReader(file))

        self.assertEqual(len(ecus), 28)
        self.assertEqual(len(waves), 5)
        self.assertEqual(len(events), 65)

        statuses = Counter(
            ecu["ota_status"]
            for ecu in ecus
        )

        self.assertEqual(
            statuses,
            Counter(
                {
                    "CONFIRMED": 20,
                    "BLOCKED": 4,
                    "REJECTED": 1,
                    "ROLLED_BACK": 1,
                    "ROLLBACK_LOCKOUT": 1,
                    "RECOVERY_BOOT": 1,
                }
            ),
        )

        self.assertEqual(
            [
                float(wave["elapsed_s"])
                for wave in waves
            ],
            [
                15.0,
                15.0,
                36.0,
                15.0,
                18.0,
            ],
        )


if __name__ == "__main__":
    unittest.main()
