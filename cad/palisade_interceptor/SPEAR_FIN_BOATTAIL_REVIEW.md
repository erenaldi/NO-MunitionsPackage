# Spear fin and turning-cap local revision

Date: 2026-09-23. State: `cad-review` for **one** prototype fin plus the
turning-cap boattail. The 2026-09-23 A/Spear selection in `REVIEW.md` remains
the parent concept; its revised fin/cap form is pending user selection.

## Local change contract

- Axial +X points toward the nose; fin radial is the 45-degree station in
  the YZ plane; tangential width follows the fin root. Cap aft face remains
  X=-600 mm and the body seam remains X=-420 mm.
- Retain original A/Spear body, nose, recessed main nozzle, total axial length,
  selected fin architecture and three untouched aft fins as visual context.
- Remove radial span only from **one** candidate fin. The existing fin is at
  radius 101 mm, with root radius 55 mm. The revised fin prototypes target
  94, 95 or 92 mm at the tip; none is repeated around the body yet.
- Rebuild the whole aft cap as a longer boattail: a visibly tapered last
  ~110 mm ending at ~55% of the 62 mm body radius instead of the historical
  76%. Seat the four lateral thrusters on the forward full-radius section of
  the cap and preserve the same detachable interface/main-nozzle exposure.
- Hard boundaries: do not change body/nose, main nozzle, cap seam or total
  length. Do not resize or overwrite `STEP/A_Spear.step` or its approved
  comparison snapshots. Do not assert fit inside the original pod.
- Acceptance views: whole assembled and separated opposed isometrics; side,
  top, aft end and focused changed-fin/cap view. Compare at matched scale
  against the original A model. Check a centerline section or analytic stations
  for the aft cap taper, not just a silhouette render.
- Excluded interpretations: pointed spear-like cap projecting aft of X=-600,
  a cap tapered at the seam (which would break the existing junction), four
  newly patterned fins before the user chooses one prototype, or decorative
  lines in place of actual boattail volume.

## Preview variants (provisional)

| Variant | Changed fin at 45° | Cap |
|---|---|---|
| 1 / Trim | original sweep and chord; tip radius 94 mm | shared boattail |
| 2 / Rake | narrower, more rear-raked tip; radius 95 mm | shared boattail |
| 3 / Broad | clipped span with longer tip chord; radius 92 mm | shared boattail |

Variants 1–3 all keep the remaining three original fin solids as neutral
context. The resulting asymmetric preview is intentionally **not** the
candidate for game delivery; the user's chosen fin shape may be propagated
fourfold only after local visual approval and a new whole-silhouette check.

## Delivered local review packet

- Three assembled and three separated preview artifacts:
  `STEP/Spear_{Trim,Rake,Broad}_Boattail.step` and corresponding
  `_Separated.step`. Every preview retains the original three other fins;
  **whole-preview maximum radius stays 101 mm** until a fin is selected and
  patterned. The one changed fin is darkened for identification.
- Local context artifacts: `STEP/Spear_{Trim,Rake,Broad}_Fin_Focus.step`
  (unchanged body and just the one new fin); `STEP/Spear_Boattail_Cap_Focus.step`
  (cap plus four thrusters); and matching original fin/cap focus artifacts.
- Source: `src/spear_revision_shapes.py` and ten thin decorated entrypoints.
  `src/check_spear_revisions.py` independently reads the serialized artifacts;
  `src/render_spear_revisions.py` emits the matched review packet.
- `reviews/Spear_Fin_Boattail_Comparison.png` compares old A with all three
  local prototypes in full, aft-fin closeup, isolated cap and separated views.
  Individual snapshots and JSON jobs reside in `reviews/`.

## Verified measurements and observations

| Fin | Original tip radius | Prototype tip radius | Difference |
|---|---:|---:|---:|
| Trim | 101 mm | 94.008 mm | −6.992 mm |
| Rake | 101 mm | 95.008 mm | −5.992 mm |
| Broad | 101 mm | 92.008 mm | −8.992 mm |

- The cap's aft section radius at X≈−599.5 is **34.193 mm** versus the
  historical aft profile near 47.12 mm; its shoulder radius at X=−485 is
  **62.0 mm**. The taper increases monotonically aft-to-forward at checked
  stations, and the X=−420 body-side seam remains full-size. The four thruster
  housings were seated forward of X=−500 on the untapered cap shoulder.
- `src/check_spear_revisions.py` PASS for all three pairs: original body,
  original main nozzle and three untouched fins Boolean-identical to A;
  prototype fin seated, four cap thrusters attached; all isolated focus STEP
  components match the assembled geometry; and separated component geometry
  matches after the cap's review translation. Report:
  `reviews/spear_revision_checks.json`.
