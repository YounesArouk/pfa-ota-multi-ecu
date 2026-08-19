import unittest

from simulator.ecu import VirtualECU


class RollbackTriggerTests(unittest.TestCase):

    def setUp(self):
        self.ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

    def test_rb01_rejects_checksum_before_installation(self):
        result = self.ecu.run_update(
            target_version="3.0.0",
            release_id="release-rb01",
            checksum_valid=False,
        )

        self.assertEqual(result["rollback_trigger"], "RB-01")
        self.assertEqual(self.ecu.ota_status, "REJECTED")
        self.assertEqual(self.ecu.current_version, "2.0.0")
        self.assertEqual(self.ecu.active_partition, "A")
        self.assertEqual(self.ecu.partitions["B"].status, "EMPTY")
        self.assertIsNone(self.ecu.partitions["B"].version)
        self.assertNotIn("release-rb01", self.ecu.accepted_releases)
        self.assertNotIn("INSTALLING", self.ecu.state_history)
        self.assertEqual(self.ecu.rollback_counter, 0)

    def test_rb04_restores_previous_slot(self):
        result = self.ecu.run_update(
            target_version="3.0.0",
            release_id="release-rb04",
            self_test_valid=False,
        )

        self.assertEqual(result["rollback_trigger"], "RB-04")
        self.assertEqual(self.ecu.ota_status, "ROLLED_BACK")
        self.assertEqual(self.ecu.current_version, "2.0.0")
        self.assertEqual(self.ecu.active_partition, "A")
        self.assertEqual(self.ecu.partitions["B"].version, "3.0.0")
        self.assertEqual(self.ecu.partitions["B"].status, "BAD")
        self.assertEqual(self.ecu.rollback_counter, 1)
        self.assertNotIn("release-rb04", self.ecu.accepted_releases)

        self.assertIsNotNone(
            self.ecu.last_rollback_duration_s
        )
        self.assertLess(
            self.ecu.last_rollback_duration_s,
            5.0,
        )

    def test_rb04_performs_no_second_download(self):
        self.ecu.run_update(
            target_version="3.0.0",
            release_id="release-rb04",
            self_test_valid=False,
        )

        expected_sequence = [
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "ROLLBACK",
            "ROLLED_BACK",
        ]

        self.assertEqual(
            self.ecu.state_history,
            expected_sequence,
        )
        self.assertEqual(
            self.ecu.state_history.count("DOWNLOADING"),
            1,
        )

    def test_recovery_partition_survives_rb04(self):
        recovery_before = (
            self.ecu.partitions["RECOVERY"].to_dict()
        )

        self.ecu.run_update(
            target_version="3.0.0",
            release_id="release-rb04",
            self_test_valid=False,
        )

        recovery_after = (
            self.ecu.partitions["RECOVERY"].to_dict()
        )

        self.assertEqual(recovery_before, recovery_after)
        self.assertTrue(recovery_after["read_only"])

    def test_rb01_release_can_be_retried(self):
        self.ecu.run_update(
            target_version="3.0.0",
            release_id="release-retry",
            checksum_valid=False,
        )

        self.ecu.run_nominal_update(
            target_version="3.0.0",
            release_id="release-retry",
        )

        self.assertEqual(self.ecu.ota_status, "CONFIRMED")
        self.assertEqual(self.ecu.current_version, "3.0.0")
        self.assertEqual(self.ecu.active_partition, "B")
        self.assertIn(
            "release-retry",
            self.ecu.accepted_releases,
        )


if __name__ == "__main__":
    unittest.main()
