# HKP-1 Palisade pod — U-frame and sensor-housing concept studies

Date: 2026-09-27. The user confirmed this concept in the alignment interview.

## Active context

- Current state (2026-09-28): `concept-approved` for the **pod housing
  silhouette**. A2's open sides and four-place layout remain approved, and
  the **A10 end silhouettes are now user-approved**: a 558 mm (1.2× A9)
  teal-dome wedge nose — roof `-211 mm·t³` holding the beam top then
  plunging to a blunt 24×12 mm tip seated on a belly line flush with the
  beam underside — plus a stubbier 345 mm level rear cap. The path ran
  A3–A9 front/end iterations, a fold, a nodding nose and length passes;
  sensor end apertures remain deferred until a separately reviewed feature
  gate on the approved curves. Exact scope:
  `cad/palisade_pod/REVIEW.md`.
  The interceptor visual concept is separately user-approved at
  `cad/palisade_interceptor/STEP/Spear_ACMWrap.step`.
- Authoritative source: this brief for the housing study; `MUNITIONS.md` §12
  for role and existing runtime; `cad/palisade_interceptor/POD_FIT_FEASIBILITY.md`
  for bounded interceptor-envelope evidence; `docs/ASSET_DESIGN_WORKFLOW.md`
  for all subsequent approval gates.
- Coordinate convention: millimetres; +X forward, +Z upward/dorsal, +Y
  starboard, consistent with the approved interceptor study. Pod orientation
  to an actual aircraft hardpoint/prefab remains to be measured.
- Preserve: four ready interceptors, two across and two fore-aft **in one
  underside tier**; a 1,200 mm interceptor with 79.006 mm radial envelope;
  continuous upside-down long-U frame, paired front/rear sensor modules, and
  a cohesive closed exterior. One hardpoint carries one pod.
- Avoid: four-abreast widening, vertical stacking that blocks downward
  drops, prominent exposed mounting hardware when complete, an implied
  production GBU-39 rack replica, and treating the donor six-door prefab as
  the approved four-door visual master.
- Emphasize: readable two-row/four-store architecture when seen from below;
  outer frame and sensor areas remain the visual identity with four boxes
  nested flush between them.
- Hard concept constraints: each ready round has an unobstructed downward
  path; each box uses two split underside shutters, and only the selected
  box opens at a time. The user has chosen a powered **downward** ejection,
  replacing their initial gravity-only release, and snap-turn after the
  round is clear. A fallback to timed flight when clearance is not confirmed
  is user-requested but unverified and not a CAD clearance proof.
- Open decisions: exact dimensions and carriage pose, hinge/door path,
  sensor windows/materials, actual donor transform
  mapping and flight-clearance/fallback timing.
- Next-gate files: this brief, `cad/palisade_pod/REVIEW.md`,
  `cad/palisade_pod/reviews/A10_DroopedEnds_Review.png`,
  `cad/palisade_pod/reviews/A10_DroopedEnds_Checks.json`,
  `cad/palisade_pod/reviews/A9_ContinuousEnds_Review.png`,
  `cad/palisade_pod/reviews/A8_RoundedTips_Review.png`,
  `cad/palisade_pod/reviews/A7_LevelBeam_Review.png`,
  `cad/palisade_pod/reviews/A6_SketchedEnds_Review.png`,
  `cad/palisade_pod/reviews/A5_ShoulderFront_Review.png`,
  `cad/palisade_pod/reviews/A4_LongFront_Review.png`,
  `cad/palisade_pod/reviews/A3_MountFront_Review.png`,
  `cad/palisade_pod/reviews/A2_OpenSides_Review.png`,
  `cad/palisade_pod/reviews/Palisade_Underside_Comparison.png`,
  `cad/palisade_pod/reviews/Palisade_Dorsal_Comparison.png`, `MUNITIONS.md` §12,
  `cad/palisade_interceptor/POD_FIT_FEASIBILITY.md`,
  `cad/palisade_interceptor/STEP/Spear_ACMWrap.step`,
  `docs/ASSET_DESIGN_WORKFLOW.md`, and the later housing packet.