- Strict `cadgen step inspect validate --every-placement` PASS for **all 12**
  new previews and focused STEP files, each with zero failures (six full
  exports 11 occurrences / 8 prototypes; four fin/cap focus artifacts 2/2
  or 5/2; two original focus artifacts 2/2 and 5/2).
- The primary model directly inspected the four-way board, prototype and
  original cap closeups, changed-fin closeups and a separated-state image.
  The boattail now reads as an actual aft cone rather than a short chamfer.
  Fin differences remain intentionally subtle at whole-missile scale; the
  local fin row makes their planform contrast legible. **Trim** is the
  provisional recommendation because it preserves the approved swept-fin
  rhythm with the smallest form change; it is not user approval.
- The CAD Viewer for `cad/palisade_interceptor/` is live at
  `http://127.0.0.1:3246/`; all six review-state STEP URLs and the isolated
  cap URL returned HTTP 200.

## Gate

User chooses Trim, Rake, Broad, or revises the boattail/fin. Then apply that
one approved local fin to the other three stations and rerun the assembled,
separated, clearance and silhouette checks before a CAD-approval claim.
Neither the asymmetrical studies nor the original pod have passed fit review.

**User feedback (2026-09-23):** "Broad is good but ill upload a picture for the
fins." Treat Broad as a promising local comparison, **not** approval to repeat
it. The incoming picture is the next visual authority for fin shape; inspect
it directly, reconcile any difference with Broad in a single-fin context,
then seek approval before fourfold propagation. No image file has been
received or assigned a path yet.

## User fin-outline reference — 2026-09-23

The user supplied a dark-background blue-line image in chat. Direct visual
inspection shows a very low, long trapezoidal side outline: straight root
along the bottom, almost horizontal long outer edge, short aft bevel at left,
and a longer forward bevel at right. Approximate drawing proportions, **not
dimensioned measurements**: base from image X≈103…564 (461 px), outer edge
X≈124…505 (381 px, ~83% base chord), height ≈41 px (~9% base chord).
Assumption for this local study: the right of the image is +X/nose-forward.
This is an interpretation for review, not proof of how the drawing is mounted.
No durable local file path for the attached image has been established.

Broad's prior outer chord was 82 mm over a 200 mm root (41%), so it misses the
new image's most distinctive feature despite the user's favorable initial
reaction. Build one-fin redraws with a ~165 mm outer chord over the preserved
200 mm root: an aft offset ~10 mm and a forward bevel ~25 mm. Show both a
92 mm tip radius that preserves the earlier "slight" span reduction and a
lower-profile ~79 mm tip radius closer to the drawing's height/chord ratio.
Keep the already verified boattail and three unchanged fins as context.
Only the user can decide whether visual height or the earlier modest-span
constraint takes precedence. Do not pattern either redraw fourfold yet.

## Drawing-led one-fin packet — awaiting user selection

New artifact pairs: `STEP/Spear_SketchSpan_Boattail.step` and `_Separated.step`,
`STEP/Spear_SketchLow_Boattail.step` and `_Separated.step`; isolated one-fin
views `STEP/Spear_SketchSpan_Fin_Focus.step` and
`STEP/Spear_SketchLow_Fin_Focus.step`. The original Broad and common boattail
remain as comparison artifacts. `src/render_spear_sketch.py` produced the
directly inspected matched board:
`reviews/Spear_UserFin_Sketch_Comparison.png`.

| Single-fin study | Root chord | Outer chord | Radial tip | Reading |
|---|---:|---:|---:|---|
| Existing Broad | 200 mm | 82 mm | 92.008 mm | Too short an outer edge for the drawing. |
| SketchSpan | 200 mm | 165 mm (82.5%) | 92.008 mm | Drawing-led long edge and bevels, but fairly tall. |
| SketchLow | 200 mm | 165 mm (82.5%) | 79.009 mm | Same outline with a lower profile closer to the drawing's height/chord. |

All drawing studies retain the source-approved A body/nose/main nozzle and
three old fins. The blue-line drawing is a 2D silhouette, not proof of fin
thickness, aerodynamic function or actual launcher fit. The inspector verified
outer-edge end datums from tessellated exported solids at X=-392/-227 mm,
which preserve the original root datums X=-402/-202 mm. `src/check_spear_revisions.py`
passed all five historical and new one-fin pairs (`reviews/spear_revision_checks.json`);
strict native every-placement STEP validation passed both assembled/separated
states and both fin-focus artifacts, zero failures (11/8 or 2/2
occurrences/prototypes). The first parallel check timed out under contention;
serial rechecks completed successfully for every target. All six new file
paths served HTTP 200 in the workspace CAD Viewer at port 3246.

