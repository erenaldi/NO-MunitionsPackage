# R6 — curved planform with late aggressive narrowing

Date: 2026-09-23. User refined the plan-view requirement: rear taper should be curved, and should only slim aggressively toward its end. This supersedes R5's linear **planform**, not the straight inlet edges, linear side-height profile or black rear faces.

## Controlled shape

- Hold the housing broad through most of its rear run, then converge faster near the stage seam.
- Use one exact cubic ease-in: `progress = u^3`, where `u=0` at X=210 mm and `u=1` at the main-stage seam. Apply it to the shoulder and crest half-widths.
- At halfway, only 12.5% of the total width reduction has occurred. The final quarter contains 57.8125% of that reduction. These define an intentional late taper, not traced drawing wobble.
- Build the rear shell from explicit cubic Bezier surface control nets rather than a multi-station interpolating loft. X and roof height remain linear; width has a single monotonic curve and no inflections.
- Keep the forward inlet geometry and R5 side-height profile unchanged. Preserve the seam endpoint, fin shapes/placement, deeper channel and all recess materials.

## Gate and evidence

One intake station remains the scope. Validate the exported cubic widths at multiple stations, monotonic/increasing narrowing rate, unchanged side-height profile and straight front edges. Check the closed passage, fin seating, core preservation, exact unchanged component shapes/colors and separated state. Directly compare R5/R6 top-down views at matched cameras/scale before handoff. No score is inherited from earlier revisions.

## Delivered R6

- [Assembled CAD](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R6.step)
- [Separated CAD](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R6_Separated.step)
- [Matched R5/R6 top-down comparison](reviews/Intake_R6_Comparison.png)
- [Geometry views](reviews/Intake_R6_Geometry.png)
- [Front/rear/opposed/separated coverage](reviews/Intake_R6_Coverage.png)

`src/check_intake_r6.py` passes on both exports:

- Nineteen rear cross-sections match `u^3` width progression within 0.002 mm. Narrowing is monotonic, with strictly increasing reduction per equal axial interval. Measured first-half reduction is 12.5% of the total; the last quarter contains 57.8125%.
- Roof height retains the R5 linear side profile, and the whole forward inlet beyond X=211 mm matches R5 by Boolean comparison. Both forward design edges remain straight within 0.002 mm.
- All non-housing parts and their colors match R5 exactly, including fins, nozzle geometry, side materials and the three black rear caps. The protected core, stage length/seam and clear channel back at X=-444.973923 mm are preserved.
- The duct remains enclosed at seven tested sections; fin/housing contact is 1561.80 mm3. Separated geometry matches after reversing the display offset.
- Both strict native every-placement validations pass with zero failures: 17 occurrences / 12 prototypes each.

Reports: `reviews/intake_R6_checks.json`, two `reviews/Selected_Intake_R6*_facts.json` files and `reviews/intake_R6_manifest.json`. Source: `src/intake_r6_shapes.py`; explicit entrypoints: `src/intake_r6.py` and `src/intake_r6_separated.py`.

The primary model directly inspected all final images. The comparison uses the same orthographic camera, image size, crop and scaling for both candidates. It shows the longer broad region and the faster curved convergence near the seam. The front/side views confirm that this is a planform change, not a new wavy inlet or side-height change.

The first snapshot invocation emitted a warm-worker crash diagnostic while still writing all outputs. A full cold rerun with process-local `CADGEN_DAEMON=0` completed without that diagnostic; the final boards were read again. No geometry check was bypassed or weakened.

Reproduce with the dedicated CAD Python interpreter: run the two model entrypoints, `src/check_intake_r6.py`, then `src/review_intake_r6.py`. The current gate is user review of this single-station taper; no fourfold or engine/runtime approval is implied.
