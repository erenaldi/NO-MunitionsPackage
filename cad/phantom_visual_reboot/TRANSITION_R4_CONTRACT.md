# R4 — upper shoulder corner cleanup

2026-09-23. State: `cad-review`, local upper-shoulder cleanup awaiting feedback.

## Authority and scope

User accepted the reduced R3 underside with "Perfect" and circled the two
upper shoulder-corner patches for cleanup. Treat that as acceptance of the
local underside revision, not whole-airframe or production approval. The
inline annotated screenshot was directly inspected; no persistent pixel path
is claimed. +X forward, +Z up; dimensions remain millimetres.

## Geometry change

- Source: `src/transition_nose_r4.py`; R3 remains the baseline for retained faces.
- Replaced five upper shoulder faces only. R3's automatic square-to-pentagon
  loft mapped rounded corner arcs to spans within the nose's top edge, creating
  the diagonal strips and roof pinch visible in the user screenshot.
- R4 uses one full-width planar roof and explicit arc/short-side profiles that
  taper to their corresponding left/right nose corners. Body corner rounding
  narrows toward the shoulder end rather than crossing the roof.
- Sewn solid is cleaned to remove inherited collinear edge subdivisions.
  The first four-vertex roof check exposed these subdivisions; cleaning the
  source solid fixed the check without relaxing its assertion.
- Retain the full pointed nose, square barrel and R3 underside exactly. There
  are still intentional shoulder boundaries and nose chines; this is not a
  fully curvature-continuous body-to-tip surface.

## Artifacts and verification

- Full body: `STEP/G_Transition_Nose_R4.step`.
- Close-up: `STEP/G_Transition_Nose_R4_Close.step`, presentation cut at X=550.
- `src/check_transition_r4.py` passes on serialized exports: each is one valid
  positive-volume solid; lengths 2800/850 mm and cross-envelope 172x172 mm;
  exact zero Boolean differences for square barrel, entire pointed nose and
  all geometry below Z=50; symmetric upper shoulder; close-up matches full body;
  single four-vertex roof with area 37793.462977 mm2.
- Saved evidence: `reviews/transition_r4_checks.json`.
- `review_G.json` generated seven snapshots. Primary model directly inspected
  all seven, including matched R3/R4 shoulder obliques, front, side, top, opposed
  underside and full body. Broad top is now uninterrupted by diagonal strips;
  both rounded shoulder edges taper neatly to the nose corners. Tiny linework
  marks remain at corner endpoints in the front projection; no claim of perfect
  tessellation or tangent continuity at those endpoints.
- Viewer serves this workspace at port 3245; both artifact paths exist and both
  page URLs returned HTTP 200.

Next: user reviews local corner cleanup before propagation or further detailing.
