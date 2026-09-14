# Texture Style Findings — vanilla munitions vs. custom models

Measured from the game's shipped textures and materials on 2026-09-13.
Source data: `reference/vanilla_textures/` (gitignored; regenerate with
`tools/dump_weapon_textures.py` + `tools/analyze_weapon_textures.py`).

## 1. Vanilla texture system (measured)

**Shared atlas families** — vanilla munitions do not use per-weapon textures; each
weapon maps into one shared atlas. Materials are white-tinted URP Lit
(`_BaseMap`/`_BumpMap`/`_MetallicGlossMap`/`_OcclusionMap`), except the newer
`Weapons5`-style material which adds a `_Paint` mask multiplied by a gray
`_BaseColor` (0.3585) — that is the faction-recolor channel (`ColorableMount` →
`WeaponManager.RegisterColorable`).

| Atlas | Size | Used by (runtime dump) | Mean metal (R) | Mean smooth (A) |
|---|---|---|---|---|
| weapons1 | 1024 | `rocket4`, `agm1` (some variants), `bomb1` | 0.061 | 0.358 |
| weapons2 | 512 | `ASHM1` | 0.069 | 0.619 |
| weapons3 | 1024 | `rocket1`, `rocket4`, `agm1`, `bomb`, `bomb1` | 0.178 | 0.420 |
| weapons4 | 512 | `agm1` (a variant) | 0.040 | 0.597 |
| weapons5 | 512 | (paint-mask weapons) | 0.077 | 0.631 |
| missiles1 | 512 | `AGM1`, `AGM_heavy`, `aam1`, `missile1` | 0.051 | 0.403 |
| missiles2 | 1024 | `ASHM1`, `missile1` | 0.025 | 0.536 |
| **missiles3** | **1024** | **`aam3`, `aam4` (Scimitar), `AAM2` (Scythe), `ASHM2`, `ashm3`** | **0.070** | **0.417** |
| missiles4 | 512 | `AGM2`, `rocket3` (+ `_o` emissive) | 0.158 | 0.481 |
| bombs1 | 512 | `bomb250`, `bomb500`, `bomb` | 0.035 | 0.290 |
| ballisticMissile1 | 512 | `ballisticMissile1` | 0.156 | 0.473 |

Packaging notes (from `materials.json`): `weapons1` uses legacy
`_MainTex`/`_MetallicGlossMap`/`_OcclusionMap` slots; all newer atlases use
`_BaseMap`/`_BumpMap`/`_MetallicGlossMap`/`_OcclusionMap`. `_m` maps pack
metallic in R and smoothness in A (means above).

**Dominant palettes (k-means k=8, luminance-sorted, sRGB 0-255):**

- `missiles3` (Scimitar + Scythe + AAM-3 + AShM-2/3 — our analog family):
  33,31,29 · 74,69,65 · 92,89,86 · 106,108,111 · 117,116,117 · 127,125,125 ·
  150,149,148 · **228,193,94** (yellow-ochre accent)
- `weapons1`: 44,42,41 · 73,72,70 · 81,80,79 · 89,85,82 · 99,94,91 ·
  120,119,119 · **167,160,121** (olive-yellow) · 209,208,208
- `missiles4` (AGM-2): near-white + charcoal + **162,22,19** (red accent)
- `bombs1`: olive grays + **225,140,40** (orange accent)
- `ballisticMissile1`: charcoal + **239,119,19** (orange) + 105,50,20 (rust)

## 2. Art-style language (visual inventory of `missiles3`/`weapons1`/`bombs1`)

1. **Base:** mid-value gray, cool and slightly blue for missiles3 (106-127 with
   B≥R), warmer gray-brown for weapons1. Panels are large and flat.
2. **Value range:** every atlas spans near-black (24-47) to near-white
   (205-240); contrast comes from large panel groups, not noise.
3. **Panel lines:** thin dark seams (1-2 px) subdividing panels; occasional
   dashed outlines marking service panels/access doors.
