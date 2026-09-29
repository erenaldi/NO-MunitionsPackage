# HKP-1 Palisade housing — three concept directions

Date: 2026-09-27 (A10 approval 2026-09-28). Lifecycle: A2 **open-side
housing silhouette** remains `concept-approved`; the **A10 housing
silhouette** — a 558 mm teal-dome wedge nose (`roof = -211 mm·t³`, belly
flush at −223, blunt 24×12 mm tip) plus a stubbier 345 mm level rear cap —
is the **user-approved housing silhouette**. The user selected A's basic
form, requested the four box skins fill the sides, and approved A2
bare/filled views. Sensor end apertures remain deferred until a separately
reviewed feature gate. The interceptor visual approval at
`../palisade_interceptor/STEP/Spear_ACMWrap.step`
is independent. Authority: `../../plans/2026-09-27-palisade-pod-housing-concepts.md`.

## Active context

- Coordinate/scale: millimetres, +X forward, +Y starboard, +Z dorsal; the
  pod-to-aircraft transform is not measured.
- Preserve: one inverted-U overhead frame, four separate single-tier boxes in
  two-across × fore/aft stations, front/rear integrated sensor ends with an
  outward recessed aperture, and a flush-bottom closed impression. Four box
  shapes are **plain volume placeholders**, not cassette or shutter designs.
- Avoid: a second vertical tier, four-across width, exposed mounting hardware,
  inferred AGM2 donor launcher/door poses or runtime ejection claims.
- Open: aircraft/pylon fit, donor-local transforms, door
  sweep, detailed boxes, individual split shutters and powered release logic.
- Next-gate files: this review, `reviews/Palisade_Underside_Comparison.png`,
  `reviews/Palisade_Dorsal_Comparison.png`, `reviews/A2_OpenSides_Review.png`,
  `reviews/A10_DroopedEnds_Review.png`, `reviews/A10_DroopedEnds_Checks.json`,
  `reviews/A9_ContinuousEnds_Review.png`, `reviews/A9_ContinuousEnds_Checks.json`,
  `reviews/A8_RoundedTips_Review.png`, `reviews/A8_RoundedTips_Checks.json`,
  `reviews/A7_LevelBeam_Review.png`, `reviews/A7_LevelBeam_Checks.json`,
  `reviews/A6_SketchedEnds_Review.png`, `reviews/A6_SketchedEnds_Checks.json`,
  `reviews/A5_ShoulderFront_Review.png`, `reviews/A5_ShoulderFront_Checks.json`,
  `reviews/A4_LongFront_Review.png`, `reviews/A4_LongFront_Checks.json`,
  `reviews/A3_MountFront_Review.png`, `reviews/A3_MountFront_Checks.json`,
  `reviews/A2_OpenSides_Checks.json`, the A2 bare/filled STEP and the pod brief.

## Matched views and contrast

The board images use the same cameras, scale and neutral CAD display per row:

- [Bare/filled underside comparison](reviews/Palisade_Underside_Comparison.png)
- [Bare/filled dorsal comparison](reviews/Palisade_Dorsal_Comparison.png)
- Each direction also has saved full-size side, top, front, rear, underside,
  opposing oblique views in `reviews/` (`review_a.json` and `review_bc.json`
  reproduce them). Primary directly inspected the comparison boards, individual
  opposed obliques, orthographic end/side/bottom and top views. The top views
  conceal the bays on all three; underside views are essential to judge the
  requested four places.

| Direction | Visible structural proposition | Strength | Cost / visual risk |
|---|---|---|---|
| **A — Straight bridge** | Continuous flat dorsal bridge and straight full-height twin side rails; rectangular sensor blocks, a narrow end aperture and a central underside spine/tie. | Restrained, coherent flush box and clear four underside cells. | From above it is almost an unarticulated rectangular slab; weakest character at combat distance. |
| **B — Open crown** | Narrow central dorsal crown, two separated roof shoulders and three full-span ties into chamfered rails; octagonal/faceted sensor ends and side-top channels. | Most explicit structural roof/rail relationship; negative spaces and facets visible from above and below. | Open crown gaps may read busier and require a later pylon/waterproofing interpretation; the three ties are concept architecture, not verified mounts. |
| **C — Slotted shell** | Broad saddle with a shallow longitudinal central valley; roof supported by windowed sidewalls; rounded-rectangular sensor end caps. | Softened end identity and two long windows per side distinguish it from A while the filled state remains one shallow shell. | Side windows reveal inset box skins; C is still rectangular over most of its length and can feel close to A at game distance. |