**Review choice:** Is the image's right side actually the forward/nose edge?
If so, prefer SketchLow for a closer low-aspect silhouette, or SketchSpan to
keep the earlier modest span reduction. A choice must be explicit before
fourfold propagation; the common boattail remains a review candidate.

**User decision (2026-09-23):** selected **SketchLow** in response to the
question explicitly stating that the drawing's right side points toward the
Spear's nose and that the chosen fin would be repeated at all four stations
with the shared boattail. This approves that local fin/boattail direction and
orientation for fourfold propagation, not the unreviewed full assembly, pod
clearance or production export.

## Fourfold candidate — awaiting whole-asset review

- `src/spear_revision_shapes.py::make_selected_spear` repeats the approved
  SketchLow fin at 45°, 135°, 225° and 315° and retains the already reviewed
  boattail. Thin entrypoints emit
  `STEP/Spear_Selected_SketchLow_Boattail.step` and
  `STEP/Spear_Selected_SketchLow_Boattail_Separated.step`. Both are CAD
  **review candidates**, not production meshes or a packaged asset.
- `src/check_selected_spear.py` independently reads those STEP files, original
  A and the local prototype: body/nose and main nozzle match A exactly;
  boattail and four thrusters match the reviewed local prototype; each of the
  four fins is a 90° rotation of the first and attached to the body without
  bridging the separable cap. The cap clears the body and reveals the same
  main-nozzle bore when moved aft. Separated-state geometry is unchanged after
  restoring the review displacement. The report at
  `reviews/spear_selected_checks.json` gives **1200 mm** length and a
  **79.009 mm radial envelope**, measured from all assembled solids.
- Strict native `cadgen step inspect validate --every-placement` passed both
  candidate STEP files, 11 occurrences / 8 prototypes and zero failures in
  each. CAD image snapshots cover opposed isometrics, side, top, nose, tail
  and two separated views. The primary model directly inspected
  `reviews/Spear_Selected_Original_Comparison.png`, the opposed and nose-end
  images and a separated-opposed view. The selected long-low fins retain a
  visibly fourfold arrangement; the stage now has a clear narrowing boattail.
- Both candidate viewer URLs on the existing study workspace at
  `http://127.0.0.1:3246/` returned HTTP 200. The original A remains intact.

The local approval authorizes fourfold propagation only. The newly assembled
whole silhouette awaits the user's visual judgment; pod cell geometry, actual
fit, detailed finish, Unity export and runtime remain separate boundaries.

## Rounded aft-end correction — local gate reopened (2026-09-23)

The user reviewed `reviews/Spear_Selected_Original_Comparison.png` and chose
**revise cap**, identifying the **flat aft face** as the problem. They selected
a **rounded closed tip** rather than a dish, near-point or rear axial nozzle.
This reopens cap/whole-asset visual review; it does not revoke SketchLow's
fourfold fin choice.

Change contract: preserve selected body/nose, four complete fins, 1,200 mm
overall length, cap/body seam X=-420, main nozzle, four lateral cap thrusters
and cap-stage ownership. Change only the cap's rear closure so the long aft
taper ends in a smooth convex, blunt closed form at X=-600, without a prominent
flat circular cut face or a new axial exhaust. Keep its forward shoulder and
thruster locations. Review isolated cap at grazing and end angles plus full
assembled and separated missile before requesting user approval. Preserve the
prior flat-ended boattail STEPs as historical comparison; no pod fit claim.

### Rounded-end CAD packet — user review pending

- New, separately named source entrypoints write
  `STEP/Spear_RoundedTip_Boattail.step`, its `_Separated.step` state, and
  `STEP/Spear_RoundedTip_Cap_Focus.step`. The older flat-ended source/STEP
  artifacts remain preserved. Geometry uses one analytic spherical aft dome
  fused into the boattail; there is no axial nozzle or wide flat rear disk.
- A ruled multi-ring trial produced visible banding. A subsequent smooth loft
  overshot the aft datum to X≈−895.5 mm and failed the independent checker.
  The final spherical dome avoids both defects and returns to the intended
  X=−600…−420 mm cap allocation.
