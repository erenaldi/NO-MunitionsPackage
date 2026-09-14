# V1 Implementation Plan

Execution roadmap for the 15-weapon V1 roster defined in `MUNITIONS.md`.
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
| RDM-9 Phantom | L05 | pending (def + signature verification) |
| GPO-2R Auger | L06 | pending (def) |
| CDM-4 Bramble | L07 | pending (submunition engine) |
| AGR-30 Hailstorm | L08 | pending (def-first dispersion test) |
| ALM-5 Vesper | L09 | pending (jamming module) |
| Tusko-D | L10 | pending (def) |
| ALBM-3 Trebuchet [U] | L11 | pending (def + air-launch integration) |
| ALBM-3 Trebuchet [C] | L12 | pending (shared submunition engine) |
| TOR-42 Halcyon | L13 | blocked on water-phase spike |
| RAT-44 Barracuda | L14 | blocked on water-phase spike |
| HKP-1 Palisade | L15 | pending — findings complete, ready to implement |

## Phase order

1. **HKP-1 Palisade** (next up; detailed below — findings are complete).
2. Def-tuned batch: ARAD-80 (runtime validation only), RDM-9 Phantom (with the RCS runtime test),
   GPO-2R Auger, Tusko-D, Trebuchet [U].
3. Submunition engine: CDM-4 Bramble, then Trebuchet [C].
4. Hailstorm dispersion test (`LaserSeeker.errorRate` def-first; salvo code
   only if the footprint misses).
5. Jamming module (Vesper; `RadarJammer`/`PowerSupply` pattern per
   `PALISADE_FINDINGS.md` §4).
6. Water-phase spike: TOR-42 Halcyon, then RAT-44 Barracuda; fallback is the
   waterline skipper.
7. Proving-ground validation pass over all lanes; role tests per
   `docs/PROVING_GROUND.md`.

## HKP-1 Palisade — implementation plan

All vanilla-system evidence is in `docs/PALISADE_FINDINGS.md`; spec is
`MUNITIONS.md` §15; test lane L15 (IADS-HARD).

### Components

1. `PalisadeCountermeasure : Countermeasure` (pod component):
   - `displayName = "Palisade"`, `ammo = 4`, `chargeable = true`,
     `threatTypes = { "MISSILE" }` (never auto-selected by
     `ChooseCountermeasure`; flares stay station 0).
   - `Fire()` override cycles Safe → Smart Engage → Max Coverage → Safe
     (Deploy CM press while Palisade is active); `UpdateHUD()` displays the
     mode name; mode persists per sortie, spawns Safe.
   - Auto-registers via `Awake()`/`AttachToUnit()`; `Rearm()` restores
     interceptors on landing rearm (manager handles it).
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
   - Commit guards per `DefendWithMissiles` reference: range window, ammo,
     refire cooldown, `TrackingInfo.missileAttacks` accounting.
3. Interceptor def: clone **RAM-45** substrate → `Erenaldi.HKP1_int`
   micro-missile (1.2 m dart, Mach 3+, ~35 G, proximity HE-frag,
   `effectiveness.antiMissile > 0`, `targetRequirements` ~0.3-4 km, small
   `minAlignment`, no `lineOfSight`).
4. Pod: gun-pod/AGR-31-style station clone carrying the two components;
   launcher doors visual per `MUNITIONS.md` §15.
5. Platform whitelist: KR-67 Ifrit, EW-25 Medusa + BepInEx config entries for
   modded heavies; station availability patched for whitelisted airframes
   only (`HardpointSpawnMountPatch` integration).

### Config (BepInEx, `Phase 3` group)

Spawn mode (Safe default), engagement envelope ranges (Smart/Max), refire
cooldown, re-engage clearance threshold, rounds per pod, platform whitelist.

### Networking / open items

- Host-authoritative interceptor launches (match Mirage conventions used by
  the existing cloners); confirm remote CM-menu state via
  `Aircraft.Countermeasures(active, index)`.
- Lock-free launch path for the interceptor def (no seeker warm-up gate).
- Remote mode display: `UpdateHUD()` runs on the local aircraft only; verify
  what remote peers see and whether a minimal sync is required.

### Verification (lane L15, IADS-HARD)

- Mode states: Safe inhibits all launches; Smart Engage withholds fire while
  flares/jammer suffice and fires when they do not (flare-depleted and
  capacitor-depleted cases); Max engages everything reachable and
  re-engages after a failed intercept.
- CM HUD shows Palisade station, mode name, and live ammo; Deploy cycles
  modes; Next CM skips past it correctly; rearm restores 4 rounds.
- Saturation counterplay: a two-missile salvo defeats a single pod (one
  round per target at a time), four rounds exhaust, rearm restores.
- Radar SAM (IADS-HARD) launches at the carrier with Palisade Safe vs Smart
  vs Max; log engagement decisions for tuning.
