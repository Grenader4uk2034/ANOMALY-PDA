# Global map aspect-ratio correction candidates

Date: 2026-11-23

## Purpose

This report calculates the two alternative endpoint values suggested by the OpenXRay DEBUG aspect check for the three surface-level entries that exceed the public Android source's absolute tolerance `EPS_L = 0.001`.

No game configuration or coordinate is changed by this report.

## Engine calculation

For each level:

- `kw = global_rect.width / bound_rect.width`
- `kh = global_rect.height / bound_rect.height`

The engine diagnostic suggests either:
- preserve the current vertical ratio and set `x2 = x1 + kh * bound_rect.width`, or
- preserve the current horizontal ratio and set `y2 = y1 + kw * bound_rect.height`.

These are alternatives, not simultaneous corrections. Choosing one requires independent evidence about which source endpoint is authoritative.

## Candidate values

| Level | Current x2 | Candidate x2 (preserve kh) | Current y2 | Candidate y2 (preserve kw) | abs(kw-kh) |
|---|---:|---:|---:|---:|---:|
| l02_garbage | 573.000000 | 570.315741 | 1980.000000 | 1982.720050 | 0.003627377 |
| y04_pole | 698.980000 | 697.000510 | 2205.000000 | 2206.979486 | 0.001799532 |
| l10_limansk | 182.000000 | 181.500000 | 1105.000000 | 1106.000000 | 0.001190476 |

## Interpretation

- `l02_garbage`: both alternative endpoint changes are about 2.7 logical units. This is the strongest mismatch by the engine's absolute criterion.
- `y04_pole`: both alternatives change the endpoint by about 1.98 logical units.
- `l10_limansk`: the alternatives are small (0.5 in x2 or 1.0 in y2), but still exceed the engine's absolute tolerance.

## Decision status

**Do not apply these values automatically.** The DEBUG check only establishes that the two configured scale ratios differ beyond the engine tolerance. It does not identify which endpoint is wrong, and the visual diagnostic stretches the source tile to the configured rectangle, so it cannot settle that question.

Before changing any `global_rect`, compare the exact original Anomaly configuration values and map-tile landmarks/edges at native scale. Keep all candidates as research data until that independent validation is available.

No game files, `global_rect`, `bound_rect`, application assets, or runtime source were modified.
