# Palisade interceptor visual redesign

Date: 2026-09-23. The user confirmed the design concept in the alignment interview.

## Active context

- Current state: `concept-approved`; A / Spear was selected on 2026-09-23 from three checked CAD directions against the old baseline. Fit and detail remain pending.
- Authoritative source: this visual brief for the interceptor study; `MUNITIONS.md` §12 for the existing system role and flight sequence; `docs/ASSET_DESIGN_WORKFLOW.md` for visual gates.
- Approved concept / review packet: user selected **A / Spear** from `cad/palisade_interceptor/reviews/Palisade_Selection_Board.png` on 2026-09-23. The original `cad/Palisade_Review.png` is an unapproved historical baseline.
- Coordinate system and scale: baseline source uses millimeters, X forward, Z dorsal, centered axial extent; its 1200 mm length and 85 mm maximum radius are comparison measurements, not new hard limits.
- Preserve: compact point-defense role; detachable aft turning cap with four lateral thrusters; concealed main nozzle exposed after cap release; ejection → snap-turn → cap release → main burn.
- Avoid: cosmetic-only variants, an unconvincing plain tube or cap, and design choices justified solely by CAD validity.
- Emphasize: distinct, plausible, game-readable whole silhouettes and a convincing main stage in the separated view.
- Rejected interpretations: the original candidate is not an approved visual master; the old pod size and four-round capacity are not fixed fit limits for these studies.
- Hard constraints: preserve the existing flight-stage order and four-thruster cap; each stage remains separately representable and the main nozzle is visible after release.
- Open decisions: pod/cell packing and capacity for A's measured envelope; detailed styling, materials and downstream delivery. Any fit-driven external shape revision reopens concept approval.
- Files for the next gate: this brief, `MUNITIONS.md` §12, `docs/ASSET_DESIGN_WORKFLOW.md`, `cad/palisade_geometry.py`, `cad/Palisade_Review.png`, `cad/Palisade_separated.png`, and `cad/HKP-1_Palisade_Checks.json`.

## 1. Problem statement

The Palisade art direction needs an interceptor that reads as a compact purpose-built point-defense round, both while housed/launching and after its turning cap separates. The existing `cad/palisade_geometry.py` candidate has a usable staged architecture and checked CAD baseline, but the overall look in `cad/Palisade_Review.png` is too visually undifferentiated to commit to. A geometry pass alone cannot decide whether the existing silhouette should be salvaged.

## 2. Solution

Leave the original candidate intact as a baseline. Develop three genuinely different, real-hardware-informed interceptor directions whose **whole silhouettes** vary coherently: body, nose, fin system, turning-cap integration, and main-stage identity. Use plausible hardware cues with enough emphasis to read at game scale, without copying a reference wholesale or claiming a reference proves flight performance. Present every direction assembled and separated at matched scale with silhouette and stage cues, then let the user select, reject, or hybridize a direction before detailed CAD.

The decision is to salvage the staged concept and useful parametric source patterns, not to preserve the old external geometry. The current runtime sequence remains the design constraint; fit against a future pod is assessed after concept selection and before detailed modeling, rather than pretending the former 1200 mm × 85 mm envelope is approved.

## 3. User stories

1. As the art director, I can compare the untouched baseline with three visibly distinct, equally presented whole-interceptor directions, so I can select or hybridize on form rather than camera or finish.
2. I can inspect assembled and separated configurations of every direction and recognize the four lateral turning thrusters, detachable cap, and uncovered main nozzle, so the staged flight sequence has a legible physical design.
3. I can judge both a compact, credible point-defense round in its stowed/launch state and a complete-looking main stage after separation, with equal visual weight.
4. I can review actual reference-to-feature attribution, dimensions and cross-state CAD checks without confusing evidence, inferred styling and user approval.
5. I can approve a concept direction (or ask for another iteration) before any detail propagation, pod packaging decision, or production delivery.

## 4. Implementation decisions

| Decision | Choice and rationale |
|---|---|
| Candidate identity | Preserve `cad/palisade_geometry.py` and its current outputs as the unmodified comparator; avoid losing an inspectable baseline. |
| Study count and contrast | Three new directions plus the baseline; vary the entire silhouette through coherent architectures, not colors or one parameter. |
| Reference basis | Gather recognizable real-world point-defense/interceptor cues and identify precisely which cues inform each study; no particular external image is yet selected or saved. |
| Visual target | Plausible engineered shapes, restrained enough to feel purpose-built but prominent enough to read in game. |
| Stage contract | Four lateral turning thrusters on a detachable aft cap; cap conceals the main nozzle, which reads clearly when the cap is removed. Keep the existing ejection → snap-turn → release → main-burn ordering. |
| Geometry envelope | Original 1200 mm length / 85 mm radius are baseline facts, not hard study constraints. Record each candidate's actual dimensions and compare relative packaging implications. |
| Pod capacity | Original 1.8 m × 0.40 m pod and four-round capacity may change; do not declare fit from isolated interceptor CAD. Any change to gameplay capacity or runtime layout requires a separate decision and validation. |
| Presentation | Matched neutral shading, cameras, scale and assembled/separated views. Focus on primary forms, fins, stage seam and open thruster/nozzle geometry; detail and textures follow concept approval. |
| Approval | Three-way selection/hybridization is a user visual gate; assistant review and valid solids alone do not approve the concept. |

