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
| AAM-44 Halberd | Cylindrical-UV body/booster; procedural 2048×1024 banded albedo + packed MS (`HalberdTexturedMaterialBuilder`); five plain part families share one tinted microsurface pair | Bands/colors close; no stencil text (user preference); preview comparison now uses extracted reference atlases + runtime UVs |
| IRM-S4 Kris | Cylindrical-UV body; procedural 2048×1024 albedo + packed MS (`KrisTexturedMaterialBuilder`); flat materials elsewhere | No stencil text (user preference); optional normal/AO maps deferred |
| AGM-110 Ballista | Cylindrical-UV airframe + planar-UV wings/fins; procedural 2048×1024 albedo + packed MS (`BallistaTexturedMaterialBuilder`); light blue-gray seams for dark-base readability | No stencil text (user preference); optional normal/AO maps deferred |

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

## 6. Texture pass updates (2026-09-14)

Changes verified by the headless bundle build + in-process validator
(`MunitionsGeometryBundleBuilder.ValidateBundle`):

- **Packed MS maps are linear data.** All three `*TexturedMaterialBuilder.cs`
  files now create packed metallic(R)/smoothness(A) textures with
  `linear: true` (`FinishTexture(..., linear)`); albedo stays sRGB
  (`linear: false`). The bundle validator asserts albedo is sRGB and the
  packed map is linear via `GraphicsFormatUtility.IsSRGBFormat` on the loaded
  bundle textures (albedo `R8G8B8A8_SRGB`, packed `R8G8B8A8_UNorm`).
- **Halberd plain microsurface pair is shared.** The five plain part families
  (intakes, sustainer fins, hardware, sustainer nozzle, booster fins) now
  reference one saved `TexHalberdPlainAlbedo`/`TexHalberdPlainMS` pair instead
  of five duplicate saves; only the material tint differs. The validator
  checks all five bind the same two texture instances.
- **Ballista dark-palette readability.** The approved dark blue-gray base
  colors are unchanged, but the detail ink switched from near-black
  (`SeamDark` 30,29,28 — invisible on the 31,38,41 base) to a lighter
  blue-gray `SeamLight` (0.28, 0.33, 0.36). Panel seams, rivets, and the
  body service marks now read as light panel-gap lines on the dark airframe.
- **Ballista wing/fin UVs are planar.** The six flat `_wing` meshes
  (WingLeft/Right + TailControl1-4) use a planar XZ unwrap (u along local x,
  v along local z) instead of the cylindrical z-axis unwrap, which degenerates
  on flat panels (u = atan2(y,x) is nearly constant per face and mirrors
  across the chord centerline). The validator checks corr(u,x) > 0.9 and
  corr(v,z) > 0.9 per wing mesh.
