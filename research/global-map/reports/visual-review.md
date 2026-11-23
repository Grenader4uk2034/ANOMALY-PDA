# Global map visual review

Branch reviewed: `global-map-tile-diagnostics-alpha`

## Scope

Reviewed all 24 surface-level diagnostic panels regenerated with alpha-aware compositing. Underground levels and `fake_start` remain excluded. No game assets or runtime configuration were changed.

## Visual findings

At the displayed panel scale, no gross placement or orientation failure is apparent across the 24 configured rectangles. Major terrain patterns, road corridors, settlement footprints, and distinctive structures are broadly consistent between each source DDS tile and the corresponding global-map crop.

This is a qualitative visual screening only. It is not a pixel-registration measurement.

## Bounds findings

Three configured rectangles extend beyond the 1024x2048 global-map canvas:

| Level | Pixel rectangle | Overflow |
|---|---:|---:|
| `k02_trucks_cemetery` | (706,1075)-(1025,1324) | 1 px right |
| `l09_deadcity` | (-6,949)-(248,1152) | 6 px left |
| `l13_generators` | (195,-31)-(414,139) | 31 px top |

These are small edge overflows relative to the map canvas. Do not clamp or modify the source rectangles without evidence from the game configuration or engine behavior.

## Scale review

The largest X/Z scale difference in the CSV is `l02_garbage` at 1.3158%. Other notable values are `y04_pole` at 0.8180%, `l10_limansk` at 0.4310%, and `l11_pripyat` at 0.4954%. These differences alone do not justify changing map rectangles or applying per-level corrections.

## Critical limitation of the diagnostic method

The diagnostic script resizes each source tile to the configured `global_rect` before compositing it over the global-map crop. This verifies whether the resulting appearance is plausible, but it does not independently derive or validate the rectangle coordinates. In addition, this panel set tests only the normal-Y placement; it does not constitute an A/B test of normal versus flipped Y.

Therefore:
- no coordinate corrections are recommended from this review;
- normal-Y remains a working hypothesis, not a proven engine convention;
- pixel-accurate registration and Y-axis direction remain open verification tasks.

## Recommended next research step

Use independent map landmarks or engine-side map transform code to verify the global coordinate-to-texture transform. Compare at least two non-collinear landmarks per level where possible. Keep all findings and scripts under `research/global-map/`; do not modify game assets.
