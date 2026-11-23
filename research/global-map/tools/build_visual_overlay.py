#!/usr/bin/env python3
"""Build visual global-map overlays from audited DDS assets.
Run: python research/global-map/tools/build_visual_overlay.py
Requires Pillow with DDS support.
Outputs in research/global-map/reports/:
  global_map_overlay_normal.png
  global_map_overlay_flip_y.png
"""
from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "research/global-map/source"
REPORTS = ROOT / "research/global-map/reports"
CSV_PATH = REPORTS / "asset_audit.csv"
GLOBAL_DDS = SRC / "textures/ui/ui_global_map.dds"
LOGICAL_W, LOGICAL_H = 1024.0, 2634.0
PX_W, PX_H = 1024, 2048
SCALE_X, SCALE_Y = PX_W / LOGICAL_W, PX_H / LOGICAL_H
EXCLUDED = {"fake_start", "jupiter_underground", "labx8", "l03u_agr_underground",
            "l04u_labx18", "l08u_brainlab", "l10u_bunker",
            "l12u_control_monolith", "l12u_sarcofag", "l13u_warlab"}

def build(flip_y: bool, output: Path):
    base = Image.open(GLOBAL_DDS).convert("RGBA")
    if base.size != (PX_W, PX_H):
        raise RuntimeError(f"Unexpected global map size: {base.size}")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        level = row["level"]
        if level in EXCLUDED:
            continue
        tex = SRC / "textures/map" / (row["texture"] + ".dds")
        if not tex.is_file():
            print(f"SKIP missing: {level} -> {tex.name}")
            continue
        try:
            tile = Image.open(tex).convert("RGBA")
        except Exception as e:
            print(f"SKIP unreadable: {level} -> {e}")
            continue
        x1 = round(float(row["global_x1"]) * SCALE_X)
        x2 = round(float(row["global_x2"]) * SCALE_X)
        z1 = float(row["global_z1"])
        z2 = float(row["global_z2"])
        y1 = round((LOGICAL_H - z2 if flip_y else z1) * SCALE_Y)
        y2 = round((LOGICAL_H - z1 if flip_y else z2) * SCALE_Y)
        left, right = sorted((max(0, x1), min(PX_W, x2)))
        top, bottom = sorted((max(0, y1), min(PX_H, y2)))
        if right <= left or bottom <= top:
            print(f"SKIP outside canvas: {level}")
            continue
        tile = tile.resize((right-left, bottom-top), Image.Resampling.LANCZOS)
        tile.putalpha(tile.getchannel("A").point(lambda a: int(a * 0.62)))
        overlay.alpha_composite(tile, (left, top))
        draw.rectangle((left, top, right-1, bottom-1), outline=(255, 40, 40, 230), width=2)
        draw.text((left+3, top+3), level, fill=(255, 255, 0, 255), font=font,
                  stroke_width=1, stroke_fill=(0, 0, 0, 255))
    result = Image.alpha_composite(base, overlay).convert("RGB")
    result.save(output, optimize=True)
    print(f"CREATED {output} ({result.width}x{result.height})")

if __name__ == "__main__":
    REPORTS.mkdir(parents=True, exist_ok=True)
    build(False, REPORTS / "global_map_overlay_normal.png")
    build(True, REPORTS / "global_map_overlay_flip_y.png")
