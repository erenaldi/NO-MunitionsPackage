# R19 — surface-detail direction (radial screws and paneling)

Date: 2026-09-28. State: **user direction recorded; prototype only.** No
propagation beyond the forward-section prototype is approved.

## User decisions (2026-09-28, chat)

1. Surface detailing means physical surface objects: radial screws and paneling
   (clarifies the earlier "texturing" request; paint/stencils are not the target).
2. Radial screw rings: **section joints only** — nose/body joint (X=1085), the
   main/booster stage joint (X=-1123.3) and the booster aft joint.
3. Paneling: **dense panels similar to the Kris 3D model**
   (`cad/kris/generate_pl10_stencil.py`, `reviews/R17_Kris_whole.png`).

This supersedes the R18 "quiet central body" reservation for paneling
(`R18_SURFACE_LAYOUT.md`). The R17 critique lessons still apply
(`R17_DESIGN_CRITIQUE.md`): no synchronized four-fold axial matrix, no heavy
dark borders, placement tied to sections rather than a count quota.

## Prototype construction (forward section X=690-1085)

- Joint ring: the accepted R16 nose-joint fasteners (4 at the cardinal clocks)
  are extended to 24 at 15 deg pitch with the identical R16 head and seat, so the
  4 approved parts stay unchanged.
- Joint seam: one circumferential 0.40 x 0.40 mm groove at X=1060, just aft of
  the screw row, so the ring sits in a joint band as on real rounds. It also
  absorbs a construction split: OCC silently skips the ring seat cuts on the
  long host, so the seats are cut on a local slab (X>=1060) that is rejoined
  there. Every cut in the build now fails loudly if it removes no material.
- Skin panels: engraved hairline panel outlines (0.40 mm wide, 0.40 mm deep, cut
  from the measured native skin) with standard R17 slotted heads. This keeps a
  distinct hierarchy from the pocket-and-cover access hatches (0.8 mm pocket).
- Panels are staggered in axial position, length and width per clock; F02 on +Z
  is retained unchanged and no panel is placed on its face.

## Prototype review (2026-09-28, chat)

User on the first prototype packet: "Fantastic, but there should be some
circular details too, not just rectangular panels." The ring, seam groove and
engraved-panel construction are accepted. Round details (engraved circular
panels with a bolt circle or a single centre screw, varied diameters) are added
to the same forward prototype before propagation.

User on the round-detail packet (2026-09-28, chat): "Approved, propagate to
the full body." Ring pitch, seam groove, engraved rectangular and round panel
construction are approved for propagation to the main body, stage joint and
booster aft joint, with placement varied per section.

## Full-body propagation (2026-09-29)

`src/halberd_r19_surface.py` -> `STEP/halberd_r19_surface.step` (323 leaves).
Cosmetic game-asset detailing only.
- 60 engraved panels (44 rectangular, 16 round, each with its own screw
  pattern) on the flat cardinal faces of the main body and booster; the
  forward section keeps the approved prototype layout. Stations are staggered
  per face; the diagonal intake ridges, fins and fairings stay clear; every
  new detail keeps >= 2 mm from existing R18 hatches.
- Joint rings with a circumferential seam: nose (24, R16 heads), stage joint
  main side (20, ridges skipped), stage joint booster side (20, fairings
  skipped), booster aft (28). Ring screws are evenly spaced by arc length.
  Seam depth is 0.4 mm at the section's largest radius and 0.29-0.36 mm on
  the flat faces (radial-scale groove on a non-round section).
- All 246 new screw heads live in one group, `r19_surface_hardware`, which
  carries the metal finish.
- Construction note: a second cause of silent no-op cuts turned up. The R17
  seat tool's top rim sits 0.02 mm above the skin, and on the booster's
  rounded corners the cut curve ran along that rim. New seats continue the
  countersink cone 0.3 mm above the skin.

Open review item (resolved below): on each face the panels mostly ran along
the centreline, which read slightly like a dotted line in pure side views.

## Staggered faces and intake housings (2026-09-29, chat)

User: "Offset some panels sideways to break up the columns. The intake
structure seems really bare; move some designs there." Now in the source:
- 71 of 92 panels are offset sideways (flat faces ±14-28 mm), alternating
  lanes along each face.
- 32 designs sit on the diagonal intake housings:
  - 24 flank panels, placed along each flank's own normal (clocks 15, 75, 105,
    165, 195, 255, 285, 345 at ±90-94 mm offset) so outlines stay undistorted;
  - 8 ridge-top pieces: 4 long narrow strips and 4 small centre-screw caps.
  They stay clear of the forward inlet, the dark recesses and the fins.
