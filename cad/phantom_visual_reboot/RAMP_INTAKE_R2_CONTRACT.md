# Ramp intake R2 — half vertical deployment travel

2026-09-27 follow-up: user requested35mm travel instead; current `RAMP_INTAKE_R3_CONTRACT.md` / `STEP/R_RampIntake_R3_*`. R2 remains28.7557mm comparison.

2026-09-27. State: `cad-review`. User requested halving the vertical distance the intake pops out.

- Source `src/ramp_intake_r2.py`; four saved `STEP/R_RampIntake_R2_{Stowed,Midfold,Deployed,Module_Deployed}.step` outputs. Original R1 preserved.
- Actual forward outer-lip drop, measured from saved edge vertices:57.511374307735 mm →28.755687153862 mm; deviation from exact half5.8e-12 mm. Angle is2.497370647093458 degrees, calculated for half vertical travel rather than simply halving5degrees.
- All part shapes, cavity, side cheeks, hinges and flush stowed position unchanged. Only moving-ramp rotation changes in intermediate/deployed states.32nonramp parts match savedR1 perstate; all33stowedparts identical; inverse-rotation/ramp-shape and module identity pass.
- Fresh savedchecker `src/check_ramp_intake_r2.py` PASS, report `reviews/ramp_intake_r2_checks.json`,0failures.33full/4module valid single solids,66crosssamples/120nonexemptpairs per sample, minclearance0.25 mm, nounexpectedoverlap. Narrower mouth test remains unobstructed:24.532 mm clear height at the R1 test plane. Stowedradius121.622367<125 andfloorZ-86 retained.
- Primary generated/directlyinspected3matchedR1-camera views: `reviews/R_Intake_R2_deployed_belly.png`, `R_Intake_R2_deployed_side.png`, `R_Intake_R2_mouth.png`. Side view confirms reduced projection; stowed rerender unnecessary because saved geometry is identical.
- No new engine/flow, structural or continuous-sweep claim. Next: user reviews reduced deployment.
