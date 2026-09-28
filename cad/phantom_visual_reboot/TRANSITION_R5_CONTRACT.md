# R5 — 10 mm horizontal wedge with 1 mm tip radius

2026-09-23. State: `cad-review`, local tip revision awaiting feedback.

## User direction and interpretation

User requested a slightly rounded tip (1 mm radius), ending in a 10 mm horizontal
wedge at the old point's centering coordinates. Horizontal means lateral Y;
the finished foremost line spans (1400,-5,40) to (1400,5,40), midpoint exactly
at the previous apex (1400,0,40). The 1 mm radius rounds the leading edge in
longitudinal section, not every chine or the wedge's lateral end edges.

## Implementation

- Source: `src/transition_nose_r5.py`; retains R4 geometry through X=1010.
- Rebuilds nose from its retained five-vertex root to a compensated sharp wedge,
  then applies a real 1 mm edge fillet. Compensation keeps finished X=1400/Z=40
  rather than letting a fillet retreat from the required tip coordinates.
- First diagnostic export with 10 mm sharp construction stock produced an
  11.4695 mm finished foremost line because the fillet meets diverging side
  faces. Corrected side-plane construction through the required finished
  endpoints; final measured width is 10.000000000000188 mm.
- Root section/shoulder and body retained exactly. Nose faces adjust to reach
  the new finite-width wedge; the old ventral centerline opens into a narrow
  triangular face toward the tip. This is part of the wedge revision.

## Files and verification

- `STEP/H_Transition_Nose_R5.step`: full 2800 mm body.
- `STEP/H_Transition_Nose_R5_Close.step`: nose/shoulder view cut at X=550.
- `STEP/H_Transition_Nose_R5_Tip.step`: last 40 mm, cut at X=1360 for review.
- `src/check_transition_r5.py` PASS on serialized exports: each a valid,
  positive-volume single solid; 2800/850/40 mm lengths; max X=1400;
  full/close/tip equivalence; zero Boolean difference for body and cleaned
  shoulder; lateral nose symmetry; measured horizontal front line endpoints;
  exact radius 1.0 from the exported cylindrical surface, axis parallel to Y,
  cylinder axis X=1399/Z=40.
- Evidence: `reviews/transition_r5_checks.json`.
- Nine snapshots from `review_H.json` directly inspected: tip front/side/top/iso,
  nose front/side/opposed/iso and full body. Radius is visible at magnification,
  small in overall silhouette. Upper shoulder cleanup remains readable.
- Viewer reused port 3245; all three file paths exist and page URLs HTTP 200.

Next: user reviews the local rounded wedge. No whole-airframe selection,
appendage propagation or production acceptance is implied.