- **Halberd preview comparison is honest.** `HalberdTexturePreviewBuilder`
  no longer paints fake procedural "reference" materials or discards the
  runtime UVs. It loads the game's extracted atlases (`weapons4_*` for
  Scythe/AAM2, `missiles3_*` for Scimitar/AAM4), binds them like the runtime
  materials (`_BaseMap`/`_MainTex`/`_MetallicGlossMap`/`_OcclusionMap`,
  white tint, `_METALLICSPECGLOSSMAP`), keeps the runtime OBJ `vt` UVs, and
  renders the complete Halberd, Kris, and Ballista prefabs (not body+booster
  only) in one 5-weapon scene with labels above each silhouette. The normal
  map is deliberately omitted (extracted normals carry a swizzle that does
  not reproduce the game's runtime import), so the preview is an
  **albedo/MS comparison**, not an exact runtime match — labels say
  "weapons4/missiles3 albedo+MS" / "CUSTOM". Extracted atlases are staged in
  gitignored `Assets/Reference/vanilla_textures/` (albedo sRGB, MS/AO
  linear); the bundle validator fails if any reference asset leaks into the
  shipped bundle.
- **Preview rendering requires graphics.** `Camera.Render()` into a
  RenderTexture produces a blank frame under `-nographics` (null graphics
  device): the first 2026-09-14 preview run saved a 23 KB uniform-gray PNG.
  The preview build must run without `-nographics` (real GPU, e.g.
  `Renderer: NVIDIA GeForce RTX 4050` in the log); the bundle build stays
  `-nographics` (no rendering).

## 7. Kris redesign + all-weapon mirror-symmetry pass (2026-09-14)

### Reference keys confirmed from runtime dumps (never assume IRMS1 = IRM-S2)

| Display name | Internal key | Prefab | Runtime material | Atlas |
|---|---|---|---|---|
| IRM-S2 | `AAM3` | `AAM3` / mount `AAM3_double` | `Missiles3` | missiles3 (1024²) |
| MMR-S3 | `AAM1` | `AAM1` / mount `AAM1_double` | `Missiles1` | missiles1 (512²) |
| IRM-S1 (SAM) | `SAM_IR1` | `IRMS1_single` | — | — |

Evidence: `weapon-schema.json:46738-46739` (IRM-S2 → weaponPrefab `AAM3`),
`:26670-26671` (MMR-S3 → weaponPrefab `AAM1`), `missile-geometry.json:1825`
(AAM3 → `Missiles3`), `:1722` (AAM1 → `Missiles1`), `:3004-3005` (IRMS1 →
`SAM_IR1`, a SAM — not IRM-S2).

### Kris palette/detail hierarchy derived from the actual references

UV-region palette measurement of the real AAM3/AAM1 meshes against their
runtime atlases (`tools/render_kris_references.py` →
`docs/kris_reference_uv_regions.json`, renders in `cad/kris_reference_*.png`):

- **IRM-S2 (AAM3)** UV region: near-black (6,5,4) · warm gray-brown
  (95,87,77 → 125,118,111) · rust accent (104,59,34) · ochre (227,190,87).
- **MMR-S3 (AAM1)** UV region: near-black (4,4,4) · warm dark (67,54,45) ·
  neutral grays (84,81,79 → 111,112,112) · muted ochre (172,146,83) ·
  near-white (197,197,196).

Kris redesign (`KrisTexturedMaterialBuilder.cs`), original Kris form kept
(light body, ochre ring, charcoal tail/nose, no text, grid fins, clearcoat
seeker):

- Body base `(165,163,160)` — warm-neutral light, between AAM3's 125 and
  AAM1's 197; charcoal `(42,39,36)`; ochre ring `(227,190,87)` (IRM-S2);
  rust band `(104,59,34)` at v 0.905-0.91 (IRM-S2 accent).
- Two reference panel zones between the 0.42 seam and the ochre ring:
  IRM-S2 gray-brown panel `(125,118,111)` at v 0.44-0.48 and MMR-S3
  near-white panel `(197,197,196)` at v 0.55-0.62, with subtle boundary
  lines. Packed MS follows the mixed references (metal 0.05-0.10,
  smooth 0.40-0.50; atlas means 0.051-0.07 / 0.403-0.417).

### Mirror mapping on the actual UVs — explicit transform algebra

Cylindrical unwrap (Halberd body/booster, Kris body, Ballista airframe):
`u = (atan2(y,x)+π)/(2π)`, `v = (z-z_min)/L`. Let `a = atan2(y,x)`.

- **y-mirror** (x-z plane, y → -y): `atan2(-y,x) = -a`, so
  `u' = (π-a)/(2π) = 1 - (a+π)/(2π) = 1-u`. ⇒ **u → 1-u**.
- **x-mirror** (y-z plane, x → -x): `atan2(y,-x) = π-a` (y>0), so
  `u' = (2π-a)/(2π) = 1 - a/(2π) = 1 - (u-0.5) = 1.5-u`. ⇒ **u → (1.5-u) mod 1**.
- **180° roll** (z-axis, (x,y)→(-x,-y)): `atan2(-y,-x) = a+π (mod 2π)`, so
  `u' = u+0.5`. ⇒ **u → u+0.5 mod 1`. This is a **rotation, not a
  reflection** — a roll-symmetric texture reads identically (not mirrored)
  between the two opposed views.

The three transformations form the D2 group: x-mirror = roll ∘ y-mirror.
A motif centered at u = 0.25 or u = 0.75 is self-symmetric under the
x-mirror; the pair (0.25, 0.75) is symmetric under the y-mirror and the
roll. Motifs centered at u = 0.5 are y-symmetric only (their x-mirror wraps
around the u seam) — that was the flank asymmetry seen in the opposed views.

- **Ballista planar wings** (u along local x, v along local z): the spanwise
  mirror (x → -x) maps to u → 1-u; the wing texture is v-only + grunge, so it
  is symmetric.
- **Kris v-offset quirk — FIXED (2026-09-14):** `KrisMeshBuilder.LoadCadMesh`
  previously called `RecalculateBounds` after the cylindrical unwrap, so the
  Kris body v was normalized against the pre-scale (1.1×) bounds — a constant
  ~0.05 v shift that misplaced the texture zones (tail tip mapped to v≈-0.05,
  wrapping to 0.95). `RecalculateBounds` now runs before the unwrap (matching
  Halberd), so v is normalized against the scaled bounds. Geometry positions
  and topology are unchanged: the vertex/triangle counts stay
  64639/100328 (the +251 seam duplicates come from the u-seam wrapping, which
  depends only on u, not bounds). Ballista has no SizeScale, so it never had
  the offset.

### Asymmetries fixed (seams/service marks/rivets/material zones)

All cylindrical service marks are now **paired at u = 0.25 and u = 0.75**
(each panel self-symmetric under the x-mirror; the pair symmetric under the
y-mirror and the 180 roll), so every flank carries the same markings:

- **Kris body:** one centered panel (0.42-0.58/0.46-0.54) → two panels
  (rect 0.21-0.29 + X-in-box 0.23-0.27, and 0.71-0.79 + 0.73-0.77).
- **Halberd body:** centered rect+X (0.42-0.58/0.45-0.55) + flank X-in-boxes
  (0.08-0.17/0.83-0.92) → two panels at 0.25/0.75 (rect 0.21-0.29 +
  X-in-box 0.23-0.27, and 0.71-0.79 + 0.73-0.77).
- **Halberd booster:** the y-only pairs (0.30-0.42/0.58-0.70, 0.26-0.38/
  0.62-0.74) → two v-stacked pairs at 0.25/0.75 (rect+X at v 0.38-0.47,
  plain rect at v 0.60-0.68); the 26-rivet row (u = 0.02+i·0.0385, not
  x-symmetric) → the body's 8-position axial-seam flank set
  {0.116, 0.144, 0.356, 0.384, 0.616, 0.644, 0.856, 0.884} (symmetric under
  all three transforms).
- **Ballista body:** one centered panel → two panels at 0.25/0.75
  (rect 0.21-0.29 + X-in-box 0.23-0.27, and 0.71-0.79 + 0.73-0.77).
- Stochastic grunge is intentionally asymmetric (per-pixel hash) and is
  excluded from the symmetry metric by its measured amplitude (see below).

### New bundle validators (`MunitionsGeometryBundleBuilder.cs`)

- `ValidateCylindricalUvs` — the shipped body meshes' UVs must follow the
  cylindrical formula (max u error ≤ 0.01) and be z-monotonic
  (corr(v,z) ≥ 0.99), so the u transforms above are real geometric mirrors
  on the body.
- `ValidateTextureMirrorSymmetry` — pixel-based, checks **all three
  transforms** (y-mirror u→1-u, x-mirror u→(1.5-u) mod 1, 180 roll
  u→u+0.5 mod 1): the fraction of albedo pixels whose max-channel difference
  to the transformed pixel exceeds **0.12** (with ±1 px tolerance) must be
  ≤ 0.05% per transform. Tolerance justification (measured, not arbitrary):
  the stochastic grunge mirror diff peaks at 0.098 on the lightest base
  (0.77, 400k-sample measurement; mean 0.022, p99.99 0.091), while the
  faintest one-sided marking in these textures is 0.18 (Ballista SeamLight on
  the dark base) — 0.12 neither false-positives on grunge nor hides the
  actual marks. Pre-fix (centered-at-0.5 motifs) measured 0.234-0.602% on
  the x-mirror/roll; post-fix (paired 0.25/0.75 motifs) 0.000% on all three.
  Runs on Halberd body/booster, Kris body, Ballista body/wing. All prior
  validators preserved.
- Preview now also renders `cad/kris/Kris_Reference_Mapping.png` (Kris between
  the actual IRM-S2/AAM3 and MMR-S3/AAM1 references) and
  `cad/shared/Weapon_Opposed_Views.png` (each custom weapon at roll 0° and roll
  180°, the two u/u+0.5 hemispheres — a rotation, not a reflection) with
  real graphics and camera-facing labels; reference atlases stay in
  gitignored `Assets/Reference/` and the bundle audit
  (`ValidateNoReferenceAssets`) still fails on any leak.
