# R9 — taller rear fin and intake-edge transition prototype

Date: 2026-09-23. Historical single-station prototype. **Superseded:** user rejected
the added-transition approach; [R10](R10_CONTINUOUS_INTAKE_CONTRACT.md) recalculates
the original intake to the fin midpoint before splitting it at the stage joint.

User clarified the annotation: increase fin height, then create a transition
from the rear second-stage intake edge to the center of the rear fin, arc-tapering
into its thickness. User authorized the proposed single-station build with "Go".

- Basis: R8 four-station assembly; mm, +X forward. Prototype station 45 degrees.
- Fin root remains X=[-1485,-1190], radius 108; centered 220 mm tip chord.
- Height becomes 80 mm (27 mm taller), inferred from the annotation and offered
  as the first visual estimate, not a measured dimension in the image.
- Transition begins at the existing intake-end profile at X=-1123.333333,
  ends inside the fin at its mid-chord X=-1337.5, and belongs to the booster.
- Its roof stays at radial height 136 mm, following the lower red guide.
  Curved Bezier side rails narrow into the blade; the final section is buried
  in the blade to avoid a visible capped end. The joint is position-matched;
  tangent continuity across the stage seam is not claimed.
- Preserve body size, stage seam, axial fin position, all main-stage geometry,
  recess colors/materials, and the other three R8 stations for comparison.
- Outputs: `STEP/halberd_r9.step`, `halberd_r9_separated.step`, and a cropped,
  unclocked review-only `halberd_r9_focus.step`.
- Next gate: user review of this one station before repeating the revision.

## Delivered evidence

- [Full prototype](http://127.0.0.1:3247/?file=STEP/halberd_r9.step)
- [Separated prototype](http://127.0.0.1:3247/?file=STEP/halberd_r9_separated.step)
- [Cropped local review](http://127.0.0.1:3247/?file=STEP/halberd_r9_focus.step)
- [Side, oblique and top board](reviews/Halberd_R9_Prototype.png)

`checks/check_halberd_r9.py` passed on saved artifacts: 80 mm fin height,
220 mm tip chord, radial tip 188 mm, exact seam contact with zero positive-volume
main-stage overlap, continuous roof samples through the bridge into the blade,
19769.499 mm3 booster contact, positive nozzle/fin clearances, and correct separated
ownership. All 22 other parts match R8 by Boolean equivalence and colors; full-state
material sidecars match their document hashes and twelve named finish assignments.
All 46 full-state placements and three cropped focus solids pass positive-volume,
topology, closed-shell and self-intersection checks. Report: `reviews/halberd_R9_checks.json`.

Five snapshots were directly inspected. The top view was reframed with explicit
Y-up after its initial default orientation made the narrow transition too small.
The side guide is a continuous roof; the curved side taper becomes hidden where
it enters the blade before its buried mid-chord endpoint. Cropped focus geometry
has deliberate cut faces and is not the full asset. The other three fins remain
53 mm high pending approval of the local revision. No engine/export acceptance.
