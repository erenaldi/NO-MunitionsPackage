# Halberd intake review and local redesign contract

Date: 2026-09-22. Boundary: geometry-only silhouette/intake concept, not production or engineering.

**Current authority: the user's annotated front/side/taper drawings supersede R2.** R3's contract is in `R3_DRAWING_CONTRACT.md`. R2's 9.0/10 below is a historical review of the earlier interpretation, not evidence that it matches the clarified intent. Fourfold propagation still requires user visual approval.

The user subsequently accepted R3's single-station exterior and requested deeper/darker interiors. The current candidate is documented in `R4_INTERIOR_CONTRACT.md`; its actual channel extension is 544.974 mm (30% of housing length), with recessed intake/nozzle liners. The historical scores below are not new ratings of R3/R4.

**Latest correction:** `R5_STRAIGHT_TAPER_CONTRACT.md` supersedes R4's wavy housing interpolation and back-face shading. The user wants ideal straight edges/uniform taper, with drawings treated as intent guides. R5 preserves side materials and channel depth, and makes only the rear faces pure black for Kris-like obscuration. Historical scores below do not rate this revision.

**Current planform refinement:** `R6_LATE_TAPER_CONTRACT.md` records the user's request for a curved top-down taper that slims aggressively only near the end. R6 replaces the linear rear planform with an exact monotonic cubic while retaining R5's straight inlet/side profile and black backs. This controlled curve is distinct from the rejected interpolation ripples.

## User-selected constraints

- Preserve the nose seen on C. Source confirms A/B/C share `ogive()` and the same nose-transition body; C's nose is therefore preserved exactly, not approximated from its render.
- Preserve A's fin planforms and existing 45/135/225/315-degree clocking on both stages. User corrected the rotation request: it is the **intakes**, not the fins, that must move 45 degrees to line up with those fins. Place the new prototype on the 45-degree rounded corner; eventual intake pattern uses 45/135/225/315 degrees measured from +Z.
- Redesign intakes against the first supplied reference. Existing rail treatment is not approved. Prototype one uncertain intake before fourfold propagation.

## Review contract and weights

Candidate assessed: delivered `STEP/A_Trace.step`, specifically its intake treatment in the full missile context. Reference priority: current user correction, supplied first image's long intake forms, then the second image's overall restraint. The first reference's red details are covers; hidden functional duct construction is not established by that image.

Weights chosen for this local visual-concept review: brief 20%, reference silhouette 30%, geometry 15%, interfaces 15%, readability 15%, CAD-review delivery 5%. Engine/fabrication/performance requirements are N/A at this boundary and receive no score.

## Baseline verdict: 5.4/10, concept-stage, medium confidence

| Factor | Weight | Score | Evidence | Main limitation / improvement |
|---|---:|---:|---|---|
| Brief fit | 20% | 5 | Four low channels and original matched views | Has the feature count, but misses the requested integrated fairing language; redesign the primary form. |
| Reference fidelity | 30% | 3 | First user image versus `reviews/A_intake_detail.png` | Narrow nearly parallel rails and abrupt rectangular ends differ from the broad sculpted covered entries; widen/blend and cant the inlet. |
| Geometry integrity | 15% | 9 | Strict native A validation and `reviews/checks_ABC.json` | Valid positive solids and open mouth probes; validity does not make the shape faithful. Preserve checks on revision. |
| Interfaces | 15% | 7 | Body intersection checks and end/close views | Rails attach but look applied rather than integrated; merge fairing into the body and check local continuity. |
| Readability | 15% | 4 | Overview, opposed and local views | At full length the rails resemble thin strips; add a clear inlet-to-fairing progression without bulky pods. |
| CAD-review delivery | 5% | 9 | Six delivered STEP states, snapshot packet and live links | Sufficient concept evidence; add isolated/grazing coverage for the new local form. |

Weighted arithmetic: 5.35, reported 5.4/10. Evidence coverage 100% of applicable concept-review factors. No invalid-solid or fit-critical failure cap applies; the visual approval gate nevertheless fails for these intakes. The user has explicitly rejected their current treatment.

Strongest match: the restrained whole-missile silhouette and chosen nose/fin family. Highest-impact mismatch: the entry-to-long-fairing relationship, not missing surface detail. Prioritized repairs: (1) broader body-blended fairing, (2) canted structured mouth, (3) visibly changing width/height along the aft run.

## Local change contract

- Local axes: X axial/forward; prototype radial axis is 45 degrees from +Z toward +Y, aligned with the first A fin; local tangential axis runs across the mouth.
- Retain: C-identical nose and forward transition, rounded-square core, stage ratio/seam, A's eight fin shapes and 45-degree clocking.
- Remove: all four old rail occurrences from the new prototype only. Historical A/B/C stay intact.
- Add: one corner-mounted fairing blended into the main body, with a canted inlet and shallow visible passage. Other intake stations are intentionally absent pending local approval.
- Boundary: fairing/cut remain on the main stage behind X=740 and ahead of the booster seam; protected core remains present. No production internal propulsion is modeled.
- Acceptance views: full context, opposite context, side/top, front/rear, local mouth, grazing fairing, separated stages.
- Excluded interpretations: constant-section box rail, tiny open scoop disconnected from a long fairing, red color as a substitute for geometry, blind replication of four unapproved details.
- Inference: the reference is a covered display configuration. The prototype keeps a visible open mouth for judging the underlying visual form; exact cover/flight-state treatment remains a user-review item.

