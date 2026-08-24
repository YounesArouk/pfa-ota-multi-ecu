import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.qemu_rauc_connector import (
    get_active_slot,
    load_qemu_ecu,
    run_ssh,
)


class QemuRaucConnectorTests(unittest.TestCase):

    @patch(
        "api.qemu_rauc_connector.subprocess.run"
    )
    def test_ssh_is_scoped_to_local_qemu(
        self,
        subprocess_run_mock,
    ):
        subprocess_run_mock.return_value = (
            SimpleNamespace(
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
        )

        result = run_ssh("true")

        command = (
            subprocess_run_mock
            .call_args
            .args[0]
        )

        self.assertEqual(
            result,
            "ok",
        )
        self.assertIn(
            "root@127.0.0.1",
            command,
        )
        self.assertIn(
            "StrictHostKeyChecking=no",
            command,
        )
        self.assertIn(
            "UserKnownHostsFile=/dev/null",
            command,
        )
        self.assertIn(
            "LogLevel=ERROR",
            command,
        )
        self.assertEqual(
            subprocess_run_mock
            .call_args
            .kwargs["timeout"],
            20,
        )
    def test_active_slot_is_read_from_cmdline(self):
        cmdline = (
            "root=/dev/sda2 "
            "console=ttyS0 "
            "rauc.slot=A"
        )

        self.assertEqual(
            get_active_slot(cmdline),
            "A",
        )

    def test_unknown_slot_is_reported(self):
        self.assertEqual(
            get_active_slot(
                "root=/dev/sda2 console=ttyS0"
            ),
            "UNKNOWN",
        )

    @patch(
        "api.qemu_rauc_connector.run_ssh"
    )
    def test_connected_qemu_returns_rauc_state(
        self,
        run_ssh_mock,
    ):
        rauc_status = {
            "booted": "A",
            "slots": [
                {
                    "rootfs.0": {
                        "bootname": "A",
                        "boot_status": "good",
                    }
                },
                {
                    "rootfs.1": {
                        "bootname": "B",
                        "boot_status": "bad",
                    }
                },
            ],
        }

        run_ssh_mock.return_value = (
            "__PFE_VERSION__\n"
            "2.0.0\n"
            "__PFE_CMDLINE__\n"
            "root=/dev/sda2 rauc.slot=A\n"
            "__PFE_RAUC__\n"
            + json.dumps(rauc_status)
        )
        state = load_qemu_ecu()

        self.assertTrue(
            state["connected"]
        )
        self.assertEqual(
            state["ecu_id"],
            "QEMU-ECU-01",
        )
        self.assertEqual(
            state["source_type"],
            "QEMU_REAL",
        )
        self.assertEqual(
            state["current_version"],
            "2.0.0",
        )
        self.assertEqual(
            state["active_partition"],
            "A",
        )
        self.assertEqual(
            state["ota_status"],
            "CONFIRMED",
        )
        self.assertEqual(
            state["health_status"],
            "GOOD",
        )
        self.assertEqual(
            run_ssh_mock.call_count,
            1,
        )

    @patch(
        "api.qemu_rauc_connector.run_ssh"
    )
    def test_stopped_qemu_is_reported_offline(
        self,
        run_ssh_mock,
    ):
        run_ssh_mock.side_effect = RuntimeError(
            "SSH QEMU indisponible"
        )

        state = load_qemu_ecu()

        self.assertFalse(
            state["connected"]
        )
        self.assertEqual(
            state["ota_status"],
            "BLOCKED",
        )
        self.assertEqual(
            state["health_status"],
            "OFFLINE",
        )
        self.assertEqual(
            state["active_partition"],
            "UNKNOWN",
        )
        self.assertIn(
            "SSH QEMU indisponible",
            state["connector_error"],
        )


class HybridApiSeparationTests(unittest.TestCase):

    def setUp(self):
        self.qemu_state = {
            "ecu_id": "QEMU-ECU-01",
            "source_type": "QEMU_REAL",
            "current_version": None,
            "active_partition": "UNKNOWN",
            "ota_status": "BLOCKED",
            "health_status": "OFFLINE",
            "connected": False,
        }

        self.patcher = patch(
            "api.main.load_qemu_ecu",
            return_value=self.qemu_state,
        )

        self.patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.patcher.stop()

    def test_simulated_fleet_remains_28_ecus(
        self,
    ):
        campaign = self.client.get(
            "/api/v1/campaign"
        ).json()

        kpis = self.client.get(
            "/api/v1/kpis"
        ).json()

        ecus = self.client.get(
            "/api/v1/ecus"
        ).json()

        self.assertEqual(
            campaign["total_ecus"],
            28,
        )
        self.assertEqual(
            kpis["total_ecus"],
            28,
        )
        self.assertEqual(
            len(ecus),
            28,
        )
        self.assertNotIn(
            "QEMU-ECU-01",
            {
                ecu["ecu_id"]
                for ecu in ecus
            },
        )

    def test_qemu_and_sources_are_separate(
        self,
    ):
        qemu_response = self.client.get(
            "/api/v1/qemu-ecu"
        )

        sources_response = self.client.get(
            "/api/v1/sources"
        )

        self.assertEqual(
            qemu_response.status_code,
            200,
        )
        self.assertEqual(
            sources_response.status_code,
            200,
        )

        sources = sources_response.json()

        self.assertEqual(
            sources["source_mode"],
            "HYBRID",
        )
        self.assertEqual(
            sources[
                "simulated_fleet"
            ]["total_ecus"],
            28,
        )
        self.assertTrue(
            sources[
                "simulated_fleet"
            ]["available"]
        )
        self.assertEqual(
            sources[
                "qemu_rauc_target"
            ]["ecu_id"],
            "QEMU-ECU-01",
        )
        self.assertFalse(
            sources[
                "qemu_rauc_target"
            ]["available"]
        )


if __name__ == "__main__":
    unittest.main()