- `src/check_rounded_cap.py` PASS on all three saved STEP documents under
  cadgen 0.6.6: closed positive-volume solids, cap topology/free edges and
  self-intersections checked at assembled/separated/focus placements; body,
  four approved fins, main nozzle and four lateral thrusters match the
  selected prior model Boolean-exactly; cap separation and open main nozzle
  remain correct. Its actual cap-radius probes rise from 6.145 mm at X=−599.5
  through 34.026 mm at X=−566 to 62.0 mm at X=−485. The assembled missile
  remains 1,200 mm long with a 79.009 mm maximum radial envelope. Evidence:
  `reviews/spear_rounded_cap_checks.json`.
- CAD runtime changed concurrently from 0.5.1 to 0.6.6. `cadgen doctor` confirms
  the new skill pin/kernel. Version 0.6.6 removed `cadgen step inspect`; the
  final exported-artifact checks use `read_step` and `cadgen.geometry`
  topology/self-intersection methods instead. Do not attribute the earlier
  0.5.1 native-inspection results to this final rounded-cap revision.
- New `cadgen step snapshot` images were rendered and directly inspected with
  0.6.6's `output` job settings: opposed whole views, side, aft end, isolated
  cap iso/side/aft and separated views. The earlier first render's visible
  rings have disappeared. Comparison:
  `reviews/Spear_RoundedTip_Comparison.png`. The primary model inspected the
  final board, standalone cap iso/side, opposed iso and separated opposed.
- CAD Viewer 0.6.6 restarted for `cad/palisade_interceptor/` at port 3246;
  all three new artifact URLs returned HTTP 200.

Whole-asset visual approval of the rounded termination is still required.
The selected long-low fins remain approved locally; pod fit, Unity/export and
runtime are not established by this review.

## Red-box cap reference — local gate reopened (2026-09-23)

The user dismissed the rounded-tip acceptance popup and supplied a side-view
image with a red box around the *straight cap band*, asking to change the cap
to that profile and add detail to its lateral nozzles. The directly inspected
inline screenshot shows the stage seam at the red box's left edge, a circular
lateral nozzle near the middle, approximately 100 px of constant-diameter
band, ~42 px of boattail and ~33 px of rounded closed end. These are visual
ratios, not measurements; the image has no verified saved filesystem path.

Local axes: +X goes toward the missile nose (left in this side screenshot),
aft is X=−600. Keep selected 1,200 mm body, four SketchLow fins, body/cap
seam X=−420, and cap length 180 mm. Interpret the screenshot as a roughly
100 mm full-radius band from X=−420 aft to X≈−520, a ~46 mm narrowing cone
to X=−566, then a ~34 mm spherical closed tip to X=−600. Keep four lateral
thruster stations within the cylindrical band near X=−470. Preserve cap
release and exposed main nozzle.

For nozzle detailing, prototype **one** of the four cardinal nozzles as a
stepped, compact raised collar around a truly recessed flared opening and
blind throat in the cap skin. Keep the other three existing nozzles for
context; no repeated-nozzle propagation before visual approval. The nozzle
must not accidentally imply an axial tail motor or pierce through the cap.
Inspect the detailed nozzle from a mouth-facing and grazing view plus the
whole cap/round. Distinguish changed local nozzle form from unchanged cap
support and preserve old rounded-tip and flat-ended artifacts for comparison.

### Banded-cap / one-nozzle packet — user review pending

- Built `STEP/Spear_BandedCap_Nozzle0.step`, `_Separated.step`, and
  `STEP/Spear_BandedCap_Cap_Focus.step` from
  `src/spear_banded_cap_shapes.py` and three separate decorated entrypoints.
  They keep the full selected body and four SketchLow fins. Only the cap
  profile and 0-degree nozzle are new; the three other nozzles retain their
  original shape for comparison.
- The new cap has a **100 mm straight band** from X≈−520 to X≈−420,
  a ~46 mm cone from X≈−566 to X≈−520, and a spherical closed tip to X=−600.
  The single revised nozzle sits at X=−470. Its compact stepped outer ring,
  flared opening and radial blind socket are actual CAD volumes; a separate
  dark recessed throat component sits at the socket back. The original
  nozzle was a plain hollow protruding cylinder backed by solid cap skin.
- `src/check_banded_cap.py` PASS against all three serialized artifacts:
  12 labeled valid positive-volume solids in assembled and separated states,
  cap/nozzle/throat positive closed topology and no self-intersections, core
  and all four selected fins Boolean-identical to the prior Spear, the other
  three thrusters unchanged, mouth/lip/cavity/blind-back probes, cap/body
  separation, exposed main-nozzle bore and identical detached components
  after undoing the review translation. Report at
  `reviews/spear_banded_cap_checks.json`: all checked band stations X=−520,
  −500, −470, −440 have **62.0 mm radius**; 1,200 mm total length and
  79.009 mm radial envelope. The detailed nozzle count is intentionally one.
