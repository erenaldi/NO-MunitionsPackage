# MUNITIONS.md — Implementation Handoff Draft
## Global design parameters
- **15 weapons** · 8 def-tuned, 7 code-touched · each munition's initial visual-design pass is geometry-only; later texture, material, color, and marking passes may add any presentation details needed · nukes deferred to v1.1
- **Code systems:** submunitions · jamming (EW-25-style, energy store) · water-phase · HOB/LOAL seekers · salvo dispersion · hard-kill auto-defense
- **Method:** clone vanilla analog def → override fields → register via BepInEx plugin; def-only weapons may alternatively ship as Blueprinter `.nobp` patches (proven by AShM-500 Yashma)
- **Phase 1 gate:** runtime reflection dump validates every def-field mapping below; all numbers are design targets until then

---

### 1. AAM-44 Halberd — medium-range ARH AAM
- Summary: medium-range BVR missile bridging the AAM-29 Scythe and AAM-36 Scimitar; tandem solid-fuel booster (2/5 of length, visually jettisoned) then ramjet-sustained cruise. 22 kg continuous-rod warhead.
- Specs: ~3.37 m × 0.20 m body, 180 kg launch / 95 kg burnout · Mach 3.5 · range at approximately 58% of the Scythe-to-Scimitar gap · active radar, LOAL
- Propulsion: 21 kN / 55 kg booster burns for 6 s and targets Mach 2.5 from a Mach 1 launch at 1 km, then separates as inert local debris; 14 kN / 30 kg sustainer burns for 30 s, ramps its speed ceiling to Mach 3.5 over 10 s, and uses a 0.25 supersonic-drag penalty while powered and after burnout (0.50 during boost). Guidance lofts the aimpoint for a cruise climb (ARH `loftAmount` 0.3, triple the AAM-36's 0.1).
- Impl: clone **AAM-36 Scimitar** (vanilla `AAM4` sources) · def-only + booster-jettison visual (Phase 3B)
- Visual: pointed radar nose with three 120-degree ramp-intake/strake assemblies at 2, 6, and 10 o'clock; dorsal mounting hardware bisects the upper intakes; the sustainer and dark tandem booster carry separate aligned three-fin tails so both stages remain visually complete after separation

### 2. IRM-S4 Kris — high-agility close-range IR
- Summary: 8.5 km dogfight dart, TVC-dominant agility, 72° off-boresight, LOAL with view-slaving, and tracking-suspension IRCCM.
- Specs: 3.1588 m × 0.1580 m (MMR-S3 mesh length scaled up 10%), 146 kg (58.6 kg propellant, 40% fraction) · Mach 3.5 · ~0.489 m maximum deployed span
- Impl: clone **MMR-S3[IR]** · def + HOB/LOAL code (AIM-9X-mod pattern) + J-hook loft guidance (config-tunable: full loft share at 8.5 km, dive inside ~2.55 km, fades vs high targets) + midcourse closing-speed lead and terminal iterative intercept guidance with turn-time/target-acceleration compensation + 3° optical discrimination that ignores flares outside the instantaneous tracking field and fast-separating flares whose predicted exit from the field is shorter than a quarter second under a sweeping (beam-aspect) line of sight, reserving the blind pause for head-on/rear-aspect dispensing; an in-field flare otherwise triggers an inertial processing pause that escalates 0.4 s → 1.0 s across salvos within 4 s of each other, during which guidance keeps steering on a frozen inertial prediction (0.5 s pre-suspension acceleration extrapolation, never re-baselined) whose sensed position additionally wanders with configurable drift (~20 m/√s default, growing with the sqrt of blind time) while the seeker head slews toward the predicted line of sight at 120°/s; reacquisition scores every live source in the slew-limited window by vanilla-style effective intensity (range curve, aircraft front/rear aspect, sun/terrain background), so a sufficiently bright flare decoys the missile into a full flare chase that ends in lock break and gimbal search when the flare burns out
- Visual: slender dart with strakes and four honeycomb lattice fins; CAD source is the Kris/PL-10 hybrid (`IRM-S4_Kris_PL10_Hybrid.step`, PL-10 body with Kris tail lattice and TVC), authored at 1.10x the MMR-S3's 2.871592 m mesh length (3.158751 m) while preserving all radial proportions; the mounted display is rolled 45° so its pylon rail occupies the gap between adjacent strakes with the mount offset solved to hold the authored 9 mm strake clearance at the larger radius; 35° physical/visual TVC, 5x steering authority with authored aero lift/drag curves and retuned PID, external tapered fairing seeker with metal bezel and smaller rounded IR window, no internal optics.
- Propulsion: dual pulse preserving 143.6 kNs and 58.6 kg propellant: 20 kN for 4 s (29.282 kg), coast, then 10.6 kN for 6 s (29.282 kg) — the second pulse's thrust is whatever remains of the impulse budget after pulse one. Pulse two ignites on the first of: range at half the launch distance, or speed below Mach 1.5; a config-selectable Immediate mode instead lights pulse two as pulse one ends for a continuous burn. An unspent pulse still ignites instead of allowing recoverable coast self-destruction.
- Warhead: blast 11 · range 8.5 km · off-boresight 72°.
- Aero: finArea 0.4235, CL curve peaking 2.475 at 45° AoA (CL = 2.475·sin(2α) character; coefficients scaled 1.10x with the enlarged area and mass to hold the authored G envelope), Cd 0.025→0.94 (grid-fin axial relief: the aligned-flight/coast keys below 20° AoA are reduced ~25-28 percent; induced-drag keys above 25° AoA stay authored), supersonic drag multiplier 0.05 (rides on top of the Cd curve, so it moves total supersonic drag by at most ~5%).
- Flight computer: coordinated acceleration-vector controller with a damped attitude-rate servo, dynamic-pressure-derived aerodynamic authority capped at 60 g, 240°/s maximum body rate, and a 35° midcourse commanded-angle limiter that opens to the 72.1° seeker envelope in the terminal phase. TVC adds 70 g during pulse one; with the identical second pulse the same thrust-to-mass ratio keeps full TVC authority through pulse two (about 70 g at 25 kN, tapering with burnoff). Turn-entry acceleration ramps from zero and is limited by predicted body rate plus nose lead so the missile rotates into the rail-exit turn instead of translating sideways. TVC contributes no authority during coast or after final burnout, and both the TVC authority and the terminal commanded-angle envelope ramp in over 0.3 s and 0.5 s respectively across each pulse ignition so the motor transition does not step the guidance.
- J-hook loft: 2762 m / dive 2550 m / blend 3825 m; after pulse two ignites the lofted arc hybridizes with the terminal intercept, tapering to a 40% share over ~2 s before the dive-range taper takes over near the target.

### 3. AGM-110 Ballista — heavy standoff glide AGM
- Summary: 60 km glide with terminal sprint; 400 kg HE, high AP, EO seeker with anti-interception maneuvering (AGM-68 lineage).
- Specs: 4.8 m × ~0.5 m, ~980 kg · high-subsonic glide · 60 km
- Impl: clone **AGM-68/AGM-99 blend** (`P_KEM1`) · def + wing-fold visual code (`BallistaWingFold.cs`)
- Visual: rectangular-section fuselage, folding diamond wings

### 4. ARAD-80 — fast-reaction SEAD
- Summary: 35 km anti-radiation, Mach 3.5, lighter than vanilla ARAD-116; punishes active emitters.
- Specs: 3.6 m × 0.26 m, ~210 kg · Mach 3.5 · 30 kg
- Impl: clone **ARAD-116** (vanilla `ARM1_single`) · def-only clone, no midcourse code: single continuous burn — the full 82 kg charge at 50 kN for 3.76 s (188 kNs = former booster 100 + former pulse 88, same solid chemistry, Isp ~234 s), one boost off the rail to strike active emitters. (2026-09-13: the earlier twin-pulse design was superseded by user decision — see `docs/SESSION_LOG.md`.)
- Visual: slender body, flush antenna window strips

### 5. RDM-9 Phantom — radar decoy missile
- Summary: no warhead; Luneburg lens + active repeater = maximum signature; flies a threat profile to bait SAM shots.
- Specs: 2.8 m × 0.25 m, ~180 kg · Mach 2 burn then glide · 30 km
- Impl: clone **AGM-48** (`AGM1_single` / `AGM1`) · projectile `radarSize` 1.0 while preserving the donor's low carriage RCS · zero blast/pierce and permanently blocked arming · 20 kN / 3.44 s / 30 kg single motor with a 650 m/s ceiling and provisional 60 s harmless termination · Phantom-only `Missile.InterceptPriority` fallback restores priority 1 for untargeted shots without bypassing radar, range, altitude, or intercept-viability gates. (2026-09-14 user decisions: lock-free from first implementation, 30 km envelope, radar size 1.0. IADS-HARD flight test confirmed a SAM engages an untargeted Phantom; practical range, harmless termination, designated-target behavior, and multiplayer remain pending.)
- Visual: unadorned cylinder, round lens housing mid-body

### 6. GPO-2R Auger — rocket-powered penetrator
- Summary: 1.3 t bomb with 4 s rocket boost and terminal dive; AP ~5000 (vs Auger's 3000); delayed burst after penetration.
- Specs: 4.2 m × 0.46 m, ~1,300 kg
- Impl: clone **GPO-2P Auger** · def-only
- Visual: thick body, hardened elongated tip, radial-nozzle tail motor ring

### 7. CDM-4 Bramble — cluster dispenser
- Summary: dispenser opens at preset altitude, scattering ~20 × 30 kg unguided bomblets over a ~200 m footprint.
- Specs: 2.6 m × 0.48 m drum, ~900 kg
- Impl: clone **Demolition Bomb** airframe · **code: submunition engine**
- Visual: drum with longitudinal seams

### 8. AGR-30 Hailstorm — indirect saturation rockets
- Summary: salvo of 4 lofted rockets with sustainer motors, 25-40 km to the designated point, deliberate 300-600 m dispersion — area saturation, no precision.
- Specs: 2.1 m × 0.24 m per rocket, ~340 kg · 30 kg HE-FRAG
- Impl: clone **AGR-18 Lynchpin** airframe · def-first using `LaserSeeker.errorRate`; add code-lite salvo dispersion only if testing misses the 300-600 m footprint
- Visual: fat tube, wraparound fins

### 9. ALM-5 Vesper — high-mach ECM cruise
- Summary: Mach 3.5-4 cruise at 11+ km, 150+ km, 650 kg HE. Self-defense jammer reuses vanilla EW-25 mechanics: internal energy store drains while jamming and replenishes over time, 40 km radius, suppresses inbound seeker locks. Counter: saturation launches.
- Specs: 6.5 m × 0.55 m, ~2,300 kg
- Impl: clone **ALND-4/ALM-C450** · **code: jamming module** (capacity/recharge = config values)
- Visual: sleek body, flush ramjet intake, spine ECM blade antennas

### 10. Tusko-D — quasi-ballistic hypersonic strike missile
- Summary: PrSM × Kinzhal mix — air-launched, quasi-ballistic arc with Mach 5-class sprint and maneuvering terminal phase; 1.2 t penetrator-HE; dual land/surface strike, 400+ km class. Terminal weave defeats single-shot intercepts.
- Specs: 8.5 m × 0.70 m, ~2,400 kg
- Impl: clone **Tusko-B (AShM3)** · def-only
- Visual: slender Kinzhal-like body, sharp ogive nose, trapezoidal control surfaces

### 11. ALBM-3 Trebuchet [U] — air-launched ballistic, unitary
- Summary: lofted ballistic arc to fixed INS coordinates, ~150+ km, 1.5 t unitary HE; positioned between Tusko-D and Piledriver; carryable across role classes (no hardpoint math). Counter: kill the shooter.
- Specs: 6.5 m × 0.60 m, ~3,200 kg
- Impl: clone **Piledriver TBM** · def + air-launch integration
- Visual: clean tapering body, three tiny strakes

### 12. ALBM-3 Trebuchet [C] — bomblet carpet variant
- Summary: identical airframe/motor; dispenses ~50 × 12 kg unguided bomblets on descent for a wide footprint.
- Specs: 6.5 m × 0.60 m, ~3,300 kg
- Impl: shared airframe · **code: shared submunition engine**
- Visual: [U] + ventral dispenser seams

### 13. TOR-42 Halcyon — air-dropped lightweight torpedo
- Summary: parachute drop, 35 kt underwater, ~8 km run, 45 kg PBX, active acoustic homing vs ships. Balance via cost (no countermeasures in-game).
- Specs: 2.9 m × 0.32 m, ~280 kg
- Impl: **no vanilla analog — code: water-phase spike first; fallback = waterline skipper**; geometry built fresh
- Visual: torpedo cylinder, propeller shroud

### 14. RAT-44 Barracuda — rocket-assisted standoff torpedo
- Summary: same 45 kg torpedo stage with a separable rocket booster delivering it 10-15 km out with skip-entry.
- Specs: 3.8 m × 0.32 m, ~650 kg
- Impl: shared with Halcyon (booster stage + transition logic)
- Visual: torpedo + separable rocket tail stage

### 15. HKP-1 Palisade — aerial hard-kill interceptor pod
- Summary: aircraft-carried point-defense pod that detects missiles inbound on the carrying aircraft and launches hard-kill interceptors against them — the aerial counterpart to vanilla ship RAM-45 point defense. Guidance reference: the vanilla `antiMissile`/`DefendWithMissiles` ship-defense pipeline.
- Platforms: heavy airframes only — KR-67 Ifrit, EW-25 Medusa, and similar modded heavies via a BepInEx config whitelist; station availability is patched for whitelisted airframes only.
- Pod: 1.8 m × 0.40 m station, ~250 kg loaded, 4 × 35 kg interceptor rounds; rearm between sorties; multiple pods stack coverage.
- Interceptor: 1.2 m micro-missile, Mach 3+, ~35 G, proximity-fuzed HE-frag, engagement envelope ~0.3-4 km, sub-second reaction from threat detection.
- Modes: pod registers as a countermeasure entry; selecting it reassigns the Deploy CM button to cycle modes (spawns Safe, configurable):
  - **Safe** — pod inhibited, rounds locked.
  - **Smart Engage** — soft-kill sufficiency check: fires only when normal CMs cannot defeat the threat in time (time-to-impact vs CM engagement cycle), when a CM defeat would take too long (re-engagement cadence can't keep up), or when flare/capacitor reserves are inadequate for the CM response the threat demands; 1 interceptor per qualifying threat.
  - **Max Coverage** — engages every munition targeted at the aircraft that can kinematically be reached; 1 interceptor per target at a time, committed at maximum intercept range, re-engaging on failure (threat survives past the clearance threshold with time-to-impact still allowing re-engagement).
- Impl: clone **RAM-45** as the interceptor substrate; functional pod cloned from `AGM2_6Pod` and reduced to four `MountedMissile` launchers · **code: hard-kill auto-defense** (threat classification from the missile-warning pipeline, CM-state access, mode state machine, CM-menu integration). The first runtime spike retains widened, short-delay SARH guidance; replace it with self-contained ARH only if Ifrit/Medusa flight tests prove carrier illumination unreliable. Player-aircraft decisions run on the owning client and use the vanilla missile command path; AI decisions run on the server. Vanilla-system findings and the integration design are recorded in `docs/PALISADE_FINDINGS.md`; the implementation plan is in `docs/V1_PLAN.md`. (2026-09-14: functional clone registered; interception validation pending.)
- Counterplay: saturation launches, breaking lock early before the pod commits, low-closure launches outside the envelope; balance via round count and cost.
- Visual: boxy under-fuselage pod with four flush launcher doors and a small flat radar window at the nose; interceptors are stubby darts with strakes.

---

This document is the design authority for the 15-weapon roster. Per-weapon
implementation and test status is tracked in
`missions/Erenaldi.ProvingGround/lane-manifest.json`; runtime findings and
gates are recorded in `docs/PHASE1_FINDINGS.md`.

## Phase 1 decisions

- Prefer the alternate live variants when an analog has multiple definitions.
- Halberd base: `AAM4` (switched from `P_AAM2` during Phase 2B); Ballista base: `P_KEM1`.
- ARAD-80 base: `ARM1_mini`, matching its lighter fast-reaction role. Later
  switched to vanilla `ARM1_single`: runtime schema review showed no aircraft
  carries any `ARM1_mini` mount (orphaned variant, same trap as Halberd's
  `P_AAM2`), while `ARM1_single` has verified carriage on five aircraft and an
  identical component structure. Renamed from the original ARAD-120 when the
  continuous sustainer became a smaller motor; 2026-09-13: consolidated to the
  single continuous burn (see §4).
- Bramble airframe base: `bomb_demo_mini`.
- Trebuchet [U] retains the unitary Piledriver base; Trebuchet [C] uses the MIRV variant as its dispenser substrate.
- Hailstorm receives a definition-only dispersion test before custom salvo-offset code is added.
- MAD-2 Thistle, AShM-150 Kestrel, and AShM-450 Maelstrom were cut from the roster; no analog, lane, or code work is planned for them.
- Palisade interceptor substrate: RAM-45; pod station cloned from a gun-pod-style mount. Phase 1 must inspect the vanilla anti-missile defense pipeline (`antiMissile`/`DefendWithMissiles`) and the countermeasure manager before the hard-kill code system is built.
