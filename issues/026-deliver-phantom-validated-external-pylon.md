---
id: "026"
title: Deliver Phantom external pylon after whole-airframe and rack approval
type: feature
status: blocked
blocked-by: ["017", "022", "023"]
---

## Slice

After Phantom issue 017 establishes the selected whole-airframe and actual donor
rack evidence, take the selected external pylon through detailed CAD, export,
Unity integration, explicit hardpoint registration and runtime acceptance. This
slice replaces the historical R5 placeholder rack only after the current 2.8 m
visual reboot is the approved source.

## Acceptance

1. Detailed pylon CAD preserves the 250 mm stowed envelope and avoids joined-wing
   covers/pin exits, tail-fin pockets, belly intake and approved RF/interface
   regions. Attachment geometry comes from recovered evidence, not a mock pad.
2. The declared release/deployment sequence proves aircraft and rack clearance
   before intake, main-wing or tail-fin motion. Applicable moving paths receive
   swept or targeted evidence rather than sparse pose assumptions.
3. Saved checks cover fixed missile identity, valid rack solids, intended
   contacts, no unintended overlap, and every candidate physical station.
4. User CAD approval precedes export; serialized mesh, materials, colliders,
   transforms and hierarchy pass independently. Engine captures show the current
   stowed Phantom, not the historical R5 mounted display.
5. Phantom registration migrates from broad `AGM1_single` mirroring to exact
   approved ledger rows. The 2.8 m/180 kg weapon is not retained on a donor set
   that fails fit solely because the 1.62 m AGM-48 used it.
6. Runtime tests pass loadout, mounted state, clean release, appendage deployment,
   harmless flight behavior, AI use, save/load and matching-peer multiplayer on
   every enabled configuration.

## Test notes

- Re-run the selected Phantom whole-airframe geometry and motion checks before
  rack checks; a pylon pass cannot mask an unresolved issue-017 gate.
- Build Release, validate bundle/import identity and verify exact runtime
  registration against approved ledger rows.
- Preserve historical R5 assets as comparison evidence; do not overwrite them.
