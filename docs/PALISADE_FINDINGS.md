# Palisade Findings — Vanilla Anti-Missile and Countermeasure Systems

Evidence from the decompiled game source (`ilspycmd` output; game 0.34.2).
These findings define the HKP-1 Palisade implementation approach and the
Vesper jamming-module reference.

## 1. Vanilla anti-missile defense pipeline

Capability is data-driven. A weapon station engages missiles when
`WeaponInfo.effectiveness.antiMissile > 0`; engagement constraints come from
`WeaponInfo.targetRequirements` (`minRange`, `maxRange`, `minAlignment`,
`lineOfSight`).

Reference engagement logic — `AIHeloTransportState.DefendWithMissiles()`:

1. Bail if no target, `radarAlt < 10`, weapon is bomb/gun/cargo, target
   outside the range window, or station ammo is 0.
2. Line-of-sight check (cached, re-run at most every 1 s) and a 30-degree
   nose-alignment cone.
3. Compare `TrackingInfo.missileAttacks` (network-tracked per-target attack
   accounting) against `WeaponInfo.CalcAttacksNeeded(target)` to avoid
   over-committing rounds.
4. Refire cooldown of 2.5 s; require `!WeaponStation.SalvoInProgress`.
5. Enumerate threats with `CombatAI.LookForMissileTargets(...)`; fire if it
   returns any targets.

`CombatAI.LookForMissileTargets(aircraft, currentTarget, weaponStation,
outTargets)` (CombatAI.cs:176) is the reusable threat enumerator:

- Searches `BattlefieldGrid.GetUnitsInRange` around the target's known
  position, filters hostile alignment (`minAlignment`), opportunity
  (`AnalyzeTarget(...).opportunity > 0`), tracking consistency, `maxRange`,
  and optional line of sight.
- Deduplicates via `TrackingInfo.missileAttacks` so multiple platforms do not
  over-commit to the same target.
- Missile-specific threat math already exists: `Missile.InterceptPriority(...)`
  and `GetWeaponInfo().GetMaxSpeed() * 0.67f` scaling inside `AnalyzeTarget`.

Palisade borrows the commit guards from this pattern, but does not call
`CombatAI.LookForMissileTargets`: that method searches around an AI-selected
target and interprets smaller `minAlignment` as a narrower forward cone. The
pod instead reads `MissileWarning.knownMissiles` directly and configures its
station for ~0.3-4 km, 180-degree alignment, and no weapon-level line-of-sight
requirement.

## 2. Threat feed — MissileWarning (MissileWarning.cs)

Per-aircraft `MissileWarning : MonoBehaviour`:

- Tracks only missiles with `missile.targetID == aircraft.persistentID` —
  i.e., munitions actually targeted at the carrier. This matches the Max
  Coverage requirement exactly.
- Detection window: default `detectionRange = 5000` m plus line of sight, or
  tracked contacts with `seekerMode < 3`.
- Public API: `knownMissiles`, `IsWarning()`, `TryGetNearestIncoming(out
  Missile)`, and events `onMissileWarning` / `offMissileWarning`.
- Threat classification: `Missile.GetSeekerType()` returns the seeker-type
  string ("IR", "ARH", "SARH" observed); closure/time-to-impact is computed
  from positions and `GetWeaponInfo().GetMaxSpeed()`.

Smart Engage inputs therefore resolve entirely from existing state: threat
list (MissileWarning), seeker type (GetSeekerType), time-to-impact (closure
geometry), CM resources (below), and `TrackingInfo.missileAttacks`.

## 3. Countermeasure architecture — Palisade UI host

`Countermeasure : MonoBehaviour` (abstract) fields: `displayName`,
`displayImage`, `chargeable`, `ammo`, `threatTypes`, `aircraft`. It
self-registers into `aircraft.countermeasureManager` on `Awake()` or
`AttachToUnit()`, and deregisters on `OnDestroy()`.

`CountermeasureManager` groups stations by `displayName`, sorts them by name,
and provides:

