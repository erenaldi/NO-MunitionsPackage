# AGM-110 Ballista RC2 — AGM-48/AGM-68 midpoint width rescale

## Active context

- **Current state:** `cad-review`. CAD, Unity, and historical runtime work exist,
  but this contract does not record final user visual approval of the current RC2
  packet or runtime acceptance of the current packaged artifact.
- **Authoritative source:** `cad/ballista/ballista_geometry.py`, with
  `cad/ballista/AGM-110_Ballista_Stowed.step` and
  `cad/ballista/AGM-110_Ballista_Deployed.step` as generated pose masters.
- **Approved concept / review packet:** user-directed reference work shaped the
  candidate, but the 27-image packet remains documented as awaiting final visual
  approval.
- **Coordinate system and scale:** CAD millimeters, +X forward, +Z dorsal, +Y
  lateral; Unity mapping `(X,Y,Z) -> (Y,Z,X) * 0.001`.
- **Preserve:** broad chamfered body, long swept folding-wing identity, compact
  tail controls, faceted seeker, recessed propulsion and intake features, and
  distinct stowed/deployed states.
- **Avoid:** board-like or weakly aligned wings, accidental loft inflation,
  undocumented recentering or axis correction, exterior upper scoops, and donor
  behavior inferred only from serialized fields.
- **Emphasize:** shaped-charge standoff identity, clean wing-body integration,
  visible deployment mechanics, and restrained vanilla-compatible detail.
- **Rejected interpretations:** combined intake/scoop revisions that changed the
  intended recess language and folding changes that did not preserve the approved
  planform or motion reading.
- **Hard constraints:** RC2 dimensions, label/group mapping, transform and pivot
  datums, motion ownership, material separation, and runtime-owned components in
  this contract.
- **Open decisions:** explicit RC2 visual approval, authoritative current bundle
  identity, final rack/deployment/FX review, and a recorded acceptance flight for
  the current propulsion and transition behavior.
- **Files required for the next gate:** this contract, the shared CAD source, both
  pose masters, current deterministic reports, and the named review images.

### Lifecycle evidence

| Boundary | State and evidence |
|---|---|
| Intent / concept | References and user-directed revisions are documented, but there is no workflow-format approval record for the current RC2 packet. |
| CAD | Both pose masters and deterministic checks are recorded as passing; user visual approval remains pending, so the controlling state is `cad-review`. |
| Export | Current reports and Unity assets exist, but source identity and the applicable RC2 export must be re-verified before promotion. |
| Engine | Prefabs and bundle work exist in the worktree. Their presence is not equivalent to representative engine visual approval. |
| Runtime | Historical flight tests found and drove repairs for rack visibility, deployment, drag, propulsion sequencing, and FX. Final current-artifact runtime acceptance is not recorded. |

The RC1 implementation-status wording retained below is historical. The active
context and RC2 table govern current state; no existing file is promoted solely by
modification time or proximity.

**RC2 supersedes the RC1 numbers below.** Per user direction the central body
cross-section moved to the midpoint of the AGM-48 and AGM-68 central body
diameters, both slice-measured from runtime mesh dumps: AGM-48 **180 mm**
(`AGM1.geometry.obj`), AGM-68 **300 mm** (`AGM_heavy.geometry.obj`) →
**240 mm** body width/height (`LATERAL_SCALE = 0.8109` of RC1 laterals; axial
constants are untouched). Key RC2 values, all enforced by
`cad/ballista/check_ballista.py` and `cad/ballista/Ballista_checks.json`:

| Property | RC2 value |
|---|---|
| Body cross-section | 240 × 240 mm (length unchanged 2594.424 mm) |
| Stowed full bounds | 2594.424 × 322.805 × 322.805 mm → Unity 0.3228 × 0.3228 × 2.5944 m |
| Deployed full bounds | 2594.424 × 1456.522 × 322.805 mm → span 1.456522 m |
| Wing pivot datums (CAD) | (395, ±63.65, -119.20); stowed 0°, deployed ±40° |
| Wing pivot child transforms (Unity) | (∓0.06365, -0.11920, 0.395) |
| Export triangles | 35,786 per pose (budget 75k) |
| Enclosed volume / launch mass | 0.131369 m³ → **175 kg** at the AGM-68 (1332 kg/m³) and AGM-48 (1304 kg/m³) density anchors |
| Prefabs / bundle | `Erenaldi.AGM110` + `Erenaldi.AGM110_single` in `erenaldi_munitions.geometry.bundle` |
| Plugin donor | AShM2 (AGM-99) def + `AGM_heavy_single` carriage; VLS booster self-removes on air launch |

