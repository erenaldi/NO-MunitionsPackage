# Tail R4 — four recessed clipped fins

2026-09-27. State: `cad-approved` for the local four-fin layout: user continued with a sketch-led intake addition after the combined review. Whole-airframe/detail/rack/engine acceptance remains open. The user previously approved the TailR3 single-corner recessed fin with “its good”; this pass propagates that geometry without redesign.

## Geometry

- Source `src/tail_fin_r4.py`; main outputs `STEP/Q_Tail_R4_Four_{Stowed,Midfold,Deployed,Body_Pocket}.step`.
- Exact TailR3 fin, two fixed mounts and pin repeated by0/90/180/270-degree rotations about globalX at upper-starboard, upper-port, lower-port and lower-starboard corners. Each stows on its adjacent body face and deploys diagonally outward into an X-tail layout.
- Each pocket is the corresponding rigidly rotated R3 shaped pocket and hinge/pin relief, subtracted from the original accepted A5 body. The remaining12 A5 components are unchanged.
- All4 folded fin faces and hinge crowns flush with their adjacent body±86 surfaces. Broad pocket depth3.3 mm; local hinge relief6.3 mm. Selected clipped planform and80 mm aft station retained.29parts/full assembly.

## Saved verification

Fresh builder performed source/build; separate fresh validation worker ran `src/check_tail_fin_r4.py`. Primary inspected source and report `reviews/tail_fin_r4_checks.json`: PASS, no failures.

- All3 full states29unique valid positive single solids; body-only1.36 A5-peer and48 saved-R3-copy comparisons pass exact Boolean identity. Body matches independent rotated cutter union; outside-cut difference0; isolated-body differences0.
- All8 embedded fixed mounts maintain positive body contact. Pin/body and movingfin/body pairs have no exemptions.
-66 synchronous fold samples cover29parts/406unique pair combinations each. No unexpected overlap; minimum moving clearance0.25 mm, separate minimum fin-to-fin gap52.0091 mm. Saved middle/deployed geometry matches rigid reconstruction of all29 stowed parts.
- Stowed conservative radius121.622367 mm<125; wholebody axial envelope and added-part containment pass with import tolerance. All4 pocket/flush depths measured in their local rotated frames.
- Existing A5 continuous pin-only proof is inherited through exact saved component/body-region preservation. Tail and cross-fin motion are sampled, not a continuous or arbitrary asynchronous-deployment proof.

## Primary visual review

Primary generated and directly inspected9views using `src/review_tail_fin_r4.py` / `review_tail_fin_r4.json`: opposed stowed/deployed full-airframe views, midfold, stowed aft focus, opposed deployed aft focus and rear-end projection. Four fin faces are visible in stow across the four body faces; deployed end view exposes the symmetric diagonal layout. Shallow pockets remain visible when fins extend, as approved.

`STEP/Q_Tail_R4_Focus_{Stowed,Deployed}.step` are explicitly cropped review diagnostics, generated from saved assemblies: body clipped toX-1400..-1020, all16tail components unchanged. They are not alternate vehicle designs.

Best images: `reviews/Q_Tail_R4_deployed_iso.png`, `reviews/Q_Tail_R4_stowed_iso.png`, `reviews/Q_Tail_R4_tail_end.png`, `reviews/Q_Tail_R4_tail_deployed.png`.

Next: user reviews the combined four-fin layout. No strength, actuator/lock, tolerance-stack, actual rack, export or engine/runtime acceptance claimed.
