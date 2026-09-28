# Phantom engine-read rough options (P03b) — 2026-09-28

Status: **rough concept studies, awaiting user choice. Not a contract, not accepted.** Visual only: no airflow, thermal or propulsion claim. R1 body, liner, fins, intake and all accepted exterior are untouched; the studies are separate insert parts placed in the existing R1 passage.

User direction: option 4 (compressor face + core + turbine/nozzle hardware), rough options first.

- Source: `src/engine_read_study.py` (reuses `aft_exhaust_r1` loft helpers). Outputs `STEP/S_EngineRead_{O1_TripleFan,O2_VaneCascade,O3_TwinEngine}_{Insert,Context}.step`. `Context` = saved R1 half-section review geometry (body Y>=0, liner, ramp, fins; review-only) plus the insert, so the port half is an open cutaway.
- O1 Triple fan: three small rotors across the 116x49 throat, one spindle core on 4 cross struts, turbine + tail cone, 12-petal converging round nozzle (28 parts).
- O2 Vane cascade: 13-vane guide grid + one fan/spinner, oval banded can on two side pylons, turbine + afterburner spray ring, four flat flap plates in the square liner (39 parts).
- O3 Twin engine: two fans matched to the wide slot throat, two round cores blending inward, two turbines, two 10-petal nozzles (38 parts).
- Check: `checks/check_engine_read_study.py` -> `reviews/engine_read_study_checks.json`. Every non-strut part lies inside the R1 void (outside volume 0.0 mm3, boolean intersect with liner-inner + connector + assumed stub sections; the stub section 116x49 r5 at Z-52.5 over X-1030..-953.3 is taken from the R1 brief, not re-measured). Struts/pylons embed 1.5 mm into the wall as attachment stand-ins (6.8-21.8 mm3 each). Not checked: strut-to-core contact, part-to-part clearance, motion.
- Review images: `reviews/EngineRead_<option>_{side,rear,throat}.png` (`review_engine_read.json`). Limitation: the throat view is from the open half, not a true belly view through the ramp; the ramp bay hides the throat from below.
- Known roughness: struts render black; nozzle petals/plates are flat placeholders; blade counts and pitch are arbitrary; O3 nozzle divider plate is crude.

## B1 — engine fixed in the ramp bay + second forward-hinged door (user concept, 2026-09-28)

User direction (supersedes O1–O3 as the layout to develop; O-series parts remain as nozzle/fan references): engine in the ramp bay (chosen "fixed in bay, face forward"), duct back to the nozzle, and a **second ramp/door forward of the main ramp that moves into the body**, keeping the main ramp's approved 35 mm deployment. User chose a **forward-hinged door swinging inward**.

- Source `src/engine_bay_study.py` (imports helpers from `engine_read_study.py`); outputs `STEP/S_EngineBay_B1_{Engine,DoorOpen_Context,DoorClosed_Context}.step`; check `checks/check_engine_bay_b1.py` -> `reviews/engine_bay_b1_checks.json`; images `reviews/EngineBay_B1_*.png` (`review_engine_bay_b1.json`).
- Layout (rough, all placeholders): single engine on the intake-stub axis (Z-52.5), fan face at X-312 looking forward (+X), Ø44 fan, Ø46-48 body with bands X-324..-810 on three ceiling pylons, tailpipe that follows the R1 connector to the liner, afterburner diffuser + spray ring + tail cone + 12-petal nozzle at the aft end. 
- Second door: 100 x 116 x 3 mm plate at X-290..-190, hinged at the forward edge (X-190, Z-84.5), open pose 34 degrees so the aft edge rises to about Z-28 into a **proposed forward pocket** X-295..-185 (same 124 x 60 section as the bay). Closed pose is flush with the belly (Z-86).
- Measured facts (probe of saved body, R1 Deployed): the existing bay is void at X-600/-320/-300 for Z-90..-26 and Y<=62 (ceiling between -26 and -22); stowed ramp bbox Z-86..-26.13; deployed ramp Z-121..-60.69, X-953..-290.93.
- Checks (concept-level, not approval): all non-pylon engine parts and both door poses lie inside bay + pocket + R1 stub/connector/liner voids (outside volume 0.0 mm3 after fixing initial 4.1 mm3 tailpipe overshoot by a ruled loft and 17.6 mm3 knuckle overshoot by mid-thickness hinge); engine and door intersect neither the stowed nor the deployed ramp (0.0 mm3). Pylons/pipe struts embed into walls as stand-ins.
- **Not** done/verified: hinge clearance sweep of the door, ramp motion sweep, the main ramp's function as scoop vs. the door opening (design intent to confirm with the user), door actuator, aerodynamics. The forward pocket is a **new exterior belly cut** in an area previously accepted flush and is unapproved; the review context shows it only in a clipped copy of the body. The door leaves ~1 mm to the ramp forward end (X-290 vs -290.93/-291).
