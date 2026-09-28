# MUNITIONS.md — Implementation Handoff Draft
## Global design parameters
- **12 weapons** · 6 def-tuned, 6 code-touched · each munition's initial visual-design pass is geometry-only; later texture, material, color, and marking passes may add any presentation details needed · nukes deferred to v1.1
- **Code systems:** submunitions · jamming (EW-25-style, energy store) · water-phase · HOB/LOAL seekers · hard-kill auto-defense
- **Method:** clone vanilla analog def → override fields → register via BepInEx plugin; def-only weapons may alternatively ship as Blueprinter `.nobp` patches (proven by AShM-500 Yashma)
- **Phase 1 gate:** runtime reflection dump validates every def-field mapping below; all numbers are design targets until then
- **Pylon/hardpoint decision (2026-09-27):** Halberd, Kris, Ballista and Phantom keep their fixed munition sizes while pylons and aircraft eligibility are redesigned around measured fit. Donor hardpoint presence is a candidate source, not authorization: only configurations with validated mounted and release clearance will be enabled. External single, internal, twin and triple carriage require distinct rack variants and evidence. Destination plan: `plans/2026-09-27-fixed-munition-pylons-hardpoints.md`.

---

### 1. AAM-44 Halberd — medium-range ARH AAM
- Visual-design authority update (2026-09-22): the fresh CAD studies follow `plans/2026-09-22-halberd-rounded-square-reboot.md`: approximately 3.37 m long, 200 mm rounded-square main/booster sections, circular-ogive nose transition, flush aft booster exactly 1/6 of assembled length, four low integrated intake channels and separate compact four-fin sets. This supersedes the older visual proportions/layout below for the new studies; existing runtime tuning and assets are not changed by the design decision.
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
- Visual: RDM-9 decoy of record (2026-09-20, R5): Dart silhouette on the smooth
  broad-shallow upward-wedge airframe — clean body converging to a sharp apex
  point riding above the centerline, four real-span tail fins, dorsal pop-out
  wings rendered deployed (swept planform: 1.4 m span, 420/110 mm chords, raked
  tips, 2.5 mm panels thinned for the folding concept; roots inside the 0.25 m
  carriage envelope, the deployed span intentionally exceeds it like the real
  ADM-160 spring-out wings), recessed turbojet exhaust. Retracted configuration:
  Tomahawk-style internal dorsal bay — panels park in the fuselage, visible as
  a 6 mm spine slot (x −950..−250) with dark panel stack plus an aft hinge
  fairing; full 250 mm carriage envelope restored. Side RF/lens emitter panels
  removed by 2026-09-20 decision. Supersedes the 2026-09-14 compact
  MALD-hybrid direction and the finless cylinder studies.
  **2026-09-23 visual reboot:** The user rejected R5's overall round-dart
  silhouette as the forward design direction. R5 remains a historical built
  CAD/Unity candidate, not the visual master for new work. The aligned new
  direction is a 2.8 m Kh-69-like faceted body with TALD-like flattened-wedge
  nose, GBU-39-inspired visible folding main wings, four corner-hinged folding
  tail fins and subtle flush RF panels, within a 250 mm stowed envelope.
  Three contrastive paired-state studies precede concept selection; the
  selected CAD must clear the actual donor rack. See
  `plans/2026-09-23-rdm9-phantom-visual-reboot.md`. No new geometry approved.
  **2026-09-23 drawing correction:** The user clarified that the fuselage
  frontal section is a lightly filleted square and supplied bottom/front nose
  sketches: a pointed triangular bottom planform with a central junction and
  an upper-biased front apex above a lower V/chine. This supersedes the flat
  nose and broad-shallow body interpretation in the first A/B/C studies.
  `cad/phantom_visual_reboot/NOSE_SKETCH_CONTRACT.md` records the local
  interpretation; D/SketchNose is an unapproved single-form prototype.
  **2026-09-23 local refinement:** current body baseline J/R7 has equal mirrored
  lower shoulders and a 20 mm horizontal tip wedge with 4 mm leading-edge radius
  centered at the former apex. User authorized starting appendage studies after
  the symmetry correction. First one-wing K study has deployed/midfold/stowed
  poses; approval before repetition and whole-airframe selection remain open.
  See `cad/phantom_visual_reboot/BODY_R7_WING_R1_CONTRACT.md`.
  **2026-09-23 wing-reference correction:** user rejected K's single-panel
  swivel as inaccurate to GBU-39. Use MBDA DiamondBack's joined tandem-wing
  architecture for the next reference-led study; K is a rejected experiment.
  Sources and motion uncertainties are recorded in
  `cad/phantom_visual_reboot/GBU39_WING_REFERENCE_RESEARCH.md`.
  **2026-09-24 joined-wing study:** L/R1 replaces K for local review with a
  forward/rear joined pair, outboard joint and sliding rear carriage. Three
  poses use identical parts; motion is explicitly a fictional adaptation.
  Opposite-side repetition and tail detailing await this local visual gate:
  `cad/phantom_visual_reboot/JOINED_WING_R1_CONTRACT.md`.
  **2026-09-27 implementation map:** later local approvals established the
  covered A5 two-set joined wings and four recessed clipped tail fins. The
  latest integrated CAD also has the user-requested belly ramp intake, currently
  a checked35 mm-travel trial pending explicit acceptance. Remaining design
  work and validation gates are ordered in
  `cad/phantom_visual_reboot/IMPLEMENTATION_CHECKLIST.md`: aft exhaust/duct
  treatment, flush RF layout, actual donor-rack interfaces, detail and final
  whole-airframe review. Intake/exhaust visuals do not change the gameplay
  motor or authorize engine delivery; historical notes above are retained.
  **2026-09-27 aft/rack study:** user selected a recessed rounded-square exhaust;
  `cad/phantom_visual_reboot/AFT_EXHAUST_R1_BRIEF.md` records the built, checked
  candidate and intake passage, awaiting visual approval. Actual donor pylon
  geometry/transforms were recovered, and unchanged-placement fit fails against
  the current body/cover/wing; see `DONOR_RACK_FINDINGS.md` in the same directory.
  No mount offset, runtime geometry or propulsion tuning was changed.