All three have two restrained opposing 102–105 mm wide recessed end apertures.
No sensor color or electronics is implied by the neutral viewport shading.

## Saved geometry and limits

`checks/check_a.py` and `checks/check_trio.py` pass after serializing all six
STEP states; report: `reviews/Trio_Checks.json`. Every named part is a valid,
positive, closed single solid without reported topology errors; shared housing
solids are Boolean-identical between bare/filled states. Every direction has
four equivalent, separate 1,310 × 180 × 180 mm placeholders centered at
X=±664, Y=±95, Z=−133, and open downward centerlines. Roof/rails and B's
roof ties have measured positive overlap; placeholder solids do not intersect
the housing or each other. The outer envelope is 2,980 × 400 × 223 mm; roof
full thickness A/C 30 mm (C valley 22 mm at center), B crown 24 mm; outer
rail transverse thickness 14 mm. All four boxes and side/end forms share
the Z=−223 underside plane. Measured box-skin gap is 10 mm transverse and
18 mm between fore/aft rows.

The approved Spear is reread from saved STEP as 1,200 mm long with conservative
maximum fin-envelope diameter **158.013 mm**. With an *example*, unmodeled
6 mm wall on each cassette side/end, the remaining half-margin is 4.994 mm
transverse and 49 mm axial; this is tight and excludes actuator/rail/door
space. These are conceptual bounding volumes, not fitted storage boxes or
verified containment of a moving round. The older 400 × 400 mm two-level
packing calculation is not this single-tier layout.

Actual `AGM2_6Pod` missile stations/door sweeps, pylon/airframe proximity,
drop-path and snap-turn clearance, and the user-requested later forced-flight
fallback remain unverified. The CLI's former `cadgen step inspect` command is
unavailable in the installed cadgen; both checkers reopen the saved STEPs and
check every placed solid, intersections and state identity independently.

## CAD Viewer

All six files exist and their Viewer pages returned HTTP 200 on a workspace
instance serving `cad/palisade_pod/`:

