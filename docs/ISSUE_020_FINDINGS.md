# Issue 020 findings — physical hardpoint dump and donor reconstruction

2026-09-28. Numbers below were re-derived from the fresh dump on disk (run 2) unless marked "from draft".

## Provenance
- Game: Steam `appmanifest_2168680.acf` buildid 24724372. The dump header `gameVersion` is the stale QoL string and is not the game version.
- Dump: `weapon-schema.json`, `generatedUtc` 2026-09-28T23:14:32.3199053Z, 18,970,411 bytes, SHA-256 `abbf970b373d92414343b8c19ca96e9be70b738629cd7b6683e0939f35cf46ca`. Poses are named `{x,y,z}` / `{x,y,z,w}` objects; a scan found no remaining numeric 3/4-element arrays under `aircraftHardpoints`.
- Plugin DLL SHA-256 (build = installed): `459e965e6cf243db4874f042b4053b608e37614462b3c952933d2a13e15b70ae`.
- Counts: 14 aircraft, 78 hardpoint sets, 114 physical hardpoints, 0 serialization errors, 769 door/bay/gear candidates, 332 weapon mounts, 974 MountedMissile records.
- Donor set counts (exact option-key match): AAM4_single 6, AAM1_single 17, AGM1_single 9, AGM_heavy_single 11.
- Run 1 vs run 2 (both after this build): the only difference is `generatedUtc`.

## Reconstruction method
missile pose (aircraft-root space) = hardpoint `rootRelativeTransform` ∘ mount hierarchy chain (each node's `localPosition` scaled by accumulated ancestor scale, rotations composed) ∘ MountedMissile node.
Inputs: `rootRelativeTransform` of the physical hardpoint, mount prefab `transforms[]`, `mountedMissiles[].localPose`. This assumes the mount spawns at the hardpoint transform with identity offset; the dump does not prove that.

## One external station per donor family
Positions: aircraft-root space, metres. Quaternions (x, y, z, w). Hardpoint root pose re-read from the dump; mount-local offsets re-read and the arithmetic re-checked; final missile positions are from the draft.

| Donor | Aircraft / set | Hardpoint root pos | Hardpoint root rot | Mount-local missile offset | Reconstructed missile pos | Missile rot |
|---|---|---|---|---|---|---|
| AAM4_single (Halberd) | Fighter1 set 2 Wing Pylons | (-3.58263, -0.72261, 0.48296) | identity | (0, -0.287, 0.187) | (-3.58263, -1.00961, 0.66996) | identity |
| AAM1_single (Kris) | AttackHelo1 set 3 Left Stub Tip Pylon | (-3.331, -0.696, -0.053) | (-0.008726, 0, 0, 0.999962) | (0, -0.2114, 0.134) | (-3.331, -0.90503, 0.08467) | (-0.008726, 0, 0, 0.999962) |
| AGM1_single (Phantom) | COIN set 2 Fuselage Pylons | (-0.983, -0.98726, 0.66447) | (0, 0, -0.271482, 0.962443) | (0, -0.219, 0.006783) | (-1.09744, -1.17398, 0.67125) | (0, 0, -0.271482, 0.962443) |
| AGM_heavy_single (Ballista) | CAS1 set 2 Inner Fuselage Pylons | (-0.412885, -1.223, 0.1) | (0.022687, 0, 0, 0.999743) | (0, -0.309, 0.006783) | (-0.412885, -1.53199, 0.092759) | (0.022687, 0, 0, 0.999743) |

Mount chains (local position, scale where not 1):
- AAM4_single: `pylon` (0,-0.083,0) → `aam4` (0,-0.204,0.187).
- AAM1_single: `pylon` (0,-0.08,0.134) scale (0.67,0.9,0.8) → `aam1` (0,-0.146,0) scale (1.4925,1.1111,1.25).
- AGM1_single: `pylon` (0,-0.074,0) scale (0.9,0.8,0.7) → `agm1` (0,-0.18125,0.00969) scale (1.1111,1.25,1.4286).
- AGM_heavy_single: `pylon` (0,-0.094,0) and `agm1` (0,-0.309,0.006783) are siblings, so the pylon offset does not enter the missile chain.

MountedMissile rail data: `railLength`, `railSpeed`, `railDelay` and `railVector` are 0 for all four; `railDirection` is Forward except AAM1_single = Down.

## Unresolved evidence (unmeasured)
- Static clearance between pylon/store and airframe, ground, wing.
- Neighbouring stores on the same and adjacent sets.
- Door/bay/gear relationships: the 769 candidates are name-heuristic only; no per-hardpoint association is asserted; door sweep, bay animation and gear travel are unmeasured.
- Release travel/trajectory (rail data is zero for all donors, so it says nothing about clearance).
- Actual fit of any custom rack. Nothing is approved.
- The mount-spawns-at-hardpoint-transform assumption is not validated in game.
- Hardpoint `rootRelativeTransform` scale is a lossy ratio; it is 1 in all sampled stations. Fighter1 reports 0 colliders.