Both STEP validations pass with 0 findings; the review packet was re-rendered.
The RC1 tables below remain as the detailed contract whose structure (axis
map, groups, movable wings, materials, anchors) is unchanged; replace their
numbers with the RC2 table above when in doubt.

---

# AGM-110 Ballista RC1 — full-chord aligned wings and 40-degree deployment

Historical RC1 status: CAD release candidate for user visual approval. Unity
meshes, prefabs, animation, bundles, and gameplay integration had not been
implemented in that pass. The exterior preserves the Ballista shaped-charge standoff identity;
internal warhead and propulsion engineering are outside this art model.

## Masters and evidence

- Shared source: `cad/ballista/ballista_geometry.py`.
- Stowed master: `cad/ballista/AGM-110_Ballista_Stowed.step`, built by
  `cad/ballista/generate_ballista_stowed.py`.
- Deployed master: `cad/ballista/AGM-110_Ballista_Deployed.step`, built by
  `cad/ballista/generate_ballista_deployed.py`.
- Both contain **58 labeled positive-volume solids**, classified into 13 semantic
  groups by `semantic_group()`; `cad/ballista/check_ballista.py` independently enumerates
  the expected labels. Review crops are diagnostic derivatives, not masters.
- The intake revision supersedes the initial RC1 tree identities. Check the
  current source/output identity with `cadgen store why` before a later export.
- The user's multi-view image governs long swept wings, compact tail controls,
  low-profile hardware, and restrained detail. Its exact scale, folding axis,
  and internal mechanisms are not measured facts. Rectangular chamfered body
  and faceted EO treatment follow the requested SPICE 250 hybrid direction.
- Runtime evidence: `missile-geometry.json`, under the game's
  `BepInEx/config/Erenaldi.MunitionsPackage/`, records `AGM_heavy_single` /
  `AGM_heavy` at **2470.88 x 493.303031 x 493.302822 mm** overall. The radial
  measurements include appendages; they are not a fuselage diameter.
- The body retains 105% of that length and 60% of the lateral envelope.
  `MUNITIONS.md`'s older 4.8 m body target is superseded for this visual candidate
  by the user's current baseline. This does not retune mass, range, or damage.

## Scale, basis, and pivot

| Property | CAD | Unity delivery requirement |
|---|---|---|
| Units | millimeters | meters; multiply by 0.001 exactly once |
| Forward / dorsal | +X / +Z | +Z / +Y |
| Lateral | +Y | +X |
| Basis map | `(X,Y,Z)` | `(Y,Z,X) * 0.001`, matching Halberd exporter |
| Root | body-midpoint datum `(0,0,0)` | identity rotation, unit scale, no recentering |
| Body dimensions | 2594.424 x 295.981819 x 295.981819 | 0.295982 x 0.295982 x 2.594424 m in Unity XYZ |
| Stowed full bounds size | 2594.424 x 398.101118 x 398.101118 | 0.398101 x 0.398101 x 2.594424 m |
| Deployed full bounds size | 2594.424 x 1505.618857 x 398.101118 | 1.505619 x 0.398101 x 2.594424 m |

The coordinate permutation has positive determinant; it introduces no geometric
reflection. Verify triangle winding and transformed landmarks in the selected
Unity importer rather than adding an undocumented axis flip.

Deployed span is now **1505.619 mm**, superseding the previous 1240.387 mm
candidate and original 1050 mm baseline. The increase follows the user's wider
wing and larger deployment-angle direction. The entire stowed width and height are about **80.7%** of
the AGM-68 mesh envelope. Length is 5% greater, so this is scale plausibility,
not proof of fit on every rack. The vanilla mesh's axial bounds are asymmetric
(-1.167039/+1.303841 m); do not inherit that midpoint offset into this centered CAD.

## Groups and movable wings

All source labels must map exactly once. Export must reject duplicate, unknown,
or missing labels and empty groups. Geometry colors/material boundaries remain
separate submeshes even when multiple fixed parts share a renderer.

