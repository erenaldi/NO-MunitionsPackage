# Session Log

Append-only handoff journal, newest entry first. Rules of use: `AGENTS.md` → "Session records & handoff". Treat every entry as a claim to re-verify against disk, not as truth.

## 2026-09-13 (22:00) — Ballista palette revert + Halberd matte pass

- User decisions: (1) Ballista keeps all texture detail but reverts fuselage/tail/wing underlying colors to the original STEP dark blue-gray family; (2) Halberd texture more matte, like Scythe/Scimitar.
- Ballista (`BallistaTexturedMaterialBuilder.cs`): `BaseGray` 182-warm → old body (31,38,41); olive zone → `ZoneGray` old wing (44,53,58); wing base → `ZoneGray`; panel material base → old panel (0.075,0.100,0.114). Kept: charcoal nose cap, orange accent ring, all seams/rivets/service marks/grunge/packed maps (panel 0.10/0.42, wing 0.08/0.44).
- Halberd (`HalberdTexturedMaterialBuilder.cs` packed maps): body base smoothness 0.45→0.40, charcoal 0.58→0.46, ochre 0.50→0.44; booster base 0.46→0.40, charcoal 0.58→0.46; plain microsurface 0.44→0.40; metals trimmed (0.14→0.10 charcoal, 0.06→0.05 base). Albedo geometry/detail unchanged.
- Verified: headless `BuildBundle` exit 0, Halberd+Kris assembly-verify pass, bundle rebuilt 22:16 (39,903,437 B); `dotnet build` 0 errors.
- **PENDING: plugin DLL not installed — game running (user session).** After closing the game run: `tools\install_plugin.ps1 -PluginPath src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll`, then launch + `tools\check_log.ps1`.
- Next: user visual check (Ballista dark blue-gray + Halberd matte); then whatever the user reviews next.

## 2026-09-13 (night) — Kris + Ballista texture passes; runtime validation green

- Installed iteration-2 plugin (game had closed; SHA f9d0b8e2...). Launched to menu: `check_log.ps1` green — bundle loaded, Halberd/Kris/Ballista all transplanted 2/2 and registered; dumper v2 regenerated 29 OBJs + `missile-geometry.json` schema 2 with per-renderer material/texture bindings. Key runtime findings: Scythe `AAM2` binds **Weapons4** at runtime (offline prefab dump was ambiguous), Scimitar `AAM4`→`Missiles3` confirmed; Kris meshes ship no UVs pre-unwrap; `Erenaldi.*` dumps list our textures loaded.
- Kris texture pass (`KrisTexturedMaterialBuilder.cs`): Missiles1-family light gray body (196) + sparse yellow-ochre ring (0.885-0.90) + tail/nose charcoal (53), 4 seam rings + flank axial lines + rivets, X-in-box service mark, packed MS; `KrisMeshBuilder` gained `GenerateCylindricalUVs` (seam-deduplicated full-2π, z-axis, v 0 tail → 1 nose) applied to the body only. Body material now texture-driven (white tint, `_METALLICSPECGLOSSMAP`); validator updated (`KrisMeshBuilder` body check + `MunitionsGeometryBundleBuilder.ValidateKrisRenderer` with new `IsKrisBodyLabel` helper covering `<root>` and rack `pylon/aam1`). `ExpectedVertexCount` 64388 → 64639 (+251 seam duplicates).
- Ballista texture pass (`BallistaTexturedMaterialBuilder.cs`): Bombs1-family warm gray (182) + olive zone (0.30-0.62) + orange accent ring (0.80-0.815) + nose charcoal, panel/wing get their own subtle textures; all 24 groups now unwrap via `KrisMeshBuilder.GenerateCylindricalUVs` (z-axis) so the textured materials cover the airframe and folding wings; hardware/edge/glass/nozzle/recess/accent stay flat.
- Gotchas fixed along the way: (a) `ValidateKrisRenderer` was rewritten through several bad edits — final form validates body structurally and keeps flat-color checks for Dark/GridFins/Seeker/Hardware; (b) Kris exact-vertex validator needed the +251 seam-duplicate allowance; (c) Unity batch runs can use a stale compiled assembly if launched immediately after editing `const` values — rerun before diagnosing.
- Verified: headless `BuildBundle` (all 3 weapons) exit 0, Kris assembly-verify 64639/100328, bundle 40,832,363 B (21:59); `dotnet build` 0 errors; installed (SHA 5c3f3dde...); in-game launch + `check_log.ps1`: all 3 transplanted 2/2, registered, no errors. Game closed after validation.
- Next: in-game visual pass by user (all 3 weapons now textured, no text anywhere); optional normal/AO maps; `TEXTURE_STYLE_FINDINGS.md` delta table can be updated after user review.

