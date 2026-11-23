#!/usr/bin/env python3
"""Build per-level visual diagnostics for Anomaly's surface map tiles.

Requires Pillow. Reads the committed source DDS assets and asset_audit.csv.
Writes per-level comparison panels, a contact sheet, and a CSV summary.
No game files are changed.
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
GLOBAL_W, GLOBAL_H = 1024, 2048
SCALE_Y = GLOBAL_H / LOGICAL_H
EXCLUDED = {
    "fake_start", "jupiter_underground", "labx8", "l03u_agr_underground",
    "l04u_labx18", "l08u_brainlab", "l10u_bunker",
    "l12u_control_monolith", "l12u_sarcofag", "l13u_warlab",
}
PANEL_W, PANEL_H = 900, 540
MARGIN = 18


def rect_for(row):
    x1, x2 = float(row["global_x1"]), float(row["global_x2"])
    z1, z2 = float(row["global_z1"]), float(row["global_z2"])
    # Global map coordinates are north-up in the NORMAL convention.
    return (
        round(x1),
        round(z1 * SCALE_Y),
        round(x2),
        round(z2 * SCALE_Y),
    )


def contain(im, size):
    im = im.convert("RGBA")
    im.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (22, 25, 29, 255))
    canvas.alpha_composite(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    return canvas


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    base = Image.open(GLOBAL_DDS).convert("RGB")
    if base.size != (GLOBAL_W, GLOBAL_H):
        raise RuntimeError(f"Expected global map {GLOBAL_W}x{GLOBAL_H}, got {base.size}")
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["level"] not in EXCLUDED]

    font = ImageFont.load_default()
    panels = []
    summary = []
    for row in rows:
        level = row["level"]
        tile_path = SRC / "textures/map" / (row["texture"] + ".dds")
        if not tile_path.is_file():
            summary.append((level, "missing_texture", "", "", "", "", "", "", "", "", "", ""))
            continue
        tile = Image.open(tile_path).convert("RGBA")
        x1, y1, x2, y2 = rect_for(row)
        clipped = x1 < 0 or y1 < 0 or x2 > GLOBAL_W or y2 > GLOBAL_H
        cx1, cy1 = max(0, x1), max(0, y1)
        cx2, cy2 = min(GLOBAL_W, x2), min(GLOBAL_H, y2)
        if cx2 <= cx1 or cy2 <= cy1:
            summary.append((level, "outside_global_canvas", tile.width, tile.height,
                            x1, y1, x2, y2))
            continue

        # Resize to the exact configured global rectangle. This reproduces
        # the game-map rectangle transform rather than preserving source DDS aspect.
        placed = tile.resize((max(1, x2-x1), max(1, y2-y1)), Image.Resampling.LANCZOS)
        local = placed.crop((cx1-x1, cy1-y1, cx2-x1, cy2-y1))
        global_crop = base.crop((cx1, cy1, cx2, cy2)).convert("RGBA")

        # Three views: source tile, configured global-map crop, and 50% overlay.
        overlay = Image.blend(global_crop, local, 0.5)
        tile_view = contain(tile, (PANEL_W-2*MARGIN, 150))
        crop_view = contain(global_crop, (PANEL_W-2*MARGIN, 150))
        over_view = contain(overlay, (PANEL_W-2*MARGIN, 150))
        panel = Image.new("RGB", (PANEL_W, PANEL_H), (16, 19, 23))
        d = ImageDraw.Draw(panel)
        d.text((MARGIN, 8), f"{level} | DDS {tile.width}x{tile.height} | global rect {x1},{y1} - {x2},{y2}", font=font, fill="white")
        labels = ["SOURCE TILE", "GLOBAL MAP CROP", "50% OVERLAY"]
        views = [tile_view, crop_view, over_view]
        for i, (label, view) in enumerate(zip(labels, views)):
            yy = 30 + i * 132
            d.text((MARGIN, yy), label, font=font, fill=(255, 220, 90))
            panel.paste(view.convert("RGB"), (MARGIN, yy+14))
        out = REPORTS / f"tile_check_{level}.jpg"
        panel.save(out, quality=90, optimize=True)
        panels.append(panel)
        summary.append((
            level, "ok", tile.width, tile.height, x1, y1, x2, y2,
            round(float(row["scale_x"]), 9), round(float(row["scale_z"]), 9),
            round(abs(float(row["scale_x"])-float(row["scale_z"])) /
                  max(float(row["scale_x"]), float(row["scale_z"])) * 100, 4),
            "clipped" if clipped else "inside"
        ))

    # Contact sheet: two columns, enough rows for every surface entry.
    cols = 2
    rows_n = (len(panels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * PANEL_W, rows_n * PANEL_H), (8, 10, 12))
    for i, panel in enumerate(panels):
        sheet.paste(panel, ((i % cols) * PANEL_W, (i // cols) * PANEL_H))
    sheet_path = REPORTS / "tile_diagnostics_contact_sheet.jpg"
    sheet.save(sheet_path, quality=88, optimize=True)

    csv_out = REPORTS / "tile_diagnostics.csv"
    with csv_out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["level", "status", "dds_width", "dds_height",
                    "pixel_x1", "pixel_y1", "pixel_x2", "pixel_y2",
                    "scale_x", "scale_z", "scale_delta_percent", "bounds_status"])
        w.writerows(summary)

    print(f"Surface levels processed: {len(panels)}")
    print(f"Contact sheet: {sheet_path}")
    print(f"Summary CSV: {csv_out}")
    print("Individual panels: tile_check_<level>.jpg")
    print("NOTE: These are configured-rectangle comparisons, not proof of pixel registration.")
    print("No game files were modified.")


if __name__ == "__main__":
    main()
