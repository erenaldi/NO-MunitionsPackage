# RDM-9 Phantom — implementation checklist

Updated 2026-09-27. Scope: the current Phantom visual reboot, through CAD approval. Engine delivery is listed separately as later work. This document orders the remaining work; it does not approve new geometry or close outstanding review gates.

## Current working baseline

- Latest integrated candidate: `src/aft_exhaust_r1.py` → `STEP/S_AftExhaust_R1_{Stowed,Midfold,Deployed}.step` (34 components per full state), retaining IntakeR3's35 mm travel. See `AFT_EXHAUST_R1_BRIEF.md` and `DONOR_RACK_FINDINGS.md` for this pass.
- Coordinates: mm; +X forward, +Y starboard, +Z dorsal; body X−1400..1400. Complete stowed assembly must remain inside radius 125 mm / diameter 250 mm.
- The body derives from J/R7, with explicit wing, tail and intake pocket cuts. Preserve the accepted exterior outside those approved regions.
- Latest intake setting: **35 mm forward outer-lip drop**, 3.04020552845° rotation. This is a checked trial, **not yet explicitly accepted**.
- Saved evidence: `reviews/ramp_intake_r3_checks.json` passes; 66 sampled cross-poses, minimum checked moving clearance 0.25 mm, stowed conservative radius 121.622367 mm. The main-wing outboard pins also have the earlier A5 continuous pin-only clearance evidence. This does not establish continuous clearance for every moving part or every possible deployment sequence.
- Aft candidate evidence: `reviews/aft_exhaust_r1_checks.json` passes saved identity, open-passage and66-pose liner/peer checks (clearance lower bound18 mm). Actual donor fit report `reviews/agm1_reference_fit.json` **fails** at the unchanged mounting transform; this is an open fit gate, not a CAD-kernel error.

## Implemented geometry

| Feature | Current implementation | Review boundary |
|---|---|---|
| Body and nose | Lightly rounded square body, symmetric lower shoulders, selected wedge/chine nose | Local direction accepted; whole-airframe review still open |
| Joined main wings | Two enlarged R2 panel sets, 5.5 mm offset, sliding rear roots and joining pins | A5 local design accepted |
| Main-wing housing and cover | Reinforced tracks, recessed assembly, side-specific exits, calculated pin openings and flush top cover | A5 local design accepted |
| Rear fins | Four clipped fins, 80 mm aft revision, flush stowage in shaped shallow pockets | TailR4 local layout accepted |
| Belly intake | Aft-hinged rectangular ramp, nested side cheeks and open mouth; aft stub now connects through the new exhaust study | Built; current 35 mm travel awaiting approval |
| Aft exhaust and passage | Recessed rounded-square liner; connector now joins the former blind intake stub | Shape direction selected; built geometry awaiting visual acceptance |

Evidence authorities: `INTERLEAVED_A5_COVER_CONTRACT.md`, `TAIL_FIN_R4_FOUR_CONTRACT.md`, `RAMP_INTAKE_R3_CONTRACT.md`. Older STEP revisions remain comparison evidence. The unselected B wing-levelling study remains blocked/deferred; it is not part of this baseline.

## Ordered CAD work

Statuses below refer to deliverables, not just whether a file exists.

### P01 — Confirm the intake setting and baseline

- [ ] Accept or revise the 35 mm lip drop using stowed, side, mouth and deployed views.
- [ ] Record one selected integrated source/STEP set as the baseline for subsequent work.
- Exit: explicit intake decision and current contract pointers; no ambiguity between intake R1/R2/R3 or tail R3/R4.
- Depends on: user review. Packaging research and planning below can proceed independently.

### P02 — Recover actual rack and attachment geometry

- [x] Identify the real `AGM1_single` / `AGM1` donor mount and attachment transforms from game assets or a reproducible dump. Recovered enabled `launchpylon1` mesh and hierarchy from installed resources.assets; see `DONOR_RACK_FINDINGS.md`.
- [ ] Establish stowed keep-out volumes, suspension positions and relevant aircraft/body interfaces.
- [x] Compare the present candidate with that source before adding mounting details. **Failed at unchanged donor placement:** actual pylon intersects body, cover and port front wing. Mounting offset/interface and aircraft fit remain open.
- Exit: source identity, transform mapping and measured clearance report; missing source remains an explicit blocker. A 125 mm radius check or old mock pad is insufficient.
- Depends on: installed-asset/source access, not cosmetic design approval. Start this investigation alongside P03.

### P03 — Rear exhaust and intake-to-exhaust visual layout

- [x] Choose the aft opening, recessed lip and local tail-face treatment while preserving the selected fins and body envelope. User chose rounded-square.
- [x] Lay out an internal visual passage from the existing intake stub at X−1030 toward the aft treatment.
- [x] Check that the proposed cavity and visible interior avoid tail hinge/pocket volumes and retain a valid connected body. Saved independent checks pass; mount contacts retained.
- [x] Build one focused aft candidate with rear, section and full-vehicle review views. `S_AftExhaust_R1_*` built; primary inspected the packet. User visual acceptance remains pending.
- Exit: approved aft silhouette and cavity/attachment checks. An engine-performance model or sustained-propulsion gameplay change is not implied by these visuals.
- Depends on: current fin/intake packaging; P01 before freezing the combined design. This is the recommended next geometry pass.

