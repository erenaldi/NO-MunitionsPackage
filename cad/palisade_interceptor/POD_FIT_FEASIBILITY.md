# Palisade interceptor versus pod — preliminary fit boundary

Date: 2026-09-27. State: `blocked` for **actual donor-station clearance**.
The user-approved interceptor visual study is
`STEP/Spear_ACMWrap.step`; the pod visual master has not been selected.
This report evaluates a conservative geometric envelope and the currently
saved donor/runtime evidence. It does not certify an AGM2_6Pod installation.

## Observed constraints

- `MUNITIONS.md` §12 historically proposes a **1,800 × 400 mm boxy pod**
  and four 35 kg rounds, but the alignment interview explicitly made pod
  envelope and capacity revisitable. No custom Palisade pod CAD exists.
- `reviews/spear_pod_envelope_feasibility.json` reads the approved 199-part
  STEP and measures **1,200 mm** axial length, **79.006 mm** maximum radial
  envelope (conservative **158.013 mm** circular cell diameter). The drawn
  barrel/cap alone is 109.12 mm diameter; fins set the maximum.
- `src/Erenaldi.MunitionsPackage/PalisadeCloner.cs:210-229` clones the vanilla
  `AGM2_6Pod` rack and destroys its last two `MountedMissile` child objects.
  It does not relocate the remaining four stations or build four new cells.
  The saved 2026-09-15 schema dump at
  `<Game>/BepInEx/config/Erenaldi.MunitionsPackage/weapon-schema.json`
  confirms **four** remaining mounted missiles paired with doors **1, 4,
  2, 5**, while the mount prefab retains six `door1`–`door6` objects. The
  Transform serialization includes hierarchy paths but **not local position,
  rotation or scale**, so the real cell centers cannot be measured from that
  dump. The six-door donor visual is not the proposed four-door final pod.
- The geometry dump at the same config path is of
  `mount.info.weaponPrefab`, not `WeaponMount.prefab`: for `AGM2_6Pod`
  it names projectile `AGM2` (mesh bounds ~369 mm transverse, 1469 mm
  axial), and for Palisade it names the untransplanted RAM-45-derived
  interceptor mesh (~523 mm transverse, 2924 mm axial). These are donor
  **local mesh** dimensions; the pod renderer, instantiated missile scales,
  door sweep and station locations are absent. The weapon definition's
  `width`/`height` is still 140 mm in `PalisadeCloner.cs:22-23,87-90`, below
  the approved CAD's 158 mm fin envelope. Metadata and runtime donor mesh
  do not establish loaded visual clearance.

## Reversible four-round envelope study

`checks/check_pod_envelope.py` passed against the saved CAD artifact and
records the following *illustrative*, not user-approved layout assumptions:

| Study case | Result |
|---|---|
| Pod length 1800 mm, round length 1200 mm | **600 mm total axial budget** before forward/aft structure. |
| Box outer section 400×400 mm, wall 10 mm, four circular cells at (Y,Z)=(±90,±90) mm | Envelope edge leaves **20.994 mm** inside clearance per outer wall. |
| Same 2×2 centers, circular 158.013 mm round envelopes | Adjacent edges remain **21.987 mm** apart, or **11.987 mm** beyond an illustrative 10 mm divider. |
| 400 mm **circular** outer shell with 10 mm wall at those centers | Fails: radial outer clearance **−16.286 mm**; with those illustrative wall/divider allowances it needs ~**415.618 mm** outer diameter. |

The box calculation demonstrates *a possible arrangement* for the visual
brief, not that the cloned six-door rack implements it. Its protective
circle allows any roll of the fin geometry; doors, hinges, ejection path,
pylon, wall thickness, aircraft hardpoint clearance and two-pod stacking
are not represented. A different spacing or wall scheme changes the numbers.

## Exact next evidence and gate

1. Obtain the runtime `AGM2_6Pod` prefab's six `MountedMissile` local poses,
   rotations/scales, missile attachment transforms, pod exterior and collider
   bounds, door meshes/hinges and opening sweeps, and the pruned Palisade
   rack's corresponding four local poses. The current dump cannot answer
   these questions; any probe must identify the *rack prefab*, not the
   `WeaponInfo` projectile prefab.
2. Compare the approved STEP in the correct Unity axis/pivot frame to those
   actual transforms, checking a stowed four-cell state and the ejection/
   cap-release path. The as-cloned six-door geometry will require a conscious
   four-door visual/hierarchy design if it cannot be adapted without broken
   doors. Source-level authority remains `MUNITIONS.md` §12; do not change
   missile or pod metadata just to make a hypothetical study pass.
3. If the historical 400 mm box and four rounds are retained, choose the
   actual pod cross-section/cell layout and obtain user concept approval
   before detailed pod CAD. A fit-driven change to the selected interceptor
   exterior reopens its visual approval; rearranging pod cells alone does not.
