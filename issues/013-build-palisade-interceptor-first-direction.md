---
id: "013"
title: Build and review the first Palisade interceptor silhouette direction
type: feature
status: done
blocked-by: []
---

## Slice

Deliver one complete, hardware-informed interceptor direction from attributed reference cues through labeled parametric source, assembled/separated STEP, independent stage checks and directly inspected review images. This proves the end-to-end study workflow before expanding to three directions. Follow `plans/2026-09-23-palisade-interceptor-visual-redesign.md` and `docs/ASSET_DESIGN_WORKFLOW.md`. Preserve `cad/palisade_geometry.py` and all of its baseline artifacts.

## Ownership and evidence

- Own a new isolated Palisade interceptor workspace under `cad/` with `src/`, `STEP/`, `reviews/` and a compact reference/visual-intent record. Do not edit baseline CAD, Unity, plugin or gameplay files.
- Use `cad` and `concept-asset-cad` for source, checks and visual packet; `cad-viewer` for live artifact links. The main multimodal agent directly inspects the actual reference images and review views; do not delegate design or visual review without the explicit scoped approval required by the project workflow.
- Attribute each real-world cue to the feature it informs, distinguishing an observed cue from proposed fictional hardware. If a reference cannot be accessed or visually checked, do not claim image fidelity.

## Acceptance

1. One coherent whole-silhouette direction reads as a compact, plausible, game-readable point-defense interceptor and is visibly distinct from the old plain-tube baseline in neutral-shaded matched views.
2. Separate, recognizable aft turning cap with four lateral thruster openings; its release exposes a convincing recessed main nozzle and leaves a complete-looking main stage. The existing ejection → snap-turn → release → main-burn order is preserved as visual architecture.
3. Editable labeled source produces assembled and separated STEP states from the same component geometry; separation is an explicit placement change. Dimensions and radial envelope are recorded as outcomes, not forced to the old candidate's limits.
4. Independent checks pass for valid positive-volume solids, semantic stage ownership, no unintended cap/body volume overlap, four cap thrusters, main-nozzle concealment/exposure and preserved stage geometry between states.
5. Opposed isometrics, side/top/front/rear, separated and focused stage views are generated, directly inspected and returned with explicit CAD Viewer links. Record visual strengths/mismatches and what remains open for the three-way choice; do not claim user silhouette approval from this one direction.

## Test notes

- Run native strict STEP validation on both emitted states; inspect facts and dimensions from actual exported artifacts. The old `cad/check_palisade.py` hard-codes baseline dimensions and is not a new-concept validator.
- Confirm the detached cap cannot be mistaken for a single-body silhouette and that the main nozzle is actually exposed rather than merely painted dark. Check matched views at game-relevant scale.
- Record source/reference identity and results in the study workspace and session journal. Pod fit, finished materials, Unity and runtime remain unverified.

## Result — 2026-09-23

Built `cad/palisade_interceptor/STEP/A_Spear.step` and `_Separated.step` from labeled `src/concept_shapes.py` and separate entrypoints. Native strict every-placement validation passed both files (11 occurrences / 8 prototypes / zero failures); `src/check_studies.py A` passed artifact-side stage/nozzle, cap contact, fin attachment and state-geometry checks. Directly inspected `reviews/A_Spear_iso.png`, opposed view, separated opposed and the comparison board; moved fin roots inward after the first snapshot showed a gap. The new pair is ready as one direction, not a user-approved silhouette. The completed three-way comparison is documented in `cad/palisade_interceptor/REVIEW.md`.