## Revised prototype verdict: 7.4/10, local concept-stage, medium confidence

Candidate: `STEP/Selected_Intake_Prototype.step`, with `Selected_Intake_Prototype_Separated.step` as the stage-ownership view. This grade assesses the one-intake concept gate, not a finished four-intake missile. Same factor weights as the baseline; 100% applicable local-review evidence coverage. No confirmed critical geometry failure remains.

| Factor | Weight | Score | Evidence | Main limitation / next improvement |
|---|---:|---:|---|---|
| Brief fit | 20% | 8 | `reviews/intake_revision_checks.json`, context/end views | C nose and A fins preserved; intake is now corner-aligned. Full fourfold look still requires approval and propagation. |
| Reference fidelity | 30% | 6 | First supplied image versus `reviews/Intake_R1_mouth.png` and context view | Broad crest, swept shoulders and changing aft width improve the form relationship. The reference's covered entry and more pronounced strake treatment are not an exact match. |
| Geometry integrity | 15% | 9 | Both native validations: 11 occurrences / 5 prototypes / zero failures | Valid positive solids; retain independent roof/sidewall checks during further refinements. |
| Interfaces | 15% | 8 | One fused main-body solid, unchanged forward-transition Boolean comparison, separated-state equality | Long fairing is now integral to the body. Shoulder transitions are still concept surfaces, not final local blend detailing. |
| Readability | 15% | 7 | Nine views in `Intake_R1_Overview.png`, `Intake_R1_Details.png`, `Intake_R1_Opposite.png` | Canted mouth and long widening crest are readable; silhouette remains subtle at full length, and one-intake asymmetry is intentional. |
| CAD-review delivery | 5% | 8 | Two STEP files, source/checker, nine snapshots and live viewer | Local approval packet is ready; three other stations are deliberately absent. |

Weighted score: 7.4/10. This is a review judgment, not user approval. Engine delivery, real aerodynamics and manufacturing remain N/A; full fourfold visual balance remains unverified at the next gate.

### Findings and verification

- Strongest improvement: the broadening, flattened fairing now flows into the body and tapers toward the retained fin station rather than reading as a constant-section rail.
- Remaining mismatch: the reference shows covered entries and a stronger long-strake visual hierarchy. The new open-mouth interpretation needs user judgment before it is repeated.
- First rounded-crest attempt passed solid validity but exposed unintended shoulder slits in the close view. Replaced the crest with swept flanks/flat roof and a tapered-width passage. An additional sidewall probe initially failed; widened the crest while preserving the test. The final checker passes mouth, roof and both sidewall probes.
- Exported-shape Boolean comparisons preserve C's ogive, A's eight fin solids and booster body, the forward transition outside the local edit, and both stages' shape under separation. Measured fin clocks: 45/135/225/315 degrees. New protrusion occupies only the 45-degree intake station.
- Independent artifact checker passes 3370 mm total length, 561.666667 mm booster, protected core and passage probes. Both native strict every-placement validations pass: 11 occurrences, 5 prototypes, zero failures.
- Primary model directly inspected all nine final views via the three final boards. No fourfold propagation was performed.

### Review links

