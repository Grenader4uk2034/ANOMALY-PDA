"""Prepare lightweight, map-ready POI data from the all_entities.json export.

Coordinates are X-Ray world coordinates: X and Z are the horizontal map plane;
Y is retained as elevation. No player tracking or in-game integration.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

CATEGORY_LABELS = {
    "stash": "Тайники и контейнеры",
    "anomaly": "Аномалии",
    "population": "Точки симуляции",
    "mutant": "Мутанты",
    "npc": "Персонажи",
    "camp": "Лагеря и костры",
    "transition": "Переходы между уровнями",
    "poi": "Другие объекты",
}

def classify(section: str, name: str = "") -> str:
    section = section.lower()
    name = name.lower()
    if section in {"inventory_box", "hidden_box", "inv_backpack"}:
        return "stash"
    if section == "anomal_zone" or section.startswith("zone_") or "anomal" in section:
        return "anomaly"
    if section == "smart_terrain":
        return "population"
    if section in {"campfire", "campfire_burn"}:
        return "camp"
    if section == "level_changer":
        return "transition"
    if section in {"m_trader", "m_lesnik"} or section.startswith(("stalker", "actor", "trader", "squad")):
        return "npc"
    if section.startswith("m_") or any(token in section for token in ("bloodsucker", "pseudodog", "snork", "controller", "chimera", "boar", "flesh", "dog", "zombie")):
        return "mutant"
    if any(token in name for token in ("stash", "treasure", "secret", "inventory_box")):
        return "stash"
    return "poi"

def _valid_position(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return None
    try:
        xyz = tuple(float(value[i]) for i in range(3))
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in xyz):
        return None
    return xyz

def build_map_data(source: dict[str, Any]) -> dict[str, Any]:
    entities = source.get("entities")
    if not isinstance(entities, list):
        raise ValueError("input JSON must contain an 'entities' array")

    features = []
    category_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    skipped = 0

    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            skipped += 1
            continue
        position = _valid_position(entity.get("position"))
        level = entity.get("level")
        section = entity.get("section")
        name = entity.get("name")
        if position is None or not isinstance(level, str) or not level or not isinstance(section, str) or not section:
            skipped += 1
            continue
        name = name if isinstance(name, str) else ""
        category = classify(section, name)
        x, y, z = position
        properties = {
            "id": f"spawn-{index}",
            "name": name or section,
            "section": section,
            "level": level,
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "x": x,
            "y": y,
            "z": z,
            "game_vertex_id": entity.get("game_vertex_id"),
            "level_vertex_id": entity.get("level_vertex_id"),
        }
        features.append({
            "type": "Feature",
            "id": properties["id"],
            "geometry": {"type": "Point", "coordinates": [x, z]},
            "properties": properties,
        })
        category_counts[category] += 1
        level_counts[level] += 1

    features.sort(key=lambda item: (item["properties"]["level"], item["properties"]["category"], item["properties"]["name"], item["id"]))
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": "all_entities.json",
            "coordinate_system": "X-Ray world coordinates; map plane is X/Z; Y is elevation",
            "entity_count": len(features),
            "skipped_count": skipped,
            "levels": dict(sorted(level_counts.items())),
            "categories": dict(sorted(category_counts.items())),
            "category_labels": CATEGORY_LABELS,
        },
        "features": features,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert all_entities.json to map-ready GeoJSON-like data")
    parser.add_argument("input", type=Path, help="path to data/processed/all_entities.json")
    parser.add_argument("output", type=Path, help="output JSON path")
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8-sig"))
    result = build_map_data(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(result["metadata"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
