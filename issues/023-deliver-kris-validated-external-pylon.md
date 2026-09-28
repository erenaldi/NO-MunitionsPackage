---
id: "023"
title: Deliver Kris external pylon and explicit validated hardpoint registration
type: feature
status: blocked
blocked-by: ["020", "021"]
---

## Slice

Take the selected Kris pylon from detailed CAD through export, Unity prefab,
explicit hardpoint registration and runtime acceptance on every enabled external
station. This is the production tracer for the program: it also introduces the
shared explicit-registration helper later weapons reuse.

## Acceptance

1. Parameterized pylon CAD implements the selected architecture around the fixed
   Kris geometry, 45-degree roll and 9 mm local strake clearance. Intended
   suspension/ejector contacts are explicit; no strake or grid-fin intersection
   is hidden by renderer state.
2. Saved checks verify valid solids, fixed missile identity, intended contacts,
   no unintended pylon/missile overlap, measured release clearance and every
   candidate aircraft station in both physical positions where applicable.
3. The user approves the final CAD packet before export. Export then validates
   source identity, basis, scale, groups, materials, collider intent and mounted
   transform independently.
4. The Unity rack replaces the placeholder box while preserving the donor-owned
   `MountedMissile` hierarchy and behavior. Representative engine captures pass
   direct visual review.
5. A shared registration helper accepts explicit aircraft definition keys and
   hardpoint-set indices, rejects missing/duplicate entries loudly and logs exact
   additions. Kris stops using broad donor mirroring only after its approved
   table is available.
6. Runtime loadout, mounted appearance, launch separation, display removal, AI
   use, save/load and matching-peer multiplayer pass on every enabled Kris set.
   Failed candidates are marked rejected/blocked in the ledger and remain absent.

## Test notes

- Preserve all existing Kris gameplay tests and geometry checks.
- Build Release, validate the bundle/import, run `tools/check_log.ps1`, and retain
  per-aircraft runtime evidence.
- Verify the final runtime registration set exactly equals approved ledger rows;
  no unapproved `AAM1_single` set may leak through.