| Source labels | Semantic group | Proposed renderer path / motion |
|---|---|---|
| `Body` | `body` | root renderer; required by transplant contract |
| `SeekerWindow` | `seeker_glass` | direct child `SeekerGlass`, fixed |
| `SeekerBezel`, `SeekerSeal` | `seeker_bezel` | direct child `SeekerBezel`, fixed |
| `WingLeft`, `WingLeftPivotCap` | `wing_left` | direct child `WingLeft`, one movable mesh group |
| `WingRight`, `WingRightPivotCap` | `wing_right` | direct child `WingRight`, one movable mesh group |
| `TailControl1` through `TailControl4` | `tail_1` through `tail_4` | four separate direct children; neutral pose only |
| `HybridNozzle`, `Nozzle*` | `propulsion` | direct child `Propulsion`, fixed |
| `IntakeLeftDuct`, `IntakeLeftRamp`, `IntakeLeftSplitter1/2`, and corresponding `IntakeRight*` labels | `intakes` | direct child `Intakes`, fixed; retain ramp/liner material separation |
| `MountRail`, `ForwardLug`, `AftLug`, `DorsalUmbilicalCover` | `mounting` | direct child `Mounting`, fixed |
| `WingBay*`, `TailRoot*`, `AftService*`, `Avionics*`, `StowageEdge*`, `Vent*`, `PanelFastener*`, `SeekerIdentificationBand` | `fixed_hardware` | direct child `FixedHardware`, fixed |

Wildcard rows describe the enumerated RC1 label set, not permission to accept
new labels. `VentralServiceCover` is included by `Vent*`.

Wing pivots in CAD are **(395,-78.5,-147)** left and **(395,78.5,-147)** right.
Both axes are CAD +Z. Stowed angle is exactly zero; deployed rotation is **+40 degrees
left / -40 degrees right**, an 8-degree increase. A wing runs along local -X when stowed. Preserve
this rigid shape; do not scale, morph, or exchange different wing meshes.

For engine export, subtract the relevant pivot from stowed CAD wing vertices,
then apply the basis/scale map. Set direct child renderer positions to Unity
**(-0.0785,-0.147,0.395)** and **(0.0785,-0.147,0.395)**. Convert the CAD rotation
matrix by `R_unity = P * R_cad * inverse(P)`; compare posed vertex landmarks to
the deployed master to avoid handedness/Euler-sign assumptions. Caps move with
their wings; the bay cover and axle remain fixed. The source STEP files contain
static poses, not persistent animation constraints.

The main wing chord is now **136 mm**, with parallel longitudinal edges instead
of a long taper. Both folded panels retain the previous X=-580..+425 mm axial
envelope. Their main span runs at Y=10.5..146.5 mm on the right and the mirrored
interval on the left, leaving a **21 mm central gap** and **1.491 mm projected
gap to each maximum-width body side**. These clearances reserve space for the
hinges and motion rather than demanding coincident wing/body surfaces. Small
clipped ends complete the planform. Independent cross-section checks at five
axial stations verify constant chord and zero folded yaw/pitch; full bounds
also verify the intended 15 mm unrolled thickness.

The hinge axes moved 25 mm forward and 3.5 mm inward relative to the previous
revision, with matching fixed seats. The wing local endpoints changed to retain
its world-space stowed length. A short root-corner chamfer keeps the wider panels
clear during the first degrees of movement as well as at full deployment.

The wing bays, axles, wings, and pivot caps move **27 mm dorsally** into matching
hull pockets. At maximum blade thickness, approximately 57% of the 15 mm section
lies inward of the nominal ventral skin. The certified rectangular clearance
regions run from X=-600 to +480 with a ceiling at Z=-133.5. The tray cores start
at lateral magnitude 10 mm. Finished tray cuts expand that envelope by 6 mm with **6 mm
shoulder/floor radii**, making the finished flat ceiling Z=-127.5 and leaving
a nominal 8 mm central keel before its lip rounds. Clearance witnesses use
inscribed boxes reaching lateral magnitude 4 mm at or below Z=-133.5, and are
checked against the exported hull before their bounds certify wing movement.
The tray's forward extension clears the wider root at 40 degrees. Deeper fixed-bay sockets
use **3 mm radii**, keeping their seating height and 0.8 mm intentional hull
contact. Exposed underside lips receive **2 mm radii**. These are curved CAD
surfaces, not a normal-smoothing substitute. The pockets are shared by
both poses and provide room for deployment. The detailed aft-service intake
assemblies now sit at CAD X=-668 mm, with no exterior upper scoops.

