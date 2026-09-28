# Selected Halberd hybrid — Chisel / Sculpted / original Shoulder

2026-09-14. Selected CAD exterior with a separate textured Unity authoring
candidate; production bundle/runtime integration has not been performed.
The native STEP intake-gap defect is repaired in the locally rebuilt cadgen
runtime. Fresh native snapshot and closed-mesh verification are recorded in
`HALBERD_MESH_GAP_FINDINGS.md`; the checked OCCT GLBs remain independent evidence.
Revised directly by the main agent following the user's annotated end-on reference.
The blue outlines indicate enlarged cutout footprints, not added housings.
Intakes are subtractive corner openings entirely within the original transition.

## Active context

- **Current state:** `engine-review`. The 19-part Shoulder hybrid is the selected
  CAD authoring candidate; deterministic checks, repaired native mesh evidence,
  export, and primary-model Unity image review exist. Explicit promotion into the
  production prefab/bundle and runtime path remains pending.
- **Authoritative source:** `cad/halberd/generate_halberd_shoulder_hybrid.py` and
  `cad/halberd/Halberd_Shoulder_Hybrid.step`, with source/output identity re-verified before
  any production export.
- **Approved concept / review packet:** the user selected the Chisel body, Sculpted
  rear, original Shoulder nose, and subtractive four-intake treatment. The review
  packet and Unity authoring images listed below record the current candidate.
- **Coordinate system and scale:** centered 3,367 mm CAD master; +X forward, +Z
  dorsal, +Y lateral; Unity mapping `(X,Y,Z) -> (Y,Z,X) * 0.001`.
- **Preserve:** selected donor responsibilities, retained native skin over
  subtractive corner openings, inward-running passages, complete separated stages,
  mounting corridor, and repaired closed-mesh appearance.
- **Avoid:** external cowls, planar pasted-on mouths, forward-expanding internal
  routes, thin breakout skin, stale pre-repair meshes, and production promotion by
  filename or modification time.
- **Emphasize:** broad integrated corner openings, a readable square-to-round
  transition, coherent stage separation, and vanilla-compatible material hierarchy.
- **Rejected interpretations:** added intake housings, widened passages that break
  through the hull, and reliance on topology checks when visual semantics fail.
- **Hard constraints:** 19 labels, 3,367 mm envelope, selected source ownership,
  stage hierarchy, transform basis, closed serialized mesh, and no gameplay scripts
  in the authoring prefab.
- **Open decisions:** explicit production promotion, colliders, rack/pylon fit,
  bundle replacement, plugin embedding, FX/jettison, aircraft fit, and runtime
  acceptance.
- **Files required for the next gate:** this contract, the authoritative source and
  STEP, current check/mesh reports, Unity authoring packet, and five Unity review
  images. Do not load the historical detailed-RC1 track unless comparing it is the
  stated task.

### Lifecycle evidence

| Boundary | State and evidence |
|---|---|
| Intent / concept | User-selected donor combination and corrected subtractive intake direction are recorded in this contract. |
| CAD | Source checks, STEP validation, repaired native tessellation, closed-mesh checks, and primary-model review pass for the selected candidate. |
| Export | The source-bound Unity authoring packet passes at 41,950 triangles and 19 closed parts. |
| Engine | A script-free Unity authoring prefab and five directly reviewed captures exist; production promotion is pending, so the current state is `engine-review`. |
| Runtime | Colliders, rack, production bundle, plugin install, aircraft fit, FX/jettison, gameplay, and runtime proof are unverified. |

## User-selected design authority

| Region | Selected source | Hybrid treatment |
|---|---|---|
| Main body | B3 Chisel | 208 × 208 mm section, 12 mm corner radius, planar sides |
| Rear | B5 Sculpted | Swept rear blades, progressively softer booster corners and aft taper |
| Forebody/intakes | Original four-intake Shoulder plus annotated reference | Four enlarged corner cuts beneath retained native skin, no projecting covers |
| Nose | Original Shoulder | Circular 86 mm-radius base and pointed smooth-loft radome |

The rear selection is interpreted as the booster and tail assembly. Chisel's
sustainer fins remain. The booster starts with Chisel's exact section at the
joint, retains it for 180 mm aft, then rounds progressively toward the Sculpted
tail. No rounded waist interrupts the stage seam. Both pieces remain complete
after separation, with recessed nozzle/closure faces.

Donor shapes are reconstructed parametrically in
`cad/halberd/generate_halberd_shoulder_hybrid.py`; no donor STEP is modified. Chosen
profile/station values live locally in the hybrid source; primitive construction
helpers remain shared with the concept sources. This is a separate candidate,
not a replacement of the production detailed master.

## Dimensions and assumptions

- Overall length **3367 mm**, centered at X=0; CAD +X forward, +Z dorsal, +Y lateral.
- Chisel's 3360 mm layout was reconciled to the original Shoulder length (+7 mm)
  to retain the established nose/tail planes ±1683.5 mm and seam X=-336.7 mm.
