#!/usr/bin/env python3
"""Build a portable global-map asset package from the audited Anomaly DDS sources.

Outputs:
  research/global-map/build/global_map.png
  research/global-map/build/levels/<level>.png
  research/global-map/build/map_manifest.json

The script does not modify source assets, game files, or Android app files.
Requires Pillow with DDS support.
"""
from pathlib import Path
import csv
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "research/global-map/source"
REPORTS = ROOT / "research/global-map/reports"
OUT = ROOT / "research/global-map/build"
CSV_PATH = REPORTS / "asset_audit.csv"
GLOBAL_DDS = SRC / "textures/ui/ui_global_map.dds"
LOGICAL_W, LOGICAL_H = 1024.0, 2634.0
GLOBAL_W, GLOBAL_H = 1024, 2048
SCALE_Y = GLOBAL_H / LOGICAL_H
EXCLUDED = {
    "fake_start", "jupiter_underground", "labx8", "l03u_agr_underground",
    "l04u_labx18", "l08u_brainlab", "l10u_bunker",
    "l12u_control_monolith", "l12u_sarcofag", "l13u_warlab",
}


def num(row, key):
    return float(row[key])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    level_out = OUT / "levels"
    level_out.mkdir(parents=True, exist_ok=True)

    with Image.open(GLOBAL_DDS) as src:
        global_map = src.convert("RGBA")
    if global_map.size != (GLOBAL_W, GLOBAL_H):
        raise RuntimeError(
            f"Global DDS must be {GLOBAL_W}x{GLOBAL_H}; got {global_map.size}"
        )
    global_path = OUT / "global_map.png"
    global_map.save(global_path, optimize=True)

    manifest = {
        "schemaVersion": 1,
        "game": "STALKER Anomaly 1.5.3",
        "coordinateSystem": {
            "globalLogicalBounds": [0.0, 0.0, LOGICAL_W, LOGICAL_H],
            "globalTextureSize": [GLOBAL_W, GLOBAL_H],
            "logicalToPixel": {
                "x": 1.0,
                "y": SCALE_Y,
                "yInverted": False
            },
            "worldToLocalTexture": {
                "x": "(worldX - worldMinX) / worldWidth",
                "y": "1 - (worldZ - worldMinZ) / worldHeight",
                "zInverted": True
            }
        },
        "globalMap": "global_map.png",
        "levels": []
    }

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        level = row["level"]
        if level in EXCLUDED:
            continue
        texture_name = row["texture"]
        texture_path = SRC / "textures/map" / f"{texture_name}.dds"
        if not texture_path.is_file():
            raise FileNotFoundError(f"Missing level DDS for {level}: {texture_path}")

        with Image.open(texture_path) as src:
            tile = src.convert("RGBA")
        tile_name = f"levels/{level}.png"
        tile.save(OUT / tile_name, optimize=True)

        gx1, gz1 = num(row, "global_x1"), num(row, "global_z1")
        gx2, gz2 = num(row, "global_x2"), num(row, "global_z2")
        px_rect = [
            gx1,
            gz1 * SCALE_Y,
            gx2,
            gz2 * SCALE_Y
        ]
        manifest["levels"].append({
            "id": level,
            "texture": tile_name,
            "textureSize": list(tile.size),
            "globalRectLogical": [gx1, gz1, gx2, gz2],
            "globalRectPixels": px_rect,
            "worldBounds": [
                num(row, "world_x1"), num(row, "world_z1"),
                num(row, "world_x2"), num(row, "world_z2")
            ],
            "worldToGlobalScale": [
                num(row, "scale_x"), num(row, "scale_z")
            ],
            "boundsStatus": (
                "partially_outside_global_canvas"
                if px_rect[0] < 0 or px_rect[1] < 0
                or px_rect[2] > GLOBAL_W or px_rect[3] > GLOBAL_H
                else "inside_global_canvas"
            )
        })

    manifest_path = OUT / "map_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"Global map: {global_path}")
    print(f"Level textures exported: {len(manifest['levels'])}")
    print(f"Manifest: {manifest_path}")
    print("Underground levels and fake_start excluded.")
    print("Coordinates are preserved exactly; no automatic correction applied.")
    print("No game files or Android app files were modified.")


if __name__ == "__main__":
    main()
