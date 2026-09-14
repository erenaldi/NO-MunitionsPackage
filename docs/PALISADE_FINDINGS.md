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

Palisade reuses this pattern; the pod's interceptor station is configured
with `effectiveness.antiMissile > 0` and short-range `targetRequirements`
(~0.3-4 km, small `minAlignment` because the pod launches omnidirectionally,
no `lineOfSight` requirement).

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
- Auto-engagement runs in a separate pod component (not `Fire()`), launching
  cloned interceptor missiles with `targetID` set to the selected threat.

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

## 5. Open items for implementation

- Network authority for engagement decisions: existing weapon code (Halberd/
  Kris cloners) follows Mirage conventions; confirm whether interceptor
  launches are host-authoritative like AI weapon fire.
- Interceptor launch mechanics: spawn the cloned RAM-45-substrate missile
  with `targetID` set to the threat; verify lock-free launch path (no seeker
  warm-up requirement) for the micro-interceptor def.
- Pod prefab: gun-pod/AGR-31-style station clone carrying the
  `PalisadeCountermeasure` + auto-defense components; platform whitelist
  patching per `MUNITIONS.md`.
- Confirm `Aircraft.Countermeasures(active, index)` network behavior for
  remote CM-menu state (mode display on remote peers).
