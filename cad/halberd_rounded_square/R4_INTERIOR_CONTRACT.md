# R4 — deeper intake channel and dark recessed interiors

Date: 2026-09-23. R3 exterior received positive user approval ("Fantastic"); this revision changes its interiors only. The one-intake prototype scope remains unchanged.

## Requested and clarified

- Add realistic dark recesses behind both nozzle openings and at the back of the intake.
- User explicitly selected **add 30% of the full intake housing length** to the existing channel, not multiply the current channel depth by 1.3.
- Measure full housing length from the exported R3 exterior added to the unchanged core. Measured bounds: X=-1123.333333 to +693.246408 mm; length 1816.579742 mm. Requested extension: **544.973923 mm**.
- Original clear channel back plane is X=100 mm. New clear back plane is **X=-444.973923 mm**, including the finished dark rear surface. The backing thickness must not shorten the requested extension.

## Implementation boundary

- Preserve the approved outer housing, rim, taper, nose, fin geometry/placement, stage seam and booster exactly.
- Extend the internal passage aft through the housing, maintaining the original curved floor and protected core. Existing voids remain voids.
- Add a recessed charcoal cup at the extended passage's rear, with a short lining and a blind back face; this is visible interior geometry, not a dark decal on the mouth.
- Add charcoal bowl-shaped liners inside the main-stage and booster nozzle recesses. Keep the external nozzle lips neutral and retain visible depth before the dark surfaces begin.
- Main-stage nozzle is inspected in the separated state. The assembled booster naturally hides it.
- Geometry/material presentation only: no engine integration, heat simulation, internal propulsion design or runtime staging changes.

## New files

`src/intake_r4_shapes.py`, explicit assembled/separated model entrypoints, an independent checker and interior-focused snapshot tooling. Outputs use `Selected_Intake_R4*.step` so the approved R3 remains recoverable.

## Acceptance

- Both strict native STEP validations and artifact checks pass.
- Added channel length equals 0.30 times the measured original housing length; clear floor position includes the back cup.
- All original non-body parts match R3 exactly; the main-body difference is removal inside the existing housing, with unchanged external section boundaries and original core.
- Intake cup and both nozzle liners are valid attached solids, recessed behind their openings, with actual open space before their blind back faces.
- Direct visual review: full context, inlet/deep-channel view, booster nozzle, main-stage nozzle and separated-stage context. New surfaces must read as deep charcoal interiors rather than flat black caps at the openings.

## Delivered result

- [Assembled R4](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R4.step)
- [Separated R4](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R4_Separated.step)
- [Actual longitudinal channel slice](http://127.0.0.1:3245/?file=STEP/Selected_Intake_R4_Cutaway.step)
- [Nozzle closeups](reviews/Intake_R4_Nozzles.png)
- [Intake/deep-channel/cutaway views](reviews/Intake_R4_Intake.png)
- [Assembled/separated context](reviews/Intake_R4_Context.png)

### Geometry and presentation

The clear channel back is now X=-444.973923 mm: exactly 544.973923 mm farther aft than R3, equal to 30% of the measured 1816.579742 mm housing. The source cuts behind that target to seat the backing; the dark cup's visible inner back face, rather than the raw cavity cut, defines the finished channel depth. Its last 80 mm has a recessed charcoal lining.

Both nozzles retain a 9 mm neutral entry before the dark liner. The main-stage and booster dark floors sit 40 mm and 70 mm behind their openings respectively. Neutral-charcoal funnels (`#505050`) and deeper charcoal back faces (`#242B30`) separate the visible wall from the dark rear; initial single-tone shading was too uniformly black, and a blue-gray trial was replaced with neutral gray. All are actual solids inside the existing recesses.

### Verified evidence

`src/check_intake_r4.py` passes:

- Exact unchanged original nose, fins, booster and retained components; unchanged main-body bounds and ten exterior section areas; unchanged forward passage beyond X=211 mm. Main-body changes only remove internal housing material, and no original core material is lost.
- Clear passage probes through the new rear endpoint, attached intake cup, attached nozzle funnels/back faces and open space before both nozzle floors.
- Read-back dark color assignments, and exact stage geometry after undoing the separated-state transform.
- All three native strict every-placement validations pass with zero failures: assembled/separated 16 occurrences / 11 prototypes each; longitudinal slice 2 / 2.

Results and facts: `reviews/intake_R4_checks.json`, three `reviews/Selected_Intake_R4*_facts.json` files and `reviews/intake_R4_manifest.json`. The primary model directly inspected all eight final snapshots through the three boards above. The frontal view shows the intake's dark back; the cutaway exposes its extended depth. The rear cup is naturally occluded in the oblique inlet view, rather than painted over the mouth to force visibility.

Reproduce using the dedicated CAD Python interpreter: `src/intake_r4.py`, `src/intake_r4_separated.py`, `src/intake_r4_cutaway.py`, then `src/check_intake_r4.py` and `src/review_intake_r4.py`. The first checker run exposed an incorrect assumed `Color.to_tuple()` call; inspected the installed API and corrected it to `tuple(color)` without changing the color assertions.

R3's single-station exterior approval remains applicable. R4 is the current interior-review candidate; fourfold assembly, engine materials and runtime delivery are separate gates.
