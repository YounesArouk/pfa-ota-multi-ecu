import unittest

from simulator.ecu import VirtualECU


class RepeatedRollbackTests(unittest.TestCase):

    def setUp(self):
        self.ecu = VirtualECU(
            ecu_id="ECU-01",
            name="Central_Gateway",
            domain="Connectivity",
        )

    def _run_failed_update(
        self,
        version: str,
        release_id: str,
    ):
        return self.ecu.run_update(
            target_version=version,
            release_id=release_id,
            self_test_valid=False,
        )

    def test_first_rollback_does_not_activate_lockout(self):
        self._run_failed_update(
            "2.1.0",
            "rb18-release-001",
        )

        self.assertEqual(
            self.ecu.ota_status,
            "ROLLED_BACK",
        )
        self.assertEqual(
            self.ecu.consecutive_rollback_counter,
            1,
        )
        self.assertFalse(
            self.ecu.rollback_lockout
        )
        self.assertEqual(
            self.ecu.rollback_trigger,
            "RB-04",
        )

    def test_second_consecutive_rollback_activates_rb18(self):
        self._run_failed_update(
            "2.1.0",
            "rb18-release-001",
        )
        self._run_failed_update(
            "2.2.0",
            "rb18-release-002",
        )

        self.assertEqual(
            self.ecu.ota_status,
            "ROLLBACK_LOCKOUT",
        )
        self.assertEqual(
            self.ecu.rollback_trigger,
            "RB-18",
        )
        self.assertEqual(
            self.ecu.rollback_counter,
            2,
        )
        self.assertEqual(
            self.ecu.consecutive_rollback_counter,
            2,
        )
        self.assertTrue(
            self.ecu.rollback_lockout
        )
        self.assertEqual(
            self.ecu.current_version,
            "2.0.0",
        )
        self.assertEqual(
            self.ecu.active_partition,
            "A",
        )
        self.assertEqual(
            self.ecu.state_history.count(
                "DOWNLOADING"
            ),
            2,
        )

    def test_third_attempt_is_blocked_before_download(self):
        self._run_failed_update(
            "2.1.0",
            "rb18-release-001",
        )
        self._run_failed_update(
            "2.2.0",
            "rb18-release-002",
        )

        downloads_before = (
            self.ecu.state_history.count(
                "DOWNLOADING"
            )
        )

        result = self.ecu.run_update(
            target_version="2.3.0",
            release_id="rb18-release-003",
        )

        downloads_after = (
            self.ecu.state_history.count(
                "DOWNLOADING"
            )
        )

        self.assertEqual(
            result["ota_status"],
            "ROLLBACK_LOCKOUT",
        )
        self.assertEqual(
            downloads_before,
            downloads_after,
        )
        self.assertNotIn(
            "rb18-release-003",
            self.ecu.accepted_releases,
        )

    def test_success_resets_consecutive_counter(self):
        self._run_failed_update(
            "2.1.0",
            "rb18-release-001",
        )

        self.ecu.run_nominal_update(
            target_version="2.1.0",
            release_id="rb18-release-success",
        )

        self.assertEqual(
            self.ecu.ota_status,
            "CONFIRMED",
        )
        self.assertEqual(
            self.ecu.consecutive_rollback_counter,
            0,
        )
        self.assertFalse(
            self.ecu.rollback_lockout
        )


if __name__ == "__main__":
    unittest.main()
