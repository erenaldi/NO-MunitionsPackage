# Palisade cap — ACM port reference and one-group prototype

Date: 2026-09-27. State: `cad-review` for **one** lateral attitude-control
motor group. The approved uniform 109.12 mm Spear barrel/cap, 130 mm cap
length, four cardinal ACM groups and SketchLow fins remain the parent form.
The previously modeled stepped collar is a historical local preview; its
repetition was not approved.

## Evidence-to-feature ledger

- [JASDF PAC-3 dummy-model side thruster photograph, Hamamatsu Air Base,
  2019](https://commons.wikimedia.org/wiki/File:JASDF_MIM-104_Patriot_PAC-3_Missile(dummy_model)_side_thruster_at_Hamamatsu_Air_Base_October_20,_2019.jpg)
  (photographer Hunini; Wikimedia Commons, CC BY-SA 4.0). The primary model
  directly inspected the actual image, not only its filename. It shows a
  dense field of small dark near-circular side openings inset into a light
  cylindrical missile skin, each with a dark inner disk and narrow surrounding
  border. Their coverage wraps around the cylinder and spans several axial
  rows. The image depicts a *dummy display model*: it establishes visible
  styling cues, not unseen nozzle internals or dimensions.
- [PAC-3 description](https://en.wikipedia.org/wiki/MIM-104_Patriot#MIM-104F_(PAC-3_CRI))
  identifies many small forebody pulse motors as attitude-control motors;
  that function differs from Palisade's four detachable-cap turning motors.
  [EUROSAM's ASTER page](https://eurosam.com/aster-missiles-family/)
  independently describes direct-thrust maneuver control (PIF-PAF), but its
  available launch photo does not expose close nozzle hardware; it is a
  functional analogue only.

## Local design translation

Reject the former raised black cylinder/large stepped collar as the motor
look. Keep Palisade's four cardinal transverse *groups*, but prototype the
first group (0° / +Y) as **six small inset circular ports** in two tangential
rows of three axial stations around the cap's X≈−535 center. Each port has
an actual shallow blind bore in the 54.56 mm-radius cap, a dark recessed
annular liner and a slightly deeper dark central face. The panel belongs to
the cap; the whole cap remains detachable, with the original main nozzle
revealed after separation. These six openings are one speculative grouped
motor's visual ports, not an assertion that the real PAC-3 has six ports per
motor or that Palisade now has 24 independent motors.

Use the approved `Spear_UniformBarrel.step` body/nose/fin/stage positions
unchanged. Leave the remaining 90°/180°/270° groups as basic context until
the user approves this one-group vocabulary. Produce matched side, mouth,
grazing and separated views that show whether the dark disks read as recessed
at game scale rather than studs, texture dots or solid plugs. Validate
individual annular parts, cavity blindness and cap/fin/main-motor clearance
on exported STEP. No external photograph is copied into this repository.

## One-group CAD evidence — user review pending

- New source: `src/spear_acm_port_shapes.py`; three thin entrypoints write
  `STEP/Spear_ACMPortGroup0.step`, `_Separated.step` and `_Cap_Focus.step`.
  The new cap has **six actual blind ports**, three axial centers at
  X=−549/−535/−521 mm and two radial directions at −8°/+8° about the
  0°/+Y side. Each has a 5.3 mm-radius skin bore, a separately labeled dark
  annular liner and a slightly deeper dark central disk. Rim maxima stay
  within radius52.774 mm, below the 54.56 mm cap skin. This prototype owns
  only one ACM group; three original large thrusters remain as comparison
  context. The entire selected missile body, nose, fins and motor nozzle are
  copied from the uniform-barrel source without change.
- An initial grazing capture exposed a semicircular hole at the new cap's
  forward face. This was **real**: a saved 0.2 mm forward cap slice measured
  1853.951 mm³ instead of the full cylinder's 1870.375 mm³. Root cause was
  `src/spear_cylinder_cap_shapes.py::cylindrical_cap` silently cutting its
  historical X=−470 socket even when used for the shortened X=−470 seam.
  Added an explicit `socket_x=None` for the later 130 mm caps and cut only
  the moved X=−535 socket where needed. Rebuilt both the short-cap and the
  user-selected uniform-body historical outputs, then rebuilt the ACM study.
  Default behavior for the older 180 mm cap variants remains unchanged.
- Final `src/check_acm_port_group0.py` PASS from all three saved STEP files:
  22 labeled positive-valid solids in each full state / 16 in cap focus,
  six distinct recessed blind bores with dark insert faces, 66 noninterfering
  insert pairs, preserved main missile and three basic motor groups,
  cap/body/nozzle clearance, attached stage shapes and identical focused/
  inverse-separated components. Cap and all twelve insert solids pass
  topology/closed-shell checks; cap self-intersection check passes. The
  section at X=−470.5 now measures **1870.375 mm³**, matching the full
  54.56 mm-radius cylinder (no cut at the stage seam). The assembled
  radial envelope remains 79.006 mm. Evidence:
  `reviews/spear_acm_port_group0_checks.json`.
- Rechecked `src/check_short_cap.py` and `src/check_uniform_barrel.py` after
  the socket correction: both PASS. Refreshed all nine uniform-barrel
  snapshots and its historical comparison board because the saved cap face
  changed. `src/render_spear_revisions.py` was **not** used to approve this
  gate: new snapshots `reviews/Spear_ACMPortGroup0_*.png` and the directly
  inspected matched board `reviews/Spear_ACMPortGroup0_Comparison.png` are
  the current evidence. From close and whole views, the first group now
  reads as small flush dark openings, not a raised button. The primary model
  inspected direct cap side/mouth/grazing and final board; the former
  forward-rim notch is absent. Source compilation and `cadgen store why`
  passed; all three artifact links on the workspace Viewer (port 3246)
  returned HTTP 200.

**Gate:** user accepts or revises the one-group six-port styling before
copying it around the other three cardinal stations. Neither the photo nor
these CAD checks prove PAC-3 dimensions, real internal nozzle physics,
Palisade pod fit, engine export or packaged runtime state.

**User response (2026-09-27):** "I have an idea that I want to show you."
This is neither approval nor rejection of the one-group prototype. Await
the user's actual idea/reference, inspect it directly, and revise the local
group contract as necessary before any fourfold propagation. No attachment
or description for that new idea has arrived yet.

## Full-circumference pattern — user-directed supersession (2026-09-27)

The user supplied an annotated cap screenshot with circles around the side
and said: "lets use the actual ACM pattern around the entire cap like this
rather than have it be in 4 clusters, and just use my drawing as a idea, you
don't need to copy the spacing or sizing". Primary model directly inspected
the inline drawing; it shows distributed openings over the cap's side, not
the one-local-module arrangement. This decision **supersedes the four-cluster
visual organization and the prior one-group approval gate**. Preserve the
approved uniform missile body, 130 mm cap, 22 mm aft fillet, chosen fins,
separable stage and main-nozzle exposure; this is a change of cap surface
detail, not flight-control software. The user did not provide dimensional
constraints for holes or authorize copying the PAC-3's exact number of pulse
motors.

Study layout, to be tested in actual CAD rather than treated as user dims:
six axial rows at X=−568, −550, −532, −514, −496, −478 mm and 16 ports
around every row (22.5° azimuth pitch, alternate rows clocked 11.25°).
This yields **96 small recessed openings** around the straight cylindrical
skin. Within the existing 130 mm cap, a 5.3 mm-radius aperture leaves at
least 2.7 mm axial wall at the X=−470 seam and avoids the X<−578 aft fillet.
Blind depth is 7 mm in radius; dark annular liner and central disk sit at
least 2 mm below the 54.56 mm outside radius. The hole count, pitches and
size are reversible visual-study choices, not engineering performance claims.

Remove all four raised basic/collared nozzle housings and the single
one-group six-port patch rather than adding the new pattern on top. Keep
the cap a *single valid detachable solid*, with each installed liner/core
owned by that cap so they move on separation. Save assembled, translated
separated and cap-only STEP states under fresh names. Check all port centers,
blind floors, neighbor spacing, cap/body contact and the main-nozzle after
release from exported geometry, then directly review cardinal/opposed views,
the aft face and a close port view. The prior one-group sources and exports
stay intact for comparison. A new whole-cap user visual gate follows build.

## Full ACM wrap — checked CAD packet, user review pending

- Source `src/spear_acm_wrap_shapes.py` and three thin decorated entrypoints
  produced `STEP/Spear_ACMWrap.step`, `_Separated.step` and `_Cap_Focus.step`.
  The 96 holes and two dark inset components per hole are real, labeled
  saved geometry rather than texture dots. The cap is one closed detachable
  solid: 199 full-state occurrences (body, main nozzle, four fins, cap,
  192 liners/disks), 193 cap-only occurrences, nine shared prototypes.
- `src/check_acm_wrap.py` PASS on all three saved outputs. It measured every
  port center in six axial rows × 16 around, verified all 96 skin points are
  open but blind-floor points still solid and dark centers sit under the
  surface, measured minimum inset-center spacing **19.532 mm**, and confirmed
  96 port openings stay in the cap's straight segment. The cap's front
  X≈−470.5 section is **1870.375 mm³**, exactly the full cap circle (no stale
  X=−470 socket). It checked valid 199/199/193 positive single-solids,
  cap topology/closed shell/self-intersection, representative insert topology,
  protected body/nose/fins/main nozzle Boolean exactness, and identical
  components after undoing the cap's review translation. The complete
  assembly's maximum radial reach remains **79.006 mm**. Report:
  `reviews/spear_acm_wrap_checks.json`.
- The first checker pass expected an axis-aligned slice radius of exactly
  54.56 mm even at perforated cardinal points and failed at X=−535
  (54.388 mm bound). That bbox criterion was inapplicable where the actual
  circumference has a hole. Corrected the check to require exact 54.56 mm
  at unperforated X sections, intact perforated-row skin within 0.5 mm,
  and **every** expected hole/open/blind point. No requested coverage was
  skipped to obtain a pass.
- Generated cap views at +Y/−Y/+Z/−Z, aft and grazing; whole opposed and
  side views, and assembled/separated snapshots. The primary model directly
  inspected each cardinal cap side, aft-grazing, and the matched board
  `reviews/Spear_ACMWrap_Comparison.png`. The result reads as a distributed
  dark recessed port field around the entire straight cap, unlike four
  raised nozzle buttons. The rear edge and exposed main nozzle remain.
- `python -m compileall -q src` passed, `cadgen store why src/spear_acm_wrap.py`
  reports current, and three artifact URLs served HTTP 200 in Viewer 0.6.6
  at port 3246. The previous uniform-barrel reference was also freshly
  checked and rerendered after correcting its stale seam socket; its
  user-approved outer silhouette remains the parent form.

The user's instruction authorizes *trying* the full pattern; the actual
six-by-sixteen look has not yet received user visual approval. The design
does not imply ninety-six independent gameplay motors, a revised flight
controller or tested launcher packaging. Production mesh grouping, Unity
materials and packaged runtime evidence remain downstream.

**User visual decision (2026-09-27):** after directly reviewing
`reviews/Spear_ACMWrap_Comparison.png`, the user selected "Approve cap
pattern." This approves the full-circumference visual port treatment on the
current 109.12 mm uniform Spear and 130 mm cap, not pod clearance, physical
ACM performance, an engine mesh or runtime integration. The old one-group
and raised-tube layouts remain historical. Proceed to actual pod/donor-fit
feasibility; a fit-driven external shape change reopens the affected gate.
