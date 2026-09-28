# Belly ramp intake R1 — sketch-led reversible prototype

2026-09-27 update: user requested half vertical deployment. Current R2 preserves geometry and stow, reducing forward-lip drop57.5114→28.7557 mm via2.49737degrees. See `RAMP_INTAKE_R2_CONTRACT.md`; R1 remains the original-height comparison.

2026-09-27. State: `cad-review`; first sketch-led intake prototype built and checked, user acceptance pending. User requested a pop-out ramp intake using two inline annotated views; primary inspected both. No verified local attachment paths exist.

## Interpreted design

- First drawing supplies rectangular belly footprint ahead of the tail. Second supplies side silhouette: forward edge lowers, aft end remains at the body. Nose is left in the drawings; model+X is forward. Single ventral intake, not paired side intakes.
- Flush-stowed panel; aft hinge and lowered forward lip create a forward-facing mouth. Internal moving triangular side cheeks close the scoop sides when deployed. A recessed cavity and short aft duct stub make the mouth visibly open; no engine/airflow-performance claim.
- Drawing lines express idealized geometry, not literal waviness or exact dimensions. Prototype dimensions below are reversible primary assumptions based on the marked proportions.
- Preserve accepted four-fin R4 and covered A5 main-wing geometry; authorize only local belly cavity/seat cuts and intake parts. Retain250 mm stowed envelope,2,800 mm length, nose and all existing moving parts.

## Trial geometry and location (mm)

- Ramp floor X-950..-290,Y-64..64,Z-86..-83:660long,128wide,3thick, outerface flush bellyZ-86.
- Aft hinge parallelY atX-950,Z-83. Whole moving scoop rotates+5degrees aboutY when deployed; forward lip drops about57mm. Crown on the belly side remains flush when closed using3mm root radius.
- Side cheeks2mm thick atY[-64,-62] and[62,64], triangular X/Z vertices(-950,-83),(-300,-83),(-300,-83+650*tan5deg). Deployed uppercheekedge stays atZ-83,3mm inside body skin; 10mm forward floor extension forms the lip. Open front, no mouth cap.
- Moving transverse root barrelY-64..64,R3,bore1.5; throughpinR1.25 withR2.5caps, radialgap0.25. Fixed knucklesY[-71,-65] and[65,71],R3/bore1.5, on small embedded body pads nearX-953..-947,Z-83..-75. Axial knuckle/rotor gap1mm; pin capgap0.3mm. Hardware geometry is conceptual.
- Trial body cavity X-953.3..-289.7,Y-64.3..64.3,Z-100..-25.8. Cavity reaches above folded cheeks. Short aft stub X-1030..-953,Y-58..58,Z-77..-28 connects above the hinge; blind rear termination is a placeholder boundary for later aft design, not a complete engine duct.
- Pin/barrel/cap reliefs must be calculated from actual geometry; no moving part/body overlap exceptions. Fixed mounting pads may intentionally embed in body but must retain positive support contact.
- Axial gap from stub aft endX-1030 to current tailhardware frontX-1074 is44mm. Check actual saved parts, not only this estimate.

## Gate

Begin with bounded in-memory packing/deployment feasibility. Measure open front aperture, body connectivity, stowedflush/envelope, support path, and intake-vs-mainwing/tail motion. Then build separate stowed/intermediate/deployed candidates and directly inspect belly/side/mouth views before user acceptance. No detail propagation, exhaust design or engine integration in this gate.

## Built prototype and verification

- Source `src/ramp_intake_r1.py`; six `STEP/R_RampIntake_R1_{Stowed,Midfold,Deployed,Body_Cavity,Module_Stowed,Module_Deployed}.step` outputs. Full33parts, isolated intake4parts, body1solid. Ramp/cheeks/root form one moving solid; two fixed mounts and pin support it.
- Initial delegated probe hit native Part/Box versus Solid wrapper errors; the worker returned the incomplete result rather than claiming success. Primary inspected the repair, moved the probe into assigned `checks/`, then executed `checks/probe_ramp_intake_r1.py`: PASS,66samples, no failures, minimum clearance0.25 mm, unobstructed mouth test124×52.830188 mm atX-305.
- Separate fresh source/build and saved-validation workers completed. `src/check_ramp_intake_r1.py` PASS; `reviews/ramp_intake_r1_checks.json` has0failures. Primary inspected source/report and rendered actual saved artifacts.
- All6 saved artifacts valid and correct counts.84 unchanged R4-component comparisons (28peers ×3states) have zero Boolean delta. Body equals independently specified local cutter subtraction in allstates; isolated body and modules match full assemblies. Newpart independent geometry and rigid pose identity pass.
-66 synchronous cross-samples cover intake/body, all existing moving parts and internal intake hardware:120nonexemptpairs/sample, minclearance0.25, unexpectedoverlap0. Only named fixedmount/body attachments exempt. Existing R4 supports remain attached. Continuous/full-asynchronous-motion and strength unverified.
- Stowed panel and lowest hardware atZ-86; full conservative radius121.622367 mm<125. Deployed floor/front-lip drop is approximately57.5 mm. Mouth test volume is geometrically open at124 mm width and52.830 mm clear height; this is not a mass-flow or engine-performance result.
- The cavity and aft stub are connected (0.3 mm X overlap,1705.2 mm3 cutter intersection), but terminate blindly atX-1030. No engine connection, actuator, lock, seal or rear exhaust is modeled/validated.

## Primary visual review

Primary directly inspected all9views from `review_ramp_intake_r1.json`: closed belly, opposed deployed belly views, matched closed/open side details, forward mouth, empty body cavity, isolated stowed/deployed scoop. The closed panel is flush and rectangular; the open profile matches the sketched forward drop/aft hinge. Side cheeks form the triangular wedge and the forward mouth is visible. Isolated module views show the cheeks that nest inside the body when closed. Cropped side/mouth views are deliberate feature closeups.

Best review images: `reviews/R_Intake_R1_stowed_belly.png`, `reviews/R_Intake_R1_deployed_belly.png`, `reviews/R_Intake_R1_deployed_side.png`, `reviews/R_Intake_R1_mouth.png`. Renderer `src/render_ramp_intake_r1.py`.

Next: user accepts/revises footprint, lip drop and mouth appearance before detailing. Earlier TailR4/mainwing assets remain unchanged as comparisons.
