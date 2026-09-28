# R15 — four-face service-cover pass

Date: 2026-09-26. State: **`cad-review`**; built, checked and directly reviewed
by the primary model. Implementation authorized by the user's request to resume
detailing after the R14 junction repair. User subsequently requested continuing;
[R16](R16_BODY_JOINT_CONTRACT.md) carries this family unchanged and adds the next
local joint prototype.

## Active context

- Baseline: `STEP/halberd_r14.step`, composed by `src/halberd_r14.py`.
- Preserve the R14 cleaned booster junctions, all approved exterior geometry,
  stage separation, intake channels and dark backs.
- Carry the R13 service-cover treatment onto the other three **flat faces**,
  at body-clock angles 0/90/180/270 degrees. Intake/fin stations remain the
  separate diagonal set at 45/135/225/315 degrees.
- Each cover stays centered at X=-320 mm. Exact copied geometry: 124x30 mm
  seat, 1.2 mm depth; 120x26 mm cover, 0.35 mm rim bevel, 0.15 mm skin recess;
  recessed border and two slotted fasteners. Preserve current colors.
- Keep the original dorsal cover and its labels. New covers/borders are
  numbered 2..4; new fasteners 3..8. Add three seats and 12 detail objects,
  giving 39 parts per full state and 16 service-detail objects in total.
- The 80–120 surface-detail-object range remains a whole-model planning target,
  not a requirement to fill this one region. This pass establishes the repeated
  cover family; body joints, fin-root and nozzle detail remain later passes.

## Verification and review gate

- Exact copies of the saved original cover/hardware at each rotated station;
  all 26 unaffected R14 parts identical in geometry/color.
- Body difference localized to the three new seats; no extra outer volume,
  unchanged R14 booster assemblies, correct stage transforms and open channels.
- All detail components seated, recessed within the old skin, clear of each
  other except intended seat support; real slots and countersink clearances.
- Material assignments resolved by role/property, sidecar hashes validated;
  every saved full/focus placement checked for valid closed positive solids
  and self-intersections. Review crop must match the full saved document.
- Primary inspects opposed assembled and close-up views, cardinal-face views,
  a cropped end view showing fourfold layout, and separated state.
- New detail families require a local prototype before repetition. No engine
  export or runtime work is authorized by this pass.

## Verified result

- Added `src/halberd_r15_shapes.py` and assembled/separated/focus entrypoints.
  Full artifacts contain 39 parts; focus contains the cropped main body and
  16 service-detail parts. All three `STEP/halberd_r15{,_separated,_focus}.step`
  outputs have hash-bound material sidecars.
- `checks/check_halberd_r15.py` passes: 26 unchanged R14 parts; exactly three
  new 1.2 mm seats; four rigid copies of the original cover family; correct
  recessed heights, slots, supports and countersink clearance; all detail pairs
  and non-body baseline interference checks; open channels; no silhouette
  expansion; exact stage transforms; materials; and all **95 saved placements**.
  Primary added the all-detail-pairs check and reran the full checker successfully
  with `CADGEN_DAEMON=0`. Evidence: `reviews/halberd_R15_checks.json`.
- Primary directly inspected `reviews/Halberd_R15_Four_Face_Covers.png`, including
  four cardinal views and cropped end view, plus full-resolution focused opposed
  obliques, whole/opposite and separated images. The repeated covers sit cleanly
  on each flat between the diagonal intakes, with consistent proportions and
  small hardware. The inherited dark perimeter remains relatively prominent in
  close-up; the full-model surface remains mostly plain outside this one band.
- This establishes one repeated detail family (16 objects), not the entire
  80–120-object detailing target. Next new family: a local body-joint/interface
  detail prototype for review before repetition, followed by fin-root/nozzle
  work in their own local gates.

## Review links

- [Four-face detail crop](http://127.0.0.1:3247/?file=STEP/halberd_r15_focus.step)
- [Whole model](http://127.0.0.1:3247/?file=STEP/halberd_r15.step)
- [Separated stages](http://127.0.0.1:3247/?file=STEP/halberd_r15_separated.step)

Launcher reused the correct study root on port 3247; all three page URLs returned
HTTP 200. No engine/runtime or physical engineering validation is claimed.
