# Phantom donor rack — recovered geometry and failed unchanged-placement fit

2026-09-27. Source recovery is verified; final rack/aircraft fit remains **blocked** by a measured static collision at the unchanged donor missile placement. No model or game attachment transform was changed.

## Evidence and provenance

- `src/Erenaldi.MunitionsPackage/PhantomCloner.cs:9-10,132-145` identifies `AGM1_single`/`AGM1` and clones the donor mount. Runtime `weapon-schema.json:82722,82835-82957` confirms `AGM1_single/pylon/agm1` and the MountedMissile component.
- Existing `MissileGeometryDumper.cs:104,129,150` exports the projectile prefab, not the rack. `AGM1.geometry.obj` must not be used as pylon geometry.
- Installed game Steam manifest `C:\Program Files (x86)\Steam\steamapps\appmanifest_2168680.acf` reports buildid24724372. Game-version provenance uses this, not the QoL-modified Application.version string.
- Read-only extractor `checks/extract_agm1_mount_reference.py` loads `NuclearOption_Data/resources.assets` with the existing Python312 UnityPy installation. No packages, game files or runtime configuration were changed. It reads only necessary mesh/transform/render-enabled data; an initial attempt to parse unrelated component payloads failed and was corrected to retain their type inventory without parsing them.
- `reference/agm1_mount/manifest.json` records source SHA256 `88cb99ea168de540fa1406ac6d12942bd3cac634597616e8e5eb057c95205d7d`, object IDs, native transforms, mesh bounds and reference-file hashes. Hashes use actual written bytes to account for Windows line endings.
- One `AGM1_single` root found, pathID13366. Visible enabled pylon at `/pylon`: `launchpylon1`, pathID3857,848vertices/648triangles, resources.assets fileID0. Root `pylon_small_single` MeshFilter has no MeshRenderer and is not treated as the visible pylon. Mounted `agm1` mesh is reference-only weapon geometry, not an obstacle to be retained around the replacement model.

## Placement recovered

- Pylon local translation(0,-0.074,0)m, scale(0.9,0.8,0.7), identity rotation.
- Mounted missile child local translation(0,-0.181250006,0.009690522)m, compensating scale(1.111111164,1.25,1.428571343), identity rotation.
- Composed mounted-missile origin in mount-root space ≈(0,-0.219000008,0.006783365)m, net scale≈1 on each axis.
- Fit test transforms the extracted pylon by the inverse composed mounted-missile transform, then uses CAD X=Unity Z, CAD Y=Unity X, CAD Z=Unity Y, converting m→mm. This is the existing centered CAD convention at the unchanged donor child origin, not a new approved installation transform.
- Actual pylon bounds in that candidate frame: X[-770.166,685.646],Y[-66.720,66.719],Z[77.426,236.661] mm.

## Static fit result — FAIL

`checks/check_agm1_reference_fit.py` tested the actual pylon triangles against saved `STEP/S_AftExhaust_R1_Stowed.step` and wrote `reviews/agm1_reference_fit.json`. It exits nonzero for the detected collisions. Source/reference and candidate hashes are bound into the report.

| Candidate component | Intersecting triangles | Surface intersection area |
|---|---:|---:|
| Port front wing |13|701.17 mm2|
| Top cover |60|13751.63 mm2|
| Body |18|20002.87 mm2|

Native solid classification found strict interior witness points for all three, distinguishing these from mere coincident surface contact. The imported pylon is treated as a triangle surface: these are area measurements, not a claimed closed-volume penetration measurement.

The pylon's minimum Z77.425665 overlaps the candidate's maximum Z86 by8.574335 mm in their vertical bounds. Lowering the candidate by about9.574335 mm would establish a1 mm **global vertical bounding-box gap** to this pylon; that is an unapplied placement study, not an approved attachment solution. A supported mounting interface, release behavior and actual aircraft/bay clearances still need review.

## Review and remaining scope

- Primary directly inspected `reviews/S_Aft_R1_actual_pylon.png` and `S_Aft_R1_donor_fit_collision.png`.
- `reference/agm1_mount/DonorPylon_Surface.step` and `Phantom_DonorFit_Unchanged.step` are derived reference-surface review artifacts. The pylon is highlighted orange; no fictional stand-in rack is used.
- Extracted meshes and derived pylon surfaces are reference-only and must not be included as authored/shipped mod geometry.
- No new mounting shoes, offset, custom pylon, aircraft clearance claim or game installation has been made. Next is a user-approved mounting-position/interface study using these actual keep-outs, followed by real aircraft and release-state checks.

## Mounting-interface study, 2026-09-29 (read-only; nothing applied)

Scripts `checks/study_pylon_interface.py` (height maps -> `reviews/pylon_interface_study.json`) and `checks/verify_pylon_lowering.py` (exact surface intersections -> `reviews/pylon_lowering_verification.json`), both on the saved B2H Stowed candidate (dorsal geometry is unchanged from the earlier baseline). The pylon surface is the recovered `launchpylon1` mesh in the unchanged donor frame.

- **Only lowering is practical.** The pylon underside sits above the candidate's top over a large footprint: top cover 38,772 mm2 (2 mm thick), body top 13,652 mm2 (172 mm column), port front wing 620 mm2 (needs only ~0.5 mm). Height-map estimate of the worst required lowering: 8.08 mm, at the side shoulders (y about +65) near X-554 (body) and X+376 (cover). That estimate is a lower bound from a 2 mm grid.
- **Relief-only or a big hybrid would destroy accepted work.** Zero lowering needs ~8 mm relief across the whole cover footprint and the body top; lowering 6 mm still leaves ~2.1 mm residual over ~11,140 mm2, i.e. the entire 2 mm A5 top cover in that area; lowering 8 mm leaves 0.08 mm. A local recess therefore either removes the flush cover or is redundant with the lowering. No saddle or shoe can fix an interference between the pylon underside and the top surface.
- **Exact surface check of straight lowerings** (pylon triangles vs candidate solids, area of intersection): 8.1 mm -> **still intersects** (top cover 3,059 mm2, body 1,040 mm2; bbox gap -0.47 mm); 9.1 mm -> **clear** (bbox gap +0.53 mm); 9.574 mm -> **clear** (bbox gap +1.00 mm). Any lowering with a positive bounding-box gap is clear, so the true threshold lies between 8.1 and 8.574 mm.
- **Not assessed:** the aircraft/bay underneath (a lower missile hangs 9-10 mm further into the airflow/bay), release states, whether the game's own hitbox/collider or bay envelope is referenced to the donor mount origin (the 250 mm stowed envelope is about the model's own axis; a pure translation does not change it, but relative to the mount origin the underside would sit ~9.6 mm lower), and where the offset is applied (asset-frame geometry offset at export vs a game-side mount transform, which needs plugin authorization).

**Decision (user, 2026-09-29):** straight lowering of **9.574 mm**, applied **in the CAD asset frame** (not in the game mount transform). Built: `src/donor_fit_lowered.py` -> `STEP/S_EngineBay_B2H_Stowed_Placed.step` (all 66 leaves translated by -9.574 mm; design-frame sources unchanged) and reference-only `reference/agm1_mount/Phantom_DonorFit_Lowered_9574.step`; renders `reviews/Phantom_DonorFit_Lowered_9574_{side,close}.png` (primary inspected: pylon rests on the top surface with a thin visible gap, no penetration). The intersection verification is on the un-translated candidate with the pylon raised 9.574 mm, which is the same relative placement; the placed file itself was not re-run through the surface check. `check_agm1_reference_fit.py` still (correctly) fails at the unchanged placement.
