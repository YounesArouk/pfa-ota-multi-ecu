import unittest
from html.parser import HTMLParser

from fastapi.testclient import TestClient

from api.main import app


class DashboardHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.ids = []
        self.tags = set()
        self.external_resources = []

    def handle_starttag(
        self,
        tag,
        attrs,
    ):
        self.tags.add(tag)

        attributes = dict(attrs)

        element_id = attributes.get("id")

        if element_id:
            self.ids.append(element_id)

        for attribute in ("href", "src"):
            value = attributes.get(attribute)

            if (
                value
                and value.startswith(
                    ("http://", "https://")
                )
            ):
                self.external_resources.append(
                    value
                )


class DashboardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.html = cls.client.get(
            "/dashboard/"
        ).text

        cls.parser = DashboardHTMLParser()
        cls.parser.feed(cls.html)

    def test_root_redirects_to_dashboard(self):
        response = self.client.get(
            "/",
            follow_redirects=False,
        )

        self.assertEqual(
            response.status_code,
            307,
        )
        self.assertEqual(
            response.headers["location"],
            "/dashboard/",
        )

    def test_static_assets_are_served(self):
        expected_content_types = {
            "/dashboard/": "text/html",
            "/dashboard/styles.css": (
                "text/css"
            ),
            "/dashboard/app.js": (
                "text/javascript"
            ),
            "/dashboard/config.json": (
                "application/json"
            ),
        }

        for path, content_type in (
            expected_content_types.items()
        ):
            response = self.client.get(path)

            self.assertEqual(
                response.status_code,
                200,
            )
            self.assertTrue(
                response.headers[
                    "content-type"
                ].startswith(content_type)
            )

    def test_html_contains_main_structure(self):
        expected_tags = {
            "header",
            "main",
            "section",
            "table",
            "footer",
        }

        self.assertTrue(
            expected_tags.issubset(
                self.parser.tags
            )
        )
        self.assertIn(
            "PFE OTA Command Center",
            self.html,
        )

    def test_html_contains_required_ids(self):
        required_ids = {
            "connectionState",
            "refreshButton",
            "campaignTitle",
            "totalEcus",
            "qemuPanelTitle",
            "qemuConnection",
            "qemuEcuId",
            "qemuSourceType",
            "qemuVersion",
            "qemuSlot",
            "qemuOtaStatus",
            "qemuHealthStatus",
            "qemuError",
            "statusChart",
            "waveChart",
            "ecuSearch",
            "statusFilter",
            "ecuTableBody",
            "eventLevelFilter",
            "eventTableBody",
        }

        self.assertTrue(
            required_ids.issubset(
                set(self.parser.ids)
            )
        )

    def test_html_ids_are_unique(self):
        self.assertEqual(
            len(self.parser.ids),
            len(set(self.parser.ids)),
        )

    def test_dashboard_has_no_external_assets(self):
        self.assertEqual(
            self.parser.external_resources,
            [],
        )

    def test_css_contains_responsive_rules(self):
        css = self.client.get(
            "/dashboard/styles.css"
        ).text

        self.assertIn("@media", css)
        self.assertIn(
            "prefers-reduced-motion",
            css,
        )
        self.assertIn(
            ":focus-visible",
            css,
        )

    def test_javascript_contains_core_logic(self):
        javascript = self.client.get(
            "/dashboard/app.js"
        ).text

        required_functions = {
            "function escapeHtml",
            "function renderCampaign",
            "function renderQemuTarget",
            "function renderStatusChart",
            "function renderWaveChart",
            "function renderEcuTable",
            "function renderEventTable",
            "async function loadDashboard",
            "async function initialize",
        }
        self.assertIn(
            "routes.sources",
            javascript,
        )
        self.assertIn(
            "sources.qemu_rauc_target",
            javascript,
        )

        for function_name in required_functions:
            self.assertIn(
                function_name,
                javascript,
            )

        self.assertIn(
            "Promise.all",
            javascript,
        )

    def test_dashboard_routes_match_openapi(self):
        config = self.client.get(
            "/dashboard/config.json"
        ).json()

        for path in config[
            "api_routes"
        ].values():
            response = self.client.get(path)

            self.assertEqual(
                response.status_code,
                200,
            )

        openapi_paths = set(
            self.client.get(
                "/openapi.json"
            ).json()["paths"]
        )

        self.assertEqual(
            openapi_paths,
            set(
                config[
                    "api_routes"
                ].values()
            ),
        )


if __name__ == "__main__":
    unittest.main()
