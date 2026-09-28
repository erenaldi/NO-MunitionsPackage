---
id: "025"
title: Deliver Ballista external single pylon and remove unvalidated availability
type: feature
status: blocked
blocked-by: ["022", "023"]
---

## Slice

Deliver Ballista's selected external single ejector rack end-to-end and replace
the current union of AGM-heavy donor mirrors with only validated external-single
rows. This slice makes unsupported internal, x2 and triple availability disappear
unless a later distinct rack program validates those variants.

## Acceptance

1. Detailed rack CAD seats against the authored forward and aft shoe datums,
   clears the complete 322.805 mm stowed envelope and folded-wing mechanism, and
   exposes a coherent heavy ejector/load path.
2. Saved geometry and fit reports validate intended contacts, no unintended
   intersections, aircraft/neighbor clearance and a clean release path on each
   proposed external-single physical station.
3. User CAD approval precedes export. Unity delivery validates source identity,
   scale, mounted offset, materials, colliders, hierarchy and folded display.
4. Ballista no longer adds its external `_single` mount through
   `AGM_heavy_internal*`, `AGM_heavyx2` or `AGM_heavy_triple`. Only approved
   aircraft/set rows are registered.
5. The ledger marks every former internal/multi candidate as deferred, blocked or
   rejected with a reason; none silently aliases the external rack.
6. Runtime evidence covers loadout, folded mounted state, launch separation,
   wing deployment, effects, AI use, save/load and matching-peer multiplayer for
   every enabled external station.

## Test notes

- Preserve Ballista gameplay and wing-motion regression checks.
- Verify registration before and after migration from fresh logs, including that
  no internal or multi-round set receives `Erenaldi.AGM110_single`.
- Test both left/right members of symmetric sets and representative neighboring
  heavy stores.