## 2026-09-13 (late) — Halberd texture iteration 2: no text, brighter, de-crowded

- User feedback: remove all words from the texture; body looked crowded vs. Scythe/Scimitar while the booster looked sparse.
- Changes (all in `HalberdTexturedMaterialBuilder.cs` + child tints in `HalberdMeshBuilder.cs`):
  - Removed every text stencil and the 5×7 font (`Glyphs`, `StampTextRotated`) + unused `InkWhite`. Markings now purely geometric: panel seams, rivet dots, rect service panels, X-in-box marks.
  - Body rings cut 7 → 3 (`{0.055, 0.40, 0.856}`); gray mid-band removed (single light field like the references).
  - Base gray brightened 133 → 194 (Scythe/Scimitar near-white range); booster stays light-gray family (184) vs. body 194.
  - Booster de-sparse: 3 ring seams (0.30/0.55/0.78) + axial panel lines (v 0.14-0.93) + 2 service panels with X-in-box + baked AO shading; packed-map smoothness bump applies on the new rings.
  - Children tints brightened to match (fins 0.80, hardware 0.61); intakes/nozzles unchanged darks.
- Verified: preview render `cad/Halberd_Vanilla_Texture_Comparison.png` (21:27, 319 KB) — Halberd now reads clean/bright next to Scythe/Scimitar, no text, 1 mid-body ring + panel detail; headless bundle build exit 0, bundle rebuilt 21:33 (26,794,766 B); `dotnet build -c Release` 0 errors.
- **Plugin DLL NOT installed — game was running (installer guard refused).** Built DLL awaiting install at `src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll`: close the game, run `tools\install_plugin.ps1 -PluginPath src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll`, restart, then `tools\check_log.ps1`.
- Next: in-game visual check of the new texture; then Kris/Ballista texture passes (unchanged from previous entry).

## 2026-09-13 (evening) — vanilla texture extraction + Halberd texture pass

- Extracted the game's weapon atlases offline (UnityPy 1.25.3, `FALLBACK_UNITY_VERSION=2022.3.62f2`): `tools/dump_weapon_textures.py` → `reference/vanilla_textures/` (gitignored) — 47 PNGs covering `weapons1-5`, `missiles1-4` (+`missiles4_o`), `bombs1`, `ballisticMissile1` + `inventory/materials/prefabs/placeholder_check.json`. Blueprinter `_donotship` copies verified pixel-identical except normal-map swizzle (game copies kept).
- Material mapping (from `materials.json` + `prefabs.json`): 5 master materials bind the atlases; `Weapons5` has `_Paint` mask + gray `_BaseColor` 0.3585 (faction recolor channel). Scimitar=`aam4` and Scythe=`AAM2` both use **missiles3** (1024², cool grays + ochre 228,193,94; metallic mean 0.070, smoothness 0.417). All numbers in `docs/TEXTURE_STYLE_FINDINGS.md` (committed; swatch at `docs/palette_swatch.png`).
- `MissileGeometryDumper.cs` → v2: emits `vt` lines + `uvBounds` per mesh (CPU + GPU readback paths) and per-renderer material/shader/color/metallic/smoothness/texture style data; target list widened to 28 mounts (AAM1/3/4, AAM2, AGM1/2/heavy, ARM1/mini, AShM1/2/3, P_KEM1, P_AAM2, BallisticMissile1, bombs, RocketPod, IRMS1, Erenaldi.*). Build green (0 errors, tolerated MSB3277). **Runtime data NOT yet regenerated — game was running during install; needs a restart to produce the new dumps.**
- Halberd texture pass DONE: new `HalberdTexturedMaterialBuilder.cs` paints original vanilla-style albedo + packed metallic(R)/smoothness(A) for body, booster, and a shared tinted microsurface for intakes/fins/hardware/sustainer-nozzle (all now UV-mapped; full-2π unwrap fixed in `HalberdMeshBuilder.GenerateCylindricalUvs`; nozzles stay flat). Stencils: "AAM-44 HALBERD", "ERENALDI ORD LOT 7", "SR-1157-90825", "DANGER", "NO STEP" (rotated 5×7 bitmap font, anisotropy-corrected cellU=16/3, cellV=3/2). Lessons: (a) builder methods save their own assets — `HalberdMeshBuilder` must NOT re-save them (DeleteAsset+CreateAsset on same object = destroyed/fake-null), (b) each plain material needs unique texture names (renamed per material in `CreateTexturedMaterial`), (c) `GetPixels32` works for dumps in `-nographics`, `Graphics.CopyTexture` does not.
- Verified: headless Unity bundle build passes (`MunitionsGeometryBundleBuilder.BuildHalberdBundle`, `unity/.../Logs/HalberdTexturedBuild.log` "Geometry bundle built"), assembly-verify + bundle validate OK; preview render `cad/Halberd_Vanilla_Texture_Comparison.png` (21:15) shows vanilla-style bands/seams/ochre/stencils next to Scythe/Scimitar; texture dump in `cad/texture_dump/` (dev-only). Bundle 26,647,604 B (21:17) embedded; `dotnet build -c Release` green; plugin installed to game (SHA-256 507eb0e343...).
- In-flight: Kris + Ballista texture passes NOT started (Kris needs cylindrical UVs replacing per-quad 0-1; Ballista needs UV generation from scratch — both per `TEXTURE_STYLE_FINDINGS.md` §4). `HalberdTextureDumpUtility.cs` added (menu Blueprinter/Halberd/Dump Textures To PNG). `tools/analyze_weapon_textures.py` → `palette_measurements.json`.
- Next: (1) restart game to main menu → `tools/check_log.ps1` → confirm `[Phase 3]` lines + regenerated `missile-geometry.json` (uvBounds non-null) + in-game look of textured Halberd; (2) Kris texture pass (wrap UVs in `KrisMeshBuilder`, light stencils, keep clearcoat seeker); (3) Ballista pass (UVs + darker AGM-family palette + wing stencils); (4) update `TEXTURE_STYLE_FINDINGS.md` delta table rows as each completes.