- Stage-joint section **208 × 208 mm**, 12 mm corner radius on both sides.
- Forebody reaches radius **86 mm** at X850. The complete circular section is
  restored from X850 to the radome base at X1080; no intake cut extends onto it.
- Four intake planes: **45/135/225/315 degrees**. Nose and mid/forward intake
  arrangement follows original Shoulder. Passages stay narrow while buried in the
  main body and widen through the square-to-round transition. Booster fins remain seated.
- There is no standalone planar mouth or external cowl. The sloping hull surface
  determines the opening boundary. The front cutter broadens to half-width42 /
  half-height24 mm; these are tool dimensions, not a claimed 84×48 mm aperture.
  The forward floor continues the intake's elliptical curvature across its width
  and turns into the original end boundary, rather than forming a planar ramp.
- All four `intake_cover_*` parts are removed. The outer cover is original body
  material above the buried passage. Existing `intake_floor_*` labels now carry
  dark blind-end backing patches inside the body. They move inward with the passage;
  the deeper end is therefore less directly visible in the head-on view.
- Booster corner progression, aft to forward: 62.4 / 78 / 64 / 12 / 12 mm,
  with the aftmost width reduced to 166.4 mm and the main width held at 208 mm.
- Display-only separation gap: 350 mm. Gameplay and real propulsion behavior
  are outside this exterior concept study.

## Review and repair

The added cowls were a mistaken interpretation and were rejected by the user.
The current source restores the pre-cowl unbroken hull profile and only removes
corner material. The user's two end-on images (one with blue outlines) establish
the intended type of geometry and approximate enlarged footprint, not exact dimensions.
Widening the buried passage too early caused side breakouts and thin pointed skin
strips in the first subtractive trial. Keeping it narrow to X535 and opening the
curved crown before widening at X620..790 repaired those breakouts.

Twenty-eight views were generated, with full-size entrance, reference-angle toe
and internal cutaway views inspected by the main agent. Four contact sheets index the packet:
opposed isometrics, side/top/end views, separated stages, intakes,
front-on mouths, roofs, nose transition, seam, and both detached-stage ends.
The integrated corner cuts were compared head-on with the reference; an additional
edge-visible end view records their footprint against the square/circular outlines.
Aircraft mounting clearance and in-game readability remain later-stage work.

## Actual validation

`python check_halberd_shoulder_hybrid.py` passes: 19 unique labels, valid positive
solids, 3367 mm envelope, correct stage ownership, fin/mount/floor/nozzle contacts,
no nozzle backing intrusion, circular forebody section checks, rear corner
progression, and four clear intake probes. Intake probes are at X=650/radial110 mm,
inside the nominal uncut 192 mm rounded section, avoiding an outboard empty-space
probe that would fail to establish a real recess.

New checks enforce zero volume outside the independently specified pre-cowl hull
for the body and all intake backing parts; retained native shoulder roof and side
skin; supporting material remains beneath the curved intake floor. The full
radius86 forebody is restored from the original X850 intake limit onward.
All four openings remain clear. No external-cowl labels are allowed.
At X650, the removed section area is **2.57×** that of the original four-intake
cutter applied to the same hull. This is a controlled CAD section comparison,
not a projected-image area, pixel-perfect trace or airflow/performance measure.
Tolerance-aware serial Boolean operations use 1e-6 mm fuzz and the existing
1e-3 mm³ volume threshold.

### Inward-running internal passages

User correction: the internal route must move toward the centerline as it runs
aft (decreasing CAD X). Authored radial centers now run from 106 mm at the front,
through 99 mm at X620 and 86 mm at X535, to 70 mm at the X350 rear end. The
previous rear center was 113 mm, outward of the 106 mm entrance.

The checker subtracts the exported body from the nominal hull in isolated
2 mm-thick slabs, measures the actual void center of mass, and requires monotonically
decreasing radius toward the rear for each of the four buried passages:

| Axial station X (mm), front to rear | Measured radial center (mm) |
|---:|---:|
| 620 | 98.97 |
| 600 | 95.94 |
| 535 | 86.02 |
| 470 | 80.38 |
| 400 | 74.32 |

The measurement uses fully buried sections so clipping of the exposed opening by
the outer skin cannot misrepresent its direction. Existing non-protrusion, roof,
contact and stage checks still pass. `Halberd_Shoulder_Hybrid_InternalPath.step`
is a display-only longitudinal cut through the actual master, not a proxy tube.
In its side snapshot the entrance is on the right and the rear is on the left;
the passage approaches the centerline toward the left.

### Smooth intake-floor / forebody junction

The user clarified the annotated view: red is the curved intake surface to follow;
blue is an unwanted extension. The flat X950 ramp was therefore removed. A
fixed-normal sweep of the existing elliptical section now continues from X790
to X850 along a quintic center path. It preserves transverse intake curvature,
matches the preceding center-floor slope, and finishes with zero center-floor
slope/curvature at X850. There is no added cover or cut beyond the original end.

