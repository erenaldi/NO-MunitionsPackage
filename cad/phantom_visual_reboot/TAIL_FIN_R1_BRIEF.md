# Rear-fin R1 — one-corner concept/packing gate

2026-09-27 selection: user chose Tall clipped and requested80 mm aft shift. Current revised-placement candidate is `TAIL_FIN_R2_CONTRACT.md` / `STEP/Q_Tail_R2_Clipped_*`. This R1 trio remains comparison evidence; no longer awaiting planform choice.

2026-09-27. State: `concept-review`. User accepted the current A5 wing/pocket/cover direction and requested continuing to rear fins. Three rough one-corner planforms are built and checked; selection and fourfold propagation remain pending. Earlier whole-airframe tail placeholders are not approved tail geometry.

## Locked intent and prototype scope

- Authority: `plans/2026-09-23-rdm9-phantom-visual-reboot.md`: four Kh-69-inspired corner-hinged folding fins, all stowed geometry inside radius125 mm. This is reference-inspired game-asset geometry, not a claimed replica or flight design.
- Preserve every saved A5 body/main-wing/cover component exactly. No changes to its pocket, pin exits, wing motion or dimensions.
- First build only one upper-starboard corner prototype with stowed/intermediate/deployed correspondence. Present three rough fin-planform choices sharing a hinge; user selects before detailing or fourfold propagation.
- Coordinate basis mm,+Xforward,+Ystarboard,+Zdorsal. Body aft taper ends aboutX-1260 in the inherited source; the proposed hinge is farther forward on the full barrel to avoid unsupported mounting on that taper. Actual saved-body contact must be measured.

## Reversible primary-selected trial dimensions

- Longitudinal hinge axis through Y82,Z88.5, parallel+X; moving root spansX-1245..-1005 (240 mm).
- Folded panel lies toward-Y across dorsal face, thickness3 centeredZ88.5. Deployed rotation-135 degrees about this hinge gives an outward diagonal panel. Sample intermediate rotations; do not assume endpoint fit establishes clearance.
- Rough outlines use local coordinates (X, inward stowed span). All share root(-1245,0)..(-1005,0):
  - Compact trapezoid: outer edge(-1210,70)..(-1105,70).
  - Strongly swept: outer edge(-1230,90)..(-1195,90).
  - Taller clipped: outer edge(-1200,110)..(-1100,110).
- Root tube outer radius3/bore1.5; pin radius1.25. Two fixed knuckles X-1255..-1246 and-1004..-995, radius3/bore1.5; each joined to a small body-contact foot aroundY79..84.5,Z80..88.5. These support primitives require contact/collision checks before build.
- End caps/pin remain within outer radius3; axial panel/knuckle gaps1 mm and cap/knuckle gap0.3 mm. These are illustrative clearance geometry, not strength/bearing/retention validation.
- Approximate conservative stowed corner bound from the proposed root hardware: hypot(85,91.5)≈124.89 mm. Verify actual saved component bounds and body clearance; don't use this estimate as a pass.

## Built evidence / review gate

- Source `src/tail_fin_r1.py`; nine `STEP/Q_Tail_R1_{Compact,Swept,Tall}_{Stowed,Midfold,Deployed}.step` outputs. Each combines the matching immutable13-part A5 state with four tail components: moving fin/root, two fixed knuckle/feet and capped through-pin.
- Bounded tall-fin feasibility passed: `checks/probe_tail_fin_r1.py`, `reviews/tail_fin_r1_probe.json`. Fresh workers then built rough sources and ran saved checks separately. Primary inspected geometry source, checker coverage and reports.
- `src/check_tail_fin_r1.py` PASS, report `reviews/tail_fin_r1_checks.json`, no failures. All9 artifacts17 unique valid positive solids;117 A5 base comparisons zero Boolean difference;36 tail pose comparisons zero after inverse rotation; saved fin/hardware match independently restated dimensions.
-31 sampled folds per variant pass, minimum clearance0.25 mm including pin fit. Both feet contact original body by194.794 mm3 each (explicit fixed attachment only); knuckles themselves do not overlap body. Pin radial gap0.25, cap axial gap0.3 mm. Stationary hardware also checked against reconstructed A5 motion; no unexpected saved pair overlaps.
- Maximum new-part conservative stowed radial bound124.889 mm<125, only about0.111 mm conservative radial margin. Tail added-part X-1256..-994. Inherited A5 raw STEP bounds extend0.0000001 mm past±1400 from import tolerance; base is exact and was not redesigned to game that bound. No actual rack/tolerance-stack fit claim.
- Primary generated12 PNGs from `review_tail_fin_r1.json` and directly inspected six full-resolution views plus the board containing all12. `reviews/Q_Tail_R1_Comparison.png` is the matched-scale selection packet; source `src/assemble_tail_fin_r1.py`. Close views deliberately crop the forward airframe to show the rear feature; full context row retains the complete vehicle.
- Visual assessment: compact fin is restrained; swept option is narrow and sharply raked; tall clipped option is most legible in full-airframe context and is the primary's recommended starting point. This is a visual recommendation, not aerodynamic or user approval. All use the same135-degree corner fold and shared hardware, without fourfold replication.

Next: user selects/revises a planform, then verify the selected fin around all four corners before detailed hardware work. Strength, continuous sweep, four-fin interactions, tolerance stack, lock/actuator and engine delivery remain open.
