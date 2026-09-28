# R11 — intake endpoint aligned to the marked fin ridge

Date: 2026-09-23. State: `cad-review`; single-station revision built and checked.

The user marked the rear fin's existing near-vertical ridge and requested that
the intake end match it, explicitly **without changing the height**.

- The marked line is the fin's maximum-thickness ridge, authored at 45% of
  each section's chord from the aft edge; it is not the geometric mid-chord
  used for R10's endpoint.
- In the unclocked local frame, the ridge runs from (X=-1352.25, Z=108) at
  the root to (X=-1348.5, Z=188) at the tip. At the intake roof Z=136,
  X=-1350.9375: **13.4375 mm aft of R10's endpoint**.
- Match the terminal plane to this slight ridge lean (dX/dZ=0.046875), so the
  exposed end aligns over its height rather than only at one point.
- Keep the intake's terminal roof at radial 136 mm, maximum roof at 147.5 mm,
  and fin root/tip at 108/188 mm (80 mm fin height). No vertical translation,
  fin reshaping, or extra transition is introduced.
- Retain the original cubic taper, inlet and channel depth. The continuous
  housing is still generated first and split at the existing stage seam.
- One 45-degree prototype only; other three stations remain comparison geometry.
- R6/R10 helper arguments retain previous defaults. Stable occurrence labels
  are kept for geometry comparison and material assignments.
- Outputs: `STEP/halberd_r11.step`, `halberd_r11_separated.step`,
  `halberd_r11_focus.step`. Focus is cropped/unclocked review geometry only.
- Next gate: local user review before repeating the approved revision.

## Verified handoff

- [Focused review](http://127.0.0.1:3247/?file=STEP/halberd_r11_focus.step)
- [Full assembly](http://127.0.0.1:3247/?file=STEP/halberd_r11.step)
- [Separated stages](http://127.0.0.1:3247/?file=STEP/halberd_r11_separated.step)
- [Review board](reviews/Halberd_R11_Continuous_Intake.png)

`checks/check_halberd_r11.py` passes against saved geometry. It independently
measures the ridge from the fin vertices and verifies that all six intake end-face
vertices lie on its projected plane within 0.002 mm. The roof endpoint is
X=-1350.9375, terminal height 136, maximum intake height 147.5, fin height 80 mm.
All 22 other parts, including the entire taller fin, are Boolean-identical to R10.
Seven section samples match the continuous cubic taper and linear roof profile.
Matched stage-cut sections, separation ownership, attachment, clearance, channels,
material bindings, and all 52 saved full/focus placements pass. R10 regenerated
with default arguments remains identical to the preserved R10 artifact.

Five snapshots were directly inspected: side, oblique, top, whole and separated.
The local side view shows the fairing termination meeting the existing ridge.
Evidence: `reviews/halberd_R11_checks.json`. User approval and fourfold propagation
remain pending.
