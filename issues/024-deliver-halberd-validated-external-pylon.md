---
id: "024"
title: Deliver Halberd external pylon and validated hardpoint registration
type: feature
status: blocked
blocked-by: ["021", "023"]
---

## Slice

Take the selected Halberd pylon through detailed CAD, export, Unity integration,
explicit hardpoint registration and runtime acceptance, reusing the registration
boundary established by issue 023. Preserve the active rounded-square Halberd
rather than fitting the rack to the historical production mesh.

## Acceptance

1. Detailed CAD follows measured shoe/rail datums and keeps the pylon within the
   dorsal corridor, clear of intakes, the stage joint and booster separation.
2. Saved checks prove fixed missile identity, valid rack solids, intended contact,
   no unintended overlap and measured mounted/release clearance on every proposed
   physical station.
3. User CAD approval precedes export. Serialized mesh, transform, materials,
   colliders and hierarchy pass their own delivery contract and engine captures
   pass direct review.
4. Halberd registration migrates from `AAM4_single` mirroring to exact approved
   aircraft/set rows without changing encyclopedia index ordering or multiplayer
   identity.
5. Runtime tests pass loadout, mounted visibility, clean launch, booster staging
   clearance, effects, AI use, save/load and matching-peer multiplayer on every
   enabled set. Failed candidate stations remain absent and documented.

## Test notes

- Re-run the active Halberd CAD regression suite and add rack/station checks
  without weakening current silhouette, stage or intake assertions.
- Build Release, validate the geometry bundle and inspect runtime logs for exact
  registration rows and fallback behavior.
