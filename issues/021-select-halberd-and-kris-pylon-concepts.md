---
id: "021"
title: Select Halberd and Kris external pylon concepts in measured context
type: feature
status: todo
blocked-by: []
---

## Slice

Deliver two user-selection packets, one for Halberd and one for Kris, using the
fresh external-station and donor-rack evidence from issue 020. Each packet shows
three genuinely different pylon architectures around the fixed munition and ends
with a recorded concept selection or named hybrid. This is concept work only;
production rack geometry, Unity integration and runtime registration remain in
later weapon slices.

## Ownership and evidence

- Create compact pylon context/contracts under weapon-specific CAD workspaces;
  do not alter the approved munition geometry.
- Use actual measured donor poses and representative hardpoint contexts. Aircraft
  geometry may appear as review context but is not copied into the shipped rack.
- The primary model directly inspects every final board. User selection is
  required before either production issue starts.

## Acceptance

1. Halberd concepts preserve the fixed 3370 mm missile, selected rounded-square
   exterior, dorsal corridor, actual shoe/rail evidence, intake clearance, stage
   joint and booster-separation path.
2. Kris concepts preserve the fixed 3158.8 mm missile, 45-degree mounted roll and
   established 9 mm local pylon-to-strake clearance while showing all strakes and
   grid-fin context.
3. Each weapon compares: a vanilla-adjacent tapered rail, an exposed
   ejector/mechanism beam, and a semi-conformal cradle/recessed adapter. Differences
   are architectural, not just color, fasteners or a small parameter change.
4. Each concept identifies aircraft-side spine, weapon-side load path, fore/aft
   suspension or ejector stations, deliberate negative spaces, intended material
   regions and release direction.
5. Review packets include opposed isometrics, side/top/front/rear views, mounted
   context, critical dimensions, and representative-distance views. Tradeoffs and
   speculative details are labeled.
6. The user selects, rejects or hybridizes one direction per weapon. The dated
   decision and exact packet identity are recorded in the asset context and
   `MUNITIONS.md` without implying CAD, export or runtime approval.

## Test notes

- Validate concept solids and fixed missile identity from saved artifacts; concept
  checks need not claim production wall thickness or structural load capacity.
- Measure every shown local missile/pylon gap used as an acceptance claim.
- Direct visual review is mandatory and cannot be replaced by text-only findings.

## Review notes (2026-09-30)

- **Halberd attachment:** the current R17-R19 model has no lugs (`cad/halberd_rounded_square/R18_REAL_MISSILE_DETAIL_SURVEY.md`); older -75/+410 mm and 0/480 mm values are constants of earlier models, not game measurements. Do not cite lug stations as measured; take attachment stations from the pylon design and settle the carriage face (+Z conflicts with F02/F10) with the user. See `docs/PYLON_CONCEPT_BRIEFS.md`.
- **Halberd length:** record both 3370 mm (plan, `plans/2026-09-22-halberd-rounded-square-reboot.md`) and 3367 mm / 3.367 m (CAD/Unity, `docs/GEOMETRY_PIPELINE.md`) in the packet.
