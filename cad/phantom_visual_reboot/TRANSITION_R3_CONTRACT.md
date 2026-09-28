# R3 — reduce nose underside bulge

2026-09-23. State: `cad-review`, local underside accepted; upper shoulder revision pending.
User subsequently said "Perfect" and marked two upper shoulder corners for cleanup.
That accepts the underside reduction locally; R4 owns the subsequent corner change.
User: "Very good so far" on R2, followed by a request to smooth the nose bottom
because front and side look bulgy. This supports a local refinement, not approval
for three-direction propagation or production delivery.

- Source: `src/transition_nose_r3.py`; artifacts `STEP/F_Transition_Nose_R3.step`
  and `STEP/F_Transition_Nose_R3_Close.step`. R2 files remain comparison evidence.
- Raised root keel from Z=-83 to -50 and side corners from -57 to -36 mm.
  Lower V depth is now 14 mm instead of 26 mm. Shoulder length remains 250 mm.
- Square barrel, 2800 mm length, upper roof heights and apex (1400,0,40)
  retained. Connected sloping side faces necessarily change with raised corners.
- This smooths the silhouette by reducing belly volume; the central chine and
  deliberate faceting remain. It is not a tangent-continuous curved underside.
- Serialized checker `src/check_transition_r3.py` passes: both valid single
  solids, expected dimensions, identical barrel, roof heights and apex retained,
  underside lifted at five stations. First checker incorrectly assumed all
  geometry above Z=0 would stay identical; the connected side faces change.
  Replaced that unsupported invariant with section roof-height checks and
  explicitly records the side-face change; no upper-half preservation claim.
- cadgen 0.6.6 removed `step inspect`; both attempted strict CLI checks therefore
  did not run. Validation here is exported build123d solid validity and direct
  Boolean/section comparisons, not the removed native command.
- Snapshot job initially rejected obsolete render keys; corrected `review_F.json`
  to current default CAD presentation. All seven snapshots generated. Directly
  inspected front, side, bottom, underside oblique, full body and R2 front/side.
  Visually the lower V is shallower and the near-flat belly then steep nose rise
  becomes a gentler two-segment rise. Subtle shoulder surface seams remain visible.
- Viewer reused port 3245; both artifact pages HTTP 200 and file paths exist.
- Next: user reviews front/side reduction before further local edits or propagation.
