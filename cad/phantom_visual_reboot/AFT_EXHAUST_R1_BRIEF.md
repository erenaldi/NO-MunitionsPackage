# Aft exhaust R1 — recessed rounded-square study

2026-09-27. User selected a **rounded-square** exhaust opening within the existing square tail. State: `cad-review`; built candidate awaiting visual acceptance. IntakeR3 remains at35 mm lip travel; no propulsion tuning or engine-performance changes are authorized.

## Preserve

- Current33-part IntakeR3 states, all32 nonbody components and their motion, outer body silhouette outside the explicit aft/duct cuts, four recessed fin pockets and hinge supports.
- Overall bodyX-1400..1400 and125 mm stowed radius. No proud nozzle extension beyond the tail.

## Reversible trial geometry (mm)

- Rounded-square body opening124×124, corner radius14, centeredY/Z0 at the rear planeX-1400. This leaves a24 mm nominal flat-face rim inside the172 mm body section.
- Recessed liner begins6 mm inside the tail atX-1394. Outer rounded-square sections: (X-1394,width124,r14),(-1360,110,12),(-1310,84,10). Inner sections: (-1394,116,10),(-1360,102,8),(-1310,76,6). Square sections are centered on the body axis. Use matched ruled lofts for an explicitly modeled4 mm nominal section-wall offset, not a claimed uniform normal wall thickness.
- Body seat cutter: outer profiles above, extended rearward toX-1401 with124/r14. Liner is a separate attached single solid; its outer surface seats against body, with no unintended volume overlap. Inner tool extends beyond liner end planes to leave both ends open.
- Visual connector to existing intake stub: rounded rectangular sections (X,width,height,centerZ,radius) = (-1310.5,76,76,0,6),(-1270,80,70,-10,6),(-1150,100,60,-35,6),(-1029.5,116,49,-52.5,5). This overlaps the original intake stubX-1030..-953 and the liner throat. It is an empty geometric passage, not an engine representation or aerodynamic/thermal design.
- Verify the exact cut-body remains one solid; connector and exhaust passage are unobstructed and joined; tail pockets and fixed mounts are retained and moving fins clear. Do not silently enlarge openings if collisions occur.

Feasibility refinement: the initial connector began turning within its0.5 mm overlap with the liner and intersected liner material by0.7851 mm3. Primary added a constant76×76/r6 section atX-1308, leaving a2.5 mm straight entry fromX-1310.5 before the bend. This retains the chosen external opening and avoids cutting into the liner. Opening tests use rounded profiles, not rectangular probes that incorrectly include the retained rounded corners.

## Gate

Start with an in-memory native-geometry feasibility probe against the saved IntakeR3 body and components. Then source/build, independent saved checks, and primary rear/section/opposed visual review. Dimensions are study assumptions within the user's selected opening shape and need visual acceptance before detail.

## Built evidence

- Source `src/aft_exhaust_r1.py`; five main artifacts `STEP/S_AftExhaust_R1_{Stowed,Midfold,Deployed,Body_Duct,Liner}.step`. Full assemblies34parts; body/liner isolates1each. All32 IntakeR3 nonbody peers remain Boolean-identical in each saved state. The only new separate component is the dark recessed liner.
- Primary completed the feasibility probe after correcting strict Solid-wrapper calls, rounded opening test profiles, and the actual IntakeR3 motion-helper references. The real initial connector/liner overlap was resolved by the straight throat section documented above.
- Exact minimum-distance queries across lofted geometry repeatedly timed out. All66poses and32peer comparisons were retained, using rigorous AABB distance lower bounds to prove the unchanged >0.2 mm clearance threshold; exact fallback remains for pairs whose bounds cannot prove it. Reported clearance is explicitly a lower bound, not an exact minimum.
- `src/check_aft_exhaust_r1.py` PASS (`reviews/aft_exhaust_r1_checks.json`,0failures): saved body/liner/isolates match independently restated geometry, no added body material or outside-cut change, body/liner volume overlap0 and boundary distance0. Coincident native face-area query returned0; matched seat profiles provide a34624.334 mm2 side-area proxy, not a strength result.
- Rear opening124/r14, liner entrance116/r10, recession6 mm verified. Rounded entrance probes clear; connector joins the original intake stub and open liner throat with no body/liner obstruction. Four tail pockets and ten tail/intake fixed-mount contacts preserved.
-2112 liner/peer checks across66samples pass with minimum conservative clearance lower bound18 mm. Stowed radius121.622367<125; body length2800 mm within imported STEP bounds tolerance. Existing validated moving geometry is unchanged; no new full-assembly continuous-motion claim.

## Primary visual review and next gate

Primary directly inspected six exhaust views plus two donor-reference views from `review_aft_exhaust_r1.json`. The aft opening follows the softened-square body, the liner is recessed, and the longitudinal diagnostic section shows the passage rising from the belly intake toward the aft opening. A straight rear view sees the bent passage's farther walls; there is no inserted cap or engine disk.

`STEP/S_AftExhaust_R1_AftSection.step` is a cropped half-section derived from saved geometry for review only. Best images: `reviews/S_Aft_R1_rear_close.png`, `S_Aft_R1_rear_opening.png`, `S_Aft_R1_duct_section.png` and `S_Aft_R1_deployed_rear.png`.

The parallel donor recovery found an actual unchanged-placement collision; see `DONOR_RACK_FINDINGS.md`. Exhaust geometry checks pass, but real rack fit is not approved. Next: user reviews exhaust dimensions/appearance and decides the mounting-offset/interface study. No actual engine, thermal design, airflow performance or runtime change is modeled.
