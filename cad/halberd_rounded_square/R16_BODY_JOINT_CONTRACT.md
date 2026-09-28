# R16 — nose/body joint surface-detail prototype

Created: 2026-09-26; verified 2026-09-27. State: **`cad-review`**; built, checked
and directly visually reviewed by the primary model. User authorized continuing
the next body-joint detail pass after reviewing R15. User subsequently responded
"Good" (2026-09-27), accepting this local treatment. Whole-asset detailing and
additional axial joint propagation remain pending.

## Design brief

- Baseline: R15's four-face covers plus preserved R14 booster junction cleanup.
- Use the existing nose/body interface at **X=1085 mm** (`NOSE_BASE`), rather
  than introducing an arbitrary new mid-body division. Millimeters, +X nose,
  +Z dorsal. Keep the nose, intake geometry, fins and staging unchanged.
- Reference cue: `cad/kris/generate_pl10_stencil.py:254-258` pairs small joint
  fasteners with 1.3 mm axial-width fine section seams. The selected Kris STEP
  inherits these features. These guide visual scale and restraint, not an
  assertion of real-world construction or copied functional internals.
- One shallow seam on the **main-body side** of the nose interface. Proposed
  annular seat X=[1083.7,1085], inner radius94.4 mm, cut through existing skin.
  Recessed metallic-gray liner X=[1083.8,1084.9], radii94.4..94.8 mm, giving a
  narrow exposed gap at each axial edge and no raised external band.
- Four small slotted fasteners at X=1078 mm on cardinal clocks0/90/180/270.
  Reuse the R13 fastener shape, rigidly translated so its radial bottom is93.5
  and top94.65 mm. Author matching blind seats/countersinks with radial clearance
  and supporting bottom contact; all hardware stays inside the original skin.
- Colors: existing small-hardware gray `#87939B`; no black circumferential stripe.
  Liner uses restrained metallic finish; fasteners reuse `detail_metal`.
- These dimensions are authored visual-study assumptions. Preserve the actual
  outer skin everywhere outside the small recesses; no expansion, nose shift,
  silhouette redesign, extra internal mechanism or engineering claim.
- New objects: one liner and four screws, taking surface-detail count16→21 and
  full assembly parts39→44. Do not add counts merely to reach the80–120 range.

## Required verification and gate

- All38 non-main R15 parts geometry/color-identical, including ogive, covers,
  booster assemblies and dark recesses; exact separated ownership/transforms.
- Main-body changes restricted to one annular seam seat and four blind hardware
  seats. Check actual seat extents/depths against saved artifacts.
- Liner and hardware inside original skin, no pairwise overlap, proper supporting
  contact with main body and clearance from ogive. Preserve3370mm total length.
- Four screw copies exact and slotted; inspect countersink clearance. Joint
  remains cosmetic: no through-cut severing of the main body.
- All full/focus placements valid positive closed single solids without
  self-intersections; bound materials to artifact hashes; focus is an exact crop
  of the full state. Check intake channels remain open.
- Primary inspects local oblique/opposite, side, axial/grazing close-ups,
  whole/separated states and actual Kris joint reference before the user gate.
- User reviews this local joint treatment before repeating at other body joints.

## Verified result — 2026-09-27

- Source: `src/halberd_r16_shapes.py`, with `halberd_r16.py`,
  `halberd_r16_separated.py`, `halberd_r16_focus.py` entrypoints. All three
  `STEP/halberd_r16{,_separated,_focus}.step` artifacts have material sidecars.
  Full states contain44 parts; the exact cropped focus contains7.
- Saved-artifact checker `checks/check_halberd_r16.py` PASS, including primary
  additions for main/new-part separated-state identity, separated materials,
  actual fastener height bounds and retained modified-body material under blind
  floors. Report: `reviews/halberd_r16_checks.json`.
- All38 non-main R15 parts retain geometry/colors. Exactly517.338 mm³ is removed
  by one annular groove and four blind seats; body remains one closed solid,
  with no volume gain. Assembly stays3370 mm long. Channels remain open and all
  stage transforms are preserved.
- Liner has0.1 mm axial gaps at either end, radius94.8 mm outer face and a
 652.446 mm² supporting contact face. Each screw has5.309 mm² floor contact.
  New parts have zero supporting-volume overlap and zero contact distance;
  hardware is clear of its countersinks, liner and ogive. All new parts remain
  inside the old skin envelope.
- All95 R16 placements pass native single-solid/positive-volume, closed-shell,
  topology and self-intersection checks. An additional13 placements in the Kris
  reference crop pass native checks and exact comparison against the selected
  source STEP. The crop comes from `src/kris_joint_reference.py` and preserves
  the source's two fine section seams and nearby hardware.
- Primary inspected all10 packet views and `reviews/Halberd_R16_Nose_Body_Joint.png`,
  then two shaded close-ups. Fine tessellation in `render_r16.py --shaded`
  (`chordTolerance=.00005`, `angleTolerance=.05`) removes the visible fine
  streaks of the default shaded macro view without geometry changes. CAD-edge
  views still show native transition-face boundaries; use shaded views for finish.
- Visual assessment: a narrow continuous gray seam with small recessed hardware;
  no raised collar or heavy black stripe. The fastener slots are clearest with
  CAD edges enabled and subtle under plain shading. Whole-model effect is
  restrained; this is21 surface-detail objects overall, not finished detailing.

## Review links and next gate

- [Joint close-up](http://127.0.0.1:3247/?file=STEP/halberd_r16_focus.step)
- [Whole model](http://127.0.0.1:3247/?file=STEP/halberd_r16.step)
- [Separated stages](http://127.0.0.1:3247/?file=STEP/halberd_r16_separated.step)
- [Actual Kris joint crop](http://127.0.0.1:3247/?file=STEP/kris_joint_reference.step)

Launcher reused the correct study root on3247; all four page URLs returned
HTTP200. User reviews this seam/fastener treatment before extending it to other
body joints or progressing to the next local detail family. No engine/runtime
or physical-engineering acceptance is implied.
