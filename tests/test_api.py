import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.data_store import CampaignDataStore
from api.main import app


class CampaignAPITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(data["status"], "ok")
        self.assertEqual(
            data["api_version"],
            "1.0.0",
        )
        self.assertEqual(
            data["source_mode"],
            "HYBRID",
        )
        self.assertTrue(data["read_only"])

    def test_campaign_and_kpi_endpoints(self):
        campaign_response = self.client.get(
            "/api/v1/campaign"
        )
        kpi_response = self.client.get(
            "/api/v1/kpis"
        )

        self.assertEqual(
            campaign_response.status_code,
            200,
        )
        self.assertEqual(
            kpi_response.status_code,
            200,
        )

        campaign = campaign_response.json()
        kpis = kpi_response.json()

        self.assertEqual(
            campaign["campaign_id"],
            "CMP-FINAL-MIXED-001",
        )
        self.assertEqual(
            campaign["status"],
            "COMPLETED_WITH_FAILURES",
        )
        self.assertEqual(
            kpis["confirmation_rate_pct"],
            71.43,
        )
        self.assertEqual(
            kpis["budget_status"],
            "EXCEEDED",
        )

    def test_collection_endpoint_counts(self):
        expected_counts = {
            "/api/v1/ecus": 28,
            "/api/v1/waves": 5,
            "/api/v1/events": 65,
        }

        for path, expected_count in (
            expected_counts.items()
        ):
            response = self.client.get(path)

            self.assertEqual(
                response.status_code,
                200,
            )
            self.assertEqual(
                len(response.json()),
                expected_count,
            )

    def test_ecu_values_are_typed(self):
        response = self.client.get(
            "/api/v1/ecus"
        )

        ecus = response.json()

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

    def test_openapi_exposes_contract_routes(self):
        response = self.client.get(
            "/openapi.json"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        paths = set(
            response.json()["paths"]
        )

        expected_paths = {
            "/health",
            "/api/v1/campaign",
            "/api/v1/kpis",
            "/api/v1/ecus",
            "/api/v1/waves",
            "/api/v1/events",
            "/api/v1/qemu-ecu",
            "/api/v1/sources",
        }

        self.assertEqual(
            paths,
            expected_paths,
        )

    def test_missing_data_returns_http_500(self):
        with tempfile.TemporaryDirectory() as directory:
            empty_store = CampaignDataStore(
                Path(directory)
            )

            with patch(
                "api.main.data_store",
                empty_store,
            ):
                response = self.client.get(
                    "/api/v1/campaign"
                )

        self.assertEqual(
            response.status_code,
            500,
        )
        self.assertIn(
            "introuvable",
            response.json()["detail"],
        )

    def test_write_method_is_rejected(self):
        response = self.client.post(
            "/api/v1/campaign"
        )

        self.assertEqual(
            response.status_code,
            405,
        )


if __name__ == "__main__":
    unittest.main()
