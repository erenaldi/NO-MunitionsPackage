# R17 — Kris-scale surface-detail pass

Date: 2026-09-27. State: **`blocked`** — user rejected the full surface layout
for excessive repetition and insufficient design. Independent critique and
primary reassessment agree; see [R17 design critique](R17_DESIGN_CRITIQUE.md).
Saved geometry remains technically validated, and artifacts are retained.
The count-driven brief below is historical, not authorization to repeat it.
User explicitly requested increasing
Halberd's surface detail to the measured Kris reference level (222 detail
instances). Aim **223** meaningful detail instances, allowing measured layout
corrections within220–230 rather than padding a numerical total.

## Authority and preservation

- Baseline: `STEP/halberd_r16.step`, `src/halberd_r16.py`; R13/R15 cover language
  and R16 seam/small-fastener language have been reviewed by the user.
- Keep the3370 mm outer envelope, approved intakes, fin silhouettes, R14 clean
  booster fin/fairing unions and stage transforms. Preserve black recess backs.
- All additions are exterior game-art details. No functional propulsion,
  guidance, structure, actuation or real-world manufacturing claim.
- New fin-root and nozzle implementations must be built/check-rendered locally
  for primary visual inspection before propagation. Reuse the accepted visual
  language; any material new style choice returns to the user.
- Preserve old sources/artifacts and unrelated concurrent work. New source and
  outputs are R17. Do not touch the shared CAD runtime or engine/plugin files.

## Layout budget (instances, excluding the23 primary R16 forms)

| Family | Layout | Objects |
|---|---|---:|
| Service covers | 8 axial stations ×4 cardinal flats ×(cover+border+2 screws) |128|
| Existing nose joint | Existing R16 liner+4 screws |5|
| Flat-face joint accents | 4 axial rows ×4 flats ×(fine liner+1 screw) |32|
| Fin-root surface interfaces | 8 fins ×(conformal narrow strip+4 screws) |40|
| Nozzle rim hardware | 2 stage nozzles ×(recessed annular liner+8 screws) |18|
| **Total** | |**223**|

Service cover stations (X center / cover length / cover width, mm): main
(-950/80/18), (-750/120/26), (-550/72/18), **(-320/120/26 existing)**,
(-80/90/22), (180/120/26), (440/72/18); booster(-1450/90/22).
Keep covers below skin with real seats, rounded bevels and paired slotted heads;
scale screw end spacing with cover length, not head size. Variants derive from
the approved template; avoid filling every gap with another identical panel.

Flat-face seam accents: main X=-850,-650,-200,320. Each is a short transverse
line on a60 mm wide cardinal flat (nominal50 mm tangent length),1.3 mm axial
seat width and0.6 mm depth, recessed liner0.2 mm below skin, one slotted fastener
7 mm aft. Stop before the corner intake skin; do not wrap grooves across channels.

Fin-root strips: shallow conformal insets on a lower exposed side face near each
root, with four small slotted heads; exact support location/depth requires the
saved-geometry local probe. Preserve all fin/fairing outer union geometry apart
from these cosmetic recesses, and never reintroduce overlapping exposed skins.

Nozzle rims: recessed face ring and8 small axial-facing fasteners per stage,
inside the existing neutral mouth lip. Main mouth X=-1123.333333, booster
mouth X=-1685. Preserve the open dark funnel/back; primary checks the separated
main nozzle as well as the booster. Exact radii/seat depths require the local
saved-geometry probe. Details on booster remain booster-owned.

## Validation and review

- Publish a label/category inventory for final actual count, distinguish major
  forms from details, and retain a map of every altered host and its cutter set.
- Compare unchanged R16 parts and existing21 details against saved baseline;
  altered hosts must equal original minus only their localized planned cutters.
- All new objects inside old host envelopes; supporting contact documented,
  no detail/detail or unintended detail/other-host intersections. Preserve actual
  R14 clean junctions; verify all inherited stage transforms, nozzle bores and
  four open intake channels.
- Validate material/hash binding, actual recess bounds, exact fourfold/eightfold
  placement as applicable, slot presence, focus/full identity, and ALL saved
  full/focus placements for positive valid closed single solids/self-intersections.
- Primary personally inspects opposed full views, all four sides, both nozzle
  close-ups, main/booster root details and cropped panel/seam density. Compare
  actual Kris views at whole-model and detail scales; count alone cannot pass.
- Final boundary is a full-detail **CAD review candidate**, with user acceptance
  pending; no engine/runtime promotion.

## Local interface gate — 2026-09-27

Primary inspected all six actual fin/nozzle prototype views. Initial dark16 mm
fin strips were too heavy; changed them to52×9 mm and casing gray `#A7B0B7`,
with nozzle rings using existing metallic gray `#87939B`. Rebuilt all pilots,
reran the unchanged interface checker and inspected all six refreshed views.
The corrected appearance fits the established recessed small-hardware language
and is selected for the user's requested whole-model expansion.

