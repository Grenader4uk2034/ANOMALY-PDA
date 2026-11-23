# OpenXRay global map transform audit

Date: 2026-11-23

## Source examined

Primary implementation: OpenXRay xray-16, commit e973013044fd9afcfa4eb214a811988d14b71a0d.

- [UIMap.cpp — full implementation](https://github.com/OpenXRay/xray-16/blob/e973013044fd9afcfa4eb214a811988d14b71a0d/src/xrGame/ui/UIMap.cpp)
- [UIMap.h — map class declarations and zoom calculation](https://github.com/OpenXRay/xray-16/blob/e973013044fd9afcfa4eb214a811988d14b71a0d/src/xrGame/ui/UIMap.h)
- [Historical OpenXRay xray-15 UIMap.cpp](https://github.com/OpenXRay/xray-15/blob/ad7b68b700d73abf6487675ab5905c06617a714a/cs/engine/xrGame/ui/UIMap.cpp)

Important provenance limitation: the public xray-16 commit inspected here is not the Android build commit from the user's log (cced8b0b48c28e11006cdf686be407f92763a006). It is direct upstream implementation evidence, not proof that the Android fork has no local changes.

## 1. Global map coordinate transform

In CUIGlobalMap::ConvertRealToLocal, the engine computes:

    res.x = (src.x - BoundRect().lt.x) * GetCurrentZoom().x;
    res.y = (src.y - BoundRect().lt.y) * GetCurrentZoom().x;

There is no Y inversion in the global-map transform. Both coordinates are translated by the top-left of the global map's logical bound_rect and multiplied by the current uniform map zoom.

The function is used by CUILevelMap::Update() to convert GlobalRect().lt and GlobalRect().rb into the displayed rectangle of each level map. Therefore global_rect is already expressed in the global map's 2D UI/texture coordinate system (top-left origin, Y increasing down), not in world X/Z coordinates.

## 2. Global rectangle loading

In CUILevelMap::Init_internal, the engine reads:

    Fvector4 tmp = pGameIni->r_fvector4(MapName(), "global_rect");
    tmp.x *= UI().get_current_kx();
    tmp.z *= UI().get_current_kx();
    m_GlobalRect.set(tmp.x, tmp.y, tmp.z, tmp.w);

The rectangle's horizontal endpoints are scaled by the UI horizontal scale factor. The vertical endpoints are left in the logical global-map coordinate system. This is UI layout scaling; it is not a geographic Y flip.

The same function calculates:

    kw = m_GlobalRect.width() / BoundRect().width();
    kh = m_GlobalRect.height() / BoundRect().height();

and emits an incorrect global rect definition diagnostic when the horizontal and vertical scale ratios differ beyond the engine tolerance. The diagnostic suggests adjusting either x2 or y2. This directly confirms that the engine expects the level map's world-bound aspect and its global-rectangle aspect to agree.

## 3. Do not confuse global-map Y with world-Z conversion

The local level-map transform is different. In CUICustomMap::ConvertRealToLocalNoTransform, the engine computes:

    res.x = (src.x - bound_rect.lt.x) * GetCurrentZoom().x;
    res.y = (bound_rect.height() - (src.y - bound_rect.lt.y)) * GetCurrentZoom().x;

Here src.y represents world Z for map locations. The subtraction from bound_rect.height() deliberately flips world Z into top-down texture/UI Y.

That world-to-local-map inversion must not be applied a second time to global_rect. Global rectangles are already top-down map UI coordinates.

## 4. Implication for the Anomaly global texture

Given the audited global logical bounds (0, 0) - (1024, 2634) and texture size 1024 x 2048, the global logical-to-texture mapping is:

    pixel_x = logical_x
    pixel_y = logical_y * (2048 / 2634)

No 2634 - logical_y term is used for global_rect placement.

Thus the existing normal overlay convention is supported by the engine implementation. The flip_y alternative is not the correct transform for placing level global_rect rectangles on the global map texture.

## 5. What this establishes — and what it does not

Established from the inspected xray-16 source:
- Global-map global_rect Y is top-down and is not inverted by CUIGlobalMap::ConvertRealToLocal.
- World Z to a local level-map texture Y is inverted separately.
- Engine code checks the ratio of a level's global rectangle to its local bound_rect and warns about mismatches.
- No reason exists to flip global rectangles vertically.

Not yet established:
- Whether the Android port's exact commit has local changes to UIMap.cpp.
- Pixel-perfect registration of every source DDS tile against the global texture.
- Whether any individual Anomaly global_rect needs correction. Do not edit map coordinates based only on the previous resized overlays.

## 6. Recommended next validation

Compare the Android port source at commit cced8b0b48c28e11006cdf686be407f92763a006 (or its exact source fork) against the functions above. Then run a numeric aspect audit using the engine's own kw / kh criterion for all 24 surface levels and rank any deviations. Keep all generated reports and scripts under research/global-map/; do not alter game assets.

## 7. Numeric aspect-ratio ranking from the 24-level audit

Using the existing asset audit CSV, the engine's two scale ratios were recomputed as:

- kw = global_rect.width / local bound_rect.width
- kh = global_rect.height / local bound_rect.height

Ranked by relative difference between kw and kh:

| Level | kw | kh | Relative difference |
|---|---:|---:|---:|
| l02_garbage | 0.27567568 | 0.27204830 | 1.3245% |
| y04_pole | 0.21998131 | 0.21818177 | 0.8214% |
| l11_pripyat | 0.12044341 | 0.11984679 | 0.4966% |
| l10_limansk | 0.27619048 | 0.27500000 | 0.4320% |
| l13_generators | 0.20541538 | 0.20608271 | 0.3243% |
| l12_stancia_2 | 0.24543349 | 0.24608912 | 0.2668% |
| k02_trucks_cemetery | 0.34262509 | 0.34196499 | 0.1928% |
| l12_stancia | 0.24558194 | 0.24604673 | 0.1891% |
| l09_deadcity | 0.29484362 | 0.29432874 | 0.1748% |

The other 15 levels are equal or differ by no more than 0.0031% in this calculation.

This ranking is a prioritization aid, not an automatic correction list. The engine uses its own fsimilar(kw, kh, EPS_L) comparison (an absolute tolerance), so relative percentages alone do not establish which levels actually emit the runtime warning. The exact EPS_L value and the Android fork's implementation still need to be confirmed before claiming engine-warning parity.

Highest-priority candidates for source/config comparison are l02_garbage and y04_pole, followed by l11_pripyat and l10_limansk. Do not change their coordinates yet.

## 8. Android-oriented OpenXRay source cross-check

A second public source was inspected:

- [Eternal-Entropia/openxray-android — UIMap.cpp](https://github.com/Eternal-Entropia/openxray-android/blob/1b84cfbc5efa3e9af942164e5a3c2dde43b77f51/src/xrGame/ui/UIMap.cpp)
- [Eternal-Entropia/openxray-android — math_constants.h](https://github.com/Eternal-Entropia/openxray-android/blob/1b84cfbc5efa3e9af942164e5a3c2dde43b77f51/src/xrCore/math_constants.h)
- [TmLev/xray-16 — UIMap.cpp](https://github.com/TmLev/xray-16/blob/tmlev/shadow-of-chernobyl/src/xrGame/ui/UIMap.cpp)

The Android-oriented public source has the same relevant implementation:
- global map X and Y are both translated from BoundRect().lt and multiplied by the global zoom; no Y flip;
- CUILevelMap::Update() converts GlobalRect().lt and .rb through that global transform;
- world-to-local-map conversion separately inverts the second world coordinate (Z) using bound_rect.height().

The public Android-oriented source defines EPS_L as 0.0010000f. Its aspect check is inside #ifdef DEBUG and compares kw and kh using fsimilar. Therefore this diagnostic is a DEBUG-build check; absence of the warning in a release log does not prove that all ratios are exact.

### Exact absolute-tolerance result

The engine comparison is absolute, not relative. For the 24 surface entries, compare abs(kw - kh) against 0.001:

| Level | abs(kw - kh) | Exceeds EPS_L? |
|---|---:|---|
| l02_garbage | 0.00362738 | Yes |
| y04_pole | 0.00179953 | Yes |
| l10_limansk | 0.00119048 | Yes |
| l11_pripyat | 0.00059662 | No |
| l13_generators | 0.00066733 | No |
| k02_trucks_cemetery | 0.00066011 | No |
| l12_stancia_2 | 0.00065563 | No |
| l12_stancia | 0.00046479 | No |
| l09_deadcity | 0.00051487 | No |

All remaining 15 levels are at or below 0.00000881 in absolute difference.

Thus only three of the 24 entries exceed the public Android-oriented source's EPS_L threshold: l02_garbage, y04_pole, and l10_limansk. This identifies config entries worth checking; it does not prove they are visually wrong or authorize coordinate edits.

### Exact-build provenance limitation

The build log supplied earlier identifies commit cced8b0b48c28e11006cdf686be407f92763a006. GitHub does not resolve that SHA in Eternal-Entropia/openxray-android, and global GitHub commit search did not locate it. Therefore the public Android-oriented source is a close corroborating implementation, but cannot be claimed as the exact source tree for that binary. Exact parity with the logged Android build remains unverified.

No source game files or map coordinates were changed.

## 9. Additional cross-check against the Stalker Mobile source repository

The project repository linked by the Stalker Mobile OpenXRay Android port documentation was located:

- [stalkermobile/openxray-mobile — UIMap.cpp](https://github.com/stalkermobile/openxray-mobile/blob/master/src/xrGame/ui/UIMap.cpp)
- [stalkermobile/openxray-mobile — math_constants.h](https://github.com/stalkermobile/openxray-mobile/blob/master/src/xrCore/math_constants.h)
- [stalkermobile/openxray-mobile — repository](https://github.com/stalkermobile/openxray-mobile)

The checked-in `UIMap.cpp` independently contains the same relevant formulas:
- `CUIGlobalMap::ConvertRealToLocal()` maps both X and Y by subtracting the global `BoundRect().lt` and multiplying by zoom; it does not invert Y.
- `CUILevelMap::Update()` converts `GlobalRect().lt/rb` through that global transform.
- `CUICustomMap::ConvertRealToLocalNoTransform()` separately inverts world Z for local level-map coordinates.
- `CUILevelMap::Init_internal()` computes `kw` and `kh` and, under `#ifdef DEBUG`, compares them with `fsimilar(..., EPS_L)`.
- The checked-in `math_constants.h` defines `EPS_L = 0.0010000f`.

This is a third matching implementation (alongside upstream xray-16 and Eternal-Entropia/openxray-android). It strengthens confidence in the transform and tolerance interpretation for this family of ports.

### Exact binary/source match still not proven

The build-log SHA `cced8b0b48c28e11006cdf686be407f92763a006` was queried directly in:
- `Eternal-Entropia/openxray-android`
- `stalkermobile/openxray-mobile`
- several publicly indexed Android OpenXRay repositories/forks

GitHub returned no matching commit in those repositories, and global commit search returned no result. The Stalker Mobile repository's visible history is old relative to the Android build log. Therefore these source trees corroborate the map-transform implementation, but none can be identified as the exact source snapshot used to build the logged APK.

### Updated conclusion

The no-flip global-map Y transform is corroborated by three separate source trees, including the repository published under the Stalker Mobile account. The separate world-Z inversion is also present in all inspected implementations.

For the 24 Anomaly surface levels, the public engine tolerance test flags exactly three entries: `l02_garbage`, `y04_pole`, and `l10_limansk`. These remain config-review candidates only. No `global_rect`, `bound_rect`, game asset, or runtime source was changed.
