# AAM-44 Halberd — Unity Delivery Contract (RC1, candidate staging)

> Historical detailed-RC1 track. The currently selected 19-part Shoulder hybrid
> is documented separately in `HALBERD_SHOULDER_HYBRID.md`. Its dedicated Unity
> authoring candidate does not promote, overwrite, bundle, or runtime-integrate
> this RC1 track.

**2026-09-14 — Status:** RC1 CAD/export candidate, visually reviewed by the
assistant and awaiting user approval. Nine OBJ meshes are staged outside Unity;
at that checkpoint, prefab, bundle, material, and gameplay integration had not
been performed. The active context below governs current interpretation of later
worktree artifacts.

## Historical RC1 track context

- **Current state:** `cad-review` for the RC1 candidate covered by this contract.
- **Authoritative source:** `cad/halberd/generate_halberd_detailed.py` and its generated
  `cad/halberd/AAM-44_Halberd_Detailed.step`, subject to a fresh source/output identity
  check before use.
- **Approved concept / review packet:** no user approval is recorded for this RC1.
  The 47-image packet listed below has assistant review only.
- **Coordinate system and scale:** CAD millimeters, +X forward, +Z dorsal, +Y
  lateral; Unity mapping `(X,Y,Z) -> (Y,Z,X) * 0.001`.
- **Preserve:** three-plane intake/fin arrangement, dorsal mounting corridor,
  separated-stage ownership, fixed stage/FX datums, open intake language, and
  recessed nozzle readability.
- **Avoid:** protruding cowl readings, flat forward-extending cuts, duplicate skin,
  wrong source substitution, and engine transforms used to hide CAD errors.
- **Emphasize:** a coherent ramjet/booster silhouette, readable intake depth, clean
  stage separation, and deliberate rather than incidental hardware.
- **Rejected interpretations:** prose-only intake revisions that changed the wrong
  positive/negative volume; CAD edits must now use the local change contract in
  `ASSET_DESIGN_WORKFLOW.md`.
- **Hard constraints:** dimensions, source labels, group ownership, transforms,
  triangle ceiling, and fixed datums in this contract.
- **Open decisions:** user CAD approval, material acceptance, source-to-Unity
  identity for newer worktree artifacts, pylon/contact fit, and current runtime
  proof.
- **Files required for the next gate:** this contract, the authoritative generator
  and STEP, current check/export reports, and the named review packet. Do not load
  unrelated weapon histories.

### Lifecycle evidence

| Boundary | State and evidence |
|---|---|
| Intent / concept | Historical direction is documented here, but no workflow-format concept approval is recorded for RC1. |
| CAD | Deterministic checks and assistant visual review are recorded; user approval is pending, so the state remains `cad-review`. |
| Export | Nine staged OBJ groups and independent export checks exist. They are candidate evidence, not production promotion while CAD approval is pending. |
| Engine | Existing Halberd Unity files and newer worktree artifacts are not proven by this contract to derive from this RC1 source. Representative engine approval is unverified. |
| Runtime | Existing dumps are explicitly from an older revision and cannot prove this candidate. |

Approval invalidation follows `ASSET_DESIGN_WORKFLOW.md`: silhouette changes reopen
CAD and later boundaries; export-only changes preserve CAD approval but reopen
export and later boundaries.

## RC1 checkpoint status summary

| Check | Result |
|---|---|
| Label count | **41** uniquely labeled parts |
| Master STEP validation | **41 occurrences / 25 prototypes**, zero failures |
| Upper-stage STEP validation | **30 occurrences / 18 prototypes**, zero failures |
| Booster STEP validation | **11 occurrences / 7 prototypes**, zero failures |
| Export triangles | **30,716** (baseline **21,106**) |
| Triangle budget | 75,000 — within limit |
| Approval state | `candidate-awaiting-review` |
| Unity integration | **Not done** — no prefab, bundle, or plugin work yet |
| Runtime proof | **None** — runtime dumps are from the old revision |
| Pylon contact | **Not validated** |

`check_halberd_detailed.py` passes the original checks plus positive-volume,
stage ownership, complete-upper-stage opening probes, recessed nozzle backing,
multi-station saddle seating, panel grooves, and shoe pockets. The occurrence /
prototype counts above are from `cadgen step inspect validate`, not test counts.
The 22 exporter unit tests pass. `check_halberd_export.py` independently reloads
all nine serialized OBJs and confirms counts, bounds, winding, semantic mapping,
stage placement and master SHA-256. The 47-image packet was generated and reviewed
via six labeled contact sheets plus full-size feature views. A bright sustainer
end face found during review was repaired upstream and the checks rerun.

## Masters and evidence

- Shared source: `cad/halberd/generate_halberd_detailed.py`, authored at final
  game scale in millimeters.