## 1. Problem statement

Palisade's existing functional rack is cloned from `AGM2_6Pod`: it retains
four mounted missiles attached to doors 1/4/2/5 but still has six donor
doors and no approved custom pod art. The original 1.8 m × 0.4 m four-door
box does not allow two 1.2 m missiles fore-aft with sensor housings at both
ends. The user wants a convincing under-fuselage four-store defense pod
whose interceptors exit downward, while the outer housing reads as one
integrated unit with protected internal carriage rather than exposed
bolt-on weapons.

## 2. Solution

Create three contrastive **geometry-only outer-housing directions** around a
long, upside-down U-section: an overhead bridge and two hanging side frames
provide small landing points for four separate box modules. The modules sit
two side-by-side × two longitudinally between an integrated front sensor
area and rear sensor area; each end has a restrained outward-facing dark
aperture. In the installed state, the module skins align with the frame and
sensor ends so the pod reads as a continuous shallow shell and does not show
external mounting hardware.

Study the bare U-frame and an assembled context using **simple cassette
bounds only**; four detailed storage boxes and their eight split shutter
leaves are a later, independently reviewed task. The user selects or
hybridizes a housing direction before that work. Carriage feasibility must
measure real hardpoint/rack poses and release/door clearance before detailed
CAD or engine integration. The four-store drop-rack reference contributes
the carriage and downward-exit idea, not exact dimensions or production
mechanisms.

## 3. User stories

1. As the art director, I can compare three genuinely different U-frame and
   paired-sensor housing architectures at matched scale, both bare and
   populated with four simple storage volumes, so I can select the pod's
   visual identity without premature box detail.
2. I can see two across × two along the fuselage in a single bottom-access
   layer and an open downward path below every box, so the concept does not
   conceal a blocked upper pair of rounds.
3. I can inspect the front and rear end housings and identify one restrained
   sensor aperture on each, while the attached modules read as a cohesive
   outer shell without exposed bolts or rack arms.
4. I can compare the chosen missile's true stowed envelope with four
   placeholder volumes, the outer housing and the nominal heavy-aircraft
   mounting datum; fit claims are separated from assumptions about donor
   launcher stations and moving shutters.
5. I can choose or hybridize one housing silhouette before the individual
   boxes, shutters, retention interface or game asset are detailed.

## 4. Implementation decisions

| Decision | Choice and rationale |
|---|---|
| Carriage | Four individually removable box modules, two left/right × two fore/aft, all in one underside tier. Individual attachment/separation hardware does not need modeling in these studies. |
| Structural form | Lengthened inverted U: dorsal bridge with two descending outer rails/sidewalls; small module seating datums inside. Frame remains visible when modules are absent; installed skins align flush and cover mounts. |
| Pod proportion | Start with ~2.8–3.0 m length, about 400 mm width and a *provisional* shallow ~220–260 mm height. These are concept targets, not aircraft-fit-certified dimensions. The old 1.8 m length is superseded for this architecture. A later two-end sketch led to an **unapproved** 3.5 m study; its length exceeds this starting target and must be reviewed against real pylon/airframe limits before detail. |
| Sensor end treatment | Integrated front and rear housing modules, each with an outward-facing restrained aperture. No protruding turret head or implied new gameplay sensor logic. No central sensor module between fore/aft pairs. |
| Box/door semantics | Four separate bottom-facing modules; two split shutters per box in the future detailed state. Only the chosen box opens on a launch. One box's shutters must clear neighbors and the drop path before release. |
| Ejection and flight | An initial gravity-only choice was explicitly replaced by a **powered downward ejection**. Keep snap-turn after clearance and the existing cap-release → main-burn order. User selected a later forced-flight fallback if clearance cannot be confirmed; its timing and ownship collision behavior need separate runtime design/validation. No runtime change is authorized by a silhouette study. |
| CAD studies | Three contrasting housing architectures must differ in actual structural profile, side-rail/roof relationships, sensor-housing forms and exposed negative spaces; presentation uses neutral matched views, not color-only variants. Each demonstrates bare and placeholder-filled states. |
| Source preservation | Leave `Spear_ACMWrap` source/exports and the AGM2 donor prefab untouched. Use the approved interceptor as an envelope datum, not a mounted clone claiming Unity fit. |

