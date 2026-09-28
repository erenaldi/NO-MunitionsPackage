---
id: "020"
title: Dump physical hardpoint geometry and seed the four-weapon compatibility ledger
type: infra
status: done
blocked-by: []
---

## Slice

Deliver the first evidence tracer for the fixed-munition pylon program: a
current-game runtime dump containing physical hardpoint and donor-rack transforms,
plus a repository-owned candidate ledger for Halberd, Kris, Ballista and Phantom.
The result must let an asset author inspect a named aircraft/set/physical station
and reconstruct the mounted donor pose without relying on chat, set names or
vanilla option presence. Authority:
`plans/2026-09-27-fixed-munition-pylons-hardpoints.md`.

This slice does not alter weapon availability or replace any pylon geometry.

## Ownership and evidence

- Modify only the dump path and new pylon-program evidence files needed by this
  slice. Preserve all current registration, CAD, Unity assets and concurrent
  work.
- Verify the installed game through Steam appmanifest build ID; do not treat the
  QoL-modified `Application.version` string as the game version.
- Treat the saved 2026-09-15 schema as historical input. Generate fresh evidence
  before approving any station.

## Acceptance

1. `WeaponSchemaDumper` deliberately emits each physical `Hardpoint` hierarchy
   path; set and physical index; active state; local transform; transform relative
   to the aircraft root; and source option keys. Vector and quaternion values use
   explicit numeric fields and named coordinate spaces.
2. Mount-prefab records deliberately emit every transform's hierarchy path and
   local pose, plus renderer/collider bounds and each `MountedMissile` local pose,
   rail direction, rail length, speed and delay. The implementation does not
   assume Unity `Transform` properties appear through field reflection.
3. Aircraft context records include renderer and collider bounds in a stated
   coordinate space. Door, bay or landing-gear transforms are included only when
   they can be identified reproducibly; unknown relationships remain named gaps.
4. The dump is deterministic apart from documented runtime IDs/timestamps and
   does not expose secrets or mutate game assets.
5. A repository-owned compatibility ledger contains every current donor-derived
   candidate: six Halberd sets, seventeen Kris sets, nine Phantom sets and the
   twenty-two-set Ballista union. Each record identifies the matching donor keys
   and starts as `candidate` or `blocked`, never `approved` without fit evidence.
6. Ballista records distinguish the eleven `AGM_heavy_single` candidates from
   external x2, triple and internal candidates. No multi/internal entry points to
   the external `_single` rack as an approved configuration.
7. A concise report demonstrates at least one external station from each donor
   family can be reconstructed from the fresh dump and lists any evidence still
   unavailable.

## Test notes

- Build `src/Erenaldi.MunitionsPackage` in Release and retain the existing warning
  policy.
- Launch the current game to the main menu with schema dumping enabled, run
  `tools/check_log.ps1`, and inspect the generated hardpoint/mount records.
- Compare candidate counts and identities against the saved historical schema;
  explain differences rather than forcing old counts.
- Add narrow deterministic tests around transform serialization or coordinate
  conversion if the existing project test structure supports them. Runtime dump
  readback is required even if unit tests pass.
