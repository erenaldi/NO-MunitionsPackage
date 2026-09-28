# Joined-wing R1 — reference-led local prototype

Date: 2026-09-24. State: `cad-review` (built and checked; local selection pending).

## Brief and approval boundary

User requested continuation after rejecting K's isolated swivel wing and reading
the DiamondBack research. Prototype one complete **joined side**: forward and
rear lifting panels, outboard joint, fixed forward root and sliding rear root.
The other side awaits this local review before repetition. This is a fictional
Phantom adaptation of the sourced architecture, not a production GBU-39 replica.

- Authority: `GBU39_WING_REFERENCE_RESEARCH.md`; retain J/R7 body and nose.
- mm; +X forward, +Y starboard, +Z dorsal; vehicle length 2800 mm.
- External dorsal housing; both folded panels visibly retained above the body.
- Reversible assumed link lengths 900/600 mm; root line Y=35, fixed root X=500.
- Rear root moves aft as the connected panels open. The closed pose has 5 mm
  outboard offset, avoiding an exactly collinear visual linkage.
- Rigid panels at two shallow heights allow overlap when stowed. Explicit
  root/outboard bores and pins depict the connections; no actuator or locking
  system is inferred from unverified production details.
- User's 250 mm diameter envelope applies to the entire stowed study, including
  housing, carriage and all pin/cap shapes. Actual rack fit remains open.
- Prototype is a form/pose study, not a manufacturing or aerodynamic design.

## Intended checks and review

Verify serialized solids, body identity, rigid-panel correspondence, closed
joint locations, visible fore/aft panel identity, carriage travel, stowed radial
bounds and moving-part clearance through sampled poses. Inspect matched stowed,
intermediate and deployed top/oblique views plus isolated module detail.
The key visual test is the linked-panel negative space opening from longitudinal
stowage; a repeated standalone wing swivel would fail this brief.

Source: `src/joined_wing_r1.py`. Output family `L_JoinedWing_R1_*`.
No opposite-side propagation or tail detailing until this local architecture is
reviewed. Previous K files are rejected history, not model inputs.

## Delivered study and evidence

- Six outputs: `L_JoinedWing_R1_{Stowed,Midfold,Deployed}.step` on the body and
  `L_JoinedWing_R1_Module_{Stowed,Midfold,Deployed}.step` in isolation.
- The rear-root carriage travels 449.9931 mm aft. Midfold is half of carriage
  travel, not half of wing span or elapsed deployment time. Maximum lateral
  extension occurs slightly before the final pose; this is a reversible
  illustrative pose law, not a measured production deployment sequence.
- `src/check_joined_wing_r1.py` PASS on serialized STEPs: seven valid single-solid
  components per body assembly, six per isolated module, identical module/body
  parts, unchanged J/R7 body and 2800 mm length. Every rigid part matches after
  inverse transforms; both panels' exported bore centers coincide with their
  root and common outboard joint. Link distances remain constant.
- Twenty-one sampled poses of the exported parts have no panel intersections
  with body/housing/pins/other panel. Minimum sampled panel clearance 0.25 mm.
  Slider and outboard pin also remain clear of the housing. This is sampled
  geometric evidence, not a continuous swept-solid or actuator/lock validation.
- Conservative radial bounds in stow: body 121.6224 mm, forward panel 121.0249,
  rear panel 110.8950, housing 108.3746, fixed root 114.2366, carriage 106.5610,
  outer pin 115.0391; all below 125 mm. These cover this one-side study, not
  an unbuilt opposite side, tail or actual donor rack.
- Report: `reviews/joined_wing_r1_checks.json`.
- First build tool call failed with `ChildProcess.kill` and no output; no L
  artifact existed then. A simple terminal date query succeeded, and the direct
  build retry generated all six files. The initial checker reached all saved
  states but exceeded 120 seconds while snapshots ran concurrently. Added
  motion progress logs and reran serially with a 300-second budget; full PASS.
  No checks or thresholds were removed or relaxed.
- `review_L.json` generated fourteen images. Primary model inspected the
  eleven individual oblique/side/end images and all three module top images
  within the composed `reviews/L_JoinedWing_R1_Review.png` board. The joined
  triangular space and rear slider are readable; folded panels visibly stack
  in the end/oblique view, though the broader forward panel hides much of the
  rear member in exact top view. Broad housing is intentionally a rough form.
- All six STEP paths exist and viewer URLs on port 3245 returned HTTP 200.

Next: user approves/revises the joined-panel layout before its opposite-side
counterpart and the tail prototype. Production GBU-39 sequencing remains unverified.
