# Global map coordinate audit — preliminary

Source: Anomaly assets committed under `research/global-map/source/`.
Branch: `main`.
Scope: surface levels only. Underground levels are intentionally excluded from the surface placement table.

## Global texture

- Texture: `textures/ui/ui_global_map.dds`
- DDS dimensions recorded during prior inspection: 1024 × 2048 px.
- `[global_map]` `bound_rect = 0, 0, 1024, 2634`.
- Logical-to-pixel scale: X = 1 px per logical unit; Y = 2048 / 2634 = 0.777525 px per logical unit.
- Therefore the logical global-map rectangle is not the same height as the bitmap. Do not treat logical Y coordinates as bitmap pixel Y values without this conversion.

## Surface-level comparison

For each level:
- `global_rect` comes from `configs/game_maps_single.ltx`.
- `bound_rect` and texture come from that level's `levels/<level>/level.ltx`.
- `R_x` = global_rect width / level bound_rect width.
- `R_z` = global_rect height / level bound_rect height.

| Level | Global rect (x1,z1,x2,z2) | Local bound rect (x1,z1,x2,z2) | R_x | R_z | Local texture |
|---|---|---|---:|---:|---|
| jupiter | 277,783,459,965 | -600,-600,600,600 | 0.1517 | 0.1517 | map_jupiter |
| k00_marsh | 22,2113,352,2443 | -445,-445,755,755 | 0.2750 | 0.2750 | map_marsh |
| k01_darkscape | 701,2071,1020,2392.344727 | -702,-704.09,708.5,716.778 | 0.2262 | 0.2262 | map_k01_darkscape |
| k02_trucks_cemetery | 706,1382,1025,1703.344727 | -543.947936,-472.688896,387.098880,467.011776 | 0.3426 | 0.3420 | map_k02_trucks_cemetery |
| l01_escape | 358,2022,564,2434 | -335,-630,415,870 | 0.2747 | 0.2747 | map_escape |
| l02_garbage | 369,1776,573,1980 | -370,-422,370,327.866848 | 0.2757 | 0.2720 | map_garbage |
| l03_agroprom | 164,1848,332,2016 | -275,-370,335,240 | 0.2754 | 0.2754 | map_agroprom |
| l04_darkvalley | 728,1705,852,1953 | -215,-665,235,235 | 0.2756 | 0.2756 | map_l04_darkvalley |
| l05_bar | 407,1414,556,1712 | 0,-512.030,512,512.001 | 0.2910 | 0.2910 | map_l05_bar |
| l06_rostok | 258,1414,407,1712 | -512,-512.030,0,512.001 | 0.2910 | 0.2910 | map_l06_rostok |
| l07_military | 425,1231,590,1396 | -420,-105,180,495 | 0.2750 | 0.2750 | map_l07_military |
| l08_yantar | 101,1572,249,1720 | -270,-405,270,135 | 0.2741 | 0.2741 | map_l08_yantar |
| l09_deadcity | -6,1220,248,1481 | -481.497344,-412.284256,379.976288,474.479296 | 0.2948 | 0.2943 | map_l09_deadcity |
| l10_limansk | 66,874,182,1105 | -210,-415,210,425 | 0.2762 | 0.2750 | map_limansk |
| l10_radar | 527,975,769,1218.704712 | -320.405472,-658.741120,890.625152,557.681216 | 0.1998 | 0.2003 | map_l10_radar |
| l10_red_forest | 198,1028,380,1210 | -285,-485,375,175 | 0.2758 | 0.2758 | map_red_forest |
| l11_hospital | 194,694,246,798 | -180,537,10,917 | 0.2737 | 0.2737 | map_hospital |
| l11_pripyat | 607,762,740,909 | -628.133056,-520.743040,671.867200,779.257088 | 0.1023 | 0.1131 | map_l11_pripyat |
| l12_stancia | 322,298,728,495 | -600.104960,-747.782016,1729.649920,850.523136 | 0.1743 | 0.1233 | map_aes_1 |
| l12_stancia_2 | 322,101,728,298 | -603.302016,-930.571136,1729.649920,966.970176 | 0.1740 | 0.1038 | map_aes_2 |
| l13_generators | 195,-40,414,179 | -525.205024,-853.156224,540.927424,209.523920 | 0.2054 | 0.2061 | map_l13_generators |
| zaton | 291,574,473,756 | -600,-615,600,585 | 0.1517 | 0.1517 | map_zaton |
| pripyat | 679,718,888,927 | -550,-550,550,550 | 0.1900 | 0.1900 | map_pripyat |
| y04_pole | 457,1965,698.98,2205 | -544.541120,-615.296064,555.461440,484.704160 | 0.2200 | 0.2182 | map_y04_pole |

## Findings

1. There is no single world-to-global scale shared by all surface levels. Observed ratios range from about 0.102 to 0.343.
2. Several level pairs show matching X/Z ratios and matching aspect ratios (for example Marsh, Escape, Agroprom, Military, Yantar, Red Forest, Hospital). Others differ, notably Jupiter, Zaton, Radar, Dead City, Pripyat, and the AES levels.
3. This table is an audit of declared rectangles, not yet a visual proof of correct bitmap alignment. It does not assume that local world bounds are transformed by one global affine transform.
4. The global texture's logical Y range (2634) must be converted to bitmap pixels (2048) when generating an overlay or pixel-space report.
5. Underground entries, including the one-unit placeholder global rectangles, are omitted from surface placement.

## Next validation required

- Read DDS headers for every referenced surface texture and record exact width/height.
- Decode the global DDS and produce a diagnostic overlay using the declared global rectangles.
- Check map orientation and edge alignment visually; do not alter original assets or app code during this research stage.
