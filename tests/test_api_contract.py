import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    PROJECT_ROOT
    / "config"
    / "api-contract.json"
)
DATA_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "latest"
)


class APIContractTests(unittest.TestCase):

    def setUp(self):
        with CONTRACT_PATH.open(
            encoding="utf-8",
        ) as file:
            self.contract = json.load(file)

    def test_contract_metadata(self):
        self.assertEqual(
            self.contract["schema_version"],
            "1.0",
        )
        self.assertEqual(
            self.contract["api_version"],
            "1.0.0",
        )
        self.assertEqual(
            self.contract["source_mode"],
            "SIMULATION",
        )
        self.assertTrue(
            self.contract["read_only"]
        )

    def test_contract_contains_expected_routes(self):
        expected_routes = {
            ("GET", "/health"),
            ("GET", "/api/v1/campaign"),
            ("GET", "/api/v1/kpis"),
            ("GET", "/api/v1/ecus"),
            ("GET", "/api/v1/waves"),
            ("GET", "/api/v1/events"),
        }

        actual_routes = {
            (
                route["method"],
                route["path"],
            )
            for route in self.contract["routes"]
        }

        self.assertEqual(
            actual_routes,
            expected_routes,
        )
        self.assertEqual(
            len(self.contract["routes"]),
            6,
        )

    def test_declared_data_sources_exist(self):
        for route in self.contract["routes"]:
            source = route["data_source"]

            if source is None:
                continue

            source_path = (
                DATA_DIRECTORY
                / source
            )

            self.assertTrue(
                source_path.is_file(),
                msg=(
                    "Source API introuvable : "
                    f"{source_path}"
                ),
            )


if __name__ == "__main__":
    unittest.main()