Evidence: `src/halberd_r17_interface_shapes.py`,
`checks/check_halberd_r17_interfaces.py`,
`reviews/halberd_r17_interface_checks.json`;38 saved placements pass. Both fin
strip pockets are0.8 mm deep/0.2 mm inset; shortened screw seats1.02 mm deep.
Measured remaining host thickness at the tightest booster screw is0.737 mm
(visual-model support evidence only). Nozzle rings occupy radii70.25–72.75;
eight heads at radii91.5(main)/78.4(booster) remain recessed and clear of bores.
Final integration must reuse these exact prototypes/cutters and verify their
rotation/ownership rather than selecting new native face indices on copies.

## Full-pass result and verification — 2026-09-27

**Actual count: 223 detail instances + 23 primary forms = 246 parts per full
state**, matching the planned family table above. This adds 202 detail instances
to R16 while retaining its existing 21. The selected Kris has 222 detail instances
under the documented conservative counting convention.

- Main source: `src/halberd_r17_shapes.py`; per-host cutters, detail ownership,
  family assignments and pose maps are exposed by `build_components()` and
  recorded in `reviews/halberd_r17_layout.json`.
- Built full, separated, body, main-fin, booster-fin and paired-nozzle review
  STEPs, each with material sidecar. Naming is `STEP/halberd_r17.step` plus
  `_separated`, `_focus`, `_main_fin_focus`, `_booster_fin_focus`, `_nozzle_focus`.
- Primary caught the seam fastener cutter stopping below the original skin;
  extended its countersink through Z=100.3, rebuilt all six outputs and checked
  all 16 openings. This repair did not alter the approved screw shape or seats.
- Independent checker `checks/check_halberd_r17.py` passes all **555 saved
  placements** (246+246+25+7+7+24): positive single solids, topology, closed-shell
  and self-intersection checks. Primary reviewed the checker, changed support
  measurements to use saved detail shapes explicitly, added their source/saved
  Boolean identity comparison, and reran the complete checker successfully.
- All 34 unchanged R16 parts retain geometry/colors, including existing detail
  objects and dark back faces. Ten changed hosts equal only the original minus
  their declared cutter sets; no gained volume. All stage transforms remain exact.
- All 202 new details remain within the old host skin, have zero host-volume
  overlap and nonzero supporting face area (minimum 3.836 mm²). All new detail
  pairs and non-owner candidates pass interference checks; inherited baseline
  contacts are preserved rather than represented as new clearance claims.
- Fourfold/eightfold copies, 120 new slotted heads, 16 visible seam screws,
  open nozzle bores, four intake channels, 3370 mm length, focus/full identity
  and all six material sidecars pass. Report: `reviews/halberd_r17_checks.json`.
- The layout JSON's `R17_GATE2_BUILT_CHECKER_PENDING` string is a historical
  source/build checkpoint; the separate hash-bound check report above is the
  current validation result. Do not edit the checkpoint to imply a new build.

## Historical primary visual review — superseded by design critique

`reviews/render_r17.py` produced 16 fresh views and two boards:
`Halberd_R17_Kris_Comparison.png` and `Halberd_R17_Detail_Review.png`.
Primary directly inspected both boards, opposed full models, all four cardinal
sides, front/aft, separated state and a full-resolution body-detail view; boards
also show both final fin roots and both final nozzle coupons.

The expanded covers form consistent rows on the four flats; varying lengths
break up the repeated template, while fine short seams and recessed hardware
retain space around the diagonal intakes. The light fin strips and metal nozzle
rims are subordinate to the main silhouette. The model now has substantially
broader detail coverage than R16. Its layout is more regularly patterned and its
panel borders heavier than Kris's; matching the instance count does not establish
identical visual complexity or real-world engineering fidelity.

`src/kris_full_reference.py` rigidly reorients the actual selected 270-object Kris
STEP to +X-forward for the new whole-model view. The comparison board uses
fit-to-frame views, not equal physical scale. Original reference data is unchanged.

## Review links and next step

- [Full R17](http://127.0.0.1:3247/?file=STEP/halberd_r17.step)
- [Separated stages](http://127.0.0.1:3247/?file=STEP/halberd_r17_separated.step)
- [Body covers and seams](http://127.0.0.1:3247/?file=STEP/halberd_r17_focus.step)
- [Main fin detail](http://127.0.0.1:3247/?file=STEP/halberd_r17_main_fin_focus.step)
- [Booster fin detail](http://127.0.0.1:3247/?file=STEP/halberd_r17_booster_fin_focus.step)
- [Both nozzle rims](http://127.0.0.1:3247/?file=STEP/halberd_r17_nozzle_focus.step)

Launcher reused the correct study root on port 3247; all six page URLs returned
HTTP 200. Next is user review of the full-detail CAD candidate, particularly
layout density and panel-border weight. Production export, engine integration
and runtime delivery remain separate unapproved/unverified boundaries.
