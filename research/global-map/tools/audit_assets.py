#!/usr/bin/env python3
"""Audit Anomaly global/local map rectangles and DDS dimensions.

Run from repository root:
  python research/global-map/tools/audit_assets.py
Outputs:
  research/global-map/reports/asset_audit.csv
  research/global-map/reports/asset_audit.txt
"""
from pathlib import Path
import csv
import re
import struct

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "research/global-map/source"
CONFIG = SRC / "configs/game_maps_single.ltx"
LEVELS = SRC / "levels"
TEXTURES = SRC / "textures"

def numbers(value):
    return [float(x.rstrip("fF")) for x in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?f?", value)]

def section(text, name):
    m = re.search(r"(?ms)^\[" + re.escape(name) + r"\]\s*(.*?)(?=^\[|\Z)", text)
    return m.group(1) if m else ""

def dds_size(path):
    try:
        with path.open("rb") as f:
            h = f.read(128)
        if len(h) < 128 or h[:4] != b"DDS ":
            return "", "", "invalid DDS header"
        height, width = struct.unpack_from("<II", h, 12)
        return width, height, ""
    except OSError as e:
        return "", "", str(e)

cfg = CONFIG.read_text(encoding="cp1251", errors="replace")
global_sec = section(cfg, "global_map")
global_bounds = numbers(re.search(r"(?im)^\s*bound_rect\s*=\s*(.+)$", global_sec).group(1))
global_w = global_bounds[2] - global_bounds[0]
global_h = global_bounds[3] - global_bounds[1]

rows = []
excluded = {"fake_start", "jupiter_underground", "labx8", "l03u_agr_underground", "l04u_labx18", "l08u_brainlab", "l10u_bunker", "l12u_control_monolith", "l12u_sarcofag", "l13u_warlab"}
for level_file in sorted(LEVELS.glob("*/level.ltx")):
    level = level_file.parent.name
    if level in excluded:
        continue
    gsec = section(cfg, level)
    if not gsec:
        continue
    gm = re.search(r"(?im)^\s*global_rect\s*=\s*(.+)$", gsec)
    if not gm:
        continue
    grect = numbers(gm.group(1))
    if len(grect) != 4:
        continue
    text = level_file.read_text(encoding="cp1251", errors="replace")
    lm = re.search(r"(?im)^\s*bound_rect\s*=\s*(.+)$", text)
    tm = re.search(r"(?im)^\s*texture\s*=\s*(.+)$", text)
    if not lm or not tm:
        continue
    bound = numbers(lm.group(1))
    if len(bound) != 4:
        continue
    tex_name = tm.group(1).strip().replace("\\", "/").split("/")[-1]
    tex_path = TEXTURES / "map" / (tex_name + ".dds")
    w, h, err = dds_size(tex_path)
    gw, gh = grect[2]-grect[0], grect[3]-grect[1]
    bw, bh = bound[2]-bound[0], bound[3]-bound[1]
    rows.append({
        "level": level, "global_x1": grect[0], "global_z1": grect[1],
        "global_x2": grect[2], "global_z2": grect[3],
        "global_width": gw, "global_height": gh,
        "world_x1": bound[0], "world_z1": bound[1],
        "world_x2": bound[2], "world_z2": bound[3],
        "world_width": bw, "world_height": bh,
        "scale_x": gw/bw if bw else "", "scale_z": gh/bh if bh else "",
        "texture": tex_name, "texture_width_px": w, "texture_height_px": h,
        "dds_status": err or "ok",
        "global_aspect": gw/gh if gh else "",
        "world_aspect": bw/bh if bh else "",
        "texture_aspect": w/h if w and h else "",
    })

out = ROOT / "research/global-map/reports"
out.mkdir(parents=True, exist_ok=True)
csv_path = out / "asset_audit.csv"
with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [])
    writer.writeheader()
    writer.writerows(rows)

ui = TEXTURES / "ui" / "ui_global_map.dds"
uw, uh, ue = dds_size(ui)
report = [
    "# Anomaly map asset audit",
    "",
    f"- Surface entries audited: {len(rows)}",
    f"- Global map DDS: {uw} x {uh} px ({ue or 'ok'})",
    f"- Global logical bounds: {global_w:g} x {global_h:g}",
    f"- Logical-to-pixel scale: X={uw/global_w if uw else 0:.8f}, Y={uh/global_h if uh else 0:.8f}",
    "",
    "## DDS files not read successfully",
]
bad = [r for r in rows if r["dds_status"] != "ok"]
report += [f"- {r['level']}: {r['texture']} — {r['dds_status']}" for r in bad] or ["- none"]
report += ["", "## Potential aspect mismatches", ""]
mismatch = [r for r in rows if r["texture_aspect"] and abs(r["global_aspect"]-r["texture_aspect"]) > 0.015]
report += [f"- {r['level']}: global={r['global_aspect']:.4f}, texture={r['texture_aspect']:.4f}" for r in mismatch] or ["- none"]
report += ["", "CSV contains all raw rectangles, scale ratios, and DDS dimensions."]
(out / "asset_audit.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n".join(report))
print(f"\nCSV: {csv_path}")
