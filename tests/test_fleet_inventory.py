import unittest

from simulator.fleet_inventory import (
    DATASET_ID,
    EXPECTED_ECU_COUNT,
    calculate_update_waves,
    load_dependencies,
    load_inventory,
    validate_inventory,
)


class FleetInventoryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.inventory = load_inventory()
        cls.dependencies = load_dependencies()
        cls.waves = validate_inventory(
            cls.inventory,
            cls.dependencies,
        )

    def test_inventory_contains_28_ecus(self):
        self.assertEqual(
            len(self.inventory),
            EXPECTED_ECU_COUNT,
        )

    def test_dataset_is_explicitly_synthetic(self):
        dataset_ids = {
            ecu["dataset_id"]
            for ecu in self.inventory.values()
        }

        self.assertEqual(dataset_ids, {DATASET_ID})
        self.assertEqual(DATASET_ID, "SYNTHETIC_PFE_V1")

    def test_central_gateway_is_unique_ota_master(self):
        masters = [
            ecu_id
            for ecu_id, ecu in self.inventory.items()
            if ecu["role"] == "OTA_MASTER"
        ]

        self.assertEqual(masters, ["ECU-01"])
        self.assertEqual(
            self.inventory["ECU-01"]["name"],
            "Central_Gateway",
        )

    def test_all_ecus_support_ab_and_recovery(self):
        for ecu in self.inventory.values():
            self.assertEqual(
                ecu["partition_scheme"],
                "A/B",
            )
            self.assertTrue(
                ecu["supports_live_rollback"]
            )
            self.assertTrue(
                ecu["has_recovery_partition"]
            )

    def test_ecus_have_specific_target_versions(self):
        target_versions = {
            ecu["target_version"]
            for ecu in self.inventory.values()
        }

        self.assertGreater(
            len(target_versions),
            10,
        )

    def test_dependencies_reference_known_ecus(self):
        for dependency in self.dependencies:
            self.assertIn(
                dependency["ecu_id"],
                self.inventory,
            )
            self.assertIn(
                dependency["depends_on"],
                self.inventory,
            )
            self.assertNotEqual(
                dependency["ecu_id"],
                dependency["depends_on"],
            )

    def test_update_waves_cover_each_ecu_once(self):
        planned_ecus = [
            ecu_id
            for wave in self.waves
            for ecu_id in wave
        ]

        self.assertEqual(
            len(planned_ecus),
            EXPECTED_ECU_COUNT,
        )
        self.assertEqual(
            len(set(planned_ecus)),
            EXPECTED_ECU_COUNT,
        )
        self.assertEqual(
            set(planned_ecus),
            set(self.inventory),
        )

    def test_central_gateway_is_first(self):
        self.assertEqual(
            self.waves[0],
            ["ECU-01"],
        )

    def test_zone_front_is_after_central_gateway(self):
        wave_by_ecu = {
            ecu_id: wave_number
            for wave_number, wave in enumerate(
                self.waves,
                start=1,
            )
            for ecu_id in wave
        }

        self.assertLess(
            wave_by_ecu["ECU-01"],
            wave_by_ecu["ECU-21"],
        )

    def test_ep150_is_planned_last(self):
        self.assertEqual(
            self.waves[-1],
            ["ECU-02"],
        )
        self.assertEqual(
            self.inventory["ECU-02"]["name"],
            "Connectivity_Unit_EP150",
        )

    def test_circular_dependency_is_rejected(self):
        cyclic_dependencies = list(self.dependencies)

        cyclic_dependencies.append(
            {
                "dataset_id": DATASET_ID,
                "ecu_id": "ECU-01",
                "depends_on": "ECU-21",
                "dependency_type": "HARD",
                "reason": "Test_circular_dependency",
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            "circulaire",
        ):
            calculate_update_waves(
                self.inventory,
                cyclic_dependencies,
            )


if __name__ == "__main__":
    unittest.main()
