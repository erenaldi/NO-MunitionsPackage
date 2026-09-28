# RDM-9 paired-state concept studies

Date: 2026-09-23. Current boundary: **concept-review candidates**; no direction selected or CAD approved.

> **Drawing correction (2026-09-23):** The user supplied a bottom/front sketch
> and clarified a lightly filleted-square main section and pointed, high-apex
> V-chined nose. The A/B/C forms below predate this correction. The separate
> `D_SketchNose_R1` paired prototype is the current **local nose/body gate**;
> no whole-airframe selection has been made.

## D / SketchNose R1 — current local review

- Contract: `NOSE_SKETCH_CONTRACT.md`. Generated from `src/sketch_nose_r1_shapes.py` by `src/d_{deployed,stowed,midsection,nose_section}.py`; historical A/B/C outputs stay intact. Original sketch was supplied inline and has no verified local image path.
- [Drawing-matched CAD views](reviews/D_SketchNose_R1_Drawing_Match.png): enlarged **bottom** taper/ridge, nose section seen from **front**, isolated lightly rounded-square body section and deployed context. [Paired-state board](reviews/D_SketchNose_R1_Paired.png) shows the identical physical wing and fin panels in both poses. Individual `reviews/D_*.png` include opposed, top, side, nose-facing, rear and section views.
- Actual modeled main-body section at X=0: 172×172 mm with true 10 mm corner arcs and 29,498.159 mm² area; the 90 mm-wide front-facing nose section at X=1160 has a lower center keel 25 mm below its flanking low points. From below, the planar nose converges to a tiny high tip near X=1400 with one intermediate chine break. The end-on projection now has a near-roof central junction and lower Y/V instead of a mid-height X; the exact interpretation still awaits the user's visual approval.
- `src/check_sketch_nose_r1.py` independently reads all four STEP files and passes: centered 2,800 mm length, 119.7539 mm maximum stowed vertex radius (5.2461 mm envelope margin), one valid body + 10 valid appendage/marker solids per pose, exact inverse-hinge shape correspondence (0 mm³ symmetric difference), attached wing seats/fins, sectional rounded-square area and bottom-keel depth, a tip section at X=1398 measuring 8.001 mm². Evidence: `reviews/sketch_nose_r1_checks.json`. All four final STEPs pass strict every-placement validation: paired states each 11 occurrences/9 prototypes and isolated sections 1/1, zero failures.
- Direct visual review: the lightly rounded square is visible in the isolated midsection and the lower V in the isolated nose section. The broad whole-vehicle front view also exposes seam/chine lines from stations; the enlarged sectional front view is the reliable local-form reference. The nose remains **concept-stage**; full folding motion, actual AGM1 donor-rack clearance, source-photo fidelity, game readability and user approval are not established.
- Live viewer (all four targets returned HTTP 200): [deployed](http://127.0.0.1:3247/?file=STEP/D_SketchNose_R1_Deployed.step), [stowed](http://127.0.0.1:3247/?file=STEP/D_SketchNose_R1_Stowed.step), [main-body section](http://127.0.0.1:3247/?file=STEP/D_SketchNose_R1_MidSection.step), [nose section](http://127.0.0.1:3247/?file=STEP/D_SketchNose_R1_NoseSection.step).

## Active context

- **Authoritative intent:** `plans/2026-09-23-rdm9-phantom-visual-reboot.md` and `MUNITIONS.md` section 5. R5 is the historical built comparator, not the new master.
- **Source:** `src/study_shapes.py`; six parameterless `src/{a,b,c}_{deployed,stowed}.py` entrypoints emit paired STEP artifacts under `STEP/`. No R5 geometry is imported into the new designs.
- **Scale:** millimetres, X=±1400 (nose +X), dorsal +Z, starboard +Y; all stowed exterior vertices radial ≤125 mm. Review composition and mock-pad STEP files are separate from candidate geometry.
- **Preserve:** Kh-69-inspired chamfered body and corner-tail reading, TALD-inspired flat-ended wedge, GBU-39-inspired lengthwise-folding wings, paired flush RF areas, corresponding wing/fin panels in each pose.
- **Avoid:** R5's rounded point and invisible internal wing slot. No claiming that a 700×80 mm abstract pad is the real AGM1 donor rack.
- **Status:** Three paired CAD studies built and checked. User visual selection, reference-image fidelity check, exact donor-rack clearance, detailed CAD, export and Unity remain open.

## Candidate distinctions

| Candidate | Central section and front | Wing architecture | Stowed radial maximum |
|---|---|---|---:|
| A / Facet | 202×108 mm, 112 mm flat-ended nose, moderate wedge | 1,038 mm deployed full span, straight tapered panels | 108.135 mm |
| B / Shoulder | 230×80 mm, broad 160 mm nose and short taper, shallow body | 1,138 mm full span, broadest wing chord | 121.5936 mm |
| C / Keel | 188×121 mm aft/mid shoulders, 152 mm waisted center, 94 mm nose | 968 mm full span, kinked/diamondback planform | 110.732 mm |

Dimensions above are study choices, not measurements of real references. All three are 2,800 mm long. B uses most of the envelope (3.4064 mm radial margin before any actual rack check). All folded main wings rotate 90° around a shared dorsal hinge into separate forward and aft seats; the four tail panels fold 75° around their corner-root axes. These are static corresponding poses, not verified continuous mechanism clearance.

## Geometry and review evidence

- `src/check_pairs.py` reads the exported STEP documents independently; `reviews/checks_ABC.json` records 11 labeled parts per state, positive valid solids, exact inverse-pose wing/fin shape correspondence (0 mm³ symmetric difference), body/hinge/fin contacts, 2,800 mm centered length, and the stowed radial envelope. A's `A_Facet_Stowed_MockPad.step` has no Boolean overlap with its **mock** 700×80 mm pad (floor Z=78 mm).
- Strict `cadgen step inspect validate --every-placement` passes with zero failures for each of the six candidate STEP files (11 occurrences / 9 prototypes each), the A mock-pad context (12 / 10), and both four-up true-scale comparison STEP files (42 / 32). `refs --facts --planes --positioning` succeeds on all six candidate files.
- `reviews/RDM9_ABC_iso.png`, `_top.png`, `_side.png` compare corresponding deployed/stowed poses with fixed camera direction. `reviews/R5_ABC_deployed_labeled.png` and `_stowed_labeled.png` come from four models placed **without resizing** inside one STEP each (`STEP/R5_ABC_{Deployed,Stowed}_TrueScale.step`); labels are A/R5 over C/B in image order. `reviews/A_mock_pad_iso.png` is explicitly mock-only.
- Primary visual inspection of final boards and individual orthographic, opposed, nose and tail images: A is restrained but still has a long boxed missile profile; B's wider, shallower body and much broader front are most visible head-on/top; C's waist and kinked wings distinguish it in top and oblique views. At full combat-distance side view, all three look quite similar. Folded main panels are now visibly present from above, but the very thin folded fins and projecting wing seats still need aesthetic/clearance resolution. The broad flat ends read as wedges in CAD, yet precise fidelity to TALD/Kh-69/GBU-39 imagery remains **unverified** until the actual reference photos are directly reviewed together with these views.

## Viewer

The CAD Viewer is serving this workspace at `http://127.0.0.1:3247/` (all candidate links returned HTTP 200 on 2026-09-23):

| | Deployed | Stowed |
|---|---|---|
| A / Facet | [STEP](http://127.0.0.1:3247/?file=STEP/A_Facet_Deployed.step) | [STEP](http://127.0.0.1:3247/?file=STEP/A_Facet_Stowed.step) |
| B / Shoulder | [STEP](http://127.0.0.1:3247/?file=STEP/B_Shoulder_Deployed.step) | [STEP](http://127.0.0.1:3247/?file=STEP/B_Shoulder_Stowed.step) |
| C / Keel | [STEP](http://127.0.0.1:3247/?file=STEP/C_Keel_Deployed.step) | [STEP](http://127.0.0.1:3247/?file=STEP/C_Keel_Stowed.step) |

Select, reject, or hybridize after inspecting **both** poses and the R5 true-scale comparison. Approval must be explicitly recorded with packet identity and scope before detailed modeling; the actual donor rack remains a separate final-CAD gate under issue 017.

## Reproduce

Run from `cad/phantom_visual_reboot/` with the dedicated CAD Python runtime:

1. Run each `src/{a,b,c}_{deployed,stowed}.py` and `src/a_mock_rack.py` individually; then run `src/compare_r5.py`.
2. Run `src/check_pairs.py` and `cadgen step inspect validate STEP/<name>.step --every-placement` on the six primary artifacts.
3. Run `cadgen step snapshot --job review_A.json`, `review_BC.json`, `review_extra.json` and `review_true_scale.json`; regenerate the two A ISO views, then run `src/assemble_review.py`.