The existing staged controller is described in `MUNITIONS.md` §12 and `docs/V1_PLAN.md` under "HKP-1 Palisade — implementation plan." The old checks at `cad/check_palisade.py` and `cad/HKP-1_Palisade_Checks.json` establish only the old candidate's dimensions and geometric properties; they are not interchangeable with review of a new direction.

## 5. Data model and modules

New paths below are **proposed ownership boundaries**, not existing artifacts:

- An isolated Palisade interceptor study workspace under `cad/` owns separate parametric concept sources, labeled assembled/separated STEP outputs, and review images. It reads the baseline as an artifact for comparison; it does not overwrite baseline source or outputs.
- A shared concept-geometry factory takes explicit named direction parameters and returns the labeled build123d assembly components: main body, main nozzle, turning cap, four cap thrusters and fin/control forms. Thin parameterless CAD entrypoints produce each direction's assembled and separated artifacts; separation changes placement of the same stage shapes, not their design.
- A study checker accepts an explicit concept artifact pair and reports common stage invariants, part validity, nozzle exposure, symmetry or deliberate departures, assembled dimensions and separated shape preservation. Per-direction styling is parameterized rather than codified as a universal length/radius assertion.
- A review packet generator uses identical camera/scale and neutral presentation across the baseline and three concepts, with assembled and separated evidence and focused stage/nose/fin views. A compact reference ledger attributes each external cue and marks measured, user-specified and inferred properties separately.

Existing plugin, Unity, and `cad/palisade_geometry.py` modules need no changes for this concept gate. Exact file names within the new workspace are implementation choices, provided artifact identity and reproducibility stay explicit.

## 6. Testing and acceptance

- Confirm each STEP has valid positive-volume, labeled stage geometry with no unintentional body/cap intersection. Verify four thrusters on the cap, the concealed-then-exposed main nozzle, and identical component geometry between assembled and translated separated states.
- Record actual dimensions and radial envelope for each direction; do not run the old fixed-envelope checks as though they governed new concepts. Check that each proposed cap can leave the main stage without visibly bridging fixed parts.
- Run independent CAD inspection/validation for each emitted STEP and read the rendered views directly. Inspect opposed isometrics, side/top/front/rear, cap/nozzle closeups and the separated main stage at matched comparison scale.
- Check that differences survive neutral shading and game-relevant viewing distance; reject merely color- or micro-detail-based variation even if geometry validates.
- Present the reference ledger, tradeoffs, source/STEP paths and CAD Viewer links. The user selects, rejects or hybridizes; record that decision before any detailed CAD or repeated-feature work.
- Carriage clearance, cap animation, Unity materials, multiplayer visuals and flight performance cannot be established by this CAD review and remain separate gates.

## 7. Out of scope

The 1.8 m pod and its four-door design, final pod size/capacity, detailed hardware and material finish, production mesh export, Unity prefab/bundle, plugin/controller edits, in-game runtime claims and real aerodynamic or propulsion certification are deferred. This study cannot silently change the existing gameplay round count merely because the visual envelope is flexible.

## Open questions for the concept review

- Which real-world reference cues actually earn a place in each direction after the source images are inspected and attributed?
- Which candidate or hybrid should proceed to dimensional pod-fit feasibility? The eventual pod size and round count remain user decisions if the chosen geometry conflicts with the older spec.

## Approved slice boundaries

User approved the two-slice board on 2026-09-23: `issues/013-build-palisade-interceptor-first-direction.md` → `issues/014-review-palisade-interceptor-trio.md`.

1. Deliver one fully checked, reference-grounded direction in both flight states with direct image review and viewer links; establish the real study workflow.
2. Deliver two further distinct directions and a matched neutral board against the untouched baseline for the user's selection or hybridization.

Neither issue authorizes pod-fit conclusions or downstream production. The user must approve a direction before detailed CAD or the subsequent feasibility gate.

## Concept packet delivered — 2026-09-23

Issue 013's first checked direction and issue 014's baseline-plus-three comparison are in `cad/palisade_interceptor/REVIEW.md`; six assembled/separated STEP artifacts pass strict native validation and the new independent checks. The user selected **A / Spear** on 2026-09-23 as the desired concept silhouette. Issue 014 is closed at concept selection; pod fit, detailed CAD and later delivery gates are not approved.