Use direct renderer children: the present transplant copies renderer-local
transforms, but does not generally copy transforms on arbitrary empty ancestor
nodes. A nested, translated empty pivot parent would therefore be unsafe without
later loader work. Tail roots intentionally overlap their neutral control roots;
tail articulation is not yet designed or clearance-validated.

## Materials and tessellation expectations

The intake revision replaces the six shallow `VentLeft/Right1/2/3` strips with
two recessed assemblies. Each has a chamfered open liner, shaped multi-break
ramp, and two finite-thickness splitter vanes forming three channels. The outer
liner is 42 mm deep, from CAD lateral magnitude 110 to 152 mm; its lip projects
only 4.009 mm beyond the main side wall. The body and existing service frames
are actually cut open. Both complete intake assemblies have moved **200 mm toward
the nose**, from X=-868 to **X=-668 mm**. Their frames, ramps, splitter vanes,
fasteners, and hull cutouts share that translation; the former sockets are healed
by regenerating the body. Intake fasteners are now at X=-751/-585 mm so the
new lip leaves their heads exposed. Splitters use the satin panel material to
avoid bright white highlights at full-asset scale. These are exterior art
passages with modeled backs, not a validated engine duct or airflow design.

Preserve the mouth openings and ramp depth during tessellation/LOD generation.
`check_ballista.py` tests 25 mm-deep witness volumes in all three channels per
side, liner/body separation, ramp/splitter attachment, fastener clearance, and
mirrored geometry. The eight intake solids remain fixed between both wing poses.
Placement checks lock the new intake/frame centers and verify material has been
restored at both former intake locations.

The CAD palette uses nine source colors: body `#626C70`, panels `#4E595F`, wings
and controls `#747E83`, hardware `#303B42`, exposed edges `#8D9699`, glass
`#2B4858`, nozzle `#66554C`, recesses/seals `#192329`, and accent `#BD8839`.
Use lit materials with satin body surfaces, low-roughness opaque tinted glass,
matte recesses, and moderately metallic nozzle/edge pieces. Preserve material
separation; a later atlas may consolidate the nine color classes. STEP retains
colors, not all `cad_material` roughness/metalness hints, so the exporter must
read the source material intent rather than assume STEP carries a complete PBR setup.

Initial export targets, **not measured delivery results**:

- Reuse the existing OBJ/grouping approach demonstrated by
  `cad/halberd/export_halberd_unity_mesh.py`; no Ballista exporter exists yet.
- Start with 0.12 mm chord tolerance and 0.12 rad angular tolerance; examine the
  nozzle rim, optic chamfers, finite wing edges, and thin seams after export.
- Provisional LOD0 ceiling: 75,000 triangles for the complete missile, matching
  the existing Halberd ceiling. Preserve split normals at designed body/wing
  facets; smooth curved nozzle/cap and pocket-blend surfaces across tangent joins.
  No duplicate coincident skin.
- Export/import landmark and bounds agreement within 0.5 mm; no nonuniform
  scale, compression, or welding across movable/material boundaries.
- LOD1 may bake fasteners and shallow panel detail; LOD2 must retain both wings,
  all four controls, the nose outline, and a dark aft opening. Budgets and screen
  thresholds require engine measurements after approval.
- Keep collision separate from render topology. Propose a small set of primitive
  body colliders; no dense render-mesh collider or wing collider is delivered here.

## Runtime-owned anchors and carriage

These are authored destination datums, not claims about existing transform names:

| Datum | CAD mm | Unity m |
|---|---|---|
| Nose plane | `(1297.212,0,0)` | `(0,0,1.297212)` |
| Exhaust exit, facing aft | `(-1297.212,0,0)`, direction -X | `(0,0,-1.297212)`, direction -Z |
| Seeker glass face | `(1285.212,0,0)` | `(0,0,1.285212)` |
| Forward shoe top center | `(155,0,170.990909)` | `(0,0.170991,0.155)` |
| Aft shoe top center | `(-330,0,170.990909)` | `(0,0.170991,-0.330)` |

Preserve the clone's Missile, seeker, Mirage components, Effects/FX references,
audio, and MountedMissile behavior. The future art prefab must carry geometry,
materials and deliberate colliders only. Do not put gameplay scripts or copied
FX into it. Reposition existing motor FX to the authored exhaust datum during
integration after discovering their actual paths and local orientation.

