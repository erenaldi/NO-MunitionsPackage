# Halberd R26 (rounded-square study) — Unity delivery contract, export candidate

**2026-10-04 — State:** CAD accepted by the user (R26 = R24 rear-fin lip seats + dark rust-maroon nozzle recess). Export is a staged candidate awaiting review. No prefab, bundle, plugin or runtime work has been done. User decision: R26 is intended to replace the shipped `Erenaldi.AAM44` geometry, but nothing replaces it yet.

## Source and transform
- Source: `cad/halberd_rounded_square/STEP/r26_nozzle_recess.step` (383 labeled leaves, X -1685..1685 mm, max radius 212.0 mm). Exporter: `cad/halberd_rounded_square/export_r26_unity_mesh.py`.
- CAD millimetres, +X forward, +Z dorsal, +Y lateral. Unity = (CAD.Y, CAD.Z, CAD.X) * 0.001.
- Stage seam at CAD X -1123.3 mm (Unity z -1.1233 m). The exporter fails if an upper-stage group extends aft of it or a booster group forward of it.
- Candidate output (not under the Unity tree): `cad/candidates/halberd_r26/` (nine OBJ groups + `HalberdR26_Export_Report.json`).

## Groups (every leaf maps to exactly one; unclassified labels abort the export)
| Group | Stage | Leaves | Triangles (tol 0.12 mm, 0.3 rad) |
|---|---|---|---|
| body (ogive, intake body, joint liner) | upper | 3 | 95,488 |
| intake_recess | upper | 8 | 272 |
| sustainer_fins | upper | 4 | 48 |
| hardware_main | upper | 249 | 93,736 |
| sustainer_nozzle (recess + floor) | upper | 2 | 790 |
| booster_body | booster | 1 | 28,018 |
| booster_fins (fairings) | booster | 4 | 6,640 |
| hardware_booster | booster | 110 | 39,654 |
| booster_nozzle (recess + floor) | booster | 2 | 832 |
| **Total** | | 383 | **265,478** |

## Open decisions (need the user before the Unity gate)
1. **Triangle budget.** 265k is far above the earlier RC1 ceiling (75k). Angular tolerance drives it: 0.2 rad gives 419k, 0.12 rad 679k. Options: accept ~265k, coarsen smooth bodies, or merge hardware as normal-mapped detail.
2. **Material slots.** One OBJ per group mixes colors (body has 3, hardware has 3 paints/metals). Split by color into material slots, or keep per-group single material.
3. **Runtime hierarchy.** R26 has four fins/intakes; the shipped runtime Halberd has three. Fin/intake child paths, the `Booster` child, colliders and FX anchors must be redefined for the transplant.
4. **Gates still pending:** export validation review, Unity import, engine capture, runtime test, fallback.