| Direction | Bare | Four placeholders |
|---|---|---|
| A | [A bare](http://127.0.0.1:3248/?file=STEP/A_Bridge_Bare.step) | [A filled](http://127.0.0.1:3248/?file=STEP/A_Bridge_Filled.step) |
| B | [B bare](http://127.0.0.1:3248/?file=STEP/B_OpenCrown_Bare.step) | [B filled](http://127.0.0.1:3248/?file=STEP/B_OpenCrown_Filled.step) |
| C | [C bare](http://127.0.0.1:3248/?file=STEP/C_SlottedShell_Bare.step) | [C filled](http://127.0.0.1:3248/?file=STEP/C_SlottedShell_Filled.step) |

## A chosen as the basis; A2 side-skin correction awaiting review

After the user opened both comparison boards in the desktop image viewer,
they chose: “The basic shape of A is good, though the side covers for the
boxes should be removed as the boxes themselves will fill that space.”
This selects A's restrained roof/end-sensor vocabulary, **not** the full-height
side panels. I interpreted the correction as retaining a structural roof-edge
lip only over each bay, with four separate box exterior skins taking the outer
sidewall plane and hiding the landing features in the filled state. The
selected direction is therefore conditional until this new visual packet is
shown and accepted.

- Comparison packet: [original A versus A2 bare/filled from above and below](reviews/A2_OpenSides_Review.png).
- New CAD: [A2 bare](http://127.0.0.1:3248/?file=STEP/A2_OpenSides_Bare.step),
  [A2 filled](http://127.0.0.1:3248/?file=STEP/A2_OpenSides_Filled.step).
- `checks/check_a2.py` PASS from the two saved states: 11/15 valid closed
  solids; all original A bridge/end/aperture parts Boolean-preserved, side
  rails reduced from Z=−223..−24 to Z=−43..−24. Revised four equal placeholder
  sections are 1,310 × 196 × 180 mm at X±664/Y±102/Z−133; their outside
  side faces coincide with the sensor housings' Y=±200 mm faces and their
  bottom is Z=−223. No placeholder/frame or placeholder/placeholder solid
  overlap; positive roof/lip contact. Exterior remains 2,980 × 400 × 223 mm.
  The illustrative 6 mm wall leaves 12.994 mm transverse half-margin around
  the 158.013 mm round envelope and 49 mm axial half-margin. Report:
  `reviews/A2_OpenSides_Checks.json`.
- Primary directly inspected final A2 bare/filled isometrics, opposed underside
  views, side, bottom, and the matched comparison. Bare A2 now reads as a
  roof spanning two end blocks with shallow lip rails, rather than a complete
  side shell; filled A2 reads as one rectangular housing with a visible
  fore/aft seam across the box skins. Box side finishes and future shutter
  clearance still need separate design.

Next gate: user judges **A2** and approves or redirects the changed bare/filled
reading. No detailed boxes, split shutters, export or runtime changes follow
from the earlier A selection alone.

## A2 housing visual approval — 2026-09-27

The user viewed `reviews/A2_OpenSides_Review.png` in the desktop image viewer
and explicitly chose **“Approve A2 sides.”** This approves the housing
silhouette and the division of visible side skin between roof-edge frame,
four separate placeholder boxes and unchanged rectangular sensor ends.
The earlier selection of A and this A2 approval supersede the full-height A
side covers in the original three-way comparison; B and C remain unselected
studies. Do not infer approval of detailed box internals or shutters from
this concept-level decision. Before detailed CAD or production/export,
measure the real donor rack station/door sweeps and aircraft clearance,
and resolve any fit conflict with the user rather than silently shrinking
the approved interceptor or treating the sample 6 mm walls as hardware.

## New mount-front reference — front-only gate (2026-09-27)

The user supplied an inline ResKit BRU-61/GBU-39 promotional image and said:
“Just the mount front (not the GPU-39s themselves) is what I want to emulate
for the frame +sensor package (Obviously for our usecase, the central sides
wouldn't be there”. The image is an in-chat attachment, with no repository
file path asserted here. Direct observations: a long restrained dorsal mount
beam with broad, smooth top planes; the forward mount cap narrows into a
rounded, shallow blunt fairing; the pictured side hardware and GBU-39 rounds
belong to that *reference product*, not to the approved Palisade design.
Use only the **front mount fairing's form and its relationship to the beam**
as visual cues; keep the A2 central sides open when bare and box-skinned when
filled. A2's rear end is preserved until separately directed. The forward
outward aperture stays a distinct recessed sensor cue, without implying the
real rack has a Palisade sensor. This dependent front-shape change reopens the
front silhouette's `cad-review` gate while leaving the user-approved A2 side
treatment intact. Actual scale, aft face and mechanisms cannot be extracted
from the promotional perspective photo.

## A3 short front-fairing prototype — awaiting user judgment

The first reversible interpretation is a five-station rounded-rectangular
fairing on the **forward 165 mm end only**. It narrows from a 400 × 223 mm
beam interface at X=1325 to a 270 × 165 mm front face at X=1490, retaining
the distinct recessed forward aperture. The rear end, all four open-side
  box volumes, frame and single-tier layout remain exactly A2, with no game
sensor function implied. Sources are `src/mount_front.py` and three thin
`src/A3_MountFront_*.py` entrypoints; the original A2 states remain intact.

- [A2/A3 bare and filled comparison plus isolated front](reviews/A3_MountFront_Review.png).
- [A3 bare](http://127.0.0.1:3248/?file=STEP/A3_MountFront_Bare.step),
  [A3 filled](http://127.0.0.1:3248/?file=STEP/A3_MountFront_Filled.step),
  [isolated front](http://127.0.0.1:3248/?file=STEP/A3_MountFront_Focus.step).
- `checks/check_a3.py` PASS on saved A3 bare/filled/focus STEPs: all placed
  parts valid closed positives; only the forward sensor shell differs from
  A2, with no material added outside the old block. The rear sensor and
  aperture, A2 roof/lips and four side-skin placeholders are Boolean-exact;
  no box/fairing or box/frame intersection. Original sample envelope stays
  2980 × 400 × 223 mm and selected Spear remains 158.013 mm maximum
  fin-envelope diameter. Report `reviews/A3_MountFront_Checks.json`.
- Primary visually inspected full bare/filled front obliques and isolated
  top, side, end and close-up. It reads as a **small rounded nose plug** on
  the A2 beam. Relative to the image's much longer tapered mount forebody,
  the 165 mm axial treatment is visually short; the photo supplies no scaled
  length. This is a fidelity question for the user, not a geometric pass
  criterion. Extending it back over the roof would reopen more of the A2
  bridge and require a fresh silhouette review. The rear remains the A2 block
  by explicit front-only assumption.

This prototype cannot establish real station pose, clearance or any flight
behavior. Ask the user whether this short front treatment captures their
cue or whether the mount-like taper should run farther aft over the dorsal
beam before detailing anything.

## A4 extended, lower mount-front study — awaiting visual review

After the A3 comparison was opened in the user's image viewer, the user
requested **“extend it and it should taper towards a section lower in height
too (refer to the picture)”**. A4 implements a reversible geometrical
interpretation: the roof begins descending at X≈650, and the front housing
continues that progression to X1490, where its end face has narrowed to
270 × 125 mm rather than A3's 270 × 165 mm. A4 still spans 2980 × 400 ×
223 mm and retains the approved A2 box-side skins and aft sensor end. The
reference establishes the slope and mount-front impression, not these
unmeasured dimensions.

- [A3 short versus A4 long/lower matched board](reviews/A4_LongFront_Review.png),
  plus ten A4 saved-STEP oblique/side/top/end/bottom snapshots from
  `review_a4.json`. [A4 bare](http://127.0.0.1:3248/?file=STEP/A4_LongFront_Bare.step)
  and [A4 filled](http://127.0.0.1:3248/?file=STEP/A4_LongFront_Filled.step)
  Viewer links were checked with HTTP 200.
- `checks/check_a4.py` PASS on both saved artifacts: 11/15 closed valid parts;
  only dorsal bridge and forward sensor shell differ from A3. Both new forms
  are subtractive within their A3 volumes, roof lips/rear sensor/apertures
  and four box skins are Boolean-identical, box/frame intersections zero,
  roof-to-lip intersections positive. Forward aperture remains inset; the
  measured Spear diameter stays 158.013 mm. Report:
  `reviews/A4_LongFront_Checks.json`.
- Primary inspected the complete bare/filled obliques, side, top, bottom and
  comparison board. The longer roof break is visible from above and the
  nose-end is lower in side silhouette, although at entire-pod distance it
  remains a restrained slope rather than a full replica of the promotional
  mount. The roof tapers only above the box volume; it does not shorten or
  displace the approved four-place layout. No claim about real pylon clearance
  or mounting geometry is supported.

**Next visual gate:** user accepts or corrects A4's foredeck slope and lower
front face. Any fit-driven length change or further whole-roof redesign
reopens the affected silhouette gate, while the A2 no-side-cover decision
remains approved.

## Exact mount-image analysis and A5 shoulder prototype — awaiting user review

After inspecting A4, the user asked an “astra agent” to analyze the image and
try again. No Astra-named subagent is available in this session; after the
user named the download, the primary directly read the exact
`C:\Users\erena\Downloads\GBU-39-SDB-8-pcs-BRU-61-rack-set-scale-model-kits.jpg`
and dispatched the available **multimodal analyst** for read-only observations
of that image and the saved A4 packet. The analyst observed a *blunt rounded
front cover, visible shoulder and short nose-to-foredeck transition flowing
into a much longer straight beam*; A4 instead still looked like a terminal
cap. The primary rechecked those visible cues against the actual image. The
reference has only one oblique view; neither its physical length nor exact
section heights can be measured. The bombs, side retention hardware and
mounting fasteners in the promotional image are not pod design authority.

A5 uses a broader raised forward shoulder to make the top mount form legible.
The added dorsal cover starts near X740, rises to Z+28 from X810–1000, then
descends toward the unchanged A4 low/blunt front face at X1490. It is fused
into the bridge as a single solid; central side covers stay absent when bare
and the four separate box placeholders still make the outer sidewall when
filled. The rear sensor and end apertures stay unchanged.

- [Matched A4/A5 bare, filled and side board](reviews/A5_ShoulderFront_Review.png)
  and ten A5 full-size saved-STEP views (`review_a5.json`).
- Saved [A5 bare](http://127.0.0.1:3248/?file=STEP/A5_ShoulderFront_Bare.step)
  and [A5 filled](http://127.0.0.1:3248/?file=STEP/A5_ShoulderFront_Filled.step)
  Viewer pages returned HTTP 200.
- `checks/check_a5.py` PASS on both serialized STEP states: 11/15 valid,
  closed positive-volume parts; A4 body/roof material not lost, only the
  local cover volume added to the dorsal bridge; sensor ends, apertures,
  A2 side lips and four 196 mm-wide box placeholders are Boolean-identical;
  no box/frame overlap and roof/lip contacts remain positive. Outer envelope
  is 2980×400×251 mm (including the 28 mm raised shoulder); Spear's saved
  maximum fin-envelope diameter is 158.013 mm. Full report:
  `reviews/A5_ShoulderFront_Checks.json`. The study does not verify donor
  launcher poses, shutter arcs or aircraft clearance.

Primary directly inspected the exact image, A5's bare/filled top and
underside obliques, side/top and matched board. A5 produces an obvious front
shoulder that A4 lacked, but the prototype still looks somewhat like a
raised plate on a rectangular beam. The reference's rounded/wrapping
forebody and the box-proportion constraints are not resolved by the STEP
checks. This is **not** visual acceptance or a claim of reference fidelity.
Ask the user whether this captures their intended mount-front cue; if not,
the next revision must improve the fairing-to-beam flow rather than adding
mount hardware or copying the GBU-39 rounds.

## User sketch gate — A4 opened for annotation

After inspecting the A5 board, the user said **“its still not what I'm
looking for”** and asked to open **“current V4”** in CAD Viewer to sketch the
intended form personally. Interpreted V4 as the saved
`STEP/A4_LongFront_Filled.step` artifact (the study's A4 version); the existing
Viewer serving `cad/palisade_pod/` on port 3248 returned HTTP 200 and its A4
filled URL was opened in the local default browser. A4 bare remains available
at [A4 bare](http://127.0.0.1:3248/?file=STEP/A4_LongFront_Bare.step).

A5 is **not** user-approved. Await the user's annotated CAD Viewer screenshot
or a correction if they meant a different V4 artifact. The Viewer toolbar's
Draw mode and Copy screenshot can convey their markup through the clipboard;
annotations alone do not change any STEP. Preserve A2's separately approved
open sides and the untouched A4/A5 sources while interpreting the sketch.

## A6 — two-ended interpretation of the user's annotated A4 side view

The user supplied a screenshot from the A4 filled CAD Viewer with red curves
at **both** ends. The forward stroke starts near the existing nose and arches
to a small rounded tip beyond it; the aft stroke makes a shorter rounded
termination extending beyond the former rectangular end. This is a side-view
shape annotation, not an orthographic dimensioned drawing, so neither the
exact widths nor pixel-to-mm scale are authoritative. Straighten and smooth
the hand-drawn contours instead of reproducing pen jitter. No other visual
approval was implied by posting the sketch.

The reversible A6 CAD makes the front fairing 300 mm longer than A4 and the
rear 220 mm longer. Both narrow in height and width toward restrained blunt
sensor faces with outward recessed apertures. The A4 dorsal beam, A2 roof-edge
lips, four separate flush-side placeholders and all four downward exits are
preserved. This leads to a **3500 × 400 × 223 mm** measured study envelope;
the initial 2.8–3.0 m length was provisional, but actual aircraft fit is now
even more important to measure. Do not claim the annotated picture confirms
the new dimensions or launch clearance.

- [Matched A4/A6 side, A6 bare/filled and end comparison](reviews/A6_SketchedEnds_Review.png)
  (the first row is scaled to common physical length); 11 full-size saved-STEP
  views in `review_a6.json` include opposed obliques, side, top, bottom and
  both outward sensor faces.
- [A6 bare](http://127.0.0.1:3248/?file=STEP/A6_SketchedEnds_Bare.step)
  and [A6 filled](http://127.0.0.1:3248/?file=STEP/A6_SketchedEnds_Filled.step).
- `checks/check_a6.py` PASS from both serialized STEPs: 11/15 valid closed
  positive solids, all A4 components except the four front/rear sensor
  shell/aperture parts Boolean-identical; four unchanged 1310×196×180 mm
  placeholders; no intersections with frame/one another and four sampled
  downward centerline paths open. Saved tip probes confirm taper and recessed
  end apertures. The independently reread Spear measures 1200 mm length and
  158.013 mm maximum fin-envelope diameter. Report:
  `reviews/A6_SketchedEnds_Checks.json`.
- Primary inspected the final bare/filled obliques, side, top, underside,
  outward front/rear views and board. From the side A6 now reads as two
  elongated curved fairings rather than A4's terminal-cap/front and square
  rear; with boxes installed it remains a single tier. The front resembles
  a thin wedge more than the original mount photograph in oblique view;
  whether the sketch intended this narrow face must be decided by the user.

**Current gate:** user reviews A6's silhouette against their red curves,
especially whether both tip heights/lengths and the end-on widths read as
intended. Any further detailed cassette/shutter design remains dependent on
separate fit/door-sweep evidence, not this CAD-only envelope study.

## A7 — direct saved-sketch review and level-beam revision

The user requested an Astra-agent redesign because A6 still did not match
their intended form. There is no Astra-named agent available here. The user
saved the exact drawing at
`C:\Users\erena\Downloads\Screenshot 2026-09-27 220011.png`; the available
`subagents/multimodal-analyst` inspected **that file**, A4/A6 side views and
the ResKit image in a bounded read-only pass. The analyst observed a nearly
level roof line until near the right/front end and rounded contours at both
ends. It claimed the left/A6 end was longer, but the primary checked the
saved source and found the opposite: A6 front measures 465 mm from the beam
root, rear 385 mm. That numerical claim was discarded. The primary directly
reviewed the drawing: its top line is flat through the main beam, while the
front nose descends near the end; the left/rear tip is shorter and rounded.
The drawing's pixel positions, waviness and single-view widths are not
engineering dimensions.

A7 is a new bare/filled study that restores the **Boolean-identical A2 flat
dorsal roof**, makes the forward fairing begin at roof height, and gives both
tips eased rounded-rectangle transitions without changing A6's intended
front-versus-rear length ordering. A6 source and artifacts remain preserved.

- [User red drawing versus A7 side, matched A6/A7 full views, and A7
  bare/filled](reviews/A7_LevelBeam_Review.png). The board embeds the user
  screenshot for durable comparison; `reviews/make_a7_board.py` uses the
  saved Downloads image if regeneration is needed. Fourteen individual
  saved-STEP views from `review_a7.json` include shaded/opposed/side/top/
  underside and edge-visible front/rear end faces.
- [A7 bare](http://127.0.0.1:3248/?file=STEP/A7_LevelBeam_Bare.step) and
  [A7 filled](http://127.0.0.1:3248/?file=STEP/A7_LevelBeam_Filled.step).
- First trial with an unrestricted smooth loft **failed** the saved-bound
  check (404.253 mm wide and 226.453 mm high against 400/223); it was not
  accepted. Replaced it with bounded monotone cubic interpolation of profile
  dimensions and ruled sections. `checks/check_a7.py` final PASS from saved
  states: 11/15 valid closed positive solids, 3500×400×223 mm envelope,
  exact A2 roof and unchanged A6 lips/apertures/box solids, zero box/frame
  collisions, sampled downward exit paths clear, 158.013 mm Spear maximum
  fin diameter. Report `reviews/A7_LevelBeam_Checks.json`.
- Primary inspected the exact red drawing, final A7 bare/filled opposed
  obliques, side, top, underside and both end faces. The center now reads
  level and the end transitions no longer show A6's large face-to-face
  bands in shaded views. The front still tapers to a relatively narrow
  rectangular sensor face in oblique view; end-on widths are an inferred
  translation of a side-only sketch and need the user's judgment.

**Current gate:** user reviews A7 before any end-shape approval. A2's central
open-side selection remains approved independently. The 3.5 m candidate
still exceeds the former provisional 3 m target, and real donor/door/pylon/
aircraft fit plus powered-ejection/fallback runtime remain unverified.

## A8 — smaller rounded ends after the user's A7 correction

The user reviewed A7 and instructed: “Please tweak both parts to look like
the image I drew, you don't need to worry about making the ends flat, in fact
they should be rounded for now.” A8 keeps A7's level beam, long front/shorter
aft layout, open central U-frame and four separate placeholder box skins.
Only the two sensor-end lofts and their placeholder apertures change. The
front and rear sections contract further near each tip to read as rounded
terminations in side and oblique views, rather than a large planar end face.
There remains a **small** terminal planar patch to carry a purely provisional
outward-facing recessed sensor cue; do not mistake this for approved sensor
packaging. A perfectly seamless dome and its actual window construction are
later interface decisions.

- [A7/A8 matched side and oblique, A8 bare/filled, forward/rear close-ups](reviews/A8_RoundedTips_Review.png),
  plus thirteen saved-STEP snapshots in `review_a8.json`.
- [A8 bare](http://127.0.0.1:3248/?file=STEP/A8_RoundedTips_Bare.step) and
  [A8 filled](http://127.0.0.1:3248/?file=STEP/A8_RoundedTips_Filled.step).
- `checks/check_a8.py` PASS on both serialized states: 11/15 positive valid
  closed parts; A7 roof, side lips and four box solids Boolean-identical;
  measured tip sections ~80.05×36.05 mm front and ~85.04×40.06 mm aft,
  each with a smaller 60×18 mm recessed cue. No box/housing or box/box
  intersections, sampled downward exits clear, outer envelope still
  3500×400×223 mm. Approved Spear's saved maximum fin diameter remains
  158.013 mm. Report: `reviews/A8_RoundedTips_Checks.json`.
- Primary directly inspected final bare/filled iso/opposed, side, end-on
  edge views and the matched A7/A8 board. Compared to A7, the tips are
  visibly smaller and the side profile loses most of its abrupt planar
  end reading. At close end-on scale a small flat aperture patch is still
  visible and may need redirection; do not infer the user has approved A8.

**Current gate:** user judges both rounded tips, especially whether the
provisional small outward windows conflict with their intended completely
rounded silhouettes. This remains a CAD concept, not proven aircraft or
AGM2 door/launcher fit, and it does not implement powered release or fallback.

## A9 — uninterrupted end silhouettes; sensor apertures deferred

The user rejected A8 in direct terms: **“the entire slope gradient looks
jagged and misaligned”**, directed removal of the apertures **for now**, and
asked for continuous rounded curves from their saved markup. A9 returns to
the approved level A2 roof and four-placeholder open-side architecture. Its
front/rear fairings are smooth native loft surfaces through a broad rounded
rectangle at each beam root and elliptic easing toward small, fully enclosed
tips. The ends are intentionally bare: **no sensor aperture solids, recesses
or production window layout exist in this variant.** This is the user's
temporary silhouette gate, not cancellation of the earlier paired outward
sensor requirement.

- [The red side markup versus A9, matched A8/A9 and bare/filled context](reviews/A9_ContinuousEnds_Review.png),
  plus eleven saved-STEP shaded opposed/side/top/underside/front/rear views
  generated from `review_a9.json`. Source `src/continuous_ends.py` has two
  thin bare/filled model entrypoints; A8 and earlier sources are preserved.
- [A9 bare](http://127.0.0.1:3248/?file=STEP/A9_ContinuousEnds_Bare.step),
  [A9 filled](http://127.0.0.1:3248/?file=STEP/A9_ContinuousEnds_Filled.step).
- `checks/check_a9.py` final PASS from both serialized STEPs: 9/13 valid
  closed positive-volume solids; all A8 parts other than the two end shells
  and omitted apertures Boolean-identical, including the approved center and
  four plain boxes. No box/frame or box/box intersection; sampled downward
  exit centerlines clear. Measured tip sections immediately behind each
  extremity are ~9.77×5.04 mm forward and ~10.05×5.21 mm aft, rather than
  A8's large flat aperture patches. Whole study remains 3500×400×223 mm;
  saved approved Spear still measures 1200 mm length and 158.013 mm maximum
  fin envelope. Result: `reviews/A9_ContinuousEnds_Checks.json`.
- The first saved smooth-loft check FAILED on a 0.036 mm width/0.020 mm
  height overshoot; an initial small profile allowance then left bare height
  222.96 mm while filled remained 223 mm. Corrected the source root profile
  to retain the full 223 mm height, rebuilt both documents and reran the
  same strict saved-bound check successfully. Neither failure is counted as
  a pass or hidden in the report.
- Primary directly inspected final A9 bare/filled obliques, side/top,
  underside, end-on views and the red-sketch comparison. The face-to-face
  loft banding and sensor slots that made A8 look cut off are absent; both
  ends now read as continuous rounded terminations. Cross-sectional breadth
  remains an inference from one side sketch, and user acceptance is pending.

**Next:** user reviews A9's full silhouette before deciding any end-sensor
window position. Restoring two outward-looking apertures must be a separately
reviewed local feature that does not undo the selected continuous outline.
The 3.5 m length, actual aircraft/pylon fit, donor doors and powered release
are still unverified.

## A10 — approved teal-dome wedge nose and stubbier level rear

After A9, the user judged the level continuous ends **"still not close"**:
the front tip must drop down like their drawing and the rear be slightly
stubbier. The iteration chain: a cosine-eased fold (rejected — **"the
frontal nose is gone; it should have the same slope as A9 but a vertical
tangent intersection at a lower height than exactly halfway"**), a 60 mm
nodding A9-slope teardrop (approved in concept, then **"lengthen the front
tip by 2x"**), a 930 mm 2× pass corrected to **1.2× (558 mm)**, a
horizontal-belly wedge with the A9-slope roof (rejected — **"the bottom
slope isn't as horizontal in the drawing"**), and finally the user's teal
outline over the render defining a **dome**: roof holds the beam top,
descends gently through the middle, plunges at the end and rounds into the
flush belly line. `src/drooped_ends.py` implements that outline:
`roof = -211 mm·t³`, belly constant −223 mm, blunt 24×12 mm tip, 558 mm
forward fairing, level A9-profile 345 mm rear cap (385−40). The user then
approved this silhouette.

- First dense-grid lesson: the 15-station non-ruled loft **folded** where
  the cosine collapse converged hardest (empty x-slices around X 1650–1700,
  a −243.7 mm overshoot and broken identical-copy Booleans); the A9 sqrt
  law at 15 stations is the stable construction and was kept.
- [The teal-outline render versus the user's drawing](reviews/A10_DroopedEnds_Review.png),
  plus eleven saved-STEP solid views generated from `review_a10.json`.
  The self-updated cadgen renamed the display mode `shaded` to `solid` and
  needed a viewer-daemon restart and a BOM-free job file.
- [A10 bare](http://127.0.0.1:3248/?file=STEP/A10_DroopedEnds_Bare.step),
  [A10 filled](http://127.0.0.1:3248/?file=STEP/A10_DroopedEnds_Filled.step).
- `checks/check_a10.py` PASS from both serialized STEPs: 9/13 valid closed
  positive-volume solids; every part except the two end shells
  Boolean-identical to A9's approved open-side frame; no apertures; forward
  shell spans X 1325–1883, aft −1670..−1325; dome probes hold the roof
  curve at four stations; tip sections 24.3×12.1 mm forward at
  Z −223..−211 and 10.26×5.33 mm aft; belly flush with the beam underside;
  downward exits clear; outer 3553×400×223 mm; saved approved Spear still
  measures 1200 mm length and 158.013 mm maximum fin envelope. Result:
  `reviews/A10_DroopedEnds_Checks.json`.
- Primary directly inspected side/iso renders at every gate, including the
  closeup the user annotated. Approval (2026-09-28) covers the housing
  **concept-level silhouette only**: sensor apertures remain deferred, the
  3553×400×223 mm envelope is a study dimension, and aircraft/pylon/door
  fit, shutters, ejection runtime, export and in-game visuals remain open
  gates.

**Next:** reintroduce outward sensor apertures as a separately reviewed
local feature on the approved curves, then the fit-evidence gates in
`../../cad/palisade_interceptor/POD_FIT_FEASIBILITY.md`.
