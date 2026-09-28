# R7 — low-profile trapezoidal booster fin

Date: 2026-09-23. User supplied a clean trapezoid outline and selected the low-profile interpretation. Plan approved with "Go". Scope: prototype one fin before fourfold propagation.

- Root chord: existing 295 mm, from X=-1655 to -1360 mm.
- Tip chord: 220 mm, centered over the root; 37.5 mm setback at each end.
- Height: 53 mm root-to-tip, replacing the prior 86 mm.
- Root radius: existing 108 mm; tip radius 161 mm.
- Prototype station: 45 degrees, preserving the intended 45/135/225/315-degree final arrangement.
- Keep the existing tapered wedge section (8 mm root thickness, 2.8 mm tip thickness) and fin material.
- Preserve R6 intake, curved late taper, dark backs, nose, main-stage fins, booster body/nozzle and stage proportions.

The sketch conveys idealized straight edges and parallel root/tip; its pixels are not exact dimensions. The intended first result contains one new fin and three old booster fins for context. Approval of the visible shape precedes applying it to all four positions.

Sources: `src/booster_fin_r7_shapes.py` and three explicit entrypoints. Outputs: `STEP/Selected_Halberd_R7.step`, `Selected_Halberd_R7_Separated.step`, and `Selected_Booster_Fin_R7.step` (the actual fin rigidly repositioned for silhouette inspection).

Acceptance: strict CAD validity, root/tip chords and centering, thickness/height, 45-degree clocking, positive attachment to the booster body, nozzle clearance, stage ownership, exact unchanged component comparisons and equivalent separated geometry. Directly review isolated side/end, mounted oblique/profile and full context before handoff.

## Current execution state: prototype verified and selected for R8

The user subsequently authorized moving this fin +170 mm X and copying the approved complete set to the remaining three stations. See `R8_FOUR_STATION_CONTRACT.md` for the delivered four-station result; the measurements below describe the preserved R7 prototype.

Terminal execution recovered on continuation. All three models have been generated and checked, and the primary model directly inspected all eight final snapshots in `reviews/Booster_R7_Fin.png` and `reviews/Booster_R7_Context.png`.

### Measured results

- Root/tip chords: 295 / 220 mm, centered at X=-1507.5 mm; 37.5 mm setback at both ends.
- Root-to-tip height: 53 mm; tapered thickness 8 mm at root / 2.8 mm at tip; clocking 45 degrees.
- Positive booster-body contact: 3138.62 mm3. The straight root preserves the existing aft overhang over the tapered boattail, visible in the mounted closeup; full-length root-to-skin contact is not claimed.
- Clearance to booster nozzle liner: 48.879 mm; clearance to nozzle back: 75.700 mm. No collision with the other fins; the fin stays within the booster axial extent.
- All other component geometry and colors match R6 exactly. Isolated and separated variants match the same fin/assembly after reversing their review transforms.
- Strict native every-placement validation: assembled/separated each 17 occurrences / 13 prototypes, isolated fin 1 / 1. All three pass with zero failures.

Evidence: `reviews/booster_fin_R7_checks.json` and three `reviews/Selected_*R7*_facts.json` reports. These are one-fin prototype checks; the subsequent authorized fourfold propagation has its own R8 evidence.

### Review links

- [Assembled R7](http://127.0.0.1:3245/?file=STEP/Selected_Halberd_R7.step)
- [Separated R7](http://127.0.0.1:3245/?file=STEP/Selected_Halberd_R7_Separated.step)
- [Isolated fin](http://127.0.0.1:3245/?file=STEP/Selected_Booster_Fin_R7.step)
- [Fin and mounting views](reviews/Booster_R7_Fin.png)
- [Full context](reviews/Booster_R7_Context.png)

### Reproduce

Run with `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe`, in order:

```text
cad/halberd_rounded_square/src/booster_fin_r7.py
cad/halberd_rounded_square/src/booster_fin_r7_separated.py
cad/halberd_rounded_square/src/booster_fin_r7_isolated.py
cad/halberd_rounded_square/src/check_booster_fin_r7.py
cad/halberd_rounded_square/src/review_booster_fin_r7.py
```

The original terminal failure (`Unknown: ChildProcess.kill`, then a built-in command timeout) was resolved by the resumed environment; no root cause was established. On resumption the first grouped build timed out after producing both full models, so the missing isolated model was built explicitly. The initial warm validation run then stalled while collecting metadata. Daemon status showed no model jobs queued/running; a full cold checker rerun using process-local `CADGEN_DAEMON=0` completed all checks and facts, followed by a successful cold snapshot run. No assertion or validation scope was reduced.