## 2026-09-13 — context-corruption recovery + ARAD-80 decision

- A prior session corrupted its own context (fabricated paths, invented tool outputs, duplicated-token artifacts) and stopped before recording state. Its "2026-09-09 handoff" claim (Ballista def-field dump validation, HOB/LOAL water-phase research, smoke test) is recorded in no file and is discarded as unverifiable.
- Reconstruction verified from disk by the recovery session:
  - Ballista CAD RC2 valid: `cad/Ballista_stowed_validation.json`, `cad/Ballista_deployed_validation.json` — both `ok`, 58 occurrences, 0 findings; `cad/Ballista_checks.json` passing.
  - Unity batch builds exited 0: `unity/BlueprinterEditor/Blueprinter-Editor/HalberdDetailedBuild.log`, `MunitionsGeometryBundleBuild.log`.
  - `missions/Erenaldi.ProvingGround/lane-manifest.json` live mounts: `Erenaldi.AAM44_single`, `Erenaldi.IRMS4_single`, `Erenaldi.ARAD80_single`.
  - Build attempt failed: `Plugin.cs(26,29): error CS0246: 'AradPulseController' could not be found`.
- Decision (user-confirmed 2026-09-13): ARAD-80 propulsion = **single continuous burn** — one motor, 82 kg propellant, 50 kN, 3.76 s (188 kNs total = former booster 100 + former pulse 88, same chemistry, Isp ~234 s). The MUNITIONS.md §4 twin-pulse text is obsolete; do not restore the twin-pulse design or `AradPulseController`.
- In-flight cleanup **completed** by the recovery session (2026-09-13):
  - `src/Plugin.cs`: removed the `aradPulseTrigger` / `aradPulseMachFloor` / `aradPulseMaxDelay` config entries, their field declarations, and the `AradPulseController` static-property assignments; `enableArad80` kept, description updated to "single-burn sprinter".
  - `MUNITIONS.md` §4 Impl: twin-pulse text replaced with the single-burn design, dated decision note added.
  - `src/AradCloner.cs`: pulse-era `ReportRange` warnings reworded to single-burn terms.
  - `docs/V1_PLAN.md`: L04 renamed ARAD-120 → ARAD-80, status "implemented (cloner, single-burn motor) — runtime validation pending"; def-tuned batch list updated.
  - Build verified after cleanup: `dotnet build -c Release .\src\Erenaldi.MunitionsPackage` — 0 errors, 1 warning (tolerated MSB3277).
- Git: zero commits at recording time. First checkpoint commit is authorized as part of the next session's work (per `AGENTS.md` milestone-commit convention).
- Next: runtime-validate lane L04 (`Erenaldi.ProvingGround`, IADS-HARD): install rebuilt DLL via `tools/install_plugin.ps1`, confirm `[Phase 2E]` registration + range-estimate log lines, single burn with no midcourse re-light, Mach 3+ sprint within the 35 km envelope. Git checkpoint commit pending (authorized per `AGENTS.md` milestone convention). Then HKP-1 Palisade per `docs/V1_PLAN.md`.
