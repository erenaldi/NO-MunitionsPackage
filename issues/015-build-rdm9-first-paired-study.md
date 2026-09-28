---
id: "015"
title: Build and review first paired-state RDM-9 silhouette
type: feature
status: todo
blocked-by: []
---

## Slice

Deliver one complete rough RDM-9 decoy end-to-end: new source-authored deployed and folded STEP studies, physical panel/hinge correspondence, independent geometry checks, and directly inspected visual review views. This proves a compact folded vehicle can still read as the intended decoy before expanding to three alternatives. Authority: `plans/2026-09-23-rdm9-phantom-visual-reboot.md`, `MUNITIONS.md` section 5, and `docs/ASSET_DESIGN_WORKFLOW.md`.

## Ownership and evidence

- Own a new RDM-9 visual-study workspace under `cad/`, this issue's status, and scoped RDM-9 context/journal updates. Keep historical `cad/phantom_r2_lib.py`, R5/R6 STEPs, R5 exporter, and Unity assets intact. Choose explicit source/STEP/review paths in this workspace and record them at handoff.
- Use `cad` and `concept-asset-cad` for the reference-driven paired CAD work; `cad-viewer` for generated STEP handoff. The main agent directly inspects external reference imagery and all new review images; do not delegate design or visual review without the user's explicit scoped approval.
- The selected source cues are TALD's flattened broad nose, Kh-69/Kh-59MK2's faceted body and compact-tail language, and GBU-39's visible folded/deployed main-wing relationship. Preserve their attributed roles; do not infer their real dimensions as game constraints.

## Acceptance

1. One rough vehicle includes a visibly faceted non-round body, wide flattened-wedge nose, two recognizable main-wing panels, four aft fins hinged at/near body corners, subtle flush paired RF areas, and an aft treatment that does not falsely imply a proud nozzle.
2. Deployed and stowed outputs use the *same identified* wing and fin panel geometry, with explicit named hinge frames/pose transforms; prove shape identity between poses after inverse placement, not just matching labels or silhouette.
3. Both states retain centered 2,800 mm length and CAD +X nose/+Z dorsal/+Y starboard. All external stowed material (including hinges/fairings) fits inside a 125 mm radial envelope; deployed surfaces may exceed it.
4. Stowed panels and all four folded fins visibly read at rack distance; the deployed wings and four fins read from side/top/end and opposed isometrics. No stand-in internal slot or fixed R5 appendages masquerading as folding.
5. Provide matched neutral-shaded opposed isometrics, side/top/front/rear, stowed close views, rack-context study and a representative distance comparison with R5. Record what was directly seen, unresolved readability/fit concerns, and functioning CAD Viewer links. Early mock-pylon views are clearly labeled as such.
6. This is a single concept-stage study, not user selection of the final RDM-9. Do not add material/engine assets or promote R5 outputs.

## Test notes

- Run artifact-independent bounds and radial-envelope checks on the stowed STEP, panel identity/hinge-placement comparison, part validity/contact checks, and strict every-placement STEP validation on both outputs. Verify source rebuild reproducibility without hand-editing exports.
- Snapshot both STEP targets; the main model reviews the actual images against the cited source images and the R5 baseline. Mechanical fit to the *real* donor rack belongs to issue 017, so this issue cannot claim that boundary.

## Progress — 2026-09-23

The complete A/Facet deployed/stowed STEP pair and a labeled mock-pad context exist under `cad/phantom_visual_reboot/STEP/`. `src/check_pairs.py A` passes 11-part pair identity, inverse hinge/panel equivalence, contact, centered length and 108.135 mm maximum stowed radial reach. Strict every-placement STEP validation passes with zero failures on all three A artifacts. Final CAD boards and individual views were directly inspected by the main model; see `cad/phantom_visual_reboot/REVIEW.md` for paths and limitations. The mock pad is not the real donor rack; direct reference-photo fidelity and user silhouette acceptance remain open, so this issue is not marked done merely because the STEP files validate.

User's later bottom/front sketch superseded A's flat nose and broad-shallow section. `cad/phantom_visual_reboot/STEP/D_SketchNose_R1_{Deployed,Stowed}.step` is a separate corrected local-form prototype; both sectional proofs are documented in `cad/phantom_visual_reboot/REVIEW.md`. Await user review before treating the sketch reading as approved or propagating it across other designs.