The inspected runtime dump provides mesh envelopes, not rack contact transforms
or FX paths. Exact AGM-68 mounted-display hierarchy, suspension alignment, and
multi-rack clearances remain to be measured. The current loader is reusable but
Ballista registration/geometry application has not been implemented. A future
asset name such as `Erenaldi.AGM110` is a proposal, not an existing registered key.

## Verification and review

With the dedicated CAD venv on PATH, run from `cad`:

```powershell
python generate_ballista_stowed.py
python generate_ballista_deployed.py
python -u check_ballista.py
cadgen step inspect validate AGM-110_Ballista_Stowed.step --every-placement --out Ballista_stowed_validation.json
cadgen step inspect validate AGM-110_Ballista_Deployed.step --every-placement --out Ballista_deployed_validation.json
python generate_ballista_reviews.py
cadgen step snapshot --job ballista_snapshot_job.json
cadgen step snapshot --job ballista_intake_snapshot_job.json
cadgen viewer --host 127.0.0.1 --json
```

Full-chord revision results: both 58-occurrence validations pass with zero findings. The
deterministic report `cad/ballista/Ballista_checks.json` passes bounds, positive-volume
BREPs, label/group identity, fixed-part symmetric differences, mirrored controls,
rigid wing transformations, attachment contact, and open optical/exhaust paths.
The STEP round-trip also verifies cylindrical pocket-blend faces at all three
authored radii: six at 2 mm, sixteen at 3 mm, and ten at 6 mm in each pose.
It tests **21 wing angles from 0 to 40 degrees**, certifying approximately **6.000 mm**
clearance to the checked fixed geometry, excluding intended pivot contact.
Minimum certified wing-to-wing clearance over those samples is **20.634 mm**,
passing the existing 20 mm separation requirement. The opposite fixed bay is
also checked for wing intersection at every angle.
The original 5 mm minimum remains enforced. Tray half-space bounds are used only
after verifying that the corresponding witness volumes are empty in the exported
hull. Other obstacles retain bounding-box checks with exact-distance fallback.
Outside the root cylinder it checks wing/bay overlap separately. This is sampled
clearance, not a continuous swept-volume proof or aircraft fit validation.

Tool caveat: `cadgen step inspect refs --facts --planes --positioning` succeeds
but its cached summary overestimates the maximum X by 1 mm. The independent STEP
round-trip BREP bounds in `Ballista_checks.json` are centered at zero and govern
this contract. The cached summary discrepancy remains a tooling issue to resolve
before using that summary as an export bound oracle.

The refreshed 27-image packet in `cad/ballista/ballista_snapshot_job.json` includes full-model
opposed views and orthographics, material previews, seeker grazing views,
propulsion/tail closeups and section, mounting views, and wing deployment/root
details. Its cropped body caps are diagnostic cuts, not extra release geometry.
The two `Ballista_wing_recess_*` images isolate the hull pockets without wings
obscuring the curved shoulder and floor transitions.
The five additional views in `cad/ballista/ballista_intake_snapshot_job.json` show the
intake face, opposed obliques, grazing depth, and a half-section.
The source repair pass seated the wing housings against the body, tapered the
tail saddles, corrected the side-detail vertical mapping, and added the optical
seal. Final CAD views were reviewed for silhouette, exposed gaps, material
separation, and opposite-side coverage. Representative Unity lighting, mesh
budgets, rack fit, deployment timing, and multiplayer behavior remain unverified.

### Review entrypoints

- [Smoothed wing recesses, isolated hull](../cad/ballista/Ballista_wing_recess_smoothing.png)
- [Smoothed recesses, opposite view](../cad/ballista/Ballista_wing_recess_opposite.png)
- [Detailed intake](../cad/ballista/Ballista_intake_detail.png)
- [Intake section](../cad/ballista/Ballista_intake_section.png)
- [Deployed material view](../cad/ballista/Ballista_deployed_material.png)
- [Deployed underside](../cad/ballista/Ballista_deployed_material_belly.png)
- [Stowed material view](../cad/ballista/Ballista_stowed_material.png)
- [Wing deployment: 0 / 20 / 40 degrees](../cad/ballista/Ballista_wing_deployment.png)
- [Wing root](../cad/ballista/Ballista_wing_root_grazing.png)
- [Seeker](../cad/ballista/Ballista_seeker_detail.png)
- [Propulsion and tail](../cad/ballista/Ballista_propulsion_detail.png)
- [Propulsion section](../cad/ballista/Ballista_propulsion_section.png)
- [Dorsal mounting](../cad/ballista/Ballista_mount_detail.png)
