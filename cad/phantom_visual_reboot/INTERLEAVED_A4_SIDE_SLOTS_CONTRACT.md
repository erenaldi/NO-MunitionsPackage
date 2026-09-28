# A4 — side-specific wing exits

**2026-09-27 correction:** user identified joint-pin obstruction. Denser early checks confirmed collisions at fractions0.001/0.002 between this revision's original21 sampled poses. A4 is preserved as failed early-motion evidence; use A5 for calculated pin exits, another5.5 mm assembly drop and a flush cover. See `INTERLEAVED_A5_COVER_CONTRACT.md`. The historical sampled-pass report below is not continuous-clearance evidence.

2026-09-27. State: `cad-review`; user acceptance pending. User annotated the two unused channels on each body side and requested filling them because port/starboard wings deploy at different heights. Primary directly inspected both supplied annotated images.

## Change

- Source `src/interleaved_wing_a4.py`. Body reconstructed from original A2 body with the A3 well retained, but only two wing-layer cuts per side. Original body material fills the unused opposite-side channels; no separate plugs.
- Starboard (+Y): slots Z65.7..70.3 and76.2..80.8, Y0..100.
- Port (-Y): slots Z71.2..75.8 and81.7..86.3, Y-100..0.
- All slot X extents remain-430..530; central well remains X-450.3..550.3,Y-74.3..74.3,Z63.25..100.
- All11 nonbody A3 components and motion unchanged; uppermost panel remains flush atZ86, caps0.75 mm proud,5.5 mm inter-set offset. Prior revisions preserved.

## Verification

- Fresh bounded feasibility probe `checks/probe_side_slots_a4.py`: PASS; report `reviews/side_slots_a4_probe.json`. Primary reviewed before authorizing separate source/build and saved-validation gates.
- Five saved outputs `STEP/O_Interleaved_A4_{Stowed,Module_Stowed,Midfold,Deployed,Body_Pocket}.step` checked by `src/check_interleaved_a4.py`: PASS, no failures. Report `reviews/interleaved_a4_checks.json`.
- Independent exact-cutter comparison against original body has zero Boolean difference. All saved A3 body material retained; additions only within the four unused side-channel regions and original A2 body. Approximately183988.76 mm3 restored; each of the four channels has positive restoration.
- Nonbody saved A4/A3 identity: zero Boolean delta in all four component states. Full saved topology, pose correspondence, support contacts, roof/cap heights and radius checks inherited without weakening thresholds.
-21 simultaneous all-pair motion samples pass: minimum panel clearance0.25 mm, no unexpected intersections. Only documented housing/fixed-root attachments exempt; body pairs are checked. No continuous-sweep or structural-strength claim.

## Primary visual review

Primary generated and directly inspected all eight images from `review_interleaved_a4.json`: opposed stowed/deployed isometrics, deployed side-channel detail from both sides, and both sides of the empty pocket. Filled bands now follow the body surface, with exits at the distinct port/starboard heights. Low-angle views can show far-side channel edges through the open well; these do not represent additional near-side openings.

Review source `src/render_interleaved_a4.py`. Best detail images: `reviews/O_A4_port_channel_detail.png` and `reviews/O_A4_starboard_channel_detail.png`. Next: user reviews A4. No engine/runtime or production acceptance.