- `NextCountermeasure()` — cycles `activeIndex` (the Next CM control).
- `DeployCountermeasure(aircraft)` — calls the active station's
  `Countermeasure.Fire()`; `activeIndex == byte.MaxValue` means none.
- `ChooseCountermeasure(Missile)` — AI auto-selection: picks the first
  station whose `threatTypes` contains the incoming missile's seeker type.
- `Rearm(RearmEventArgs)` — re-arms every station (landing rearm restores
  interceptors automatically).
- HUD: `CombatHUD.DisplayCountermeasureAmmo(ammo)` and per-station
  `UpdateHUD()`; `CountermeasureIndicator` renders the active station.

Palisade integration design — no Harmony patch on the manager is required:

- Implement `PalisadeCountermeasure : Countermeasure` on the pod.
- `displayName = "Palisade"` so it appears as its own CM-menu station;
  station ordering keeps flares at index 0 (flares sort before "Palisade"),
  preserving `GetFlareAmmoProportion()` semantics.
- `threatTypes = { "MISSILE" }` — a type no seeker uses, so
  `ChooseCountermeasure` never auto-selects Palisade for IR/ARH/SARH threats;
  the pod's own logic decides engagement.
- `chargeable = true` so `DeployCountermeasure()` does not trigger
  `RequestRearm()` on a mode cycle.
- `ammo = 4` (interceptor rounds); the CM HUD displays the count natively.
- **Mode cycling lives in the `Fire()` override**: each Deploy CM press while
  Palisade is active cycles Safe → Smart Engage → Max Coverage → Safe.
  `UpdateHUD()` displays the current mode name.
- Auto-engagement runs in a separate pod component (not `Fire()`). It fires the
  cloned pod's existing `MountedMissile` children through the vanilla station
  path, which sets the interceptor target and preserves server spawn authority,
  client commands, remote launch visuals, ammo, and rearm behavior.

## 4. Capacitor / power — RadarJammer reference

`Countermeasure.chargeable` is only a rearm-suppression flag; the actual
energy system is `PowerSupply`:

- `aircraft.GetPowerSupply()` exposes `DrawPower(powerUsage)`,
  `ModifyCapacitance(capacitance)`, `AddUser()` / `RemoveUser()`.
- `RadarJammer : Countermeasure` is the vanilla energy-based CM reference:
  it registers a capacitance contribution, draws power on `Fire()`, scales
  effect by delivered power (`jammingIntensity * num / powerUsage`), and adds
  ECM intensity to the aircraft via `aircraft.AddECMIntensity(...)`.
- Smart Engage's "capacitor reserves inadequate" check reads the
  `PowerSupply` state; Vesper's jamming module reuses the RadarJammer
  pattern (capacitance contribution + power draw + `AddECMIntensity`).
- Flare/chaff adequacy reads per-station `ammo` from
  `CountermeasureManager` stations (flares are station 0).

## 5. Implementation result and open runtime gates (2026-09-14)

- Functional pod source is `AGM2_6Pod`, reduced from six to four
  `MountedMissile` children. The mount is marked `countermeasure`; dormant
  activation is handled by `HardpointSpawnMountPatch`.
- Player-aircraft decisions run on the owning client; AI decisions run on the
  server. The vanilla `MountedMissile` command/RPC path owns network spawning.
- RAM-45 is SARH. The first spike removes its long launch delays and widens its
  seeker, but Ifrit and Medusa must prove carrier illumination against
  missile-sized targets. Failure triggers a self-contained ARH conversion.
- Default whitelist keys are `Multirole1` and `EW1`. A set must also contain a
  compatible pod anchor (`Rocket2_4Pod` or `JammingPod1`); main-menu registration
  found four eligible sets.
- Multiplayer must verify one launch per decision, remote visibility, mode/ammo
  consistency, and rearm. Custom 1.8 m four-door pod and 1.2 m interceptor
  geometry remains gated on functional approval.
