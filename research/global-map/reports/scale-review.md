# Global map scale review

## Scope

Review of the four entries previously flagged by the asset audit for a possible aspect-ratio mismatch. This is a metadata/coordinate review, not a pixel-perfect validation against the in-game PDA.

## Coordinate orientation

The global logical map uses bounds 1024 x 2634 and the global texture is 1024 x 2048. Therefore the logical-to-pixel scale is:

- X: 1.0 px per logical unit
- Z/Y: 2048 / 2634 = 0.77752468 px per logical unit

The normal Z placement is consistent with the world layout: northern AES/Stancia entries are at the top, while southern Marsh/Escape entries are at the bottom. The flipped variant reverses this north-south arrangement and is not suitable.

Use the normal orientation for subsequent work:
- pixel_x = global_x
- pixel_y = global_z * 2048 / 2634

## Review of flagged entries

The global rectangle aspect ratio is compared with the DDS texture aspect ratio. The world rectangle aspect ratio is also included because the game map texture is mapped to the level's world bounds; a non-square world rectangle can legitimately stretch a square texture.

| Level | Global aspect | World aspect | DDS aspect | scale X | scale Z | X/Z scale delta |
|---|---:|---:|---:|---:|---:|---:|
| l09_deadcity | 0.973180 | 0.971481 | 1.000000 | 0.294844 | 0.294329 | +0.175% |
| l11_pripyat | 0.904762 | 0.900280 | 1.000000 | 0.120443 | 0.119847 | +0.498% |
| l12_stancia | 2.060914 | 2.064814 | 2.000000 | 0.245582 | 0.246047 | -0.189% |
| l12_stancia_2 | 2.060914 | 2.066419 | 2.000000 | 0.245433 | 0.246089 | -0.266% |

## Findings

1. The four aspect-ratio flags do not, by themselves, indicate a bad texture or incorrect placement. The source DDS dimensions differ slightly from the world/global rectangle proportions, which is compatible with the game stretching a map texture over its configured world bounds.
2. The X/Z scale deltas are small: 0.175%, 0.498%, 0.189%, and 0.266% in absolute value. They should be treated as coordinate/config precision differences until an in-game reference proves otherwise.
3. Do not force square tiles or preserve DDS aspect ratio when placing these textures. The current overlay's resize-to-global-rectangle behavior is intentional for this diagnostic.
4. The visual overlay is still only a rectangle-based placement check. It does not prove pixel-level alignment, rotation, crop, or internal map-content alignment.

## Decision

- Keep the NORMAL north-up placement for the next research stage.
- Do not apply corrective scaling to these four levels based only on aspect ratio.
- Keep the four entries marked as low-level visual verification items, not confirmed errors.
- Exclude underground levels and fake_start as before.
- No game files or runtime assets were modified.