- [Assembled prototype](http://127.0.0.1:3246/?file=STEP/Selected_Intake_Prototype.step)
- [Separated prototype](http://127.0.0.1:3246/?file=STEP/Selected_Intake_Prototype_Separated.step)
- [Overview](reviews/Intake_R1_Overview.png) / [Details](reviews/Intake_R1_Details.png) / [Opposite](reviews/Intake_R1_Opposite.png)

Rebuild using `src/intake_revision.py` and `src/intake_revision_separated.py`; verify with `src/check_intake_revision.py`; reproduce images with `src/review_intake_revision.py`, all using the project's CAD Python interpreter. Next gate: approve or revise this single intake's shape before its fourfold pattern.

## R2 iteration contract — user requested continued refinement toward 9/10

The same six weights and score anchors remain in force. A requested score is not evidence, and does not grant automatic visual approval or fourfold propagation.

R2 targets two observed remaining gaps: (1) explicitly show the reference's covered entry as a removable neutral-shaded review part, while retaining the open geometry view; (2) replace the low aft fade with a rising, narrowing strake crest tied into the selected fin-root region. Preserve R1 files as the previous scored candidate; new R2 filenames keep evidence distinct.

Visual acceptance: entry, broadening duct shoulder and aft strake must read as a coherent sequence in the full reference-facing view as well as closeups; crest must not become a detached blade/pod; cover must actually occupy the opening; no unintended sidewall breakthrough; selected nose and fins must remain exactly unchanged. New geometry and score are pending verification.

## R2 final review — 9.0/10, single-intake concept, medium confidence

Assessed artifacts: `STEP/Selected_Intake_R2.step`, `Selected_Intake_R2_Covered.step` and `Selected_Intake_R2_Separated.step`, identified by SHA-256 in `reviews/intake_R2_manifest.json`. Same factor weights and anchors as R1; no confirmed critical failure remains. This is the primary model's context-specific visual judgment, not an independent human approval or a production score.

| Factor | Weight | Score | Evidence and reason | Remaining boundary |
|---|---:|---:|---|---|
| Brief fit | 20% | 9 | Exact Boolean preservation of C's nose and all A fins; 45-degree intake alignment; unchanged stage proportions; low integrated silhouette retained in side/top/context views. | User still judges the interpretation. |
| Reference fidelity | 30% | 9 | The wider canted entry with its cover now leads into a broad shoulder and an aft-rising narrow crest; `Intake_R2_Covered.png`, overview, grazing and aft views support the reference's entry/duct/strake relationship. | This is an inspired blend under the user's rounded-square/slender-body constraints, not a dimensioned replica of the reference. |
| Geometry integrity | 15% | 9 | All three exports pass native strict every-placement validation; valid positive solids, open/widened passage probes, roof/sidewall probes and forward-notch regression checks pass. | Mesh/engine and physical performance are outside this gate. |
| Interfaces | 15% | 9 | Fairing is fused into the main body; cover seats on the rim; a leading-edge-derived aft boundary retains 99.9909% of the aligned fin's prior exposed volume. No stage seam is crossed. | Fine interface finishing belongs after concept approval. |
| Readability | 15% | 9 | Full context and closeups now distinguish the entry rim, wider duct shoulder and narrowing strake. The enlarged opening reads at full length; the chosen fin remains visible instead of being buried. | Full fourfold balance must be reviewed after local approval. |
| CAD-review delivery | 5% | 9 | Open/covered/separated STEP files, 12 directly reviewed snapshots, five boards plus an R1/R2 progression board, fact reports, artifact checker and identity manifest are available. | Viewer and snapshots are CAD evidence only. |

Weighted total: **9.0/10**. Applicable local-gate evidence coverage: **100%**. Confidence remains medium because the reference is a single perspective illustration with inferred dimensions. Engine, fabrication and aerodynamic factors remain N/A, as in the prior review; they were not removed to raise this score.

### What actually changed

1. **Entry:** widened the outer forward fairing from the first R2 attempt's 63-70 mm to 104-110 mm, with a 64 mm passage-profile width. The canted rim now has a distinct reference-style cover, supplied as a separate neutral-shaded review state. Raising the forward passage floor removed the tiny notch that previously extended ahead of the lip.
2. **Long form:** the broad forward crest narrows and rises aft into a strake rather than fading into a strip. Cross-view review confirms a continuous integrated form.
3. **Fin junction:** the first taller-strake attempt retained only 48.36% of the aligned fin's exposed volume despite preserving its source solid. That failed the new >=80% exposure check. Shaping the aft boundary from the actual selected fin leading edge, with a 2 mm axial seat, raises retention to 99.9909% without changing the fin.

The aperture enlargement deliberately moved the sidewall locations. Tests were updated to assert the enlarged void and probe the new walls, not merely dropped or loosened. The final suite retains the prior protected-core, open-mouth, unchanged-nose/fin, rotation and separation criteria and adds forward-notch, cover-seat/coverage and fin-exposure checks.

### Verification and review packet

- `src/check_intake_r2.py`: PASS. Three native validations with zero failures; open/separated each 11 occurrences / 5 prototypes; covered 12 / 6. Records 20 roof/sidewall probes, three widened-aperture probes, two forward-notch probes, 12 cover-opening probes and exact selected-part comparisons. Results: `reviews/intake_R2_checks.json`.
- `src/publish_intake_r2.py`: three refs/facts/planes/positioning reports, 15 hashes covering three STEP files and 12 snapshots, readable-image checks, and `reviews/Intake_R2_Progression.png`.
- Primary model directly inspected all 12 final views through `Intake_R2_Overview.png`, `Intake_R2_Details.png`, `Intake_R2_Opposite.png`, `Intake_R2_Covered.png`, `Intake_R2_Aft.png`, then inspected the progression board.
- All seven R2/review/publication Python modules passed compilation. One concurrent build encountered a shared-store access-denied error; serial retry succeeded, followed by the full final verification. No cache relocation or validation bypass was used.

### Current handoff

- [Open intake](http://127.0.0.1:3246/?file=STEP/Selected_Intake_R2.step)
- [Covered reference presentation](http://127.0.0.1:3246/?file=STEP/Selected_Intake_R2_Covered.step)
- [Separated stages](http://127.0.0.1:3246/?file=STEP/Selected_Intake_R2_Separated.step)
- [R1/R2 progression](reviews/Intake_R2_Progression.png)

Rebuild using `src/intake_r2.py`, `src/intake_r2_covered.py`, `src/intake_r2_separated.py`; check with `src/check_intake_r2.py`; render with `src/review_intake_revision.py --revision R2`; collect facts/manifest with `src/publish_intake_r2.py`. The other three intake stations remain intentionally absent pending approval of this local form.
