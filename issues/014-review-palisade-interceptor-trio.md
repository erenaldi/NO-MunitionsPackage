---
id: "014"
title: Deliver three Palisade directions and baseline comparison for selection
type: feature
status: done
blocked-by: ["013"]
---

## Slice

Extend the checked first Palisade direction into three contrasting whole-silhouette studies and a matched selection board against the unchanged baseline. This slice ends in an inspectable, validated, user-selectable concept packet, not merely more CAD files. Follow `plans/2026-09-23-palisade-interceptor-visual-redesign.md`, the reference ledger and direction one created in issue 013, and `docs/ASSET_DESIGN_WORKFLOW.md`.

## Ownership and evidence

- Own additional concept sources and assembled/separated artifacts in the new Palisade study workspace, plus the independent three-direction checks, reference mapping and four-way review packet. Preserve baseline source/STEP/review images.
- Main multimodal agent owns reference interpretation, visual continuity and direct inspection of every board. No image-blind visual gate or unapproved delegated art review.

## Acceptance

1. Three directions vary meaningfully in body/nose, fin or control-surface arrangement, and cap integration, while all retain a detachable four-thruster turning cap, exposed-after-release main nozzle and the current flight-stage order. Name each direction's architectural distinction, borrowed cues and tradeoffs.
2. Each direction has labeled parametric source and checked assembled/separated STEP states using the same shapes with explicit separation placements. Record dimensions, radial envelope and preliminary pod-packing implications as comparisons, not verified carriage fit.
3. Each export passes independent validity, stage ownership, cap/nozzle exposure and cross-state geometry checks; strict native STEP validation has zero failures. Deliberate non-fourfold geometry, if any, is documented and checked against its stated intent rather than hidden by a generic symmetry assertion.
4. One consistent, neutral, matched-scale board shows the untouched baseline plus all three new directions in assembled and separated views; supplementary opposed isometrics, orthographic/end views and cap/nozzle closeups expose hidden weaknesses. All acceptance images are directly inspected.
5. Present source/STEP paths, reference cue ledger, geometry evidence, viewer links, candidate tradeoffs, recommended direction and outstanding fit decisions to the user. The gate ends with user selection, rejection or requested hybridization; record a decision only if actually received, and do not advance to detail or production on CAD validity alone.

## Test notes

- Run strict native validation and artifact-only checks on every new assembled/separated STEP; compare the baseline without rewriting its original output or retroactively imposing its fixed dimensions on new designs.
- Verify the silhouettes differ at the same viewing scale with finishes suppressed; read every review board directly. Document missing reference images or unverified fit instead of guessing.
- This concept review does not certify pod capacity, final launcher fit, materials, export, Unity or runtime stages.

## Packet delivered — 2026-09-23

Added B/Shoulder and C/Facet assembled/separated STEP studies and the matched historical baseline-plus-three `cad/palisade_interceptor/reviews/Palisade_Selection_Board.png`. All six new STEP files pass native strict every-placement validation with zero failures; `src/check_studies.py` passes artifact-side checks for all three pairs (`reviews/checks.json`). Main-agent image review, evidence mapping, dimensions, tradeoffs and preliminary recommendation are in `cad/palisade_interceptor/REVIEW.md`. CAD Viewer links use the live study workspace. The packet was then presented for user selection.

## Selection — 2026-09-23

After viewing the comparison packet, the user selected **A / Spear**, describing it as "great and 100% the taste that I was going for." This closes the three-way concept-selection issue. `cad/palisade_interceptor/REVIEW.md` records the exact approval boundary and the remaining fit problem: A's 101.01 mm radial envelope does not support an untested four-round assumption in the historical 400 mm pod.
