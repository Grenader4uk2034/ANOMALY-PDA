"""Prepare map-ready POI data from all.spawn and optional reference exports.

Coordinates use the X-Ray world system: X/Z are the horizontal map plane;
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
    "quest": "Квестовые точки",
    "weapon": "Оружие и уникальные предметы",
    "special": "Особые точки",
    "vehicle": "Транспорт",
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
    if section == "m_car":
        return "vehicle"
    if section.startswith("reference_"):
        ref_type = section.removeprefix("reference_")
        if ref_type in {"quest", "weapon", "special"}:
            return ref_type
    if section.startswith("m_") or any(
        token in section
        for token in (
            "bloodsucker", "pseudodog", "snork", "controller", "chimera",
            "boar", "flesh", "dog", "zombie", "tushkano", "poltergeist",
            "gigant", "fracture", "burer", "cat",
        )
    ):
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


def _feature(
    entity: dict[str, Any],
    index: int,
    source_kind: str,
    position: Any,
    section: Any,
    name: Any,
    level: Any,
    category_override: str | None = None,
) -> dict[str, Any] | None:
    xyz = _valid_position(position)
    if (
        xyz is None
        or not isinstance(level, str)
        or not level
        or not isinstance(section, str)
        or not section
    ):
        return None

    name = name if isinstance(name, str) and name else section
    category = category_override or classify(section, name)
    x, y, z = xyz
    properties = {
        "id": f"{source_kind}-{index}",
        "name": name,
        "section": section,
        "level": level,
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "source_kind": source_kind,
        "x": x,
        "y": y,
        "z": z,
        "game_vertex_id": entity.get("game_vertex_id"),
        "level_vertex_id": entity.get("level_vertex_id"),
    }
    if source_kind == "reference_export":
        properties["reference_type"] = entity.get("type")
    return {
        "type": "Feature",
        "id": properties["id"],
        "geometry": {"type": "Point", "coordinates": [x, z]},
        "properties": properties,
    }


def build_map_data(
    source: dict[str, Any],
    additional_entities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    entities = source.get("entities")
    if not isinstance(entities, list):
        raise ValueError("input JSON must contain an 'entities' array")
    if additional_entities is not None and not isinstance(additional_entities, list):
        raise ValueError("additional reference data must be a JSON array")

    features: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    skipped = 0
    seen: set[tuple[Any, ...]] = set()

    def add_feature(feature: dict[str, Any] | None) -> None:
        nonlocal skipped
        if feature is None:
            skipped += 1
            return
        props = feature["properties"]
        key = (
            props["level"],
            props["name"],
            round(props["x"], 3),
            round(props["y"], 3),
            round(props["z"], 3),
        )
        if key in seen:
            return
        seen.add(key)
        features.append(feature)
        category_counts[props["category"]] += 1
        level_counts[props["level"]] += 1

    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            skipped += 1
            continue
        add_feature(
            _feature(
                entity,
                index,
                "spawn",
                entity.get("position"),
                entity.get("section"),
                entity.get("name"),
                entity.get("level"),
            )
        )

    for index, entity in enumerate(additional_entities or []):
        if not isinstance(entity, dict):
            skipped += 1
            continue
        ref_type = entity.get("type")
        ref_type = ref_type.lower() if isinstance(ref_type, str) else "special"
        if ref_type in {"treasure", "secret"}:
            section = "inventory_box"
            category = "stash"
        else:
            section = f"reference_{ref_type}"
            category = ref_type if ref_type in {"quest", "weapon", "special"} else "poi"
        add_feature(
            _feature(
                entity,
                index,
                "reference_export",
                [entity.get("x"), entity.get("y"), entity.get("z")],
                section,
                entity.get("name"),
                entity.get("level"),
                category,
            )
        )

    features.sort(
        key=lambda item: (
            item["properties"]["level"],
            item["properties"]["category"],
            item["properties"]["name"],
            item["id"],
        )
    )
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": "all_entities.json",
            "reference_source": "optional stashes_and_poi.json",
            "coordinate_system": "X-Ray world coordinates; map plane is X/Z; Y is elevation",
            "entity_count": len(features),
            "spawn_entity_count": sum(
                1 for item in features if item["properties"]["source_kind"] == "spawn"
            ),
            "reference_entity_count": sum(
                1 for item in features if item["properties"]["source_kind"] == "reference_export"
            ),
            "skipped_count": skipped,
            "levels": dict(sorted(level_counts.items())),
            "categories": dict(sorted(category_counts.items())),
            "category_labels": CATEGORY_LABELS,
        },
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert all_entities.json and optional reference POIs to map-ready JSON"
    )
    parser.add_argument("input", type=Path, help="path to data/processed/all_entities.json")
    parser.add_argument("output", type=Path, help="output JSON path")
    parser.add_argument(
        "--references",
        type=Path,
        help="optional JSON array with treasure, secret, quest and special POI coordinates",
    )
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8-sig"))
    references = None
    if args.references:
        references = json.loads(args.references.read_text(encoding="utf-8-sig"))
    result = build_map_data(source, references)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(json.dumps(result["metadata"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