### 6. ALM-5 Vesper — high-mach ECM cruise
- Summary: Mach 3.5-4 cruise at 11+ km, 150+ km, 650 kg HE. Self-defense jammer reuses vanilla EW-25 mechanics: internal energy store drains while jamming and replenishes over time, 40 km radius, suppresses inbound seeker locks. Counter: saturation launches.
- Specs: 6.5 m × 0.55 m, ~2,300 kg
- Impl: clone **ALND-4/ALM-C450** · **code: jamming module** (capacity/recharge = config values)
- Visual: sleek body, flush ramjet intake, spine ECM blade antennas

### 7. Tusko-D — quasi-ballistic hypersonic strike missile
- Summary: PrSM × Kinzhal mix — air-launched, quasi-ballistic arc with Mach 5-class sprint and maneuvering terminal phase; 1.2 t penetrator-HE; dual land/surface strike, 400+ km class. Terminal weave defeats single-shot intercepts.
- Specs: 8.5 m × 0.70 m, ~2,400 kg
- Impl: clone **Tusko-B (AShM3)** · def-only
- Visual: slender Kinzhal-like body, sharp ogive nose, trapezoidal control surfaces

### 8. ALBM-3 Trebuchet [U] — air-launched ballistic, unitary
- Summary: lofted ballistic arc to fixed INS coordinates, ~150+ km, 1.5 t unitary HE; positioned between Tusko-D and Piledriver; carryable across role classes (no hardpoint math). Counter: kill the shooter.
- Specs: 6.5 m × 0.60 m, ~3,200 kg
- Impl: clone **Piledriver TBM** · def + air-launch integration
- Visual: clean tapering body, three tiny strakes

