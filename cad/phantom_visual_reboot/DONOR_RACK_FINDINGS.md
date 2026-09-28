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
