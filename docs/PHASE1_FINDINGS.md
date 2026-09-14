# Phase 1 Findings

Generated from Nuclear Option 0.34.1 with Blueprinter 2.0.1 and the currently
installed mod set. The complete local reports are written to:

```text
BepInEx\config\Erenaldi.MunitionsPackage\weapon-schema.json
BepInEx\config\Erenaldi.MunitionsPackage\analog-validation.json
```

These generated reports contain game-derived runtime data and are not copied
into the repository.

## Runtime Result

- Plugin `Erenaldi.MunitionsPackage` 0.1.0 loaded successfully.
- The schema dump completed with no plugin exceptions.
- `weapon-schema.json` contains the live weapon catalog, serialized field
  schemas, prefab component inventories, and aircraft hardpoint mappings.
- `analog-validation.json` distinguishes rack variants from materially
  different projectile definitions and records a preferred candidate without
  silently treating alternatives as equivalent.

## Analog Validation

Resolved to one projectile definition despite multiple rack variants:

- MMR-S3 (`AAM1_single` preferred)
- AGM-99 (`AShM2_internal_single` preferred)
- AGM-48 (`AGM1_single` preferred)
- GPO-2P Auger (`bomb_penetrator1_doubleP` preferred)
- AGR-18 Lynchpin (`RocketPod1_single` preferred)
- ALND-4 (`CruiseMissile20kt_internalx2` preferred)
- ALM-C450 (`CruiseMissile1_cargox16` preferred)
- Tusko-B (`AShM3_single` preferred)
- AShM3 internal label (`AShM3_single` preferred)

Multiple projectile definitions require review before cloning:

- AAM-36 Scimitar: `AAM4` and `P_AAM2`
- AAM-29 Scythe: `AAM2` and `P_AAM1`
- AGM-68: `AGM_heavy` and `P_KEM1`
- ARAD-116: `ARM1`, `ARM1_cluster`, and `ARM1_mini`
- Demolition Bomb: `bomb_demolition` and `bomb_demo_mini`
- Piledriver TBM: unitary and MIRV projectile definitions
- AShM-300: `AShM1` and `P_HAsM1`

Missing:

- `AShM-200` has no live weapon, mount, short name, or projectile match.

The `P_` alternatives and specialized variants may come from installed mods.
The preferred non-`P_`, non-cluster, non-nuclear candidates are reported for
inspection, but Phase 1 does not assume provenance.

## Capability Gates

- AAM-29's preferred `AAM2` projectile has one `ARHSeeker`. No dual-seeker
  definition was observed, so a dual-seeker weapon would require code; no
  dual-seeker weapon remains on the roster.
- Radar-signature tuning exists on `WeaponMount.RCS`,
  `WeaponMount.emptyRCS`, and `Unit.RCS`. Decompiled runtime flow confirms the
  flying missile copies `MissileDefinition.radarSize` into `Unit.RCS`; mount RCS
  affects only the carrier. RDM-9 now uses `radarSize = 1.0` plus a narrowly
  scoped lock-free intercept-priority patch. An IADS-HARD firing test on
  2026-09-14 confirmed a SAM engages the untargeted decoy; practical range,
  harmless termination, designated-target behavior, and multiplayer remain
  unverified.
- AGR-18 exposes `LaserSeeker.errorRate`; no dedicated salvo-dispersion field
  was found. Hailstorm needs a firing test before deciding whether this field
  alone produces the requested footprint.
- No water-phase missile field or component was found. The only relevant live
  serialized fields were buoyancy on `AeroPart` and a gun water-impact effect.
  Halcyon therefore requires the planned physics/networking spike.
- Ship/air-defense behavior (`antiMissile`/`DefendWithMissiles`) and the
  countermeasure manager are the reference implementations for the HKP-1
  Palisade hard-kill system. They were inspected before the Phase 4 functional
  clone; current findings are in `docs/PALISADE_FINDINGS.md`.

## Decisions Recorded

1. Ambiguous mappings prefer role-aligned variants: `AAM4` (Halberd, switched
   from `P_AAM2`), `P_KEM1`, `ARM1_mini`, `bomb_demo_mini`, and the Piledriver
   MIRV substrate for Trebuchet [C]. Trebuchet [U] remains unitary.
2. Hailstorm starts with a definition-only `LaserSeeker.errorRate` test and
   receives custom salvo dispersion only if it misses the specified footprint.
3. MAD-2 Thistle, AShM-150 Kestrel, and AShM-450 Maelstrom were cut from the
   roster; the missing-`AShM-200` analog finding no longer blocks any weapon.
4. HKP-1 Palisade uses RAM-45 as its interceptor substrate and the vanilla
   ship anti-missile defense pipeline as its guidance reference.

Blueprinter reports no loaded bundles and no external weapon-pack plugin is
currently installed, yet these variants remain in the live encyclopedia. Their
base-game/addressable provenance must be confirmed during asset export; no
NOMM dependency should be declared without that evidence.
