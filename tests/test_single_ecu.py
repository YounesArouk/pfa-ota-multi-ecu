import unittest

from simulator.ecu import VirtualECU


class VirtualECUTests(unittest.TestCase):

    def setUp(self):
        self.ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

    def test_initial_state(self):
        self.assertEqual(self.ecu.current_version, "2.0.0")
        self.assertEqual(self.ecu.active_partition, "A")
        self.assertEqual(self.ecu.ota_status, "IDLE")
        self.assertEqual(self.ecu.progress_pct, 0)
        self.assertEqual(
            set(self.ecu.partitions),
            {"A", "B", "RECOVERY"},
        )

    def test_nominal_update_switches_from_a_to_b(self):
        result = self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="pfe-ota-v3-release-001",
        )

        self.assertEqual(self.ecu.current_version, "2.1.0")
        self.assertEqual(self.ecu.active_partition, "B")
        self.assertEqual(self.ecu.ota_status, "CONFIRMED")
        self.assertEqual(self.ecu.progress_pct, 100)
        self.assertEqual(
            self.ecu.partitions["B"].version,
            "2.1.0",
        )
        self.assertEqual(result["source_type"], "SIMULATED")

    def test_state_sequence(self):
        self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="pfe-ota-v3-release-001",
        )

        expected_sequence = [
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "CONFIRMED",
        ]

        self.assertEqual(
            self.ecu.state_history,
            expected_sequence,
        )

        self.assertLess(
            self.ecu.state_history.index("VERIFYING_SIGNATURE"),
            self.ecu.state_history.index("INSTALLING"),
        )

    def test_recovery_partition_remains_read_only(self):
        recovery_before = self.ecu.partitions["RECOVERY"].to_dict()

        self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="pfe-ota-v3-release-001",
        )

        recovery_after = self.ecu.partitions["RECOVERY"].to_dict()

        self.assertEqual(recovery_before, recovery_after)
        self.assertTrue(recovery_after["read_only"])

    def test_anti_replay_rejects_accepted_release(self):
        self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="pfe-ota-v3-release-001",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Release déjà acceptée",
        ):
            self.ecu.run_nominal_update(
                target_version="2.2.0",
                release_id="pfe-ota-v3-release-001",
            )

    def test_offline_ecu_cannot_start_update(self):
        self.ecu.connected = False

        with self.assertRaisesRegex(
            RuntimeError,
            "ECU non joignable",
        ):
            self.ecu.run_nominal_update(
                target_version="2.1.0",
                release_id="pfe-ota-v3-release-001",
            )

        self.assertEqual(self.ecu.ota_status, "IDLE")
        self.assertEqual(self.ecu.active_partition, "A")

    def test_second_update_switches_from_b_to_a(self):
        self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="pfe-ota-v3-release-001",
        )

        self.ecu.run_nominal_update(
            target_version="2.2.0",
            release_id="pfe-ota-v3-release-002",
        )

        self.assertEqual(self.ecu.current_version, "2.2.0")
        self.assertEqual(self.ecu.active_partition, "A")
        self.assertEqual(
            self.ecu.partitions["A"].version,
            "2.2.0",
        )
        self.assertEqual(
            len(self.ecu.accepted_releases),
            2,
        )


if __name__ == "__main__":
    unittest.main()
