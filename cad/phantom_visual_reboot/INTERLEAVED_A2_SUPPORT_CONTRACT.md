# A2 — elevated sliding-track support revision

2026-09-27 follow-up: user requested recessing the entire assembly with the top wing panel flush with the body roof. Current candidate is A3: `INTERLEAVED_A3_RECESS_CONTRACT.md`. All A2 nonbody geometry is retained and translated22.75 mm down; A2 remains the elevated comparison.

2026-09-26. State: `cad-review`; revised support arrangement awaits user acceptance. User feedback on A: “Good, one critique is that the elevated sliding track lacks supports.” This reopens the shelf-support gate, while retaining the positively reviewed A geometry/direction.

## Change

- Source `src/interleaved_wing_a2.py` reuses A and adds material only to its housing. Exact body, panels, hardware, layer heights, 5.5 mm offset and motion law preserved. Original A and N artifacts retained.
- Second longitudinal web X-300..250, Y-44..-42, Z88..93 supports the shelf close to the outer elevated guide (Y-41).
- Three cross-ribs at X-250/-50/150, each X±5,Y-70..-42,Z88..93, tie that web to the original outer wall and base.
- Two inner-guide posts at X190/225, each X±5,Y-20..-18,Z88..93, support the shelf's forward region directly. Positive X is forward.
- A continuous support wall directly beneath inner guide Y-19 collided with the stowed lower rear panel and missed required clearance at5% deployment. Discrete inner posts at X-250/-50/150 also failed. Hence the inner shelf edge retains a24 mm overhang from the new web in the swept region; it is not directly supported everywhere. No structural-strength claim.

## Evidence

- Bounded worker probe `checks/probe_a_track_support.py` / `reviews/a_track_support_probe.json`: direct inner wall blocked; X190/225 posts clear. Primary outer-web probe `checks/probe_a_outer_support.py` / `reviews/a_outer_support_probe.json`:21 samples pass.
- Fresh builder exported `STEP/O_Interleaved_A2_{Stowed,Module_Stowed,Midfold,Deployed}.step`.
- Primary ran `src/check_interleaved_a2.py`: PASS. Independent saved Boolean comparison finds zero change to every nonhousing component in all four outputs; zero old housing removal; all six required support volumes present. Full A-family saved checks pass:12/11 single valid positive solids, exact R2/body identity, saved-pose correspondence,21 simultaneous motion samples, no unexpected checked overlap, supports seated, minimum panel clearance0.25 mm and stowed radius124.270643 mm<125.
- Reports: `reviews/interleaved_a2_support_checks.json`, `reviews/interleaved_a2_checks.json`. Shared A checker gained default-preserving output-prefix/report parameters; A geometry/source and old reports unchanged.
- Primary directly inspected all six PNGs from `review_interleaved_a2.json`: end/module oblique, opposed deployed views and exploded-support oblique/end. Support frame is visible in the diagnostic; normal stowed oblique still hides it beneath panels.
- Diagnostic `STEP/O_Interleaved_A2_Support_Exploded.step` comes from saved housing slices: base and supports at actual positions; shelf shifted Y-100/Z+50 solely to expose support frame. Gold highlights are diagnostic, not materials. This is not a deployment state. Initial diagnostic views clipped/occluded supports; only affected views were reframed/rerendered and inspected.

## Review paths

- `reviews/O_A2_support_exploded.png` — clearest view of second web, three cross-ribs and two posts.
- `reviews/O_A2_module_end.png` — actual assembled stack and support placement.
- Source for review `src/review_interleaved_a2.py`; canonical job `review_interleaved_a2.json`.

Limits: sampled CAD clearance/support connectivity only. Strength, continuous swept volume, tolerances, retention, actuation/locks and engine/rack validation remain unverified. B is a separate blocked mechanism study. Next: user reviews A2 support correction.
