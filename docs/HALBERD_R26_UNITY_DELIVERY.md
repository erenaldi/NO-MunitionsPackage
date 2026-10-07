# Halberd R26 (rounded-square study) — Unity delivery contract, export candidate

**2026-10-04 — State:** CAD accepted by the user (R26 = R24 rear-fin lip seats + dark rust-maroon nozzle recess). Export is a staged candidate awaiting review. Engine import candidate built 2026-10-07 (see "Unity import candidate"); no bundle, collider, plugin or runtime work has been done. User decision: R26 is intended to replace the shipped `Erenaldi.AAM44` geometry, but nothing replaces it yet.

## Source and transform
- Source: `cad/halberd_rounded_square/STEP/r26_nozzle_recess.step` (383 labeled leaves, X -1685..1685 mm, max radius 212.0 mm). Exporter: `cad/halberd_rounded_square/export_r26_unity_mesh.py`.
- CAD millimetres, +X forward, +Z dorsal, +Y lateral. Unity = (CAD.Y, CAD.Z, CAD.X) * 0.001.
- Stage seam at CAD X -1123.3 mm (Unity z -1.1233 m). The exporter fails if an upper-stage group extends aft of it or a booster group forward of it.
- Candidate output (not under the Unity tree): `cad/candidates/halberd_r26/` (nine OBJ groups + `HalberdR26_Export_Report.json`).

## Groups and material slots (updated 2026-10-04)
Each of the nine groups is split by color, because one Unity mesh carries one material. Result: 18 OBJ meshes using 8 distinct colors (= 8 material slots): #3E4A54 dark hardware/liner, #636F79 mid-grey covers and booster skin, #76828B body, #8B959D ogive, #495660 fins, #000000 / #040608 intake and floor darks, #160906 rust-maroon nozzle recess. Every leaf maps to exactly one group and color; unclassified labels abort the export. Colors are the exporter's linear-to-8-bit reading of the STEP colors, so final Unity albedo values are set at the material gate.

| Base group | Stage | Leaves | Triangles |
|---|---|---|---|
| body | upper | 3 | 95,488 |
| intake_recess | upper | 8 | 272 |
| sustainer_fins | upper | 4 | 48 |
| hardware_main | upper | 249 | 47,000 |
| sustainer_nozzle | upper | 2 | 790 |
| booster_body | booster | 1 | 28,018 |
| booster_fins | booster | 4 | 6,640 |
| hardware_booster | booster | 110 | 18,876 |
| booster_nozzle | booster | 2 | 832 |
| **Total** | | 383 | **197,964** |

Tessellation: body and fins 0.12 mm / 0.3 rad; hardware (fasteners, covers) 0.3 mm / 0.6 rad. OBJ vertices are split above a 35 degree crease angle and exported with normals, so curves shade smooth and hard edges stay sharp. User accepted this export on 2026-10-07 ("This model looks good").

## Decisions
1. Triangle budget: 198k accepted (hardware coarsened, smoothed normals). Known limit: the tail shroud and nose silhouettes remain visibly polygonal because the shell skin is coarse (nose is 632 triangles); the preview renderer ignores normals, so smooth shading is unverified until the Unity import. Refining only the large skin faces would cost about 50k triangles (about 250k total) if the engine capture shows it matters. Shipping ceiling still to be confirmed at the engine gate.
2. Material slots: split by color (done, 8 slots).
3. Runtime hierarchy: the user decided the runtime hierarchy is fixed to R26 (four fins and four intakes), not the shipped three-fin layout. Fin/intake child paths, the direct `Booster` child, colliders and the FX anchor are defined from R26 at the Unity gate. Not started.
4. Gates still pending: export validation review, Unity import, engine capture, runtime test, fallback.

## Unity import candidate (2026-10-07)
- `unity/BlueprinterEditor/Blueprinter-Editor/Assets/Editor/HalberdR26Importer.cs` (`Blueprinter > Halberd R26 > Build Candidate`) reads the 18 OBJs directly (Unity's OBJ importer mirrors X), builds `Assets/Blueprinter/Mods/HalberdR26/Erenaldi.AAM44.R26Candidate.prefab` and 18 meshes, 8 flat URP/Lit materials (export linear hex converted to sRGB), and a preview scene. Run: Unity 2022.3.62f2 `-batchmode -quit -executeMethod Erenaldi.Halberd.HalberdR26Importer.BuildAndPreview` (no `-nographics`; log under `Logs/`).
- Hierarchy: body (largest upper-stage color) on the prefab root; `SustainerFins` child (4 fin leaves); `Booster` child carrying the booster hull plus booster fins, hardware and nozzle children. No scripts, no colliders, no UVs (flat colors).
- Checks that passed in the batch run: 197,964 triangles equals the export report, 18 renderers, root identity transform, stage ownership against the seam, z bounds +-1.685 m, no scripts or colliders. Axis map (Y,Z,X) is a cyclic permutation, so winding was kept and the model is the engine-handedness mirror of CAD, as in the earlier Halberd exports.
- Engine renders (GPU, 2000x1200): `cad/halberd_rounded_square/reviews/R26_unity_{whole,side,tail,nose,intakes,separated}.png`. Smoothed normals work in Unity: the tail shroud and nose read smooth. In Unity lighting the nozzle recess reads copper-brown, lighter than in the CAD render.
- Not done: colliders, the four-fin child paths for the transplant loader, exhaust FX anchor, rack prefab, bundle, plugin build/install, in-game test. A cold Unity library rebuild logs harmless editor-only asset import errors from over-long package paths in this worktree (UXML files); they did not affect the build.
- 2026-10-07 nozzle tweak: at the user's request the engine material for the nozzle recess is slightly redder than the CAD color (sRGB `#5E2822` via `EngineColorOverride` in `HalberdR26Importer.cs`; CAD R26 stays `#52342C`). Any later re-export must keep this override or move the color into the CAD source.
