# Palisade interceptor — three concept studies

State: `concept-approved` (2026-09-23). The user selected **A / Spear** from
the four-way visual comparison as "great and 100% the taste that I was going
for." This approves its concept silhouette, not pod fit, detailed CAD or a
production/export boundary. Authority:
`plans/2026-09-23-palisade-interceptor-visual-redesign.md`.

## Active context

- Authoritative source: `src/concept_shapes.py` plus six thin `src/[abc]_*.py`
  entrypoints. The pre-existing `../palisade_geometry.py` and
  `../HKP-1_Palisade_Interceptor.step` remain the untouched comparison baseline.
- Review packet: `reviews/Palisade_Selection_Board.png`, individual views in
  `reviews/`, and `reviews/checks.json`. All new geometry is concept-level.
- Coordinate system: millimetres; +X nose, +Z dorsal; cap displaced 270 mm aft
  for display in separated exports. The production-stage datum remains open.
- Preserve: four lateral cap thrusters, separate cap, recessed main nozzle,
  ejection → snap-turn → release → main-burn visual order.
- Avoid: choosing a visual master from a validity test or claiming pod fit.
- Open decisions: full pod layout and capacity, local detail refinement and
  any clearance tradeoff that might reopen the selected silhouette.

## Reference-cue ledger

These are *textually verified functional analogs*, not image-matched models.
The fetched pages expose some image links, but no original reference image was
saved and directly inspected for fidelity. Feature geometry is a new design
inference, not measured hardware or an aerodynamic claim.