- Source STEP: `cad/halberd/AAM-44_Halberd_Detailed.step`, built by
  `cad/halberd/generate_halberd_detailed.py`.
- Candidate export: `cad/candidates/halberd/Halberd_Export_Report.json`
  and the nine `*_*.obj` groups under `cad/candidates/halberd/`.
- The old baseline is preserved at `cad/halberd/Halberd_Export_Report.json`
  (labeled **baseline**, not overwritten or replaced).
- Runtime evidence (`missile-geometry.json` under the game's
  `BepInEx/config/Erenaldi.MunitionsPackage/`) is from the **old
  revision**. It cannot serve as candidate runtime proof; it only
  confirms the pre-change state.
- The inspected runtime dump provides mesh envelopes, not rack contact
  transforms or FX paths. Exact mounted-display hierarchy, suspension
  alignment, and multi-rack clearances remain to be measured.

## Nine groups — exact labels and hierarchy paths

### Transform, tessellation, and runtime boundary

- CAD millimeters, +X forward, +Z dorsal, +Y lateral. Bake exactly
  `(X,Y,Z) -> (Y,Z,X) * 0.001` into mesh vertices, with no additional rotation
  or mirroring. The cyclic axis permutation preserves winding.
- Missile root: centered runtime origin `(0,0,0)`, identity rotation, unit scale.
  Do not recenter on the asymmetric fin-envelope bounding-box midpoint.
- Intake/fin azimuths remain 60, 180, 300 degrees; dorsal corridor stays clear.
- Rack: empty root, `pylon` visual, mounted display at `pylon/aam4` so the
  inherited `MountedMissile` hides the display after launch. Retain the existing
  mounted placement until aircraft-specific contact/clearance is measured.
- Runtime anchors: booster FX Unity `z=-1.6835 m`; sustainer FX
  `z=-0.3367 m`. All other anchor coordinates remain runtime-owned.
- Geometry prefabs may contain meshes, materials, and deliberate colliders only:
  no Missile/seeker/gameplay scripts, NetworkIdentity, particles, or audio.
- Root and `Booster` retain separate capsule colliders. Every booster collider
  and renderer must descend from the direct `Booster` child. Retain the baseline
  hull capsules rather than deriving a smaller collider from the recessed body.
- Export tessellation: 0.12 mm chord tolerance, 0.12 rad angular tolerance;
  75,000-triangle ceiling. Validate normals, winding, silhouette, group bounds,
  and axis landmarks again on Unity import. No LODs added in this pass.
- Target importer remains Unity 2022.3.62f2, StandaloneWindows64. Reuse existing
  materials and importer conventions after approval; compare UV placement because
  the body mesh's aft bound moves forward 5 mm. CAD palette previews are not
  evidence of Unity material appearance.
- The generated candidate report records master SHA-256 and exact group bounds.
  Production `cad/halberd/Halberd_Export_Report.json` is historical baseline evidence.

All 41 source labels map exactly once. The exporter rejects duplicate,
unknown, missing, or ambiguous labels and empty groups.

| Group | Labels | Proposed Unity renderer path |
|---|---|---|
| `body` | `ramjet_body`, `forward_body`, `seeker_section`, `radome` | root renderer; required by transplant contract |
| `intakes` | `intake_ramp_{1,2,3}`, `intake_lip_{1,2,3}`, `intake_duct_{1,2,3}`, `intake_cheek_{1,2,3}_{1,2}` | direct child `Intakes`, fixed |
| `sustainer_fins` | `sustainer_fin_{1,2,3}` | direct child `SustainerFins`, fixed; remains on missile root after stage separation |
| `hardware` | `stage_joint_band`, `ramjet_joint_band`, `forward_joint_band`, `dorsal_launch_rail`, `suspension_lug_{1,2}`, `dorsal_wiring_conduit` | direct child `Hardware`, fixed |
| `sustainer_nozzle` | `sustainer_nozzle` | direct child `SustainerNozzle`, fixed |
| `booster_body` | `booster_body`, `booster_forward_collar`, `booster_nozzle_outer` | `Booster` renderer |
| `booster_fins` | `booster_fin_{1,2,3}`, `booster_fin_root_{1,2,3}` | `Booster/Fins` |
| `booster_nozzle` | `booster_nozzle_inner` | `Booster/Nozzle` |
| `booster_nozzle_recess` | `booster_nozzle_recess` | `Booster/NozzleRecess` |

The `SustainerFins` child and the body renderer remain on the missile root
after stage separation. Booster body, fins, nozzle, and collider all
remain below the direct `Booster` child required by runtime jettison.