- Totals: 92 panels (the approved prototype's 13 + 79 new), 4 joint rings
  (92 screws), 322 new screw heads.

This source edit and rebuild were started by an earlier session that ended
before checking. This session verified the saved build is current with the
source, ran the checker (PASS) and inspected the renders.

## Density, variety and raised F05 strips (2026-09-29, chat)

User: "The details are too dense near the mid section, and overall aren't of
varied design enough. The center strip is good but should have some more height
over the body surface and be mirrored to the other side." User picked: the
long underside strip (F05), mirrored to the opposite (top) face, ~2 mm high.

- Composition:
  - Forward cluster (X 250..1085) and aft cluster (X -1085..-650) stay
    moderately dense.
  - The mid-section (X -650..250) is quiet except for statement pieces:
    both raised F05 strips, vent grille LV1, boss RB2 and the long ridge
    strips T01/T05.
  - Aft-cluster stations were spread so no cross-face ring forms.
- F05: the flush R18 strip (3 pieces + 2 heads) is replaced by raised pieces.
  They fill the 0.8 mm pocket and stand 2.0 mm (strip) / 2.5 mm (end pieces)
  proud, with chamfered tops (the right end piece fell back to 0.2 mm on its
  acute corner). The two screws sit on the strip ends. An exact XY-plane mirror
  copy, with its own 0.8 mm pocket, sits on the top face.
- New families, all only on truly flat skin:
  - 4 raised doubler plates, 1.5 mm with chamfered edges and screws in the
    plate;
  - 3 raised bosses with a recessed centre;
  - 4 vent grilles (engraved outline + 4-5 slots, 0.6 mm deep);
  - hinge-row panels (a screw line along one edge).
  Housing flanks carry only engraved (conformal) designs: a raised plate
  and a boss there failed the planarity guard and the overlap check.
- Totals: 58 engraved panels (incl. 4 grille outlines), 13 raised parts, 250
  screw heads, 4 joint rings.

## Even distribution (2026-09-29, chat)

User: "Keep the same number of objects but evenly distribute them across the
body (junction specific features are exempt)." The 65 movable designs keep
their outline, size and screw pattern: 13 forward-prototype, 17 flat engraved,
11 flank, 6 ridge, 9 main raised/vent and 9 booster designs.
`plan_layout()` in `src/halberd_r19_surface.py` now stations them. The hand
tables only define the designs.
- Main body: 56 evenly spaced stations over X -1080..1045 (~38 mm apart).
  Booster: 9 over X -1496..-1160.
- Flank and ridge designs are Bresenham-scheduled over the housing zone.
  Raised and vent designs are scheduled over the flat zone (X <= 620), and
  engraved designs fill the rest.
- Each station takes the next lane in a rotating face order. Blocked
  intervals (hatches, the F05 pair, F02, inlet/recess zones, joint zones) are
  skipped. Tangent offsets alternate per face.
- Kinds are mixed proportionally, so every 250 mm band holds several kinds.
- Result: 4-8 designs per 250 mm band along the main body (was dense ends /
  quiet middle).
Fixed and exempt: 4 joint rings + seams, the raised F05 pair, the R18 hatches.

## Transverse panels and even inlet walls (2026-09-29, chat) — approved

User: panels nearly all run along the body; turn one rectangular panel per
cardinal face to run around it, picked at random where two similar panels sit
next to each other and conflict. Also make the inlet side walls a constant
thickness, slightly thinner than the top (roof) wall. User: "Looks good to me."
- Transverse panels, `TRANSVERSE` in `src/halberd_r19_surface.py`. Candidates
  were adjacent pairs with dissimilarity < 0.35 and gap < 300 mm (+Z has no
  such pair, so both its panels were candidates). `random.Random(19)` picked:
  - +Z P03, 16 x 44 mm;
  - +Y P02, 20 x 50;
  - -Z Z10, 14 x 36;
  - -Y B02, 18 x 50.
  Each keeps its station, is pinned to its face and has two screws at the
  circumferential ends. Planner order uses the original lengths, so no other
  design moved. An earlier Z09/N08 trial was reverted.
- Inlet walls (`src/halberd_r19_intake_walls.py`). The inherited side walls
  measured 1.4 / 2.2 / 3.1 mm (floor to roof).
  - All four inlets are re-cut in R19: the old channel is filled over X
    350..mouth, then a channel whose side face is offset 3.0 mm inside the
    outer side face is cut. The roof and floor are unchanged.
  - Measured side walls: 3.01 mm at every probe (8 walls, X 600/625, 3
    heights). Roof wall: 3.62 mm.
  - Historical intake sources and older STEPs are untouched.
  - The checker allows host gain only in the inlet zones, equal to the
    declared value (precise integration).
- Checker PASS: 335 leaves, 58 panels, 13 raised, 250 heads.

## Gate

Primary inspects the prototype packet; the user approves or corrects panel
density, groove form and ring pitch before any propagation to other sections or
the stage/booster joints.
