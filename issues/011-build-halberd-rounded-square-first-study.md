---
id: "011"
title: Build and review the first rounded-square Halberd study
type: feature
status: done
blocked-by: []
---

## Slice

Deliver one fresh parametric silhouette end-to-end: assembled and separated STEP models, independent checks, actual image review and CAD Viewer links. Follow `plans/2026-09-22-halberd-rounded-square-reboot.md` and `docs/ASSET_DESIGN_WORKFLOW.md`. This proves the section transition and stage split before extending the comparison set. It does not select the final design.

## Ownership and evidence

- Own new `cad/halberd_rounded_square/src/`, `STEP/` and `reviews/` files and this issue's status. Update the brief and journal with actual results.
- Load `cad`, `concept-asset-cad` and `cad-viewer`; use the dedicated CAD Python runtime documented in project instructions.
- Main agent owns visual interpretation and reads images directly. No delegated design or visual review without explicit scoped user approval.
- Supplied references currently exist in the alignment conversation, not verified local image paths. If unavailable, request actual image files before reference-fidelity review.
- Old models are tooling examples only. Do not import their body shapes or dimensional constraints.

## Acceptance

1. New source uses 3370 mm nominal total length, approximately 200 mm rounded-square width/height, broad corners and short flats. Nose transitions smoothly into a circular pointed ogive.
2. Booster occupies exactly L/6 at the aft end; centered X-forward seam is -L/3. Main and booster sections match at the seam.
3. Four low elongated intake forms and separate compact four-fin sets read clearly. Main-stage fins remain with that stage; no fairing bridges the stage seam.
4. Geometry-only blockout preserves the second reference's slender restraint. Do not build fine repeated details before their applicable approval gate.
5. Separated view uses the same stage geometry with explicit placement offsets, not separately remodeled approximations.
6. Native labels distinguish stage ownership and feature roles. Parameterless decorated model entrypoints write explicit STEP outputs; proposed factory interface is `build_study(key, separated=False)`.
7. Deliver opposed isometrics, side/top/front/rear, separated state and focused nose-transition/intake images. Read all acceptance images directly and fix visual failures.
8. Return working CAD Viewer links and record geometry results separately from user visual approval. Final selection awaits the trio.

## Test notes

- Independent measurements: total length, across-flat section, exact stage ratio/seam, matching join, fourfold layout, fin ownership, separated-state shape preservation.
- Validate all emitted STEP placements with cadgen strict validation; fail on invalid/nonpositive solids. Inspect actual mouths and joins, not just part counts.
- Snapshot the explicit STEP targets and inspect the resulting images. Keep inferred radius, clocking and fin dimensions explicit and reviewable.
- No Unity, exporter, plugin, flight or aerodynamic acceptance is claimed by these checks.

## Result — 2026-09-22

Built `cad/halberd_rounded_square/STEP/A_Trace.step` and `A_Trace_Separated.step`. Both pass strict every-placement STEP validation (15 occurrences / 6 prototypes; zero failures). `src/check_studies.py A` passes artifact-only length, stage ratio, join, section shape, attachment, fourfold volume symmetry, open mouths and separated-placement checks; report `reviews/checks_A.json`.

Primary model directly reviewed the nine views via the five `A_*.png` boards: main/booster remain complete, broad corner section and circular ogive are visible, intakes read as low rails with forward openings. Initial analytic nose was rejected by the independent STEP reader despite Python validity; replacement spline-ogive export passes. Review framing is being tightened in issue 012 for the final comparison. Viewer launch returned `http://127.0.0.1:3246/`; final handoff will recheck HTTP availability. This is a study result, not user selection.
