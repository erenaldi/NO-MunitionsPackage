# R3 — drawing-led intake and housing-mounted fin

Date: 2026-09-23. Current gate: one intake/fin assembly, `concept-review`.

**Subsequent approval:** the user responded "Fantastic" to R3 and requested interior enhancements. R3's single-station exterior is accepted as the baseline for `R4_INTERIOR_CONTRACT.md`; the interior revision does not authorize fourfold propagation or engine delivery.

## Authority and approved intent

The user's three annotated views supersede the earlier inferred intake design and its review scores. Blue defines the intake/housing; red defines the exposed main-stage fin. These are shape references, not dimensioned engineering drawings. Their actual chat images have been directly inspected; durable local copies have not been established.

1. Front: large opening with thin walls. The lower opening follows the curved body corner; the roof is narrower than R2's broad cap. It must not read as a small hole in a thick block.
2. Side: forward sloped entry, long gently rising housing, a short aft reduction in roof height and housing continuing to the main-stage seam beneath the fin.
3. Taper view: preserve the long narrowing planform but extend both taper edges to a small termination at the main-stage seam. Do not stop at the fin leading edge.
4. User clarification: the red exposed silhouette is the target; fins sit on top of the rear intake housing. Main-stage fin roots/height may change to achieve that relationship.
5. Preserve C-identical nose, rounded-square core, 3370 mm total length, 561.666667 mm booster and booster fins. Retain the 45-degree intake/fin alignment.

## Local modeling contract

- Coordinates: millimeters, +X forward, +Z dorsal. Local radial axis at 45 degrees from +Z toward +Y; local tangent perpendicular to it.
- Main-stage rear datum: X=-3370/3 mm. Housing ends exactly at this datum and does not cross onto the booster.
- Main body: use the existing 200 mm rounded-square core and forward transition unchanged.
- Inlet: a trapezoidal outer roof/flank boundary with an opening whose lower edge is concentric with the rounded body corner. Initial nominal rim thickness is approximately 3 mm; exact drawing dimensions are inferred and remain editable.
- Housing: broad near the inlet, narrowing monotonically toward an 8 mm-wide terminal section at the stage seam. Initial roof rises from radial 145 mm to 153 mm near the aft fin station, then reduces to 136 mm at the seam.
- Fin: one cropped, swept main-stage fin whose root is seated in the housing rather than the core. Tip height/leading sweep/trailing edge are study parameters chosen to reproduce the red contour. The other three main fins remain historical context for this one-feature prototype; they are not an approved mixed final layout.
- Open inlet is the acceptance state. R2's optional cover is not carried into this drawing-led packet.

## Sources and outputs

New source: `src/intake_r3_shapes.py` and explicit `src/intake_r3.py`, `src/intake_r3_separated.py` entrypoints. Outputs: `STEP/Selected_Intake_R3.step` and `STEP/Selected_Intake_R3_Separated.step`. Historical A/B/C/R1/R2 files and their checks remain intact.

## Acceptance evidence

- Native strict STEP validation and independent positive-solid checks for both states.
- Exact unchanged nose/core/booster comparisons; correct stage length and seam; housing material still present immediately ahead of the seam and absent aft of it.
- Large aperture cross-section relative to the available housing envelope; actual body-following floor; intact roof/flanks and protected core.
- Main fin contacts the housing while having no overlap with the original core. Its exposed profile is checked against the new red-contour parameterization, not against preservation of the old A fin solid.
- Front, side, intake-plane taper view, opposed context, mouth/fin-root closeups and separated view. Include an isolated local section to make the curved-floor opening assessable.
- Main agent directly inspects all views against the drawings. No inherited 9/10 score or fourfold approval. The next user gate approves or revises this one assembly before repetition.

The old R2 fin-exposure threshold and exact A main-fin preservation remain valid historical tests for R2. They do not describe this newly authorized housing-mounted fin and will not be used to force the new housing back into the rejected layout.

## Delivered R3 prototype

- [Assembled CAD](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R3.step)
- [Separated CAD](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R3_Separated.step)
- [Actual transverse section](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R3_Section.step)
- [Drawing-oriented views](reviews/Intake_R3_Drawing_Views.png)
- [Mouth and fin-seat details](reviews/Intake_R3_Details.png)
- [Opposed/context/stage views](reviews/Intake_R3_Context.png)

### What was verified

`src/check_intake_r3.py` passes against the exported artifacts:

| Requirement | Evidence |
|---|---|
| Thin, large corner-following aperture | At X=560 mm, actual opening area 1369.00 mm2 / available above-core envelope 1941.70 mm2 = 70.505%. Curved-floor material/void probes pass at three tangent positions. Nominal roof/floor thickness 3 mm; sidewalls are checked independently. |
| Full-length taper | 35 exported section samples narrow monotonically aft; actual terminal width 7.928 mm at seam +0.1 mm. Added housing reaches X=-1123.333333 mm; all main-stage solids remain ahead of that plane. |
| Fin on rear housing | Housing contact 5975.22 mm3; original-core contact 0 mm3. Fin root minimum radius 135.526 mm, tip radius 212 mm, clock 45 degrees. Visible contour is the new proposed interpretation of the red outline. |
| Preserved airframe | Original main-body core lost 0 mm3; forward transition unchanged. Ogive, booster and booster fins pass exact Boolean comparisons. |
| Stage proportions and ownership | 3370 mm overall; booster 561.666667 mm. Separated bodies are geometrically identical after reversing the 340 mm review offset. |
| Native CAD integrity | Assembled/separated each 11 occurrences / 6 prototypes; transverse section 1 / 1. All three strict every-placement validations report zero failures. |

Evidence files: `reviews/intake_R3_checks.json`, three `reviews/Selected_Intake_R3*_facts.json` files and `reviews/intake_R3_manifest.json`. Rerun using the project's dedicated CAD Python interpreter: three `src/intake_r3*.py` entrypoints, then `src/check_intake_r3.py`, then `src/review_intake_r3.py`. `--manifest-only` refreshes the hash handoff without rerendering.

### Visual readback

The primary model directly inspected all ten final snapshots through the three boards above. The front/section show the large curved-bottom opening and narrow rim; profile shows the fin emerging from the rear housing; the intake-plane taper view carries the narrowing edges through to the seam. The initial ruled housing showed conspicuous segment boundaries, so it was replaced with a smooth loft. A flank probe then caught insufficient material at an intermediate station; widening that station's roof half-width by 1 mm restored the required wall without changing or weakening the check. The full final suite and fresh snapshots were rerun.

Front, profile and taper are true orthographic camera views; profile and taper look along the local tangent and radial axes respectively. The section is a physical 16 mm slice derived from the actual model, included because the nose partly occludes the curved floor in a full front view. Closeups use perspective cameras for interface readability.

### Approval boundary

R3 is ready for comparison with the drawings, not automatically accepted. No numerical score is inherited from R2. The exact rim thickness, roof heights and fin dimensions remain proposed interpretations of undimensioned annotations. Only one new intake and one housing-mounted fin are present; the other three main-stage fins are unchanged context. User approval is required before fourfold propagation, after which the complete silhouette must be reviewed again.
