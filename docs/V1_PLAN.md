# V1 Implementation Plan

Execution roadmap for the 12-weapon V1 roster defined in `MUNITIONS.md`
(GPO-2R Auger, CDM-4 Bramble, and AGR-30 Hailstorm are deferred to a possible
later release; specs preserved in `MUNITIONS.md` § Deferred).
Design authority for specs and analog decisions is `MUNITIONS.md`; runtime
findings live in `docs/PHASE1_FINDINGS.md` and `docs/PALISADE_FINDINGS.md`;
per-weapon test status is tracked in
`missions/Erenaldi.ProvingGround/lane-manifest.json`.

## Status

| Weapon | Lane | Status |
|---|---|---|
| AAM-44 Halberd | L01 | implemented (cloner, motor patch, booster jettison) |
| IRM-S4 Kris | L02 | implemented (full stack incl. IRCCM, TVC, custom geometry) |
| AGM-110 Ballista | L03 | implemented (cloner, wing fold) |
| ARAD-80 | L04 | implemented (cloner, single-burn motor) — runtime validation pending |
| RDM-9 Phantom | L05 | implemented; untargeted SAM engagement passed — range/lifetime/multiplayer gates pending |
| ALM-5 Vesper | L06 | pending (jamming module) |
| Tusko-D | L07 | pending (def) |
| ALBM-3 Trebuchet [U] | L08 | pending (def + air-launch integration) |
| ALBM-3 Trebuchet [C] | L09 | pending (shared submunition engine) |
| TOR-42 Halcyon | L10 | blocked on water-phase spike |
| RAT-44 Barracuda | L11 | blocked on water-phase spike |
| HKP-1 Palisade | L12 | functional clone registered — SARH/interception and multiplayer validation pending; geometry candidate Gate-2 only |

## Phase order

1. **HKP-1 Palisade runtime gates** (SARH viability, mode/HUD, interception, rearm, and multiplayer).
2. Def-tuned batch: ARAD-80 and RDM-9 Phantom (runtime validation only),
   Tusko-D, Trebuchet [U].
3. Submunition engine: Trebuchet [C].
4. Jamming module (Vesper; `RadarJammer`/`PowerSupply` pattern per
   `PALISADE_FINDINGS.md` §4).
5. Water-phase spike: TOR-42 Halcyon, then RAT-44 Barracuda; fallback is the
   waterline skipper.
6. Proving-ground validation pass over all lanes; role tests per
   `docs/PROVING_GROUND.md`.

## HKP-1 Palisade — implementation plan

All vanilla-system evidence is in `docs/PALISADE_FINDINGS.md`; spec is
`MUNITIONS.md` §12; test lane L12 (IADS-HARD).

### Components

1. `PalisadeCountermeasure : Countermeasure` (pod component):
   - `displayName = "Palisade"`, `ammo = 4`, `chargeable = true`,
     `threatTypes = { "MISSILE" }` (never auto-selected by
     `ChooseCountermeasure`; flares stay station 0).
   - `Fire()` override cycles Safe → Smart Engage → Max Coverage → Safe
     (Deploy CM press while Palisade is active); `UpdateHUD()` displays the
     mode name; mode persists per sortie, spawns Safe.
   - Registers through `Hardpoint.SpawnMount`/`AttachToUnit()`; its `Awake()`
     deliberately does not register a second time. HUD ammo mirrors the actual
     interceptor weapon station after launch and rearm.
2. `PalisadeDefense : MonoBehaviour` (pod component — auto-engage logic):
   - Threat feed: `MissileWarning.knownMissiles` / `onMissileWarning`
     (already filtered to missiles targeting the carrier).
   - Classification: `Missile.GetSeekerType()`, closure/time-to-impact from
     positions and `GetWeaponInfo().GetMaxSpeed()`.
   - Smart Engage: fire only when normal CMs cannot defeat the threat in
     time, would take too long (CM cycle vs time-to-impact), or flare
     (station ammo) / capacitor (`PowerSupply`) reserves are inadequate;
     1 interceptor per qualifying threat.
   - Max Coverage: engage every threat with a kinematic intercept solution;
     1 interceptor at a time from max intercept range; re-engage on failure
     (threat survives the clearance threshold with TTI above minimum
     interceptor flight time).
   - Commit guards borrowed from `DefendWithMissiles`: range window, closure,
     kinematic time-to-intercept, ammo, refire/clearance cooldown, and
     `TrackingInfo.missileAttacks` accounting. Threat enumeration comes directly
     from `MissileWarning`; `CombatAI.LookForMissileTargets` is not suitable for
     an omnidirectional aircraft pod.
3. Interceptor def: clone **RAM-45** substrate → `Erenaldi.HKP1_int`
   micro-missile (1.2 m dart, Mach 3+, ~35 G, proximity HE-frag,
   `effectiveness.antiMissile > 0`, `targetRequirements` ~0.3-4 km,
   `minAlignment` 180 degrees, no weapon-level `lineOfSight`). The staged
   controller applies 0.2 s housing ejection, a bounded pitch/yaw snap-turn
   toward the SARH aimpoint, alignment-gated turning-cap release, and a 2.0 s
   high-authority TVC main burn. SARH seeking remains active throughout; vanilla
   steering and aerodynamics are suppressed only before main-motor ignition.
4. Pod: `AGM2_6Pod` clone reduced to four `MountedMissile` children and carrying
   the two Palisade components; custom four-door geometry follows functional approval.
5. Platform whitelist: KR-67 Ifrit, EW-25 Medusa + BepInEx config entries for
   modded heavies; station availability patched for whitelisted airframes
   only (`HardpointSpawnMountPatch` integration).

The first CAD silhouette candidate is Gate 2 only: centered 1,200 mm length,
140 mm body diameter, 170 mm turning cap, four tiny diagonal stabilizers, four
cardinal hollow cap nozzles, and an exposed recessed main nozzle after separation.
Unity export, prefab creation, and bundle integration remain gated on user approval.

### Config (BepInEx, `Phase 4` group)

Spawn mode (Safe default), engagement envelope ranges (Smart/Max), refire
cooldown, re-engage clearance threshold, rounds per pod, platform whitelist.

### Networking / open items

- Player-aircraft engagement decisions run only on the owning client and launch
  through `MountedMissile.Fire`/`CmdLaunchMissile`; server-controlled AI decides
  on the server. This avoids duplicate server-and-owner launches while retaining
  vanilla server spawn authority and remote launch RPCs.
- Mode HUD is local-only. Multiplayer must still verify mode/ammo consistency,
  remote interceptor visibility, and exactly one launch per engagement.

### Verification (lane L12, IADS-HARD)

- Mode states: Safe inhibits all launches; Smart Engage withholds fire while
  flares/jammer suffice and fires when they do not (flare-depleted and
  capacitor-depleted cases); Max engages everything reachable and
  re-engages after a failed intercept.
- CM HUD shows Palisade station, mode name, and live ammo; Deploy cycles
  modes; Next CM cycles through it correctly; rearm restores 4 rounds.
- Saturation counterplay: a two-missile salvo defeats a single pod (one
  round per target at a time), four rounds exhaust, rearm restores.
- Radar SAM (IADS-HARD) launches at the carrier with Palisade Safe vs Smart
  vs Max; log engagement decisions for tuning.
