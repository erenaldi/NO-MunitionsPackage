# Halberd Four-Intake Clean-Sheet Concepts

## Problem statement

The selected Halberd hybrid proves the runtime datums and four-intake arrangement,
but it represents only one visual direction. Four genuinely contrastive concepts
are needed before committing the production asset to that silhouette.

## Solution

Create four independent concept-stage CAD missiles using the selected hybrid only
as inspiration and dimensional authority. Preserve its runtime interfaces and
outer envelope while giving each candidate a different body, nose, fin, booster,
and recessed four-intake design language: Razorback, Manta, Citadel, and Petal.

## User stories

1. As the art director, I can compare four unmistakably different Halberd
   silhouettes at identical scale so I can select or hybridize a direction.
2. As the runtime integrator, I can trust that every candidate preserves length,
   pivot, seam, mount, tail plane, and carriage envelope.
3. As the reviewer, I can inspect four real recessed intake openings and internal
   paths on every candidate rather than relying on painted or projecting details.

## Implementation decisions

- Preserve 3367 mm length, centered pivot, X=-336.7 mm stage seam, current mount
  stations, tail/FX plane, and the current pre-intake outer envelope.
- Four intakes remain on 45/135/225/315-degree planes and wholly inside the
  existing cross-section; no external cowls or intake cuts beyond X=850.
- Candidates are authored independently from primitives and loft stations. The
  current STEP is not imported, cut, or modified.
- Candidate directions are hard-faceted Razorback, organic Manta, armored
  Citadel, and rounded/fluted Petal.
- Lifecycle ends at `concept-review`; detailed CAD, Unity, and runtime promotion
  require a later user selection.

## Data model and modules

- `cad/halberd_four_intake_concepts.py`: locked datums, independent candidate
  factories, and review-part extraction.
- `cad/generate_halberd_four_intake_concepts.py`: four declared STEP models.
- `cad/check_halberd_four_intake_concepts.py`: artifact-only acceptance checks.
- Snapshot packet and comparison-board script for equal-scale visual review.

## Testing decisions

- Check exact axial datums, envelope containment, labels, positive valid solids,
  stage ownership, mount placement, body contacts, four clear mouths, inward
  passage movement, protected X850..1080 forebody, and fourfold intake symmetry.
- Run `cadgen step inspect validate --every-placement` on all four masters.
- Render and directly review opposed isometrics, orthographic/end views, intake
  closeups, and separated stages. Visual contrast remains a human judgment.

## Out of scope

- Production detailing, textures, UVs, Unity assets, colliders, rack prefabs,
  bundles, plugin changes, aerodynamic claims, and runtime validation.

## Concept-review result (2026-09-21)

- Lifecycle state: `concept-review`; no candidate has been selected or approved.
- All four masters and their intake/separated review derivatives pass strict STEP
  validation. Artifact checks pass the locked datums, envelope, contacts, intake
  probes, protected forebody, symmetry, and semantic-label contract.
- The matched-camera packet confirms four readable recessed intake languages:
  Razorback slots, Manta elliptical scoops, Citadel rectangular scoops, and Petal
  recessed ramps with paired guide chines. Manta's waist and Petal's rounded
  waist/ramp treatment provide the strongest immediate differentiation.
- Residual visual issue: the locked carriage envelope keeps Razorback and Citadel
  relatively close in side/top silhouette despite different faceting, fin, nose,
  and scoop treatments. Selection may use either as-is or request a more extreme
  in-envelope revision before the detailed-CAD gate.
- Review evidence: `cad/Halberd_Four_Intake_Overview.png`,
  `cad/Halberd_Four_Intake_Details.png`,
  `cad/Halberd_Four_Intake_Separated.png`, and
  `cad/Halberd_Four_Intake_MatchedScale.png`.

## Petal revision result (2026-09-21)

- User reopened Petal to remove the visually square midbody and replace the flush
  skin slits with intakes that have visible capture structure.
- The Petal sustainer and booster now meet at a nearly circular 196 mm section;
  the forward sustainer waists to 156-160 mm to make room for the intake inside the
  unchanged carriage envelope. The updated baseline Petal master remains a valid
  19-part concept.
- One 45-degree intake was prototyped before propagation. Visual review rejected
  the first long/dark hood because it read as a blade, and the user selected a
  recessed-ramp direction instead of the compact scoop/cowl alternatives.
- The selected treatment uses a rounded recessed passage with two short,
  flattened, body-colored guide chines. It is integrated at all four intake
  stations, fused into `sustainer_body`, and preserves the 19-part semantic
  contract, locked datums, protected core, and carriage envelope.
- The Petal master, intake review, separated review, 40-view packet, and all four
  comparison boards were regenerated. Artifact checks and strict every-placement
  STEP validation pass; direct board review found the rounded waist and localized
  ramp structure readable without reviving the rejected blade-like hood.
- The intake-direction approval is complete, but no whole Halberd candidate has
  been selected. Lifecycle remains `concept-review`; detailed CAD still requires
  a later candidate-selection gate.
- This is exterior concept geometry only. The opening and duct continuity are
  checked geometrically; no aerodynamic intake-performance claim is made.
