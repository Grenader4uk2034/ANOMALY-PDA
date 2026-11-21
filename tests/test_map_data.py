import unittest

from anomaly_pda.map_data import build_map_data, classify


class MapDataTests(unittest.TestCase):
    def test_classifies_core_map_categories(self):
        self.assertEqual(classify("inventory_box"), "stash")
        self.assertEqual(classify("anomal_zone"), "anomaly")
        self.assertEqual(classify("zone_mine_acidic_average"), "anomaly")
        self.assertEqual(classify("smart_terrain"), "population")
        self.assertEqual(classify("level_changer"), "transition")

    def test_builds_map_features_and_keeps_elevation(self):
        result = build_map_data({"entities": [
            {"section": "inventory_box", "name": "box_01", "level": "jupiter",
             "position": [10, 2.5, -30], "game_vertex_id": 4, "level_vertex_id": 8},
            {"section": "anomal_zone", "name": "anom_01", "level": "jupiter",
             "position": [1, 0, 2]},
        ]})
        self.assertEqual(result["metadata"]["entity_count"], 2)
        self.assertEqual(result["metadata"]["levels"]["jupiter"], 2)
        feature = result["features"][0]
        self.assertEqual(feature["geometry"]["coordinates"], [10.0, -30.0])
        self.assertEqual(feature["properties"]["y"], 2.5)
        self.assertEqual(feature["properties"]["category"], "stash")

    def test_skips_invalid_coordinates_and_rejects_missing_entities(self):
        result = build_map_data({"entities": [
            {"section": "x", "level": "jupiter", "position": [float("nan"), 0, 0]},
            {"section": "x", "level": "jupiter", "position": [1, 2]},
        ]})
        self.assertEqual(result["metadata"]["entity_count"], 0)
        self.assertEqual(result["metadata"]["skipped_count"], 2)
        with self.assertRaises(ValueError):
            build_map_data({})


if __name__ == "__main__":
    unittest.main()
