# R6 — 20 mm horizontal wedge, 4 mm rounding

2026-09-23. State: `cad-review`, local tip revision awaiting user review.

User requested increasing the leading-edge rounding to 4 mm and doubling the
previous 10 mm horizontal wedge span. The finished span is 20 mm along Y,
centered at the old point (1400,0,40), with total length 2800 mm retained.

- Source: `src/transition_nose_r6.py`, using the existing compensated wedge
  factory in `transition_nose_r5.py`, now parameterized with preserved R5 defaults.
- Artifacts: `STEP/I_Transition_Nose_R6.step`, `_Close.step`, `_Tip.step`.
  Close-up cuts remain X=550 and X=1360, respectively.
- The radius applies to the horizontal leading edge; lateral end edges and
  other nose chines are not independently filleted. The nose faces adapt to
  the larger wedge; barrel and cleaned shoulder through X=1010 are identical.
- Serialized checker `src/check_transition_r6.py` PASS: 20 mm finished line
  endpoints (1400,-10,40) and (1400,10,40), cylinder radius exactly 4.0 mm,
  cylinder axis parallel to Y at X=1396/Z=40, symmetric nose; three valid
  positive-volume single solids, lengths 2800/850/40 mm; cropped exports match
  the full body; zero Boolean difference for retained body/shoulder. Direct
  comparison also verifies unchanged R5 factory defaults against the saved R5.
- Evidence: `reviews/transition_r6_checks.json`.
- `review_I.json` generated seven snapshots. All directly inspected: tip
  iso/front/side, nose iso/front/side and full body. Larger leading-edge roll
  is clear at close distance; overall nose remains a slender wedge. Display
  tessellation is visible at extreme tip magnification; radius is analytically
  verified from the STEP cylindrical surface.
- Viewer reused port 3245; all three paths exist and artifact page URLs HTTP 200.

Next: user reviews this local radius/span choice. Whole-airframe selection,
appendage deployment, donor-rack fit and production delivery remain later gates.