- `reviews/Spear_BandedCap_Comparison.png` compares old rounded cap and new
  straight-band cap in side, isolated-cap side, mouth and matched separated
  views. The primary model directly inspected this board, individual nozzle
  mouth and grazing/side cap captures. The nozzle reads as a stepped dark
  ring at close range; the blind socket wall can still appear as a pale
  crescent from an oblique angle, which is a review concern rather than a
  claimed uniformly dark opening.
- `cadgen 0.6.6` has no `step inspect` command; the saved-STEP checker and
  actual snapshots are the relevant validation. `compileall -q src` passed,
  `cadgen store why src/spear_banded_cap_nozzle0.py` reports current, and all
  three new CAD Viewer links on port 3246 returned HTTP 200.

Next gate: user approves or redirects the cap-band proportion **and** the
one-nozzle detail. On approval, repeat only the tested nozzle treatment at
the other three stations, validate all four deep sockets and the assembled/
separated states, then obtain whole-asset visual approval. Pod fit, game
asset export and runtime remain unverified.

## Cylindrical cap supersession — 2026-09-23

The user rejected the red-box interpretation after inspecting its review
board: "make the Cap just be a basic cylinder and then fillet the back side
facing away from the main body." This explicit direction supersedes both
the shortened cone/hemisphere and the earlier long tapered boattail. Keep a
straight 180 mm cylindrical cap with the same X=−600 rear and X=−420 body
seam, match its seam radius to the existing main body, and round only the
**aft exterior circular edge** with a visible but reversible 22 mm fillet.
The resulting central aft disk is a consequence of an edge fillet, not an
axial nozzle; its size is for the user to judge in the actual CAD views.

Preserve all four selected SketchLow fins, original body/nose/main nozzle,
stage split, existing four nozzle stations and the earlier one-nozzle detail
prototype. Change no other cap or body edge. Produce isolated side/end and
assembled/separated packet; inspect the body-side seam for a step or clash.
The three other nozzle details remain gated on local user approval.

### Cylindrical-cap CAD packet — user review pending

- The new `src/spear_cylinder_cap_shapes.py` produces a constant-radius
  **180 mm cylinder** at radius 60.76 mm, matching the body's aft seam at
  X=−420. Only the rear outer circular edge has a 22 mm native fillet; the
  aft center remains a plain closed face, with no axial port. All four
  SketchLow fins, missile body and main nozzle are unchanged. The existing
  **one** detailed nozzle plus dark blind socket are reused at the 0° station,
  with three earlier nozzles retained for local comparison.
- Three independent CAD files under `STEP/`: `Spear_CylinderFillet_Nozzle0.step`,
  `Spear_CylinderFillet_Nozzle0_Separated.step` and
  `Spear_CylinderFillet_Cap_Focus.step`. Original A, flat, tapered and
  rounded cap artifacts are preserved as historical alternatives.
- `src/check_cylinder_cap.py` PASS on all three serialized artifacts.
  The rear fillet increases radius from **43.692 mm at X=−599.5** to
  **57.238 mm at X=−590** and reaches exactly **60.76 mm by X=−577**;
  checked sections remain 60.76 mm through X=−421, flush with the body-side
  seam. All 12 full-state components are valid single positive-volume solids;
  new cap/collar/dark throat topology, free-edge and self-intersection checks
  pass. Four approved fins, body and main nozzle, three other nozzles and
  the detailed first nozzle are Boolean-preserved from their respective
  approved or preview sources. Stage separation and open main nozzle remain
  intact. Report `reviews/spear_cylinder_fillet_checks.json`: 1,200 mm length
  and 79.009 mm maximum radial envelope.
- Primary model directly inspected `reviews/Spear_CylinderFillet_Comparison.png`
  plus isolated side/grazing/aft cap and complete assembled/separated views.
  The difference from the taper is plainly visible; the back now reads as
  a rounded **cylinder edge** with a central plain disk. This implements the
  latest explicit request, not the previous all-rounded-hemisphere choice.
- `python -m compileall -q src` passed and `cadgen store why` reports the
  assembled entrypoint current. The 0.6.6 viewer on port 3246 served all
  three new STEP URLs with HTTP 200. There is no `step inspect` CLI in this
  version; the native exported-solid diagnostics above are the applied check.