4. **Stencils:** small uppercase microtext, usually black on light panels and
   white on dark: weapon designation ("AAM-29 SCYTHE", "AGM-95/SGM-SG",
   "RAM-45", "R15-45R49"), "LOCK"/"UNLOCK", "OPEN"/"CLOSED", "DANGER",
   "CAUTION", "REMOVE BEFORE FLIGHT"-style strips, lot/part numbers, hazard
   triangles (radiation trefoil, warning triangle), X-in-box (component) marks,
   red diamonds, up-arrows, small barcode blocks.
5. **Accents:** saturated yellow/ochre bands or corner marks (yellow used as
   the faction-tint channel on weapons5), orange band on bombs, red on AGM.
6. **Grunge:** subtle — faint vertical streaks, dust speckle, edge wear on
   panel borders; never large-scale rust or heavy scorching. AO is baked into
   albedo corners + a separate AO map.
7. **Rivets:** small dark dots in rows along structural seams.
8. **Metallic:** LOW everywhere (means 0.03-0.18) — vanilla munitions read as
   painted composite, not bare metal. Smoothness means 0.29-0.63 (semi-matte
   paint, glossier on weapons2/5).

## 3. Current custom models vs. the vanilla language

| Model | Today | Gap |
|---|---|---|
| AAM-44 Halberd | Cylindrical-UV body/booster; procedural 512×128 banded albedo (`HalberdTexturePreviewBuilder`); flat materials elsewhere | Bands/colors already close; missing seam density, stencil text, rivets, grunge, AO; nose charcoal too pure; no packed m/s variation |
| IRM-S4 Kris | Per-quad 0-1 UVs only; five flat materials (clearcoat seeker) | No texture at all; needs cylindrical-wrap UVs + light stencil set |
| AGM-110 Ballista | No UVs; ten flat materials from STEP palette | Needs UV generation + darker AGM-family treatment + wing stencils |

Measured deltas vs. `missiles3`/`weapons3` family:
- Our flat colors (Kris body 0.63 gray, Ballista body 0.12-0.15 dark) sit in
  the vanilla value range, but uniform color reads "untextured" next to
  vanilla's 4-6 value bands per weapon.
- Our metallic 0.1-0.35 uniform is too high for painted bodies (vanilla mean
  0.03-0.16); keep higher values only for dark hardware/nozzles.

## 4. Target texture spec for custom weapons

- Shader: URP Lit, white tint, single albedo + optional packed metallic(r)/smoothness(a) map + AO map — mirroring the vanilla material layout.
- Palette: sample base grays from `missiles3`/`weapons3` (charcoal 35 →
  mid-gray 110 → light 150-170); one saturated accent per weapon (Halberd
  yellow-ochre 228,193,94; Ballista red/orange; Kris minimal accents).
- Markings: designation stencils ("AAM-44 HALBERD", "IRM-S4", "AGM-110"),
  LOCK/UNLOCK arcs, OPEN/CLOSED, X-in-box service marks, dashed service-panel
  outlines, hazard triangles, lot/barcode strips.
- Detail: panel seam lines with rivet dots, faint streak grunge, baked-in AO
  shading near seams; normal maps optional (defer).
- Textures are **original** work matching this language — vanilla atlases are
  reference-only and never ship in our bundle.

## 5. Data provenance

- Extraction: `tools/dump_weapon_textures.py` (UnityPy 1.25.3, FALLBACK_UNITY_VERSION 2022.3.62f2) over `resources.assets`, `sharedassets0-4.assets`, and both StreamingAssets `.bundle`s; 47 PNGs + `inventory.json`, `materials.json`, `prefabs.json`.
- Prefab→atlas mapping from the in-game renderer dump; placeholders in
  Blueprinter `_donotship` verified pixel-identical (normal maps differ only in
  channel swizzle; game-extracted copies kept).
- Palette measurements: `tools/analyze_weapon_textures.py` →
  `palette_measurements.json`, swatch committed at `docs/palette_swatch.png`.
- Mesh UVs are not recoverable offline (UnityPy cannot read streamed vertex
  data for these meshes); UVs come from the runtime dumper
  (`MissileGeometryDumper` v2, obj `vt` lines + `uvBounds`).
