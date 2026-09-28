# Tail R3 — flush-stowed clipped fin in a shallow pocket

2026-09-27. State: `cad-approved` for the local one-corner recessed fin. User approved with “its good” after the stowed/deployed/pocket review; proceed to the stated fourfold propagation gate. Whole-airframe and downstream acceptance remain pending.

Fourfold result is now built/checked: `TAIL_FIN_R4_FOUR_CONTRACT.md` and `STEP/Q_Tail_R4_Four_*`. The combined layout remains at its own `cad-review` gate; this approved local prototype is preserved.

## User intent and interpretation

User requested fins recessed inside the body, with the flat edge flush when stowed, and explicitly accepted a shallow visible hole when extended. Primary interpreted this as the folded panel's outer broad face level with the adjacent body skin. The selected clipped planform and80 mm aft placement remain.

- Source `src/tail_fin_r3.py`; four `STEP/Q_Tail_R3_Recessed_{Stowed,Midfold,Deployed,Body_Pocket}.step` outputs.
- Panel remains110 mm span,240 mm root and3 mm thickness at the R2 X/Y outline. Its flat outer face is Z86 (panel range83..86),4 mm lower than R2.
- Hinge axis is nowY82,Z83,5.5 mm below R2. Root barrel radius3 has crownZ86, also flush. The1.5 mm change in panel/axis relation avoids leaving the barrel proud while retaining the selected flat panel shape.
- Both fixed mounts and capped pin are exact saved-R2 shapes shiftedZ-5.5. Root X-1325..-1085 and overall tail X-1336..-1074 remain. Fold law remains-135 degrees about the revised longitudinal axis.
- Body pocket follows the actual fin outline with0.3 mm XY allowance, broad floorZ82.7 (**3.3 mm below roof**). Cylindrical root relief reachesZ79.7 (**6.3 mm locally**); additional pin/cap relief prevents interference. No oversized rectangular well or added pocket cover.
- Body differs from accepted A5 only in these local tail cuts. All12 A5 nonbody components, main-wing pocket/cover and nose remain exact.

## Measured evidence

- Separate fresh workers completed bounded feasibility, source/build and saved checks. Primary inspected source/report, switched raw STEP exports to the project's decorated cadgen entrypoints, retained saved input styling and fin review color, rebuilt all outputs, then reran full saved validation.
- Reexport initially exposed a standalone-document label mismatch in the checker, not a geometry failure. Checker now accepts only the exact cadgen singleton document label as an alias, retaining strict part counts/topology and exact isolated-body Boolean checks. Full rerun PASS with0 failures.
- `src/check_tail_fin_r3.py` / `reviews/tail_fin_r3_checks.json`:17 valid single solids in each full state;36 A5 nonbody comparisons zero delta; fixed hardware equals lowered R2; moving fin matches independently specified profile/barrel; saved mid/deployed match rigidly rotated saved stowed geometry.
- Modified body is one valid solid and exactly equals independent declared cutter subtraction; isolated body matches full stowed body with zero Boolean difference.
-66 fold samples (61 uniform plus five early fractions) pass, minimum clearance0.25 mm, no unexpected intersections. Only named embedded fixed-mount/body contacts are intentional; moving fin and pin are checked against body without exemptions.
- Stowed complete-assembly conservative radius121.622367 mm; tail-only120.917327 mm; both within125. Fin face and hinge crown measured atZ86. Imported bbox tolerance≈1e-7 mm is retained, not altered to force exact decimal bounds.

## Direct visual review

Primary generated and inspected six views from `review_tail_fin_r3.json`: stowed, intermediate, deployed and empty-pocket closeups, flush side detail and full deployed context. The stowed flat panel is flush; its perimeter remains identifiable. Deployment exposes the matching shallow fin-shaped recess, with a deeper rounded channel only along the hinge. This matches the requested visible open pocket.

Best images: `reviews/Q_Tail_R3_Stowed_close.png`, `reviews/Q_Tail_R3_Deployed_close.png`, `reviews/Q_Tail_R3_Body_Pocket_close.png`, `reviews/Q_Tail_R3_flush_side.png`. Review source `src/render_tail_fin_r3.py`.

Next: user accepts/revises this recessed mounting; then copy it to the remaining corners with cross-fin and pocket checks. No fourfold geometry yet. Continuous full-motion, structural strength, locks/actuators, fastening, tolerances, sealing, rack and engine validation remain open.