### 9. ALBM-3 Trebuchet [C] — bomblet carpet variant
- Summary: identical airframe/motor; dispenses ~50 × 12 kg unguided bomblets on descent for a wide footprint.
- Specs: 6.5 m × 0.60 m, ~3,300 kg
- Impl: shared airframe · **code: shared submunition engine**
- Visual: [U] + ventral dispenser seams

### 10. TOR-42 Halcyon — air-dropped lightweight torpedo
- Summary: parachute drop, 35 kt underwater, ~8 km run, 45 kg PBX, active acoustic homing vs ships. Balance via cost (no countermeasures in-game).
- Specs: 2.9 m × 0.32 m, ~280 kg
- Impl: **no vanilla analog — code: water-phase spike first; fallback = waterline skipper**; geometry built fresh
- Visual: torpedo cylinder, propeller shroud

### 11. RAT-44 Barracuda — rocket-assisted standoff torpedo
- Summary: same 45 kg torpedo stage with a separable rocket booster delivering it 10-15 km out with skip-entry.
- Specs: 3.8 m × 0.32 m, ~650 kg
- Impl: shared with Halcyon (booster stage + transition logic)
- Visual: torpedo + separable rocket tail stage

### 12. HKP-1 Palisade — aerial hard-kill interceptor pod
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
- Visual: boxy under-fuselage pod with four flush launcher doors and a small flat radar window at the nose. The interceptor is an almost cylindrical 1.2 m dart with a rounded nose, four tiny diagonal rear stabilizers, and a detachable aft turning cap carrying four cardinal transverse motors. The cap performs pitch/yaw snap-turning, not axial roll; it separates before the recessed main nozzle ignites.
- Visual-study decision (2026-09-23): the existing 1.2 m interceptor CAD remains an unapproved comparison baseline. Retain the detachable four-thruster turning cap and staged flight sequence, but explore three different full-silhouette, hardware-informed interceptor directions before choosing or hybridizing a visual master. The old interceptor and pod dimensions and four-round packaging are revisitable during subsequent fit review; runtime capacity and pod design do not change merely by starting the visual study. Authority for the study: `plans/2026-09-23-palisade-interceptor-visual-redesign.md`.
- Visual selection (2026-09-23): the user approved **A / Spear** as the interceptor's concept silhouette from `cad/palisade_interceptor/reviews/Palisade_Selection_Board.png`. Its 1,200 mm length and 101.01 mm maximum radius are CAD study measurements, not validated pod clearance or a runtime spec change; check the actual pod/cell layout before detail or production work. Selection and tradeoffs: `cad/palisade_interceptor/REVIEW.md`.
- Visual revision (2026-09-23): after supplying a long, low trapezoidal fin sketch, the user selected **SketchLow** for fourfold propagation on A/Spear with a full aft boattail cap. The resulting CAD candidate's 79.009 mm radial envelope is a measured visual-study result; the assembled/separated review and exact approval boundary are in `cad/palisade_interceptor/SPEAR_FIN_BOATTAIL_REVIEW.md`. Whole-asset visual acceptance and pod-fit review remain open; this does not change runtime missile or pod definitions.
- Current interceptor shape selection (2026-09-27): user approved A/Spear's uniform **109.12 mm diameter** main barrel and matching shortened **130 mm cylindrical cap** up to the original pointed nose, with four long-low SketchLow fins reseated on the narrower barrel. The selected study is `cad/palisade_interceptor/STEP/Spear_UniformBarrel.step` (separated state and evidence in `SPEAR_FIN_BOATTAIL_REVIEW.md`). Lateral cap-nozzle detail is prototyped at one station only and awaits approval before fourfold repetition; pod clearance and runtime/production delivery remain separate gates.
- ACM visual direction (2026-09-27): user superseded the earlier four clustered cap-nozzle appearance with an all-around field of small recessed ports inspired by real PAC-3 ACM display imagery; their drawing establishes distribution, not dimensions. `cad/palisade_interceptor/STEP/Spear_ACMWrap.step` is the current 96-port CAD **review candidate** (paired separated state and reference/evidence ledger in `cad/palisade_interceptor/ACM_PORT_REVIEW.md`), awaiting user visual judgment. The visual port count does not change the existing staged pitch/yaw controller or imply 96 separately commanded motors; pod fit/export/runtime remain pending.
- ACM visual approval (2026-09-27): user accepted the `Spear_ACMWrap` full-circumference cap pattern from `cad/palisade_interceptor/reviews/Spear_ACMWrap_Comparison.png`. The uniform barrel, pointed nose and cap arrangement remain the chosen concept-level appearance; feasible launcher packing, engine export and runtime visuals are still to be verified. Scope recorded in `cad/palisade_interceptor/ACM_PORT_REVIEW.md`.
- Packaging feasibility (2026-09-27): `cad/palisade_interceptor/POD_FIT_FEASIBILITY.md` measures the approved interceptor's 1,200 mm length and 158.013 mm maximum fin-envelope diameter. Four could fit an *illustrative* 400×400 mm box with 2×2 stations and explicit example walls/dividers, but this is not evidence that the current six-door `AGM2_6Pod` clone is arranged or sized that way. Its saved dump retains four missiles on doors 1/4/2/5, leaves six door objects, and omits launcher local transforms. Pod/cell design and real aircraft clearance remain open.
- Pod concept decision (2026-09-27): user chose four ready rounds in a single bottom-access tier, two across × two fore-aft, carried by a lengthened ~2.8–3.0 m inverted-U frame between integrated front/rear sensor areas with visible end apertures. Four separate removable storage boxes nest flush into the frame with mounting hardware hidden when installed; boxes and two-leaf underside shutters per box are a later design, opening one selected box per launch. Release changes from forward to **powered downward** ejection, snap-turn after clearance, with user-requested later forced-flight fallback still to be engineered and tested. Study width ~400 mm and shallow ~220–260 mm height are provisional visual targets, not aircraft-fit evidence. Authority: `plans/2026-09-27-palisade-pod-housing-concepts.md`; interceptor approvals remain independent.
- Pod silhouette direction (2026-09-27): after inspecting the bare/filled three-direction boards, the user chose the **basic shape of A** with one explicit correction: remove the long side covers that hide the boxes; the four separate box skins should fill that outer side space. `cad/palisade_pod/STEP/A2_OpenSides_{Bare,Filled}.step` is the resulting **review candidate**, retaining A's dorsal bridge and sensor ends, shortening the long side rails to roof-edge lips and widening only the four placeholder volumes to the outer ±200 mm faces. A2 visual acceptance is pending; box construction, split shutters, aircraft fit and runtime remain separate gates. Evidence/limits: `cad/palisade_pod/REVIEW.md`.
- Pod A2 housing silhouette approval (2026-09-27): after viewing the original-A/A2 bare/filled comparison opened in the desktop image viewer, the user selected **“Approve A2 sides.”** Approval covers A's straight bridge, paired sensor ends, shortened roof-edge lips and four placeholder skins forming the side shell, as shown in `cad/palisade_pod/reviews/A2_OpenSides_Review.png`. It is housing **concept-level visual approval** only: exact rack/aircraft fit, detailed boxes, split shutters, ejection/fallback runtime, export and in-game visuals remain open. The measured sample layout is 2980×400×223 mm outer, with 1310×196×180 mm placeholders and a 158.013 mm round fin envelope; these do not certify release clearance.
- Pod front reference revision (2026-09-27): user supplied an inline BRU-61/GBU-39 model-kit image and attributed **only the mount's forward fairing**, not the bombs, as a cue for the Palisade frame/sensor package; central side panels remain excluded. `cad/palisade_pod/STEP/A3_MountFront_{Bare,Filled,Focus}.step` is a front-only short tapered/rounded **review prototype**, preserving A2's approved open sides, four placeholder skins and rear sensor block. Its visual match/length is not yet user-approved; `cad/palisade_pod/REVIEW.md` records image-derived cues versus assumptions. Do not infer donor geometry or fit from the photo.
- Pod longer-front direction (2026-09-27): after inspecting A3's short-nose packet, user requested extending the mount-front taper and reducing its forward height as in the image. `cad/palisade_pod/STEP/A4_LongFront_{Bare,Filled}.step` is a new **review prototype**: a 840 mm foredeck/fairing progression over the existing overall length ending in a 270×125 mm front face; it preserves A2's open central sides, four box placeholders, aft sensor and outward aperture. Saved STEP check passes; visual correspondence still awaits user judgment and real rack/aircraft clearance is unknown. See `cad/palisade_pod/REVIEW.md`.
- Pod front reference reanalysis (2026-09-27): user asked for a separate image-analysis agent after A4 still read as a terminal cap. The exact ResKit BRU-61/GBU-39 image was found in Downloads and directly read by the primary model and the available `subagents/multimodal-analyst` (no Astra-named agent is registered). Observable mount cues are a rounded/blunt front cover, a visible shoulder and a longer foredeck flowing into the dorsal beam; no bomb detail is attributed to the pod. `cad/palisade_pod/STEP/A5_ShoulderFront_{Bare,Filled}.step` is a new **unapproved** front-cover study, adding a raised, tapered forward shoulder while preserving A2's open sides/four boxes and A4's sensor ends. It measures 2980×400×251 mm, still a study envelope, not a donor/aircraft fit result. Primary visual finding: more obvious shoulder than A4 but still a rather slab-like foredeck versus the reference; see `cad/palisade_pod/REVIEW.md`.
- Pod front correction gate (2026-09-27): user judged A5 **“still not what I'm looking for”** and asked to sketch their intent on “current V4” in CAD Viewer. Opened the existing [A4 filled study](http://127.0.0.1:3248/?file=STEP/A4_LongFront_Filled.step) for markup; await that sketch before another front revision. This does not undo the user's prior A2 open-side approval and does not approve A4/A5 front geometry or any fit/runtime behavior.
- Pod two-end sketch revision (2026-09-27): user drew **both** ends on the A4 filled side view. Treat the red upper/lower contours as intended smooth, blunt, height-reducing front and shorter aft sensor fairings, not literal irregular edge traces or measured pixels; keep the A2-approved central open sides and four flush box skins. `cad/palisade_pod/STEP/A6_SketchedEnds_{Bare,Filled}.step` is an **unapproved** visual study with approximately 300 mm front and 220 mm aft extension, now measuring 3500×400×223 mm overall. This exceeds the old provisional 2.8–3.0 m length target; its aircraft/pylon/door clearance and any requirement to shorten the design are unresolved. Exact visual/geometry evidence: `cad/palisade_pod/REVIEW.md`.
- Pod sketched-end redesign (2026-09-27): user requested an Astra-agent redesign after A6. No Astra-named agent is available; the available image analyst directly inspected the saved red markup `C:\Users\erena\Downloads\Screenshot 2026-09-27 220011.png`, the ResKit image and A6 views. Primary rechecked the drawing and corrected one analyst comparison: measured A6 forward end is **465 mm**, longer than its **385 mm** aft end already; the clearer misses were A4's early roof slope retained in A6 and visibly segmented contours. `cad/palisade_pod/STEP/A7_LevelBeam_{Bare,Filled}.step` is a new **unapproved** study restoring A2's flat bridge through the forward root and using bounded denser end sections. Four-place layout and 3500×400×223 mm candidate envelope remain; real fit and visual approval remain open. See `cad/palisade_pod/REVIEW.md`.
- Pod rounded-end correction (2026-09-27): after reviewing A7, user asked to tweak **both ends** closer to the sketch and said the ends should be **rounded for now**, without a large flat end requirement. `cad/palisade_pod/STEP/A8_RoundedTips_{Bare,Filled}.step` is the **unapproved** resulting silhouette study: narrower curved front/rear terminations with reduced provisional recessed sensor cues (60×18 mm); only the two end-shell/aperture pairs differ from A7. Saved geometry retains the checked 3500×400×223 mm concept envelope and A2 central open sides/four boxes. The tiny terminal cue faces are not a detailed sensor design or proof of donor/aircraft clearance. See `cad/palisade_pod/REVIEW.md`.
- Pod continuous-curve correction (2026-09-27): user rejected A8 as **jagged/misaligned** and explicitly deferred end apertures to prioritize continuous rounded contours matching their side sketch. `cad/palisade_pod/STEP/A9_ContinuousEnds_{Bare,Filled}.step` is the new **unapproved silhouette-only** study: smooth non-ruled front/rear lofts ending in near-point rounded noses, no aperture geometry, with the A2 level roof and four placeholder side skins unchanged. The intended front/rear outward sensor apertures must be reintroduced only after silhouette approval, on the approved curves without reinstating large flat end faces. Candidate bounds are 3500×400×223 mm and actual aircraft/donor door clearance remains unknown. See `cad/palisade_pod/REVIEW.md`.
- Staged flight authority (2026-09-14): 0.2 s controller-applied housing ejection; snap-turn toward the SARH-owned aimpoint; cap release when alignment is within 5 degrees and angular rate is at most 60 deg/s after a 0.1 s minimum, or at a 0.55 s timeout; then an 18 kN, 2.0 s, 15 kg main burn with 1,050 m/s speed ceiling and high-authority TVC. Snap-turn torque is limited to 60 rad/s2 and 720 deg/s; powered TVC is limited to 35 degrees and 35 G with a 0.2 s authority ramp.