## 5. Data model and modules

New boundaries proposed for implementation:

- `cad/palisade_pod/`: new housing-only workspace with parametric source,
  STEP artifacts, checks, reference/decision notes and review snapshots.
- One shared parameterized U-frame/sensor factory accepts a named housing
  direction and returns native labeled parts for the bridge, outer rails,
  front/rear sensor modules and restrained aperture geometry. Thin CAD model
  entrypoints declare a bare-frame state and a *placeholder-filled* state.
- Four placeholder envelopes use source-independent measurements from the
  approved Spear CAD. Each has an explicit fore/aft and left/right datum and
  an unobstructed underside. These are review volumes only, not detailed
  cassette faces, shutters, colliders or runtime mounts.
- A saved-artifact checker reports each direction's length/width/height,
  four-case carriage space and clearance against the selected missile's
  conservative circular envelope, U-frame/placeholder intersections,
  readable bare/filled composition and exact shared-part preservation
  between the two states. Additional door-sweep and aircraft-fit checks
  follow direction choice.

Plugin code, Unity prefabs and BepInEx config are outside this concept-stage
ownership. `PalisadeCloner` currently uses four retained donor
`MountedMissile` components on six-door AGM2 geometry; saved schema dumps
do not include launcher poses. Real hardpoint/door mapping needs a later
runtime-prefab probe or authenticated source extraction before engine delivery.

## 6. Testing and acceptance

- For each bare and context STEP, check solid validity, positive volumes,
  meaningful named groups, exact repeated-box count and that the module
  placeholders are equivalent across study states except deliberate display
  placement. Measure all envelope dimensions and nominal roof/sidewall
  thicknesses from saved geometry; compare placeholder intersection with
  solid frame and each other.
- Recheck the approved round's 1,200 mm length and 158.013 mm circular
  envelope against both two-across and two-fore/aft positions. Provide
  conservative clearance with explicit example wall and end-structure
  assumptions; mark unknown carriage pose, door swept volume, pylon and
  aircraft hardpoint fit *unverified*.
- Primary model directly inspects matched opposed isometrics, side/top,
  front/rear, underside, one bare-frame view and the context-populated view
  for every direction. Differentiate actual negative spaces, sensor-end
  hierarchy and the four underside exits at intended game distance.
- Present validated source/STEP and review PNGs, plus working CAD Viewer
  links. User selection/hybridization is the exit gate for this concept
  deliverable; validity does not imply visual approval or production fit.

## 7. Out of scope

Detailed four cassette meshes, hinge kinematics, shutters/retention/ejector
hardware, definitive sensor electronics or radar functionality, runtime
force/fallback logic, real donor-transform reconstruction, engine meshes,
colliders, materials/textures, Unity prefab/bundle, installed aircraft
clearance and combat/multiplayer validation are later work. No CAD-only
concept study changes registered round count or network serialization.

## Open questions deferred to later gates

- Which housing direction (or hybrid) is selected, and does actual Ifrit/
  Medusa pylon/gear/terrain clearance permit its length and sensor ends?
- Which exact split-shutter hinge motion clears the neighboring box and
  frame? What are the real donor launcher and door local poses?
- What force/clearance check and bounded later forced-flight fallback can
  meet the user-requested downward release without a cap/aircraft conflict?
