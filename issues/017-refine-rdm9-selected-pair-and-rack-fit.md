---
id: "017"
title: Refine selected RDM-9 pair and verify real rack fit
type: feature
status: blocked
blocked-by: ["016"]
---

## Slice

Take the user's selected/hybridized concept through a focused paired-state CAD candidate, preserved source-to-artifact validation, and a real donor-rack clearance review. End with a visual-approval packet so the user can approve or redirect the 3D design. This issue starts only after issue 016 records a selection; mere publication of three studies is insufficient. Authority: `plans/2026-09-23-rdm9-phantom-visual-reboot.md` and the selected concept record.

## Ownership and evidence

- Own the selected RDM-9 CAD sources/artifacts and issue-017 reports under the visual-study workspace, plus scoped RDM-9 contract/journal updates. Preserve all exploratory variants, R5/R6 historical sources and generated R5/Unity assets.
- Reuse existing coordinate conventions/checking approaches, not R5's hardcoded loft, span, source labels or triangle expectations. Main agent owns source-image comparison and direct CAD-review packet inspection.

## Acceptance

1. Build selected deployed and folded models from a common source with named, corresponding physical wing/fin panels, shared hinge frames and reversible pose transforms. Preserve the chosen faceted body, flattened wedge, visible folded wings, four corner fins and flush RF cues; any significant silhouette change reopens user review.
2. Verify full 2,800 mm length centered on X=0 and every folded external part inside the 125 mm radial envelope. Validate solid integrity, panel/contact relationships, mirrored features and inverse-pose equality. Record exact deployed dimensions rather than silently inheriting R5's 1.4 m span.
3. Identify the *actual* AGM1_single/AGM1 RDM-9 donor rack and its real attachment/pylon transform or geometry from installed game assets or a reproducible dump. Measure clearance and alignment of the stowed candidate against that actual source; a procedural preview pylon is insufficient. If the donor cannot be recovered, name the blocker and leave CAD approval pending.
4. Produce opposed isometrics, orthographic side/top/front/rear, hinge/fin closeups, stowed-on-actual-rack context, combat-distance and R5 comparison views; main agent inspects all final images directly and gives a candid, bounded visual verdict.
5. Record the selected source identity, user decision, hard checks, actual rack evidence, unresolved readings and boundary state in the RDM-9 context contract. User CAD visual approval is required before claiming `cad-approved`; a technically passing model or assistant score does not confer approval.
6. End at the 3D-design boundary. Existing gameplay, Unity prefabs/materials, serialized production mesh, bundle and runtime swap remain separate later work.

## Test notes

- Run new source-specific paired-state checker and strict native STEP validation on both outputs; compare exact panel shapes after inverse hinge transform, not just volumes. Use the donor rack's actual geometry/transforms for a measurable clearance report.
- Snapshot final targets and review the views directly against the user's chosen concept and attributed references. A failed clearance, topology, or visual gate remains open rather than weakening assertions or silently changing the selected concept.

## Implementation map update — 2026-09-27

**Rack evidence recovered later the same day:** `cad/phantom_visual_reboot/DONOR_RACK_FINDINGS.md` records the actual enabled `launchpylon1` mesh and transforms from installed `AGM1_single`. The unchanged-donor-placement surface test fails against the current body, top cover and port front wing, with strict interior witnesses. Source recovery is no longer the missing input; mounting-position/interface design and actual aircraft/release fit remain open. No fit approval or issue completion is implied.

Local body/wing/fin decisions have progressed through successive user reviews; the latest integrated candidate includes a35 mm-travel belly intake. Current work is ordered in `cad/phantom_visual_reboot/IMPLEMENTATION_CHECKLIST.md`. Rear exhaust/duct and flush RF layout, actual donor-rack evidence, detailed interfaces, integrated review and whole-airframe approval remain pending. Historical issue015/016 concept statuses are not evidence that these later local approvals did not occur, and those approvals do not close this issue's rack/final-acceptance requirements. No issue acceptance or frontmatter status was advanced by this planning update.