**Flat intakes group note:** The `intakes` group contains 15 labels
(ramps, lips, ducts, cheeks) that share a combined renderer in the
exported OBJ. Per-part CAD colors assigned in `generate_halberd_detailed.py`
(`style()` calls) **cannot be preserved as separate per-part colors** in
this flat group — the OBJ merges them into a single mesh. Material
separation within the intakes group must be handled at the Unity material
layer (e.g., submesh splits or texture atlases), not inherited from CAD
part colors.

## Changes from baseline

All changes below are measured against the old baseline
(`cad/halberd/Halberd_Export_Report.json`, 21,106 triangles, maximum radius
0.218082553 m). The baseline is preserved as-is and labeled **baseline**;
this document records the RC1 delta.

### Beveled intake cheek shoulders
Intake cheek top edges now carry a 2 mm beveled transition.
The cheek loft overlaps the changing
duct sidewall at every section, preventing visible separation along the
taper.

### Tapered hexagonal saddle fin roots and tips
Root fairings changed from constant-width prisms to tapered hexagonal saddles.
The fin blades also taper in thickness toward their tips:

| Blade | Root thickness | Tip thickness |
|---|---|---|
| Sustainer | 8 mm | **6 mm** (previously 8 mm) |
| Booster | 12 mm | **8 mm** (previously 12 mm) |

The `root_fairing()` helper in `generate_halberd_detailed.py` now
produces a tapered hexagonal profile via `bd.Solid.make_loft` over
six-point polygon wires, embedded into the body with narrow shoulders.

### Tapered annular collars
Annular trim bands (collars) at stage joints are now tapered with
sloped shoulders instead of stacked solid drums:

| Collar | Rise |
|---|---|
| Stage 2 (sustainer) | **2 mm** |
| Ramjet | **1.5 mm** |
| Forward | **1.8 mm** |
| Booster | **3 mm** (vs old) |

Implemented via `tapered_band()` — a lofted annular ring with
`bevel` parameter controlling the shoulder slope.

### Shallow panel grooves
New shallow panel grooves cut into the body surface:

| Property | Value |
|---|---|
| Width | **1.4 mm** |
| Depth | **0.65 mm** |
| Location | Seeker near radome; booster ends |

Implemented via `panel_ring()` — an annular cylinder subtraction
creating a shallow recessed ring. The grooves are shallow cuts, not
disconnected rings; `check_halberd_detailed.py` verifies this with
witness-volume intersection tests at the groove stations.

### Shoe pockets
Suspension lugs now carry shallow inset pockets (`lug -= bd.Box(...)`)
so the shoes read as hardware without fragile bolt features. The
pocket depth is 1.3 mm below the lug's upper surface.

### New genuine blind sustainer visual recess
A new blind visual recess is added to the sustainer section:

| Property | Value |
|---|---|
| Sleeve axial extent | **82 mm**, including 4 mm closed backing |
| Visible cavity depth | **78 mm** |
| Sleeve outer radius / mouth radius | **76 mm / 70 mm** |
| Type | Blind — dark closed backing, not internal engine geometry |
| Body start | **Seam + 5 mm** (not at the seam) |
| Nozzle position | Still at the seam |

The recess is authored in `make_sustainer_nozzle()` as a closed
cylinder subtraction with a lofted cavity that tapers from 70 mm to 32 mm
radius. A radial bridge joins the trim to the recessed sleeve without
closing its mouth.

**Collider note:** The collider should retain the **baseline physical hull**
rather than silently shrinking from the new body mesh. The visual recess
is surface detail only; the runtime collider must still approximate the
original body envelope. This is a known gap — the collider transplant
logic in `CustomGeometryLoader.cs` copies colliders from the custom
prefab, so the custom prefab's collider must be authored to match the
baseline hull, not the recessed geometry.

### Fixed datums (unchanged by design)
The following are fixed and must not drift:

| Datum | Value |
|---|---|
| Overall length | **3.367 m** |
| Body diameter | **0.201 m** (radius 0.1005 m) |
| Pivot | X = 0 (nose-forward, exhaust at -length/2) |
| Stage seam | **z = -0.3367 m** |
| FX anchor | Fixed at CAD X = -1683.5 mm |
| Radome | Unchanged by intentional baseline inspection |
| Booster nozzle | Unchanged by intentional baseline inspection |

### Radial measurement delta

| Report | Maximum radius |
|---|---|
| Old baseline | 0.218082553 m |
| RC1 candidate | **0.218036694 m** |
| Delta | **-0.000045859 m** (-0.046 mm) |

The radial decrease is within the exporter's `RADIAL_LIMIT_METERS`
tolerance (0.219 m + 1e-4) and follows the tapered saddle and collar
revisions. The `validate_bounds()` check enforces `maximum_radius <=
RADIAL_LIMIT_METERS + 1e-4`.

## Material contract

