# R10 — original intake recalculated to the rear-fin midpoint

Date: 2026-09-23. State: `cad-review`; single-station CAD revision verified.

## User correction and controlling intent

The R9 added-transition approach is rejected. Recalculate the **old intake's
length**, ending the complete intake housing at the middle of the rear fin.
Only after generating that continuous shape, cut it at the booster split so its
aft fairing/structural section drops away with the booster.

- One revised 45-degree station remains the local prototype before propagation.
- Preserve R6's inlet and exact late cubic width law, but use X=-1337.5 (rear-fin
  mid-chord) instead of X=-1123.333333 (stage seam) for its rear endpoint.
- Preserve its 8 mm terminal shoulder width, 3.2 mm roof width and 136 mm roof
  radius. The same linear roof profile is recalculated over the longer length.
- Split the one generated housing at X=-1123.333333; both mating sections are
  portions of the same surfaces, rather than independently fitted transitions.
- Retain the R9 80 mm fin-height estimate. The fin and booster-owned housing
  section are separate labeled solids with intentional attachment overlap.
- Channel clear depth, inlet, black back, core, nose, nozzles, axial fin location,
  and the other three stations remain the existing comparison baseline.
- The intake-backed main fin stays in its existing position; verify its contact
  after recalculating the housing roof.
- The full housing is lengthened by 214.166667 mm. This is an exterior housing
  edit; the internal visual channel is not automatically lengthened again.
- Source: `src/halberd_r10_shapes.py`. R6's new `end_x` parameter defaults to the
  previous stage seam, preserving historical callers.
- Outputs: `STEP/halberd_r10.step`, `halberd_r10_separated.step`, and cropped,
  unclocked `halberd_r10_focus.step` for local review only.
- Next gate: user review of the continuous intake and split before replication.

## Delivered review

- [Full R10](http://127.0.0.1:3247/?file=STEP/halberd_r10.step)
- [Separated R10](http://127.0.0.1:3247/?file=STEP/halberd_r10_separated.step)
- [Cropped local review](http://127.0.0.1:3247/?file=STEP/halberd_r10_focus.step)
- [Side / oblique / top board](reviews/Halberd_R10_Continuous_Intake.png)

`checks/check_halberd_r10.py` passes on saved artifacts. Eight independently
calculated section samples match the original cubic roof-width law and linear
roof-height law across the recalculated length, including both sides of the
stage seam. At the seam, roof radius is 137.591546 mm and roof width is
13.578851 mm; at the fin midpoint they are 136 mm and 3.2 mm. Cut faces match,
the roof slope is continuous, and main/aft solids have zero volumetric overlap.

The aft fairing is physically attached to both the booster body (167881.855 mm3
overlap) and fin (12719.945 mm3). Main-fin housing contact is 2753.818 mm3.
Clearance, open channels, all stage-owned separated transforms, 21 unchanged
separate parts, forebody and the other three housing corners pass. Regenerating
R8 with the newly parameterized R6 factory matches every saved R8 part.

All 48 full-state part placements and four cropped-focus solids pass positive
volume, topology, closure and self-intersection checks. Material sidecars are
bound to the matching document hashes with all twelve expected finish assignments.
Evidence: `reviews/halberd_R10_checks.json`. Five snapshots were directly inspected.
This is local CAD review evidence; fourfold propagation remains pending.
