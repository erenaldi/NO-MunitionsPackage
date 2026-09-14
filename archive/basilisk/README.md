# AAM-41 Basilisk — Retired Prototype

The AAM-41 Basilisk (dual-seeker IR+ARH air-to-air missile) was cut from the
munitions roster during Phase 2B. The implementation reached runtime
registration and geometry transplant but never achieved validated guidance
behavior, and the roster was reduced to 17 weapons.

This directory preserves the source for reference; nothing in it is built or
shipped.

## Contents

- `src/BasiliskCloner.cs` — runtime clone from `P_AAM1`/`P_AAM1_single`, IR
  tuning from `AAM1`, ARH tuning from `AAM2`, motor/registration pipeline.
- `src/BasiliskSeeker.cs` — composite `MissileSeeker` with sequential
  ARH-first, IR-fallback channel management.
- `src/BasiliskGuidancePatches.cs` — Harmony patches for target retention,
  child-seeker `SlowChecks` suppression, disabled-target cleanup, and
  warning-delivery tracing.
- `cad/generate_basilisk.py` — parametric finless 3.4 m CAD master.
- `cad/AAM41_Basilisk_Onshape_Finned.step` — authoritative finned Onshape
  export (20 parts, nose along CAD `+Y`).
- `cad/export_basilisk_unity_mesh.py` — deterministic STEP→OBJ conversion:
  `(x, y, z) → (x, -z, y)`, 3.4 m → 2.9 m scale, body/seeker/strakes/tail-fin
  grouping.
- `unity/BasiliskMeshBuilder.cs` — Unity prefab/bundle authoring with build
  assertions for length, seam, radius, span, and pivot centering.

## Preserved findings

- No definition-only dual-seeker mechanism exists in Nuclear Option 0.34.2:
  each projectile prefab carries exactly one `MissileSeeker`, so a dual-seeker
  weapon requires code.
- `Missile.Awake` caches `GetComponent<MissileSeeker>()` from the prefab root;
  the composite seeker must be the single root `MissileSeeker` component, with
  vanilla seekers relocated to children.
- Missile warning dispatch flows through `Missile.TargetIDChanged` →
  `Aircraft.LockedByMissile` only when the cached seeker has
  `triggerMissileWarning`; AI reaction then takes a random 1-4 s windup
  (`missileReactTime`), so a missile dying early can look like a missing
  warning.
- Child vanilla seekers run their own `SlowChecks` self-destruct timers that
  compete with composite channel management; they must be suppressed for the
  host missile.
- The extra kinematic self-destruct (`LosingGround`/`MissedTarget`/
  low-speed checks layered on top of vanilla) caused premature detonations
  while the missile was still tracking; vanilla seeker self-destruct logic
  alone is the safer baseline.
- Projectile source and hardpoint compatibility must be chosen independently:
  cloning from `P_AAM1_single` registered against 0 hardpoint sets while
  mirroring `AAM2_single` matched 11; the rack source (`P_AAM1_single`) is not
  a compatibility reference.
- Imported missile geometry must be authored centered on the runtime pivot
  (`z = -length/2..+length/2`); a `z = 0..length` authoring convention offsets
  the visual and collider forward of the physics body, and preserved motor FX
  anchors must be repositioned to the custom tail after transplant.
- Registration, hardpoint integration, geometry transplant, and startup
  validation all passed in-game (indices 545/546, 11 hardpoint sets); what was
  never validated was end-to-end guidance: staged ARH→IR handoff under real
  countermeasures, warning delivery, networking, and self-destruct timing.
