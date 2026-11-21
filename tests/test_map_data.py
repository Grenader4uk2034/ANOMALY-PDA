import unittest

from anomaly_pda.map_data import build_map_data, classify


class MapDataTests(unittest.TestCase):
    def test_classifies_core_map_categories(self):
        self.assertEqual(classify("inventory_box"), "stash")
        self.assertEqual(classify("anomal_zone"), "anomaly")
        self.assertEqual(classify("zone_mine_acidic_average"), "anomaly")
        self.assertEqual(classify("smart_terrain"), "population")
        self.assertEqual(classify("level_changer"), "transition")
        self.assertEqual(classify("m_trader"), "npc")
        self.assertEqual(classify("m_lesnik"), "npc")
        self.assertEqual(classify("m_car"), "vehicle")
        self.assertEqual(classify("m_bloodsucker"), "mutant")

    def test_builds_map_features_and_keeps_elevation(self):
        result = build_map_data({"entities": [
            {"section": "inventory_box", "name": "box_01", "level": "jupiter",
             "position": [10, 2.5, -30], "game_vertex_id": 4, "level_vertex_id": 8},
            {"section": "anomal_zone", "name": "anom_01", "level": "jupiter",
             "position": [1, 0, 2]},
        ]})
        self.assertEqual(result["metadata"]["entity_count"], 2)
        self.assertEqual(result["metadata"]["levels"]["jupiter"], 2)
        stash = next(item for item in result["features"] if item["properties"]["name"] == "box_01")
        self.assertEqual(stash["geometry"]["coordinates"], [10.0, -30.0])
        self.assertEqual(stash["properties"]["y"], 2.5)
        self.assertEqual(stash["properties"]["category"], "stash")

    def test_merges_reference_stashes_and_special_points(self):
        source = {"entities": [
            {"section": "inventory_box", "name": "zat_treasure_1", "level": "zaton",
             "position": [1, 2, 3]},
        ]}
        references = [
            {"level": "zaton", "name": "zat_treasure_1", "type": "treasure",
             "x": 1, "y": 2, "z": 3},
            {"level": "jupiter", "name": "jup_secret_1", "type": "secret",
             "x": 10, "y": -2, "z": 30},
            {"level": "jupiter", "name": "jup_quest_1", "type": "quest",
             "x": -10, "y": 4, "z": -30},
            {"level": "jupiter", "name": "jup_weapon_1", "type": "weapon",
             "x": 5, "y": 0, "z": 5},
        ]
        result = build_map_data(source, references)
        self.assertEqual(result["metadata"]["entity_count"], 4)
        self.assertEqual(result["metadata"]["spawn_entity_count"], 1)
        self.assertEqual(result["metadata"]["reference_entity_count"], 3)
        by_name = {item["properties"]["name"]: item["properties"] for item in result["features"]}
        self.assertEqual(by_name["jup_secret_1"]["category"], "stash")
        self.assertEqual(by_name["jup_quest_1"]["category"], "quest")
        self.assertEqual(by_name["jup_weapon_1"]["category"], "weapon")
        self.assertEqual(by_name["jup_secret_1"]["source_kind"], "reference_export")

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
