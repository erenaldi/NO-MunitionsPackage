# A5 — calculated pin exits, lowered assembly and flush cover

2026-09-27. State: `cad-approved` for the local main-wing/pocket/cover design. User responded “Alright, continue to the rear fins,” accepting this local candidate as the next-stage baseline. Whole-airframe, actual rack and engine/runtime acceptance remain open.

## User instruction and retained geometry

User identified joint pins obstructed by filled side channels, requested calculated openings, another5.5 mm drop of the whole wing assembly, and a top cover. All11 original A4 nonbody parts are translated Z-5.5, with no shape or relative-placement change. Total drop from elevated A2 is28.25 mm. The5.5 mm inter-set offset and original joined-wing motion remain.

Source `src/interleaved_wing_a5.py`; six saved `STEP/O_Interleaved_A5_{Stowed,Module_Stowed,Midfold,Deployed,Body_Pocket,Cover}.step`. Full assemblies13 parts; module12 including cover; body/cover isolates1 each. Prior revisions preserved.

## New pocket and cover

- Well retains X-450.3..550.3,Y-74.3..74.3, floor nowZ57.75. Top reaches cover undersideZ84.
- Side-specific A4 panel channels retain their X/Y ranges and move down5.5 mm.
- Separate fixed top cover: X-455..555,Y-76..76,Z84..86, thickness2 mm, top flush with original body roof. Thickness is a CAD study assumption, not structural sizing.
- Body receives a matching cover seat; the strips outside the central well provide ledges. Measured seat gap0 and overlap0;0.01 mm landing-band proxy gives4830.84 mm2 support area. No fasteners, attachment strength or sealing claim.
- Highest internal hardwareZ81.25 leaves2.75 mm beneath the cover. The top wing panel is nowZ80.5; the cover, not the wing, supplies the flush exterior.

## Pin openings / corrected verification gap

The prior A4 21-position test missed join-pin collisions very early in opening: starboard overlap11.98 mm3 at fraction0.001; at0.002 starboard92.73 and port52.38 mm3. That historical sampled pass must not be cited as continuous clearance. A4 remains preserved as failed early-crossing evidence.

- Both joint centers follow radius900 circles about their fixed roots(500,+/-30). The angle reverses near fraction0.824042603; cutter bounds include this analytic interior extremum as well as endpoints.
- Starboard angular sweep138.189685..179.681688 degrees; port mirrored negative angles.
- Starboard shaftZ60.25..75.25, cap75.25..75.75; port shaft65.75..80.75, cap80.75..81.25. Nominal shaft/cap radii3.5/7 mm.
- Each opening comes from a true annular-sector sweep plus round discs at the angular extrema, with0.3 mm radial and axial allowance. Tools are clipped to original body material. This forms localized connecting openings between each side's panel slots near the aft joint crossing rather than reopening unused channels everywhere.
- The feasibility worker's final text accidentally repeated port Z values for starboard; its saved JSON and code held the correct distinct ranges. Primary checked those before build. Production uses discs at angular extrema (correcting the probe's use of fractions0/1).

## Executed validation

Separate fresh workers completed feasibility, build, and saved validation; primary reviewed source/reports at each gate. `src/check_interleaved_a5.py` PASS, report `reviews/interleaved_a5_checks.json` contains no failures.

- All6 saved artifacts valid, correct inventories; exact A4-translated nonbody identity across4 saved component states; saved mid/deployed match rigid transforms of saved stowed parts. All reported Boolean deltas0.
- Saved body exactly matches independently reconstructed original-body-minus-cutters, no added material/outside-cut change; body remains one solid. Isolated body and cover match full assembly; cover matches independently specified box.
- Independently built **continuous pin-only sweeps**, nominal and0.3 mm inflated, have zero intersection with saved body and cover. This addresses the identified early pin obstruction over the complete pin path.
-31 all-part motion samples:21 regular,9 early and the analytic turning point. Minimum panel clearance0.25 mm; unexpected intersection0; body/cover pairs not exempted. Existing housing/fixed-root attachment overlaps remain explicit exceptions.
- Housing/body floor gap and overlap0; root/carriage seating retained. Complete stowed conservative radius121.622367 mm<125.

## Primary visual review

Primary generated and directly inspected eight views from `review_interleaved_a5.json`: opposed stowed/deployed views, midfold, empty pocket, and both pin-opening closeups. Stowed view now has a continuous flush cover; deployed wings emerge below it. Closeups expose the local shaft-height opening and wider cap clearance joining the two side slots. The cover hides the mechanism in normal assembled views by design.

Review source `src/render_interleaved_a5.py`; best images `reviews/O_A5_stowed_iso.png`, `reviews/O_A5_deployed_iso.png`, `reviews/O_A5_port_pin_exit.png`, `reviews/O_A5_starboard_pin_exit.png`.

Limits: continuous verification is pin-vs-body/cover only; full assembly motion remains sampled. No strength, continuous full-assembly sweep, tolerance stack, fastener/retention, actuator/lock, rack or engine/runtime validation. Next: user reviews covered A5 and localized pin exits.