The checker measures first-positive face intersections at 17 axial stations per
intake plus transverse offsets ±8 mm at X800 and X820. Heights follow the actual
ellipse, within 0.001 mm; a flat floor would fail these checks. Sampling on either
side of X850 uses 0.1 mm spacing and verifies near-zero join slope/curvature.
The entire X850..950 cylinder has **0.0 mm³ missing volume**, and the complete
X850..1080 cylinder is also protected. This supersedes the earlier positive
cylinder-removal requirement, which represented the rejected interpretation.
Reference-angle shaded/edge views and the longitudinal cutaway were reviewed.

The outer 60 mm bands on either side of the seam match with zero symmetric
BREP difference; half-band/extrusion checks also pass, establishing a matching
outline and zero taper adjacent to the joint. Circular forebody slabs at X860,
X900, X960 and X1000 match radius86 cylinders with zero difference.

Fresh `cadgen step inspect validate` after the repair:

| Document | Occurrences | Prototypes | Failures |
|---|---:|---:|---:|
| Complete hybrid | 19 | 9 | 0 |
| Upper stage | 13 | 6 | 0 |
| Booster | 6 | 3 | 0 |
| Intake review | 7 | 7 | 0 |
| Internal-path cutaway | 2 | 2 | 0 |
| Toe-blend closeup | 1 | 1 | 0 |

Default first-placement self-intersection mode. Report:
`cad/halberd/Halberd_Shoulder_Hybrid_Checks.json`.

## Artifacts

- Master: `cad/halberd/Halberd_Shoulder_Hybrid.step`
- Reviews: same stem with `_Separated`, `_Upper`, `_Booster`, `_Intakes`, `_Seam`, `_Nose`, `_InternalPath`, `_Toe`.
- Sources: `generate_halberd_shoulder_hybrid.py`, `review_halberd_shoulder_hybrid.py`,
  `check_halberd_shoulder_hybrid.py`, `summarize_halberd_hybrid.py`, all in `cad/`.
- Snapshot job: `cad/halberd/halberd_shoulder_hybrid_snapshot_job.json`.
- Key PNGs: `cad/halberd/Halberd_Hybrid_iso.png`, `Halberd_Hybrid_nose_transition.png`,
  `Halberd_Hybrid_intakes.png`, `Halberd_Hybrid_separated.png`, all under `cad/`.
- Mouth/roof views: `cad/halberd/Halberd_Hybrid_intake_mouths.png`, `cad/halberd/Halberd_Hybrid_intake_roofs.png`.
- Reference-comparison view: `cad/halberd/Halberd_Hybrid_nose_edges.png`.
- Internal direction: `cad/halberd/Halberd_Hybrid_internal_path.png` and `cad/halberd/Halberd_Hybrid_internal_path_iso.png`.
- Smoothed junction: `cad/halberd/Halberd_Hybrid_toe_blend.png`, `cad/halberd/Halberd_Hybrid_toe_grazing.png`, `cad/halberd/Halberd_Hybrid_toe_edges.png`.
- Annotated-view comparison: `cad/halberd/Halberd_Hybrid_toe_reference.png`, `cad/halberd/Halberd_Hybrid_toe_reference_edges.png`.
- Review boards: `cad/halberd/Halberd_Hybrid_Board_1.png` through `cad/halberd/Halberd_Hybrid_Board_4.png`.
- Native repaired-render evidence: `cad/halberd/Halberd_Hybrid_NATIVE_FIXED_FRESH.png`.
- Unity exporter: `cad/halberd/export_halberd_hybrid_unity.py`; outputs only the derived
  `HalberdHybridMeshData.json` authoring packet under the dedicated Unity folder.
- Unity authoring candidate: `Assets/Blueprinter/Mods/HalberdHybrid/` in the
  Blueprinter Editor project, including 19 mesh assets, original procedural
  vanilla-style materials/textures, `Erenaldi.AAM44.HybridCandidate.prefab`, and
  `HalberdHybridTexturePreview.unity`.
- Unity review PNGs: `cad/halberd/Halberd_Hybrid_Unity_Textured.png`, `_Intakes.png`,
  `_Side.png`, `_Opposed.png`, and `_Separated.png`.

The Unity candidate has 41,950 triangles and 19 renderers. Its root is centered,
identity-scaled and script-free; the direct `Booster` child owns all booster
renderers. Albedo textures are sRGB and packed metallic/smoothness textures are
linear. Main-agent visual review found continuous upper-stage paint, readable
mirrored geometric markings, dark recessed intake interiors, no visible UV reset
at the body/radome boundary, and coherent separated-stage treatment.

This is authoring evidence only. No colliders, rack prefab, geometry bundle,
plugin embedding/install, aircraft-fit test, FX/jettison test, or runtime proof
was created. Those remain gated production-delivery work.