---

## Deferred to a possible later release

The three munitions below are archived from the active roster. Specs are
preserved verbatim for revival; no analog, lane, or code work is planned.
Analog decisions for revival: GPO-2R → `GPO-2P Auger`; Bramble →
`bomb_demo_mini`; Hailstorm → `AGR-18 Lynchpin` airframe with a
definition-only `LaserSeeker.errorRate` dispersion test before any custom
salvo code.

### D1. GPO-2R Auger — rocket-powered penetrator
- Summary: 1.3 t bomb with 4 s rocket boost and terminal dive; AP ~5000 (vs Auger's 3000); delayed burst after penetration.
- Specs: 4.2 m × 0.46 m, ~1,300 kg
- Impl: clone **GPO-2P Auger** · def-only
- Visual: thick body, hardened elongated tip, radial-nozzle tail motor ring

### D2. CDM-4 Bramble — cluster dispenser
- Summary: dispenser opens at preset altitude, scattering ~20 × 30 kg unguided bomblets over a ~200 m footprint.
- Specs: 2.6 m × 0.48 m drum, ~900 kg
- Impl: clone **Demolition Bomb** airframe · **code: submunition engine**
- Visual: drum with longitudinal seams

### D3. AGR-30 Hailstorm — indirect saturation rockets
- Summary: salvo of 4 lofted rockets with sustainer motors, 25-40 km to the designated point, deliberate 300-600 m dispersion — area saturation, no precision.
- Specs: 2.1 m × 0.24 m per rocket, ~340 kg · 30 kg HE-FRAG
- Impl: clone **AGR-18 Lynchpin** airframe · def-first using `LaserSeeker.errorRate`; add code-lite salvo dispersion only if testing misses the 300-600 m footprint
- Visual: fat tube, wraparound fins

---

This document is the design authority for the 12-weapon roster. Per-weapon
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
- Trebuchet [U] retains the unitary Piledriver base; Trebuchet [C] uses the MIRV variant as its dispenser substrate.
- MAD-2 Thistle, AShM-150 Kestrel, and AShM-450 Maelstrom were cut from the roster; GPO-2R Auger, CDM-4 Bramble, and AGR-30 Hailstorm are deferred to a possible later release (specs preserved verbatim in the deferred section above). No analog, lane, or code work is planned for any of them.
- Palisade interceptor substrate: RAM-45; pod station cloned from a gun-pod-style mount. Phase 1 must inspect the vanilla anti-missile defense pipeline (`antiMissile`/`DefendWithMissiles`) and the countermeasure manager before the hard-kill code system is built. The countermeasure-system investigation is complete — see `docs/PALISADE_FINDINGS.md`.