### P04 — Flush RF/electronics panel layout

- [ ] Place the restrained flush RF areas retained by the visual-reboot brief.
- [ ] Choose their extent, orientation and relationship to the nose, main-wing bay, belly intake and rack interfaces.
- [ ] Review an annotated all-side layout before cutting pockets or adding borders.
- [ ] Build and verify the selected panel treatment, preserving the stowed envelope and moving clearances.
- Exit: approved placement and clearly identified RF versus service-panel surfaces.
- Depends on: P02 keep-outs and P03 packaging. The older R5 decision to remove emitters does not cancel the reboot's later flush-RF brief.

### P05 — Visible mounting and mechanism interfaces

- [ ] Model suspension/attachment features from P02's actual source, not a generic invented rack.
- [ ] Resolve visible wing-track ends, hinge seats, pin retention and cover seating at the level required for the asset.
- [ ] Decide what intake and fin stops/locks or actuation cues need to be visible; represent any geometry needed to support the shown motion.
- [ ] Define the intended release/deployment sequence and check the allowed poses against the rack and other appendages.
- Exit: no unexplained floating or intersecting visible mechanism; attachment and motion reports identify their intentional contacts and limitations.
- Depends on: P02 and selected local mechanisms. Real load ratings, bearings and actuator sizing are not established by a CAD contact check.

### P06 — Purposeful surface details and finish

- [ ] Map service access covers, construction seams and fasteners around the chosen internal/interface layout.
- [ ] Prototype the detail language before repeating it. Keep the broad skin readable at whole-vehicle scale.
- [ ] Refine appropriate exposed edges, intake/exhaust lips and joints without changing accepted silhouettes silently.
- [ ] Separate temporary review colors from intended material regions; prepare a material-region proposal when geometry is stable.
- Exit: approved all-side detail layout and focused visual reviews; repeated details follow approved intent.
- Depends on: P03–P05. Do not fill empty surfaces with arbitrary panels before their layout is settled.

### P07 — Integrated regression and review packet

- [ ] Rebuild the selected source chain and verify saved geometry, part identity, support paths and the complete stowed envelope.
- [ ] Preserve existing checks. Add independent tests for each new pocket/interface and any newly affected motion path.
- [ ] Check critical wall crossings with swept geometry or sufficiently targeted additional evidence; the earlier A4 pin collision showed why evenly spaced poses alone are insufficient.
- [ ] Verify the intended deployment sequence, including intake, four fins and main wings. Assess asynchronous combinations only where that sequence permits them.
- [ ] Check actual-rack fit in the agreed stowed/release states.
- [ ] Produce opposed full views, orthographic views, underside/aft closeups, stowed rack context and representative-distance images. Primary directly inspects the final packet.
- Exit: final CAD evidence and an explicit list of residual limitations, with no concealed failed checks.
- Depends on: P01–P06; regression runs incrementally, not only at the end.

### P08 — Whole-airframe CAD acceptance

- [ ] Present the completed feature layout and all applicable verification evidence for user approval.
- [ ] Record approved source/artifact identities and the exact boundary accepted.
- [ ] Reconcile the historical issue 015–017 records against this selected design and completed acceptance criteria.
- Exit: whole-airframe `cad-approved`; individual feature approvals and passing tests alone do not confer it.
- Depends on: P07 and user approval. The legacy issues are not marked done by this checklist.

## Later delivery milestones — separate authorization

These remain outside the current 3D-design implementation pass.

1. **Engine-ready export:** mesh groups, hierarchy, material slots, local axes, hinge/slider pivots, animation ownership, LOD/collider decisions and serialized mesh checks. Load the game-asset workflow when this boundary is actually entered.
2. **Unity presentation:** import the approved export; build matching materials and prefab/bundle geometry; validate scale, pivots, state transitions and reference lighting. Directly review engine captures.
3. **Runtime integration:** connect the approved stowed/released/deployed states through the existing geometry pipeline and verify mounting and fallback behavior. Preserve existing gameplay unless separately changed by the user.
4. **Runtime acceptance:** verify actual aircraft fit, release sequence, moving visuals, peer behavior and the agreed gameplay checks. Existing outstanding Phantom range, harmless-termination, designated-target and multiplayer checks remain separate from visual CAD proof.

## Immediate next actions

1. Review 35 mm intake travel.
2. Review the built rounded-square exhaust and connected visual passage.
3. Resolve the measured unchanged-donor-placement collision with an approved mounting-position/interface study; then assess actual aircraft fit.
4. Place flush RF areas after those keep-outs are known.

Authority: `../../plans/2026-09-23-rdm9-phantom-visual-reboot.md`, `../../MUNITIONS.md` section 5, `../../docs/ASSET_DESIGN_WORKFLOW.md`, and the feature contracts above. This checklist records a proposed execution order; new dimensions, visible mechanisms and downstream delivery decisions still require their owning design gates.
