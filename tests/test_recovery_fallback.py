import unittest

from simulator.ecu import VirtualECU


class RecoveryFallbackTests(unittest.TestCase):

    def setUp(self):
        self.ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

    def _trigger_dual_bank_failure(self):
        return self.ecu.run_update(
            target_version="3.0.0",
            release_id="recovery-release-001",
            dual_bank_failure=True,
        )

    def test_dual_bank_failure_boots_recovery(self):
        self._trigger_dual_bank_failure()

        self.assertEqual(
            self.ecu.ota_status,
            "RECOVERY_BOOT",
        )
        self.assertEqual(
            self.ecu.active_partition,
            "RECOVERY",
        )
        self.assertEqual(
            self.ecu.current_version,
            "1.0.0",
        )
        self.assertEqual(
            self.ecu.health_status,
            "RECOVERY",
        )
        self.assertEqual(
            self.ecu.rollback_trigger,
            "PFE-RECOVERY",
        )
        self.assertEqual(
            self.ecu.recovery_boot_counter,
            1,
        )

    def test_banks_are_bad_and_recovery_is_read_only(self):
        recovery_before = (
            self.ecu.partitions["RECOVERY"].to_dict()
        )

        self._trigger_dual_bank_failure()

        recovery_after = (
            self.ecu.partitions["RECOVERY"].to_dict()
        )

        self.assertEqual(
            self.ecu.partitions["A"].status,
            "BAD",
        )
        self.assertEqual(
            self.ecu.partitions["B"].status,
            "BAD",
        )
        self.assertEqual(
            recovery_before,
            recovery_after,
        )
        self.assertEqual(
            recovery_after["status"],
            "GOOD",
        )
        self.assertTrue(
            recovery_after["read_only"]
        )

    def test_failed_release_is_not_accepted(self):
        self._trigger_dual_bank_failure()

        self.assertNotIn(
            "recovery-release-001",
            self.ecu.accepted_releases,
        )
        self.assertEqual(
            self.ecu.rollback_counter,
            0,
        )

        expected_sequence = [
            "IDLE",
            "DOWNLOADING",
            "VERIFYING_SIGNATURE",
            "VERIFYING_CHECKSUM",
            "INSTALLING",
            "REBOOTING",
            "SELF_TEST",
            "RECOVERY_BOOT",
        ]

        self.assertEqual(
            self.ecu.state_history,
            expected_sequence,
        )

    def test_new_ota_is_blocked_in_recovery_mode(self):
        self._trigger_dual_bank_failure()

        downloads_before = (
            self.ecu.state_history.count(
                "DOWNLOADING"
            )
        )

        self.ecu.run_update(
            target_version="3.1.0",
            release_id="recovery-release-002",
        )

        downloads_after = (
            self.ecu.state_history.count(
                "DOWNLOADING"
            )
        )

        self.assertEqual(
            downloads_before,
            downloads_after,
        )
        self.assertEqual(
            self.ecu.ota_status,
            "RECOVERY_LOCKOUT",
        )
        self.assertEqual(
            self.ecu.rollback_trigger,
            "PFE-RECOVERY",
        )
        self.assertEqual(
            self.ecu.active_partition,
            "RECOVERY",
        )
        self.assertNotIn(
            "recovery-release-002",
            self.ecu.accepted_releases,
        )

    def test_normal_rb04_does_not_boot_recovery(self):
        self.ecu.run_update(
            target_version="3.0.0",
            release_id="normal-rb04-release",
            self_test_valid=False,
        )

        self.assertEqual(
            self.ecu.ota_status,
            "ROLLED_BACK",
        )
        self.assertEqual(
            self.ecu.active_partition,
            "A",
        )
        self.assertEqual(
            self.ecu.recovery_boot_counter,
            0,
        )


if __name__ == "__main__":
    unittest.main()