| Study | Cited cue | Intended feature and limits |
|---|---|---|
| A / Spear | [RIM-116](https://en.wikipedia.org/wiki/RIM-116_Rolling_Airframe_Missile): compact point-defence missile, prominent control-surface family | Slim ogive and broad swept aft fins. Not a RAM replica: unlike rolling RAM, Palisade's cap snap-turns pitch/yaw and then leaves. |
| B / Shoulder | [CAMM](https://en.wikipedia.org/wiki/CAMM_(missile_family)): gas ejection followed by turnover and rocket burn | Fuller forebody and shoulder with two small fin stations; own wider turning cap makes staging conspicuous. CAMM is much larger; no CAMM dimension or real turnover mechanism is copied. |
| C / Facet | [MHTK](https://en.wikipedia.org/wiki/Miniature_Hit-to-Kill_Missile): miniature short-range interceptor role | Dense, narrow faceted body and a clearly removable polygonal rear cap. The actual MHTK's profile is not evidenced here; faceting is speculative game styling. Palisade remains HE-frag, not hit-to-kill. |

## Directions and tradeoffs

| Candidate | L (mm) | Cap (mm) | Measured max radius (mm) | Reading and concern |
|---|---:|---:|---:|---|
| Historical baseline | 1200 | 170 | ≤85 | Readable staging but plain long tube and button-like thrusters. Existing CAD check is historical. |
| A / Spear | 1200 | 180 | 101.01 | Slender ogive and large swept rear fins; strongest traditional interceptor read, also the widest fin span and most generic missile shape. |
| B / Shoulder | 1120 | 215 | 91.01 | Shorter fuller body, prominent shoulder, reduced aft fins and second small fin station; clearest compact point-defence character, but its blunt nose and small fore fins may need work. |
| C / Facet | 1280 | 230 | 103.01 | Octagonal body, hard chines, cropped fins and a long tapered polygonal cap; distinctive, but longer/wider and more stylized than the other two. |

**User selection (2026-09-23): A / Spear.** Its pointed nose and prominent
swept fins matched the user's intended taste. The earlier reviewer preference
for B was provisional and is superseded by this explicit choice. A is not
proven to fit four rounds in the original 400 mm pod: its measured maximum
radius is 101.01 mm (202.02 mm diameter), so two side-by-side envelopes alone
exceed 400 mm before clearance. Actual packing and allowable pod revision
remain to be decided at feasibility.

## Evidence and gates

- `src/check_studies.py` passed all three artifact pairs: labeled valid solids,
  body/cap no-intersection, attached fins and thrusters, central main-nozzle
  bore and visible lip, and Boolean-equivalent geometry after undoing the cap
  review offset. Serialized results: `reviews/checks.json`.
- `cadgen step inspect validate STEP/<name>.step --every-placement` passed for
  all six emitted STEP files with **zero failures**. A and C have 11 occurrences
  / 8 prototypes each, B has 15 / 12 in both assembled and separated states.
- `src/render_reviews.py` emitted 24 individual views and one four-way board.
  Primary model directly inspected the board, all opposed iso views, B top,
  C nose and A separated opposed; the separate ISO/side/end/separated snapshots
  are also represented on the board. Same camera direction and neutral shading
  are used; board sizes are scaled by axial length or cross-section diameter.
- Fin roots were moved into the actual skin when the first A snapshot exposed
  a visible floating-edge gap. The first C checker run found a detached dorsal
  thruster because octagonal flats sat below the nominal radius; it was inset
  and both exports were rebuilt and rechecked without loosening assertions.
- Viewer root: `cad/palisade_interceptor/`; the six files under `STEP/` are
  individually browsable. No production export, engine or runtime check ran.

## Artifacts

- `STEP/A_Spear.step` and `STEP/A_Spear_Separated.step`
- `STEP/B_Shoulder.step` and `STEP/B_Shoulder_Separated.step`
- `STEP/C_Facet.step` and `STEP/C_Facet_Separated.step`
- `reviews/Palisade_Selection_Board.png` (baseline + three candidates)

Next gate: assess A against real pod volume and missile mounting before
detailed CAD. A fit-driven external shape change reopens silhouette approval.

**2026-09-23 local revision:** the user requested a slightly smaller fin span,
three fin-planform variants and a stronger cap boattail. The accepted A nose,
body and stage order remain intact. One-fin Trim/Rake/Broad preview studies
and the boattail cap are in `SPEAR_FIN_BOATTAIL_REVIEW.md`; local fin/cap approval
is pending. Do not mistake these asymmetrical previews for a four-fin master.
The user subsequently said Broad is good but will provide a fin picture;
that reference must be reviewed before any repeated-fin approval.
The user later supplied a trapezoidal drawing and selected its lower-profile
SketchLow interpretation with the boattail. The verified fourfold candidate
is now recorded in `SPEAR_FIN_BOATTAIL_REVIEW.md`, awaiting whole-asset review.
The user then rejected the flat cap aft face, choosing a rounded closed tip.
The new isolated and complete candidate, validation and review packet are
recorded in that same local contract. Rounded-cap visual approval is pending.
The subsequent user screenshot instead emphasizes a straight cylindrical cap
band with the nozzle centered on that band and a shorter boattail. Its new
one-nozzle-detail prototype, not a four-nozzle master, is now the active local
review packet in `SPEAR_FIN_BOATTAIL_REVIEW.md`.
The user then explicitly superseded the taper again with a plain full-length
cap cylinder and a fillet on its aft edge. The newest one-nozzle candidate
and matched comparison are under that local contract; no nozzle repetition or
whole-CAD visual approval has yet been given.
After inspecting the cap-cylinder packet the user flagged a remaining local
height rise at the body/cap joint. `SPEAR_FIN_BOATTAIL_REVIEW.md` now records
the separate 62 mm flush-junction CAD study and matched section-profile board;
its user visual acceptance is still pending.
The user accepted that junction and requested a 50 mm shorter cap and a
slight fin-plate thickness reduction. A separate assembled/separated
candidate, verified stage relocation and comparison packet are now recorded
in the same local contract; its whole-asset visual gate remains open.
The user then specified a uniform barrel and cap at the existing smaller
forward diameter. The separate 54.56 mm-radius study, attached low fins,
saved-section checks and matched view are now in that local contract.
User accepted that 109.12 mm body/cap diameter and original pointed nose on
2026-09-27. Nozzle detailing remains at one station pending its own visual
decision, so the whole CAD design is still `cad-review` at that detail gate.
The one-group ACM form inspired by a directly inspected PAC-3 dummy-model
side-thruster image is in `ACM_PORT_REVIEW.md`; its visual approval is still
pending before any fourfold repetition.
The user instead directed a distributed ACM pattern around the *entire* cap,
using their annotated screenshot for layout intent rather than exact sizing.
`ACM_PORT_REVIEW.md` identifies the current 96-port CAD candidate and review
packet; the prior one-group study is historical. At the time of that packet,
user whole-cap approval was still pending.
The user approved the distributed-port cap visual packet on 2026-09-27;
`STEP/Spear_ACMWrap.step` is the active approved **visual study** identity.
Actual pod fit and later CAD/engine/runtime boundaries remain open.
`POD_FIT_FEASIBILITY.md` is the current next-gate report: a conceptual
400 mm box can hold four CAD envelope circles under stated allowances, but
the actual six-door donor's four remaining launcher transforms and doors
are not in the saved dump. No installed-pod clearance is approved.