Next gate: user confirms this cylinder/fillet and the local nozzle detail
before repeating the detailed nozzle at the other three stations. Only
after that may the whole-asset review be reopened for CAD visual acceptance;
pod packing/engine/runtime remain separate and unverified.

## Flush cap/main-body seam correction — local gate reopened (2026-09-23)

After inspecting the cylindrical-cap comparison the user rejected it because
"there is still a change in height right between the mid main body and start
of the cap." Source tracing finds A/Spear's body starts at radius
`62 × .98 = 60.76 mm` at X=−420, then swells to `62 mm` at X=−398; the
current cap is also radius 60.76 mm. The cap/body circles match at the seam
but the body has an immediate 1.24 mm rise and a tangent break directly
forward of it. This is a *real local geometry kink*, not just a gray-material
seam. The body away from that 22 mm region is unchanged.

Build a separate reversible candidate: set **only the main body's first
axial section** at X=−420 to 62 mm, equal to its existing next section at
X=−398, and set the cap-cylinder radius to 62 mm. Keep the 22 mm rear
round on the cap, both stage datums, unchanged hollow body aft nozzle and
unchanged four selected low fins. No new external form may appear at the
body/cap join. Independently compare the old/new bodies for exact equality
from X=−398 toward the nose and sample both sides of X=−420 for radius and
slope. Keep the existing first detailed nozzle and dark blind throat *at one
station only*, with the other three unchanged pending approval. The prior
cylinder-filleted cap pair remains preserved for before/after review.

### Flush-junction candidate — awaiting user visual judgment

- New `src/spear_flush_junction_shapes.py` changes the A/Spear body's initial
  station from 60.76 to 62 mm at X=−420; its next station at X=−398 was
  already 62 mm. The rest of the body, nose, cavity, main nozzle, all four
  SketchLow fins, four cap-nozzle stations and the cap's aft 22 mm fillet are
  preserved. The cap cylinder is also 62 mm radius, so the two geometries
  meet without a radial step. The source-default A/Spear studies retain
  their old 0.98 aft ratio unless this separate candidate is requested.
- Artifacts: `STEP/Spear_FlushJunction_Cap.step`,
  `STEP/Spear_FlushJunction_Cap_Separated.step`, and
  `STEP/Spear_FlushJunction_Cap_Focus.step`. Only the 0-degree nozzle has the
  previously detailed socket/collar/dark backing for local review.
- `src/check_flush_junction.py` PASS on the three serialized files:
  12 valid single positive-volume components per full state, affected body
  and cap topology/free edges/self-intersections checked, original body
  Boolean-identical from X=−398 forward, all protected fins/nozzles and
  separately staged component shapes identical. The old body radius rose
  from 60.792 mm near X=−419.5 to 61.975 mm at X=−398.5; the new body holds
  **62.0 mm** at those stations and at X=−409/−399. The cap matches at
  X=−420.5. Report `reviews/spear_flush_junction_checks.json` records
  1,200 mm total length and 79.009 mm radial envelope.
- Matched views and exported-section chart are in
  `reviews/Spear_FlushJunction_Comparison.png`. Primary model directly read
  the board: the tiny aft-body bulge is removed and the cap is level with the
  first 22 mm of body. A material/part seam remains visible in CAD shading,
  which should not be mistaken for a geometric diameter change. Separated
  cap and nozzle views were also rendered. Syntax compilation passed,
  `cadgen store why src/spear_flush_junction.py` reported current, and all
  three viewer URLs at port 3246 returned HTTP 200.

The change reopens the whole junction's visual gate. Ask the user to inspect
the side/iso views and the section chart before claiming the cap/body seam
is visually accepted. The three other detailed nozzles and pod fit remain
unapproved and unverified.

## Short cap and thinner plate fins — 2026-09-23

The user accepted the flush-junction correction ("Good") and requested a
**50 mm shorter cap** plus a **slight decrease in fin thickness**. The 62 mm
cap/body junction is now the approved local form. The following reversible
CAD variant must preserve its meaning as the seam moves:

- Cap still begins at X=−600, but its forward seam moves aft from X=−420 to
  **X=−470**, making the cap 130 mm long. Preserve the 22 mm rear-edge fillet
  and cylindrical 62 mm section. Extend the 62 mm main-body barrel aft by
  50 mm so the new junction stays flush and the overall 1,200 mm envelope
  does not change. Preserve body solid at and forward of X=−420.
- Move the body-owned main-nozzle geometry and its recessed cavity aft to the
  new seam. The selected four SketchLow fins keep their absolute X stations
  and 79 mm radial silhouette; their root/tip **tangential plate thickness**
  becomes 6.0 / 2.0 mm instead of 7.0 / 2.4 mm. This is a chosen reversible
  interpretation of "thickness," not a change to their visible span or chord.
