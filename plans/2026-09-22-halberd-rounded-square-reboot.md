# Halberd rounded-square visual reboot

Date: 2026-09-22. Design concept confirmed in the alignment interview, then amended by the user's cross-section reference and approval to proceed.

## Active context

- Latest deliverable (2026-09-27): `cad/halberd_rounded_square/R18_SURFACE_LAYOUT.md`,
  **`concept-review`**. Annotated four-face and whole-model map plus seven individual
  feature outline studies built and directly inspected. Separate28-part planning
  base preserves the exterior/nose joint, hides old service covers and restores
  only their seats; saved checks pass. New detailed features remain unbuilt.
  User layout/shape approval is the next gate; do not resume R17's cover matrix.

- Current design deliverable (2026-09-27): `cad/halberd_rounded_square/R18_SURFACE_FEATURE_CATALOG.md`,
  `intent-draft`. User requested defining an actual feature list before placing
  details. Proposed twelve families cover collars, conformal hatches, circular
  caps, selected access doors, one longitudinal cover, form-led intake/root/stage
  interfaces, booster hatch, nozzle rims and restrained alignment marks. Region
  and face roles include deliberate quiet skin. Catalogue is awaiting selection;
  annotated distribution and R18 CAD are not yet built or approved.

- Superseding user correction (2026-09-27): R17's repetition degraded the asset;
  surface features need deliberate design comparable to Kris. State **`blocked`**
  on revised surface composition. Authority: `cad/halberd_rounded_square/R17_DESIGN_CRITIQUE.md`.
  Independent critique and primary review concur. Keep silhouette/local geometry
  evidence; reject the blanket panel/seam matrix. Next deliverable is an annotated
  four-face layout with form-related clusters and intentional quiet spans.
  Object count is descriptive, not a placement rule or acceptance quota. The
  technical R17 candidate facts below remain historical evidence, not approval.

- Latest candidate (2026-09-27): R17 Kris-scale surface-detail pass; `cad-review`. Authority: `cad/halberd_rounded_square/R17_FULL_DETAIL_CONTRACT.md`.223 detail instances plus23 primary forms,246 parts/full state. All555 saved full/focus placements pass;34 R16 parts unchanged,10 hosts modified only by localized pockets,202 new details supported without unintended overlap. Primary inspected all-side and actual Kris comparison packets. Selected reference remains `cad/IRM-S4_Kris_PL10_Hybrid.step` (222 measured detail instances).

- Current baseline: user approved R11 ridge-aligned intake and authorized fourfold propagation, verified in R12. Intake/fin heights and +170 mm fin shifts remain fixed; the original continuous intake taper crosses the stage seam and its aft portion belongs to the booster. R9's added transition is rejected.
- Authoritative sources: `cad/halberd_rounded_square/R17_FULL_DETAIL_CONTRACT.md` plus preceding R11/R12/R14/R15/R16 contracts; R10 remains the continuous-taper/stage-split basis. Current builder is `src/halberd_r17_shapes.py`, composing decorated and saved R16 with checked local interface prototypes. No engine/runtime promotion has been approved.
- Approved concept / review packet: user annotations and fin-on-housing clarification govern the accepted R3 exterior. R4 interior evidence is in `cad/halberd_rounded_square/reviews/Intake_R4_*.png`; ABC/R1/R2 packets are historical.
- Coordinate system and scale: millimeters, X forward and Z dorsal, centered assembled axial extent; 3370 mm nominal length.
- Preserve: slender reference-led proportions, rounded-square section, circular ogive, flush short booster, four shallow intake channels, two compact four-fin sets.
- Avoid: dominant bulky intake pods, a fully cylindrical main body, long booster inherited from old models, color-only concept differences.
- Emphasize: continuous slender outline and clear main-stage identity after separation.
- Hard constraints: booster axial length equals assembled length / 6; both stages share the rounded-square section at the join.
- Selected decisions (2026-09-22, amended 2026-09-23): preserve C's nose and booster fins. Intake/fin stations are 45/135/225/315 degrees. New annotations explicitly authorize main-stage fins seated on top of the rear intake housing, with the red exposed silhouette taking precedence over exact A-main-fin preservation. Blue defines a thin curved-floor inlet and full taper to the main-stage seam. C's nose source is identical across the original trio.
- Next gate: user reviews R17's full-detail layout, particularly density and panel-border weight. The user's explicit request for Kris-scale density supersedes the earlier80–120 planning range;223 objects now meet that count goal. R16 local joint acceptance is recorded. Count parity does not prove equal visual complexity or physical fidelity. Export/engine/runtime gates remain pending.
- Next-gate files: this brief, `docs/ASSET_DESIGN_WORKFLOW.md`, `cad/halberd_rounded_square/REVIEW.md`, and the new study sources/review packet.

