# RDM-9 Phantom — B2H integrated baseline contract

Date: 2026-09-29. Fictional game asset, visual/CAD only: no engine, airflow, thermal, structural or gameplay claim is made or implied.
Supersedes `AFT_EXHAUST_R1_BRIEF.md` as the **working baseline** (that R1 exhaust concept, the 35 mm intake setting and the earlier S-curve connector are replaced by the changes below). Older STEPs and studies stay as comparison evidence and are never edited.

## Status of each feature

| Feature | State | Basis |
|---|---|---|
| Rounded-square body, nose, joined main wings (A5), four tail fins (TailR4) | Locally accepted earlier; unchanged | Their own contracts; identity re-verified below |
| Rear opening + recessed rounded-square liner (R1) | Accepted shape; unchanged | R1 brief; liner leaf unchanged |
| Engine envelope carried on the main ramp | User-directed concept (2026-09-28); surface-visible parts detailed only | Sketch-driven; user said "looks good" after B2D |
| Main ramp deployment ~50 mm lip drop (4.3424 deg) | User-directed change of the earlier accepted 35 mm; recorded as replacing it | User request 2026-09-28 |
| Second belly door (340 x 116 x 3, hinge X+53, 9.86 deg) + pocket/chamber | User-directed; **new exterior belly cut, not separately approved beyond the user's direction** | User request |
| Straight bypass duct to the nozzle, engine sweep cavity | Internal review-level cuts | Sketch |
| Square rear nozzle (B2H) | User-selected (square over circular) and "looks good" | User 2026-09-29 |
| Restrained cosmetic engraving (door, ramp underside, bay surround, intake frame) | User-selected scope | User 2026-09-29 |
| Whole-airframe CAD acceptance (P08) | **Not given** | Pending P02/P04/P05/P06/P07 |

## Source chain and artifacts

Immutable inputs: `STEP/R_RampIntake_R3_{Stowed,Deployed}.step` (body, wings, fins, ramp, pins) and the R1 liner definition.
Model chain (run from `src/`): `engine_read_study.py` (helpers) -> `engine_bay_b2.py` (layout constants) -> `engine_bay_b2d.py` (details) -> `engine_bay_b2e.py` (ramp +15 mm) -> `engine_bay_cosmetic.py` (engraving) -> `engine_bay_b2g.py` (turbine stage, shaft, cone) -> `engine_bay_b2h.py` (square nozzle).
Baseline STEPs (66 leaves each): `STEP/S_EngineBay_B2H_Stowed_Full.step` sha256 `3d85839829219d4d0bafe05c825d8e363351a0d6632cc944b7bea11431d24def`; `STEP/S_EngineBay_B2H_Deployed_Full.step` sha256 `a6d9ccba9e5280a339f97604fa77d8f795d7777cdf1da855a0f1693fe9f0a44b`. Review sections: `STEP/S_Nozzle_B2H_Section.step`. Earlier B2/B2D/B2E/B2F/B2G outputs are unchanged comparison evidence.

## Key parameters (mm, +X forward, +Y starboard, +Z dorsal)

- Ramp hinge X-950, Z-83 (axis +Y). Deployment 3.0402 (accepted R3) + 15/660.007 rad = **4.3424 deg**; measured deployed lip drop **49.96 mm**. Stowed ramp is unchanged (Z-86..-83 plate).
- Engine envelope (stowed frame) X-897..-322, 112 wide x 90 tall, bottom Z-82.9 (0.1 mm above the plate); it rotates with the ramp. Fan face frame at X-322..-319 with lip, fan and spinner ahead of it.
- Door 340 long, hinge X+53 / Z-84.5, aft edge X-287 (abuts the ramp), open 9.86 deg (aft edge Z about -26); pocket X-292..+58; belly aperture seam 1 mm.
- Nozzle: rounded-square mount ring X-1355..-1349, 4 side flaps + 4 corner facets (X-1391..-1352, inset 2.6 mm from the liner), 4 diagonal struts at X-1347.5, tail cone, shaft, 24-blade turbine stage at X-1322.
- Engraving: 0.4 mm deep, 0.8 mm wide seams; rings r1.5-2.3; recessed vent slots.

