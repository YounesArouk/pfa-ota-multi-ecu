import tempfile
import unittest
from pathlib import Path

from api.data_store import (
    CampaignDataError,
    CampaignDataStore,
)


class CampaignDataStoreTests(unittest.TestCase):

    def setUp(self):
        self.store = CampaignDataStore()

    def test_loads_reference_json_objects(self):
        campaign = self.store.load_campaign()
        kpis = self.store.load_kpis()

        self.assertEqual(
            campaign["campaign_id"],
            "CMP-FINAL-MIXED-001",
        )
        self.assertEqual(
            kpis["confirmation_rate_pct"],
            71.43,
        )
        self.assertEqual(
            kpis["budget_status"],
            "EXCEEDED",
        )

    def test_loads_reference_csv_records(self):
        ecus = self.store.load_ecus()
        waves = self.store.load_waves()
        events = self.store.load_events()

        self.assertEqual(len(ecus), 28)
        self.assertEqual(len(waves), 5)
        self.assertEqual(len(events), 65)

    def test_csv_values_are_typed(self):
        ecus = self.store.load_ecus()
        waves = self.store.load_waves()

        ecu_02 = next(
            ecu
            for ecu in ecus
            if ecu["ecu_id"] == "ECU-02"
        )

        self.assertIsInstance(
            ecu_02["progress_pct"],
            int,
        )
        self.assertIsInstance(
            ecu_02["elapsed_s"],
            float,
        )
        self.assertIsInstance(
            ecu_02["connected"],
            bool,
        )
        self.assertEqual(
            ecu_02["dependencies"],
            ["ECU-01"],
        )
        self.assertEqual(
            waves[0]["ecu_ids"],
            ["ECU-01"],
        )

    def test_missing_file_raises_data_error(self):
        with tempfile.TemporaryDirectory() as directory:
            empty_directory = Path(directory)
            store = CampaignDataStore(
                empty_directory
            )

            with self.assertRaises(
                CampaignDataError
            ):
                store.load_campaign()


if __name__ == "__main__":
    unittest.main()
