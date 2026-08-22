import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_CONFIG_PATH = (
    PROJECT_ROOT
    / "dashboard"
    / "config.json"
)
API_CONTRACT_PATH = (
    PROJECT_ROOT
    / "config"
    / "api-contract.json"
)


class DashboardConfigurationTests(
    unittest.TestCase
):

    def setUp(self):
        with DASHBOARD_CONFIG_PATH.open(
            encoding="utf-8",
        ) as file:
            self.config = json.load(file)

    def test_dashboard_metadata(self):
        self.assertEqual(
            self.config["schema_version"],
            "1.0",
        )
        self.assertEqual(
            self.config["dashboard_version"],
            "1.0.0",
        )
        self.assertEqual(
            self.config["source_mode"],
            "SIMULATION",
        )
        self.assertEqual(
            self.config["time_budget_s"],
            90,
        )
        self.assertGreater(
            self.config["refresh_interval_s"],
            0,
        )

    def test_routes_match_api_contract(self):
        with API_CONTRACT_PATH.open(
            encoding="utf-8",
        ) as file:
            api_contract = json.load(file)

        dashboard_routes = set(
            self.config["api_routes"].values()
        )
        api_routes = {
            route["path"]
            for route in api_contract["routes"]
        }

        self.assertEqual(
            dashboard_routes,
            api_routes,
        )

    def test_status_definitions_are_complete(self):
        expected_statuses = {
            "CONFIRMED",
            "REJECTED",
            "ROLLED_BACK",
            "BLOCKED",
            "ROLLBACK_LOCKOUT",
            "RECOVERY_BOOT",
        }

        definitions = (
            self.config["status_definitions"]
        )
        actual_statuses = {
            item["status"]
            for item in definitions
        }

        self.assertEqual(
            actual_statuses,
            expected_statuses,
        )
        self.assertEqual(
            len(definitions),
            6,
        )

        for item in definitions:
            self.assertRegex(
                item["color"],
                re.compile(
                    r"^#[0-9A-Fa-f]{6}$"
                ),
            )

    def test_sections_are_unique(self):
        sections = self.config["sections"]

        self.assertEqual(len(sections), 6)
        self.assertEqual(
            len(sections),
            len(set(sections)),
        )


if __name__ == "__main__":
    unittest.main()