- Place all four lateral cap-nozzle stations in the 130 mm cap's cylindrical
  band at about X=−535; carry the single previously modeled stepped/recessed
  nozzle and its dark blind throat to that station. The other three remain
  vanilla-style placeholders until the user approves the nozzle detail for
  repetition. No cap-owned object should extend over the new seam.
- Compare full assembled/separated states with the approved flush junction;
  check cap/body/nozzle datums, fins/cap clearance, stored geometry beyond the
  extended region, valid solid geometry, and fourfold fin symmetry. Request
  visual review before advancing the pod-fit or production gates.

### Short-cap candidate — awaiting user review

- New `src/spear_short_cap_shapes.py` writes separately named
  `STEP/Spear_ShortCap_ThinFins.step`, `_Separated.step` and `_Cap_Focus.step`
  through thin decorated entrypoints. The cap spans **X=−600…−470** (130 mm)
  and keeps the 62 mm cylindrical radius and 22 mm aft-edge fillet. The main
  body starts at the new seam and holds radius 62 mm through the old joint;
  total assembled length stays **1,200 mm**.
- The main nozzle now starts at X=−470, with the main-body recess open to
  the same aft face. Four lateral cap nozzles sit at X=−535; the 0-degree
  nozzle remains the **one** detailed recess prototype. The other three are
  unmodified basic shapes, moved with their stage. Fins stay at the selected
  absolute X and radial locations; plate root/tip widths decrease from
  **7.0/2.4 mm to 6.0/2.0 mm**.
- An initial extension created by fusing to the old body passed initial
  export but the independent cross-state Boolean check failed by the entire
  body volume; the first separated snapshot also did not visibly reveal the
  main nozzle. Replaced that construction with one continuous parametric
  loft from the new seam and a continuous recess down to the prior blind
  floor. No checks were weakened. Fresh `src/check_short_cap.py` now PASS
  from saved assembled/separated/focus STEP: valid 12/12/6 labeled solids,
  forward body at X≥−420 Boolean-identical to the prior flush candidate,
  exact stage datums, 62 mm junction, relocated main nozzle and all four
  mid-cap nozzle stations, actual 6.0/2.0 mm fin plate widths, fourfold
  symmetry, cap/body and fin/cap no-intersection, physical open nozzle and
  unchanged geometry after separated-state inverse placement. Affected
  body/cap/nozzle and a representative fin pass topology, closed-shell and
  self-intersection checks. Report: `reviews/spear_short_cap_checks.json`; measured assembled
  maximum radial reach **79.006 mm**.
- `reviews/Spear_ShortCap_Comparison.png` uses matched whole views, a
  180:130 true-scale isolated cap comparison, and a cap-removed main-nozzle
  view. The primary model directly inspected the board and rerendered the
  repaired separated state: the main nozzle reads as an open black recess,
  unlike the failed first body extension. Earlier failed diagnostic images
  remain under `reviews/Spear_ShortCap_diagnostic_*.png` as historical
  debugging evidence, not acceptance views.
- `python -m compileall -q src` passed, the active source entrypoint is
  `current` under `cadgen store why`, and all three new viewer URLs on port
  3246 returned HTTP 200. This is a **CAD visual candidate** only; the user
  has not yet accepted the shortened-cap/thin-fin whole appearance, and pod
  fit, other-three nozzle detail, Unity and runtime remain pending.

## Uniform small-diameter barrel — 2026-09-27

User redirected the shortened-cap review: "The main body needs to be an even
diameter all across (use the current forward smaller diameter as the constant
for the entire body and turning cap)." For this reversible study, interpret
"forward smaller diameter" as the measured **54.56 mm radius (109.12 mm
diameter)** at the current nose-base section X=355. The prior shaft gradually
narrowed from radius 62 mm near the X=−470 cap seam through 57.04 mm at
X=−255, 55.18 mm at X=190, to 54.56 mm at the nose base X=355. Keep the
pointed nose *forward* of X=355, unchanged.

Change contract:

- Rebuild one constant 54.56 mm-radius main barrel from the current cap seam
  **X=−470 to the nose base X=355**, and a matching cylindrical 130 mm cap
  from X=−600…−470. Fillet only the cap's aft edge by the prior 22 mm.
  Preserve total 1,200 mm length and the stage release/motor order.
- Preserve the original pointed nose geometry at and forward of X=355, and
  preserve the body-owned main nozzle at the new X=−470 seam with its
  continuous 37.82 mm-radius recessed cavity ending at X=−367. This reduces
  barrel-wall thickness; do not silently shrink or bury the main nozzle.
