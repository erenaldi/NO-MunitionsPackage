---
id: "012"
title: Deliver three contrastive rounded-square Halberd CAD studies
type: feature
status: done
blocked-by: ["011"]
---

## Slice

Extend the checked first study into a three-direction visual comparison with two additional coherent intake/fin treatments, each built, validated and shown assembled and separated. Deliver one matched review packet for user selection. Authority: `plans/2026-09-22-halberd-rounded-square-reboot.md` and `docs/ASSET_DESIGN_WORKFLOW.md`.

## Ownership and evidence

- Extend only the new `cad/halberd_rounded_square/` workspace, this issue, brief and journal.
- Load applicable CAD skills; preserve the first slice's source and inspection conventions.
- Main agent owns design continuity and directly reviews all images. Do not delegate design or image review without explicit scoped approval.
- Read the actual three supplied references; do not substitute historical concepts as visual authority.

## Acceptance

1. Three visibly distinct but coherent interpretations share the 3370 mm baseline, approximately 200 mm broadly rounded-square main/booster sections, circular-ogive transition, flush L/6 booster, four shallow elongated intake forms and two compact four-fin sets.
2. Differences arise from intake integration, fin shape/placement and their visual relationships, not merely color, arbitrary protrusions or tiny numerical changes. Explain each study's emphasis and tradeoff.
3. All six assembled/separated STEP outputs validate; both states derive from the same geometry for each study.
4. Every study has opposed isometrics, side/top/front/rear, separated state and critical close views. Comparison boards use identical camera orientation, scale and neutral shading.
5. Direct primary-model review rejects unreadable intakes, square-to-round transition defects, missing stage features and variants that are not meaningfully distinguishable.
6. Provide explicit source paths, measurement/validation results, review PNGs and live CAD Viewer links. Record state as `concept-review`, with no selected production master.
7. Ask the user to select, reject or hybridize the three directions. Detailed CAD and later feasibility/integration gates require their own approval.

## Test notes

- Run the independent brief checks for every study, including stage ratio, section dimensions, join, feature ownership and separated-state equivalence.
- Strict cadgen validation on every emitted STEP; targeted inspection for intakes, transitions and stage clearance.
- Fresh matched snapshots and direct image review are mandatory even if geometric checks pass.
- Record deficiencies honestly and revise their source; do not relax acceptance to pass a visually wrong study.

## Result — 2026-09-22

Delivered A/Trace, B/Chine and C/Shoulder plus matching separated states under `cad/halberd_rounded_square/STEP/`. `check_studies.py` passes all three; `validate_exports.py` passes all six with zero failures and captures refs/facts/planes/positioning. `review_packet.py` generated 27 final views and five matched boards, all directly inspected by the primary model. Nose-transition and intake-mouth details use enlarged CAD linework views; orthographic comparison scale is explicitly normalized across candidates.

`cad/halberd_rounded_square/REVIEW.md` provides all six live viewer links (HTTP 200), file paths, measurements, tradeoffs and reproducible commands. Current state is `concept-review`, with the user's selection requested at handoff. No final asset or downstream integration approval is implied by closing this study-delivery issue.