## 1. Problem statement

The user wants a fresh Halberd visual identity combining supplied K-77ME/AIM-260-inspired imagery. Earlier models and text encode conflicting proportions and feature treatments. Reusing those shapes as authority would undermine the new direction; three comparable CAD studies must expose the visual choices before detailed work.

## 2. Solution

Create three geometry-only interpretations of a slender missile led by the second supplied reference, borrowing restrained elongated intake fairings from the first. The main body has four short flat faces connected by broad rounded corners, as shown in the user's cross-section screenshot. Toward the nose, those flats blend away into a circular section and a traditional pointed ogive. A matching rounded-square booster continues flush across the seam and occupies the aft sixth of the complete missile. Each stage has its own compact four-fin set.

The user reviews matched assembled and separated views, selects or hybridizes a direction, and approves its silhouette before detailed CAD begins. Differences must be visible in intake integration and fin architecture/placement while preserving the fixed brief.

## 3. User stories

1. As the art director, I can compare three genuinely distinguishable interpretations at identical scale and cameras, so that selection rests on shape rather than presentation.
2. I can see the rounded-square body transitioning to the circular ogive in end, side and oblique views, with the supplied screenshot serving as shape evidence.
3. I can inspect assembled and separated states and see a booster exactly one sixth of total axial length, a flush join and a complete-looking main stage retaining four fins.
4. I can distinguish four shallow intake channels with readable mouths and elongated integrated fairings from painted marks or detached pods.
5. I receive editable parametric source, checked STEP studies, review PNGs and CAD Viewer links, with visual approval clearly distinct from geometry validation.

## 4. Implementation decisions

| Decision | Choice and rationale |
|---|---|
| Starting dimensions | 3370 mm length; approximately 200 mm across body flats in both transverse axes. These are study baselines, not verified aircraft-fit dimensions. |
| Main section | Rounded square with broad corner rounds and short flats; screenshot is qualitative, with no supplied radius. |
| Nose | Smooth transition into a circular section and pointed ogive; preserve the second image's restrained elongated reading. |
| Booster | Exactly L/6 = 561.666... mm axial allocation; remaining main-stage allocation is 5L/6. Use expressions, not rounded constants, for the ratio. |
| Stage seam | With centered X and nose at +L/2, seam X = -L/2 + L/6 = -L/3. Fairings must not bridge detachable stages. |
| Booster section | Continue rounded-square main section flush at the join; aft nozzle transition can round down locally. |
| Intake language | Four equally spaced low integrated channels on the main stage; visible mouths feeding long shallow fairings. |
| Reference covers | Red details in the first image are intake covers. They establish reference form, not an approved red palette or a requirement to fly with covers fitted. |
| Fins | Four compact fins per stage; main-stage set ahead of the seam. Exact relative clocking and sweep are review variables. |
| Presentation | Geometry-only, neutral consistent shading. Assembled and separated configurations for each study. |
| Source independence | New source namespace; old Halberd studies provide tooling examples only and are not shape donors. |
| Approval gates | Three-study comparison, then silhouette selection and feasibility before detail. Prototype any ambiguous repeated detail once and obtain approval before propagation. Initial simple fourfold blockout establishes layout only. |

### Reference evidence

