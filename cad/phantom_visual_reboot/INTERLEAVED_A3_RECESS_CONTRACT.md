# A3 — wing assembly recessed flush with body roof

2026-09-27 follow-up: user requested filling unused opposite-side exit channels. Current candidate A4 retains only each side's two used layer exits; see `INTERLEAVED_A4_SIDE_SLOTS_CONTRACT.md`. A3 remains the four-slots-per-side comparison.

2026-09-27. State: `cad-review`; user acceptance of the recessed candidate pending.

## User direction / authority

User requested sinking the entire fin assembly into the body and explicitly selected **uppermost wing panel flush**, rather than hinge caps flush. This authorizes the local body pocket and deployment openings, superseding the exact-unchanged-body lock only within that recess. The original J/R7 and N/A/A2 outputs remain preserved.

- All11 nonbody A2 parts move downward22.75 mm, with no changes to their shapes, relative heights, supports, pins, or motion law.
- Upper port/front panel top Z86.0 matches the remaining body roof Z86.0. Highest hinge caps Z86.75, intentionally0.75 mm proud.
- Housing bottom Z63.25 seats on the new pocket floor. Inter-set offset remains5.5 mm.
- New source `src/interleaved_wing_a3.py`; saved `STEP/O_Interleaved_A3_{Stowed,Module_Stowed,Midfold,Deployed,Body_Pocket}.step`.

## Body cuts

- Central open well: X-450.3..550.3, Y-74.3..74.3, from floorZ63.25 through roof.
- Four deployment exit slots: X-430..530, cuttersY-100..100, Z65.7..70.3 /71.2..75.8 /76.2..80.8 /81.7..86.3. Each gives0.3 mm vertical allowance around its panel layer.
- These are conservative rectangular openings, not an optimized continuous-sweep cavity. They leave visible horizontal slits along both upper body sides. No added covers, seals or shutters.
- Body outside the cutter union, including the nose and remaining silhouette, is exactly preserved. The resulting body remains one valid positive solid.

## Verification

Fresh bounded feasibility, build, and saved-validation workers ran as separate gates. Primary inspected probe/code/report before build and reviewed saved checker/code/report before visual acceptance.

- `checks/probe_flush_recess_a3.py` PASS:21 sampled poses fit the specified well/slots without widening; panel-to-body clearance0.3 mm; floor/root/carriage support contacts intact.
- `src/check_interleaved_a3.py` PASS on all five saved STEP outputs (`reviews/interleaved_a3_checks.json`, `passed:true`, no failures).
- Saved nonbody parts exactly equal corresponding A2 saved parts translated22.75 mm down: zero Boolean difference in every saved pose. Saved mid/deployed states also exactly match rigid transformations of saved A3 stowed geometry.
- Saved body equals independently reconstructed A2-minus-specified-cutters, with zero Boolean difference and zero outside-cut change. Standalone pocket body matches full assembly body.
-12 valid single solids/full state,11/module,1/body-only. Floor/body contact gap0, overlap0. Both fixed roots and carriages remain seated.
-21 all-pair simultaneous deployment samples: minimum panel clearance0.25 mm, unexpected overlap0. Only housing/fixed-root intentional attachments exempt; body/hardware intersections are not exempted.
- Complete stowed conservative radial bound121.622367 mm<125. Highest panel Z86.0 and hardware Z86.75 measured from saved geometry.

## Direct visual review

Primary inspected all nine views from `review_interleaved_a3.json`: opposed stowed isometrics, top, side, end, body-pocket isometric, intermediate and opposed deployed isometrics. Full side initially clipped the extreme ends; camera widened and that view alone rerendered and inspected.

The stowed assembly is visibly sunk into the roof; end view hides the wing stack behind the body outline except the slight cap protrusion. Obliques expose the pocket perimeter and layered side exits. Deployed joined openings and panels are unchanged, now emerging through the body slots. This remains an open trough when deployed. Supports are retained inside the recess rather than omitted.

Best views: `reviews/O_A3_stowed_iso.png`, `reviews/O_A3_stowed_side.png`, `reviews/O_A3_stowed_end.png`, `reviews/O_A3_deployed_iso.png`. Review source `src/render_interleaved_a3.py`.

Limits: sampled CAD fit/motion only, no continuous sweep, structural strength, tolerances, environmental sealing, actuation/locks, donor-rack or engine/runtime validation. Next: user reviews the recessed appearance and visible exit slots.