- Keep the selected four low trapezoidal fins at their absolute X stations,
  79 mm outer radial tip and 6.0/2.0 mm plate thickness. Their previous
  55 mm root radius would float outside the 54.56 mm shaft; reseat each root
  to 52.5 mm and check actual positive root overlap with the new body.
- Recenter four lateral cap-nozzle stations at X=−535 and lower all mounts
  into the smaller cap skin. Keep **only one** stepped/recessed/dark-backed
  nozzle as the local prototype; three basic counterparts await approval.
  Check openings and blind backs at the new radial datum, including the
  retracted-cap and cap-removed states.
- Do not overwrite the earlier short-cap or historical Spear exports. Produce
  a separate assembled/separated/isolated-cap CAD set plus a matched true-scale
  comparison and an exported-section radius trace. Verify no aft barrel taper
  remains before asking for visual approval. Packaging and runtime follow
  later gates.

### Uniform-barrel study delivered — visual approval pending

- New `src/spear_uniform_barrel_shapes.py` emits
  `STEP/Spear_UniformBarrel.step`, `_Separated.step` and `_Cap_Focus.step`
  through separate decorated entrypoints. The 130 mm cap and long barrel
  hold **radius 54.56 mm (109.12 mm diameter)** from X=−600 to the existing
  pointed-nose base at X=355, except for the cap's 22 mm aft-edge fillet.
  The original A/Spear nose beyond X=355 is Boolean-identical to the prior
  short-cap study. The total length remains 1,200 mm.
- The main-nozzle recess remains radius 37.82 mm and ends blind at X=−367;
  the existing main nozzle stays at X=−470 and exposes its open bore on cap
  separation. Four lateral cap nozzles remain at X=−535 and have been seated
  on the new 54.56 mm cap. Only the 0-degree stepped socket/dark throat is
  detailed; the other three are still basic placeholders pending approval.
- All four selected SketchLow fins keep their axial planform and 79 mm outer
  radial tip. Their plate thickness remains 6.0/2.0 mm; root radius is now
  **52.5 mm** so each fin actually contacts the 54.56 mm barrel. The fins
  consequently project farther above the narrower barrel than before; this
  is visible in the full review and must be judged by the user.
- `src/check_uniform_barrel.py` PASS on all three saved STEP states:
  valid positive single solids (12 full, 6 cap-only), full body sections
  sampled at seven axial stations from X=−469 to 354.5 all exactly 54.56 mm,
  four cap samples also 54.56 mm, positive attachment of all four fins and
  lateral nozzles, main nozzle/floor and blind lateral socket clear, and
  exact stage-owned geometry after undoing cap displacement. The nose at
  X≥355 matches the prior CAD Boolean-exactly; representative body/cap,
  main nozzle, fin and detailed nozzle/throat topology/closure and
  self-intersection checks pass. `reviews/spear_uniform_barrel_checks.json`
  reports unchanged total length and **79.006 mm maximum radial envelope**.
- `reviews/Spear_UniformBarrel_Comparison.png` compares previous short-cap
  and uniform-barrel full/side/separated/cap views at matched scale, with
  an explicit saved-radius graph. Primary model directly inspected this
  board plus individual opposed, cap-nozzle and separated views. The body
  now reads as one narrow-diameter shaft through to the nose transition;
  cap/body interface remains a visual material seam, not a height step.
  `compileall -q src` passed, `cadgen store why` reports the model current,
  and all three CAD Viewer links at port 3246 returned HTTP 200.

Next: user verifies that the **nose-base diameter** is the intended constant
and that the taller-looking fins still match their visual intent. No nozzle
detail repetition, pod fit, Unity or gameplay approval follows automatically.

**User visual decision (2026-09-27):** accepted the full uniform-barrel/cap
shape in `reviews/Spear_UniformBarrel_Comparison.png`: one 109.12 mm diameter
through body and turning cap to the unchanged pointed nose. This closes the
barrel/cap silhouette interpretation and the fin reseating required by it.
It does **not** approve the single prototype nozzle detail for propagation,
nor the eventual four-nozzle CAD packet, actual pod clearance or game delivery.

The user then requested research-backed *real ACM* styling rather than the
single large nozzle. See `ACM_PORT_REVIEW.md` for directly inspected PAC-3
side-thruster photo cues, the one six-port-group prototype, exported checks
and the corrected shortened-cap forward face. User group-detail approval is
pending; three other groups remain unmodified.