- First user-supplied image: pointed nose, forward red intake covers, long raised intake/strake forms, aft fins. Used for integrated intake form relationships.
- Second user-supplied image: slender circular body, long pointed nose, compact tail. Dominant proportion and restraint reference, superseded specifically for main-body cross-section.
- Third user-supplied image: rounded-square section with broad corners and short flats. Explicit authority for main and booster sections, not a dimensioned drawing.
- The primary model directly inspected these chat images. Durable image paths have not been established; do not invent them or silently substitute earlier repository images. Before a future-session visual comparison, preserve the actual supplied images if accessible or request their files.
- No claim is made that the imagery proves real-world missile construction or performance.

## 5. Data model and modules

New files below are proposed ownership boundaries, not existing artifacts:

- `cad/halberd_rounded_square/`: isolated study workspace with `src/`, `STEP/` and `reviews/` subdirectories.
- `src/study_shapes.py`: encapsulates sections, circular-ogive transition, stage split, intake forms and compact fins; exposes `build_study(key, separated=False)` returning a labeled build123d compound. Explicit named study parameters, no environment-driven geometry.
- Six thin parameterless decorated entrypoints: three assembled studies and their separated review derivatives, each output declared explicitly. Both states use the same geometry factory; separation changes placement only.
- `src/check_studies.py`: verifies source-independent geometric facts against brief constants, semantic groups and state relationships. Reports failures without weakening checks.
- Review tooling: explicit target list, matched camera packet and comparison boards, using supported cadgen snapshot commands. Existing `cad/compare_halberd_four_intake_concepts.py` and `cad/generate_halberd_four_intake_reviews.py` may inform tooling conventions without importing old shape constraints.

Native labels distinguish main body, intake features, main-stage fins, booster body, booster fins and visual nozzle forms. Exact solid count follows the geometry rather than becoming a quality target. Runtime plugin and exporter modules are outside this delivery boundary.

## 6. Testing and acceptance

- Check total axial bounds, exact one-sixth booster allocation, flush section at seam, fourfold layout, separate fin ownership, and separated-state geometry preservation.
- Check body width/height independently from appendage span. Record inferred corner radius and transition dimensions for each study.
- Run `cadgen step inspect validate --every-placement` for every emitted STEP; require valid positive-volume solids with no reported failures.
- Run refs/facts and targeted measurements for bounds and stage placement. Inspect intake openings and joins, including interference at the stage boundary.
- Produce side, top, front, rear, opposed isometrics and separated-state views with matched cameras/scale; include a section/nose-transition close view and intake close view where needed.
- Primary model directly reviews every acceptance image. Reject visually obstructed views, indistinguishable variants, unreadable intake forms or a transition that fails the user's cross-section intent even when CAD checks pass.
- Start/reuse CAD Viewer and return explicit links to the three assembled studies and relevant separated states.
- User selection is the final gate for this delivery. Valid geometry alone does not approve a direction.

## 7. Out of scope

Detailed hardware, engineered internal propulsion, aerodynamic/performance validation, textures and markings, production export, Unity assets, bundles, plugin edits, installation and runtime tests are deferred. Actual aircraft clearance is a later feasibility gate before detailed modeling; the 200 mm baseline is not clearance evidence. No old asset is promoted or overwritten by this brief.

## Approved slice boundaries

User approved the two-slice breakdown on 2026-09-22. Board: `issues/011-build-halberd-rounded-square-first-study.md` -> `issues/012-review-halberd-rounded-square-trio.md`.

1. First complete study: fresh source through validation, assembled/separated snapshots and viewer handoff; proves the shared section/transition and short-booster treatment.
2. Contrastive trio: add two coherent alternative intake/fin treatments and deliver all three in one matched, validated review packet for user selection.

No additional functional requirements are needed before the silhouette studies. Geometric/artistic choices listed as study variables remain reviewable rather than silently locked.

## Delivery result — 2026-09-22

Issues 011 and 012 delivered A/Trace, B/Chine and C/Shoulder, with six valid STEP files and 27 directly reviewed snapshots in five comparison boards. Artifact-only checks pass for all three; strict native every-placement validation passes all six with zero failures. `cad/halberd_rounded_square/REVIEW.md` records exact files, viewer links, dimensions, tradeoffs, validation and reproduction. User selection, detailed CAD, fit feasibility and downstream delivery remain pending.

