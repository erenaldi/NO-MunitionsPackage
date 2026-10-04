# Halberd R26 (rounded-square study) — Unity delivery contract, export candidate

**2026-10-04 — State:** CAD accepted by the user (R26 = R24 rear-fin lip seats + dark rust-maroon nozzle recess). Export is a staged candidate awaiting review. No prefab, bundle, plugin or runtime work has been done. User decision: R26 is intended to replace the shipped `Erenaldi.AAM44` geometry, but nothing replaces it yet.

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

Tessellation: body and fins 0.12 mm / 0.3 rad; hardware (fasteners, covers) 0.3 mm / 0.6 rad. This is the user-approved guidance for the budget decision (down from 265k). The single body leaf (about 94k triangles, from the surface panel and seam engraving) is now the dominant cost; coarsening it is the next lever if the budget must drop further.

## Decisions
1. Triangle budget: coarsen hardware only (done, ~198k). Shipping ceiling still to be confirmed at the engine gate.
2. Material slots: split by color (done, 8 slots).
3. Runtime hierarchy: the user decided the runtime hierarchy is fixed to R26 (four fins and four intakes), not the shipped three-fin layout. Fin/intake child paths, the direct `Booster` child, colliders and the FX anchor are defined from R26 at the Unity gate. Not started.
4. Gates still pending: export validation review, Unity import, engine capture, runtime test, fallback.
