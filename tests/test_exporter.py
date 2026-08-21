import csv
import json
import tempfile
import unittest
from pathlib import Path

from simulator.exporter import (
    build_campaign_kpis,
    export_campaign_data,
)
from simulator.orchestrator import (
    CampaignOrchestrator,
)


class CampaignExporterTests(unittest.TestCase):

    def setUp(self):
        self.orchestrator = (
            CampaignOrchestrator()
        )

        manifest = (
            self.orchestrator.build_manifest(
                campaign_id=(
                    "CMP-EXPORT-MIXED"
                ),
                release_id=(
                    "release-export-mixed"
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

        self.summary = (
            self.orchestrator.run_campaign(
                manifest
            )
        )

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )
        self.addCleanup(
            self.temporary_directory.cleanup
        )

        self.output_dir = Path(
            self.temporary_directory.name
        )

        self.paths = export_campaign_data(
            self.summary,
            self.output_dir,
        )

    def test_export_creates_expected_files(self):
        self.assertEqual(
            set(self.paths),
            {
                "summary",
                "kpis",
                "ecus",
                "waves",
                "events",
            },
        )

        for path in self.paths.values():
            self.assertTrue(path.is_file())

        with self.paths["summary"].open(
            encoding="utf-8"
        ) as file:
            exported_summary = json.load(file)

        self.assertEqual(
            exported_summary["campaign_id"],
            "CMP-EXPORT-MIXED",
        )

    def test_ecu_csv_contains_28_sorted_rows(
        self,
    ):
        with self.paths["ecus"].open(
            encoding="utf-8",
            newline="",
        ) as file:
            rows = list(
                csv.DictReader(file)
            )

        self.assertEqual(len(rows), 28)

        ecu_ids = [
            row["ecu_id"]
            for row in rows
        ]

        self.assertEqual(
            ecu_ids,
            sorted(ecu_ids),
        )
        self.assertEqual(
            rows[0]["campaign_id"],
            "CMP-EXPORT-MIXED",
        )

    def test_wave_and_event_csv_content(self):
        with self.paths["waves"].open(
            encoding="utf-8",
            newline="",
        ) as file:
            waves = list(
                csv.DictReader(file)
            )

        self.assertEqual(len(waves), 5)
        self.assertEqual(
            [
                float(row["elapsed_s"])
                for row in waves
            ],
            [
                15.0,
                15.0,
                36.0,
                15.0,
                18.0,
            ],
        )

        with self.paths["events"].open(
            encoding="utf-8",
            newline="",
        ) as file:
            events = list(
                csv.DictReader(file)
            )

        self.assertEqual(
            len(events),
            len(self.summary["events"]),
        )

    def test_mixed_campaign_kpis(self):
        kpis = build_campaign_kpis(
            self.summary
        )

        self.assertEqual(
            kpis["confirmation_rate_pct"],
            71.43,
        )
        self.assertEqual(
            kpis["failure_rate_pct"],
            28.57,
        )
        self.assertEqual(
            kpis["blocked_rate_pct"],
            14.29,
        )
        self.assertEqual(
            kpis["budget_utilization_pct"],
            110.0,
        )
        self.assertEqual(
            kpis["budget_status"],
            "EXCEEDED",
        )

    def test_nominal_campaign_kpis(self):
        orchestrator = CampaignOrchestrator()

        manifest = orchestrator.build_manifest(
            campaign_id=(
                "CMP-EXPORT-NOMINAL"
            ),
            release_id=(
                "release-export-nominal"
            ),
        )

        summary = orchestrator.run_campaign(
            manifest
        )

        kpis = build_campaign_kpis(summary)

        self.assertEqual(
            kpis["confirmation_rate_pct"],
            100.0,
        )
        self.assertEqual(
            kpis["failure_rate_pct"],
            0.0,
        )
        self.assertEqual(
            kpis["budget_utilization_pct"],
            83.33,
        )
        self.assertEqual(
            kpis["budget_status"],
            "WITHIN_BUDGET",
        )


if __name__ == "__main__":
    unittest.main()