The Halberd ships with original vanilla-style textures per the existing
`HalberdTexturedMaterialBuilder.cs` contract (albedo + packed
metallic/smoothness, panel seams, rivets, geometric service marks;
palette measured in `docs/TEXTURE_STYLE_FINDINGS.md`). The Halberd body
uses a seam-deduplicated full-2π cylindrical unwrap.

**No materials have been edited in this RC1 pass.** The material contract
is pending — the candidate OBJ groups carry no Unity materials and no
texture assignments. Material assignment is a future pass after visual
approval.

## Evidence ledger

| Item | Classification |
|---|---|
| 41 labels, one positive-volume solid each | **Measured** (`cad/halberd/check_halberd_detailed.py`) |
| 41/25 master, 30/18 upper-stage, 11/7 booster occurrences/prototypes; zero failures | **Measured** (`cadgen step inspect validate`) |
| 30,716 export triangles | **Source-measured** (`cad/halberd/export_halberd_unity_mesh.py`) |
| Beveled cheeks, tapered saddles/collars, grooves, shoe pockets, blind recess | **Assistant artistic decisions** within authorized scope |
| 82 mm sleeve extent, 76 mm sleeve radius, seam+5 mm body start | **Assistant artistic decisions**, source-verified |
| Radial delta (-0.046 mm) | **Source-measured** (candidate vs baseline report) |
| Fixed datums (length, diameter, pivot, seam, FX) | **User-specified** constraints |
| Radome + booster nozzle retained | **Assistant decision** after baseline inspection |
| Material reuse, no materials edited | **User-specified** contract |
| Flat intake export does not retain CAD color subdivisions | **Current exporter limitation**, not an OBJ format restriction |
| Visual approval of RC1 | **Aesthetic judgment** — pending user review |
| Unity prefab/bundle/runtime integration | **Not yet attempted** |
| Rack/pylon contact validation | **Not validated** |
| Candidate runtime proof | **Not available** (runtime dumps are old revision) |

## Stage gates

1. **CAD master RC1** — 41 occurrences / 25 prototypes, zero failures.
   Deterministic checks and assistant visual review complete.
2. **Candidate export** — Nine OBJ groups staged to
   `cad/candidates/halberd/`. 30,716 triangles, within budget.
   ✅ Complete.
3. **Visual/user approval** — User reviews RC1 renders and STEP views.
   ⏳ Pending.
4. **Unity prefab authoring** — Create Unity prefabs matching the
   nine-group hierarchy, apply materials per the existing contract.
   ⏳ Not started.
5. **Bundle build & embedding** — Build `erenaldi_munitions.geometry.bundle`,
   embed in plugin DLL.
   ⏳ Not started.
6. **Runtime validation** — Launch game, confirm `[Phase 3]` geometry
   load lines, transplant 2/2, correct hardpoint alignment, launch FX.
   ⏳ Not started. Requires fresh runtime dumps (current dumps are old revision).
7. **Pylon/contact validation** — Measure rack contact transforms and
   multi-rack clearances. ⏳ Not validated.

## Review artifacts

The main and all six originally requested review STEPs were rebuilt from the
current master. Additional reviews cover intake/body context, the seam, the
exposed sustainer nozzle, and separated stages (350 mm display-only gap).
`cad/halberd/halberd_detailed_snapshot_job.json` declares all 47 views. Full-resolution
PNGs are in `cad/`; `cad/halberd/summarize_halberd_review.py` generates six labeled
`cad/candidates/halberd/Halberd_review_sheet_*.png` contact sheets.
Primary views: `Halberd_detailed_rendered.png`, `Halberd_separated_iso.png`,
`Halberd_sustainer_nozzle_close.png`, `Halberd_nozzle_rendered.png`,
`Halberd_intake_context_rendered.png`, `Halberd_mount_top.png`.
Camera signs were corrected: +X sees the nose, -X sees the exhaust, +Z sees dorsal.

## Known limitations and gaps

- **No candidate runtime proof.** Runtime dumps are from the old
  revision. The candidate has not been launched in-game.
- **Pylon contact not validated.** The inspected runtime dump provides
  mesh envelopes only; exact mounted-display hierarchy, suspension
  alignment, and multi-rack clearances remain to be measured.
- **Flat intakes per-part colors.** The `intakes` group is a single
  merged OBJ; per-part CAD colors cannot be preserved. Material
  separation must be handled at the Unity layer.
- **Collider retention.** The new blind sustainer recess changes the
  visual body mesh; the collider must retain the baseline physical hull
  and must not silently shrink. This requires explicit authoring in the
  Unity prefab and verification in the loader transplant.
- **Dark CAD shading:** recessed detail is subtle in rendered views; section
  and edge-visible diagnostics establish shape. Unity lighting is not verified.