- `WeaponInfo.hideInDisplay` has no reader in the 0.34.2 game assembly.
  Palisade therefore marks its interceptor hidden and patches manual station
  initialization/cycling/fire to skip hidden stations while retaining the
  station and its network index for direct automatic `LaunchMount` calls.
- Rack activation reasserts the Palisade countermeasure/defense attachment and
  logs its runtime mode. State-change diagnostics expose the first authority,
  mode, warning, envelope, readiness, assignment, radar, or launch gate that
  prevents an engagement.
- Flight evidence at 20:xx on 2026-09-14 showed two equipped racks attaching
  and cycling to Max Coverage, followed by both defenses reporting no
  countermeasure component. Mounted racks are not reliably descendants of the
  aircraft root, so Palisade now registers each rack explicitly against its
  `Aircraft` instance. The registry elects one coordinator, pools the shared
  weapon-station ammo without double-counting the countermeasure HUD, and
  removes preview/sortie entries when racks are destroyed.
- The next flight reached Max Coverage assessment but rejected a Scythe at
  3,938 m as unreachable. The old gate compared impact time against
  `distance / interceptorSpeed`, incorrectly treating the incoming threat as
  stationary. Palisade now solves the constant-speed relative-motion
  interception quadratic, compares that intercept time against impact time,
  and logs TTI, intercept time, closure, and interceptor speed on rejection.

## 6. Approved interceptor sequence and control authority (2026-09-14)

User approved the following on 2026-09-14:

- **Pitch/yaw snap-turn (not axial roll):** the interceptor snaps toward the SARH-owned aimpoint using pitch and yaw only; axial roll is not used for the snap maneuver.
- **Alignment-gated cap release:** after at least 0.1 s of snap-turning, the detachable cap releases when the interceptor is within 5 degrees and below 60 deg/s angular rate; a 0.55 s timeout forces the handoff if it cannot settle.
- **Full sequence:**
  1. **0.2 s controller-applied axial ejection** — the interceptor is pushed out along its launch axis.
  2. **Snap-turn toward SARH-owned aimpoint** — pitch/yaw rotation aligns the interceptor with the seeker's target.
  3. **Cap release** — detachable cap releases once the alignment gate is met (<=5°, <=60°/s, >=0.1 s or 0.55 s timeout).
  4. **RAM-45 motor 1 ignition** — 18 kN thrust, 2.0 s burn, 15 kg propellant, 1,050 m/s speed ceiling, with 35-degree TVC capped at 35 G and a 0.2 s ramp.
- **RAM-45 motor 0:** retains its nonzero 0.1 N, 0.01 s, 0.01 kg placeholder profile so vanilla delta-V/range calculation never divides zero fuel by a zero burn rate; it advances immediately after cap release.
- **Local-authority torque limits:** maximum 60 rad/s² and 720°/s.
- **Vanilla steering/aero:** suppressed only during pre-ignition phases; SARH Seek continues throughout.
- **Remote missile rotation:** velocity-derived and not synchronized across peers, so sub-second snap rotation and cap timing can differ visually; physics forces are LocalSim-only.

## 7. Geometry candidate status

The HKP-1 Palisade interceptor CAD candidate is **Gate-2 only** — it is a design-review artifact, not an approved Unity asset.

- **Candidate files** under `cad/`: `palisade_geometry.py`, generate/check/review/snapshot scripts, `HKP-1_Palisade_Interceptor.step`, separated review STEP, 10 PNG review views, and `Palisade_Review.png`.
- **Candidate dimensions:** centered X −600…600 mm, body radius 70 mm, near-hemisphere nose 70 mm long, cap 170 mm long, four diagonal tiny fins, four cardinal hollow cap nozzles, recessed main nozzle.
- **Validation:** 11 valid closed solids, exact 1200 mm length, radial envelope ≤85 mm, symmetry/contact/no-intersection/nozzle probe checks pass.
- **Main-agent visual review:** found no remaining asymmetry, collision, or blocked opening; the silhouette reads as requested.
- **User approval is required** before Unity export, prefab creation, or bundle generation.