## Evidence (all in `reviews/`, produced 2026-09-29)

- `engine_bay_b2h_integrated_checks.json` — new saved-artifact regression `src/check_engine_bay_b2h_integrated.py`: **0 failures**. Covers: 66 valid leaves per state, identical label sets; every non-body/non-ramp R3 leaf identical to the matching R3 state (body only lost material); pose model (rotated stowed group = saved deployed, ramp 4.3424 deg, door 9.86 deg) confirmed by volume/centre-of-mass/bbox/vertex-set invariants (the boolean symmetric difference is unreliable on the fan and face frame and is reported as such); lip drop 49.96 mm; stowed envelope max conservative radius **121.62 mm < 125**; static overlap list (36 pairs per state, all listed and classified below); 29-pose ramp-group and door sweeps vs stowed peers; 5-pose sweeps vs deployed-state wings/fins; 25 asynchronous door x ramp combinations — no unexpected overlap anywhere.
- Static overlap pairs (identical in both states): tail knuckle and intake fixed-mount body contacts, fixed-root/housing contact (accepted mounts); liner<->nozzle ring and turbine stage (intentional 0.3 mm wall embed); ring<->flaps/facets/struts, struts<->cone, cone<->shaft<->turbine (intentional attachment chain); face frame<->lip and fan; door panel/frame<->hinge barrels. Mount pads touch the engine flank by **face contact only (zero volume overlap)**.
- Existing checkers rerun against their own saved artifacts (unchanged files): `check_ramp_intake_r3.py`, `check_aft_exhaust_r1.py`, `check_tail_fin_r4.py` exit 0 (see the regression note in the session journal for A5 and the AGM1 fit).
- Renders: `reviews/EngineBay_B2H_*.png`, `EngineBay_B2F_*`, earlier B2 studies; primary inspected axial/oblique nozzle views, door, ramp underside and belly views.

## Residual limitations and open items (nothing hidden)

1. Sampled poses only: no continuous swept-volume proof; clearance for pairs whose bounding boxes touch is reported as "no volume overlap", not as an exact minimum. Smallest lower-bound gap among disjoint-AABB pairs during sweeps is 1.0 mm.
2. The ramp regression evidence in `ramp_intake_r3_checks.json` covers the accepted 3.04 deg setting; the 4.34 deg setting is covered only by the new B2H integrated sweep.
3. **Actual donor rack fit at the unchanged donor placement still fails** (`reviews/agm1_reference_fit.json`, checker exits 1 by design). **Decision 2026-09-29 (user):** resolve it by a straight lowering of **9.574 mm applied in the asset frame** (game mount transform untouched; carried into the later export milestone). Study and verification: `DONOR_RACK_FINDINGS.md` (Mounting-interface study), `reviews/pylon_lowering_verification.json` — pylon-surface intersections at 9.574 mm: none (bbox gap +1.00 mm; 9.1 mm also clear, 8.1 mm not). Placed file `STEP/S_EngineBay_B2H_Stowed_Placed.step` (rigid translation, design-frame sources unedited) and reference-only view `reference/agm1_mount/Phantom_DonorFit_Lowered_9574.step`. Not assessed: aircraft/bay clearance below, release states, whether the envelope or hitbox is referenced to the donor mount origin.
4. Mount pads are face-contact only; the duct/engine sliding joint, door and ramp actuation, engine-to-ramp mounting hardware and internal engine parts are not modelled.
5. The door pocket, chamber, bypass duct and engine sweep cavity are real cuts in the B2H body but were not separately approved as exterior changes.
6. RF-panel layout (P04), remaining surface detailing of nose/tail/flanks/top (P06) and whole-airframe acceptance (P08) are open. Export, Unity and runtime milestones are not started.

## Boundaries

250 mm stowed envelope, 2800 mm length, accepted A5/TailR4/R1-liner geometry and the rounded-square rear opening remain locked. No game/config/propulsion change is authorized by this document; reference meshes remain reference-only.