Subsequent partial selection and intake revision are recorded in `cad/halberd_rounded_square/INTAKE_REVIEW.md`: C-identical nose, unchanged A fins, one revised corner-aligned fairing with a canted mouth. The initial reviewer score was 5.4/10 for the old intake treatment; the revised local prototype scores 7.4/10 at its concept boundary. Both prototype STEP states pass strict native validation and the independent preservation/passage checks. This does not approve or complete the four-intake assembly.

User requested continued refinement toward 9/10. R2 now receives a 9.0/10 **single-intake concept** review under the unchanged rubric: wider covered/open entry, aft-rising strake and a leading-edge-derived fin seat that retains 99.9909% of the aligned fin's exposed volume. Open/covered/separated exports pass strict checks and have a 12-view packet plus progression board. `INTAKE_REVIEW.md` and `reviews/intake_R2_manifest.json` identify the current candidate. Full fourfold appearance remains a separate user-approval gate.

**2026-09-23 supersession:** the user's annotated drawings and explicit fin-on-housing correction replace the R2 interpretation above; its score is historical, not current acceptance. R3's source, three checked STEP artifacts, ten directly reviewed views and exact acceptance results are recorded in `cad/halberd_rounded_square/R3_DRAWING_CONTRACT.md`. R3 preserves the nose/core/booster, enlarges the curved-floor opening, carries the taper to the seam and seats the revised main fin on the rear housing. It remains a one-station prototype awaiting approval.

**2026-09-23 R4 update:** user accepted R3's exterior and requested dark rear intake/nozzle recesses plus an extension explicitly defined as 30% of the full housing length. R4 adds 544.973923 mm of clear channel depth and recessed charcoal geometry while preserving R3's outer form. Three outputs pass native and independent checks; eight final views are directly reviewed. Current handoff: `cad/halberd_rounded_square/R4_INTERIOR_CONTRACT.md`.

**2026-09-23 R5 correction:** user identified wavy boundaries and requested straight lines, a uniform full rear taper, and darker backs only, comparable to the Kris CAD model. R5 uses ruled geometry with exact endpoint interpolation, retains the channel/fin/nozzle-side geometry and materials, and splits out pure-black rear caps. `R5_STRAIGHT_TAPER_CONTRACT.md` records the Kris evidence, linearity/color checks and solid/rendered review packet. Hand annotations are now explicitly intent guides rather than traced surface boundaries.

**2026-09-23 R6 refinement:** user clarified that the top-down taper should be curved and only narrow aggressively toward its end. R6 uses an exact cubic planform, with 12.5% of total narrowing in the first half and 57.8125% in the final quarter. The straight inlet, linear side-height profile, channel, fins and materials remain unchanged. Two validated STEP states and a matched R5/R6 comparison are documented in `R6_LATE_TAPER_CONTRACT.md`.

**2026-09-23 R7 booster-fin prototype:** user supplied a low trapezoid and selected the low-profile interpretation. Delivered one 295 mm root / 220 mm centered tip / 53 mm height fin at the existing 45-degree station. All other R6 parts are preserved. Assembled, separated and isolated-fin STEP files pass strict validation; eight views have been directly reviewed. The earlier terminal blocker is resolved. `R7_BOOSTER_FIN_CONTRACT.md` records the positive attachment, existing boattail overhang, nozzle clearances and pending visual gate before fourfold propagation.

**2026-09-23 R8 propagation:** user authorized a 170 mm noseward booster-fin shift and copying the complete approved set to the other three stations. R8 implements all four housings/channels, mounted main fins, intake lining/back pairs and shifted booster fins. Both 23-part states pass all per-placement topology/closure/positive-volume/self-intersection checks and independent replication/clearance/material checks. The shared runtime upgraded to cadgen 0.6.6 during the task; R8 uses its named material declarations, native Python checks and current snapshot schema. Eight views were directly reviewed. Current handoff: `R8_FOUR_STATION_CONTRACT.md`, viewer port 3247.
