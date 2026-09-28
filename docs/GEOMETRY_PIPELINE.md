# Custom Geometry Pipeline (Path A — plugin-authoritative transplant)

The plugin remains the single registration/tuning authority. Custom art ships as a
pure-geometry AssetBundle; the plugin transplants visuals onto the runtime-cloned
prefabs. Component data (Missile, seeker, motors, Mirage networking) stays owned by
the clone pipeline — see `docs/PHASE2A_FINDINGS.md`.

Reference-driven assets must first follow
[`ASSET_DESIGN_WORKFLOW.md`](ASSET_DESIGN_WORKFLOW.md). That workflow owns visual
intent, concept selection, approval provenance, lifecycle state, and the rule that
the primary multimodal model reviews visual packets directly. This document owns
the approved CAD-to-Unity transplant path; it does not turn CAD validity into
visual, engine, or runtime acceptance.

Evidence boundaries are independent:

1. `cad-approved` proves the applicable source checks and user CAD review.
2. `export-validated` proves the serialized mesh matches its delivery contract.
3. `engine-review` proves the imported hierarchy and presentation are under review;
   it passes only with representative engine captures.
4. `runtime-review` proves the packaged asset is being exercised in game.
5. `runtime-accepted` requires the applicable loadout, launch, transition, effects,
   flight-role, packaging, and fallback rows to pass.

## Loader behavior (`CustomGeometryLoader.cs`)
- After the clone graph is wired, the loader looks for an embedded resource
  `erenaldi_munitions.geometry.bundle` (any single `*.bundle` resource is accepted as
  fallback).
- From the bundle it loads GameObjects named exactly:
   - `Erenaldi.AAM44` — missile geometry
   - `Erenaldi.AAM44_single` — rack geometry
   - `Erenaldi.IRMS4` — Kris missile geometry
   - `Erenaldi.IRMS4_single` — Kris rack geometry
- Transplant per prefab:
  - Copies `MeshFilter.sharedMesh` + `MeshRenderer.sharedMaterials` for every
    renderer in the custom prefab, matched onto the clone by relative child path
    (children are created when missing).
  - Removes the clone's colliders (except those on particle systems) and copies
    Capsule/Box/Sphere/Mesh colliders from the custom prefab.
- Untouched (must stay runtime-owned): `Missile`, all seeker components, `NetworkIdentity`,
  `MissileNetworkTransform`, motor FX references, `Effects` child anchors, audio
  sources, `MountedMissile` rail config.
- Fallback: no bundle, missing prefab, or any load error → vanilla geometry is kept
  and a `[Phase 3]` log line explains why. Gated by BepInEx config
  `Phase 3 > EnableCustomGeometry`.

## Authoring contract (Unity project)
1. Unity **2022.3.62f2** (exact game version), build target **StandaloneWindows64**.
2. Prefab requirements:
   - Missile: root carries the main body `MeshFilter`/`MeshRenderer` (the loader
     overwrites the clone's root visual only if the custom root has a renderer —
     always put the body mesh on the root). Children allowed for fins/canards.
    - Halberd rack: root is empty; `pylon` carries the pylon visual, and
      `pylon/aam4` carries the mounted missile display. Matching the source mount's
      `MountedMissile` path ensures the display is hidden after launch.
   - Colliders should approximate the visual hull (capsule preferred for the
     missile body).
   - Author missile geometry centered on the runtime pivot (exhaust at
     `-length/2`, nose at `+length/2`). A `0..length` authoring convention
     offsets the visual and collider forward of the physics body, and any
     preserved motor FX anchors must be repositioned to the custom tail after
     transplant (lesson from a retired prototype).
   - Do NOT add scripts, `NetworkIdentity`, particle systems, or audio — the clone
     already carries all gameplay components; extra components are ignored or can
     break the transplant.
3. Materials: the Halberd, Kris, and Ballista ship original vanilla-style
   textures (`HalberdTexturedMaterialBuilder.cs`, `KrisTexturedMaterialBuilder.cs`,
   `BallistaTexturedMaterialBuilder.cs` — albedo + packed metallic/smoothness,
   panel seams, rivets, geometric service marks; palette measured in
   `docs/TEXTURE_STYLE_FINDINGS.md`). Halberd/Kris bodies use a seam-deduplicated
   full-2π cylindrical unwrap; Ballista groups share the same unwrap via
   `KrisMeshBuilder.GenerateCylindricalUVs`; Kris hardware/dark/gridfins/seeker
   and Ballista hardware/edge/glass/nozzles stay flat-color (Kris seeker keeps
   Complex Lit clearcoat). Markings carry no stencil text by user preference.
   Do not bake vanilla textures into any shipped asset.
4. Approved baseline (RC1 candidate differences below): `cad/halberd/generate_halberd_detailed.py` authors the Halberd directly at
   final game scale in millimeters. CAD +X is forward, +Z is dorsal, and +Y is
   lateral; `cad/halberd/export_halberd_unity_mesh.py` maps those axes to Unity +Z, +Y,
   and +X respectively and converts millimeters to meters. The approved model
   is 3.367 m long with a 0.201 m body diameter, a 0.2181 m maximum radius, and
   a stage seam at Unity z=-0.3367 m. Three swept-trapezoid ramp-intake/strake
    assemblies use open U-shaped cowls, three-break compression ramps, faired
    splitter ledges, tapered side cheeks, and 745 mm recessed diffuser passages
    that continue into the sustainer-fin roots. Each cheek is lofted against and
    overlaps the changing duct sidewall at every section, preventing visible
    separation along the taper. Intake stand-off from the body is scaled to 85%
    of the initial design. The intakes and three booster fins occupy
    the same 60/180/300-degree CAD planes, leaving the dorsal mounting rail
    centered in the gap between the upper intakes. The Kris-style mounting
    corridor uses a 920 x 10 mm tapered rail with 3.5 mm stand-off, two
    44 x 18 x 8 mm suspension shoes at CAD X=-75/410 mm, and a shallow offset
    service strip. The detachable solid booster terminates in a modeled
     body-integrated nozzle with a rounded gray tail shroud, recessed 80 mm exit,
     27 mm throat, and 5 mm ablative liner. Its exhaust plane remains fixed at
     CAD X=-1683.5 mm for the runtime FX anchor. The recessed nozzle uses a dark
     oxide-red finish around a near-black disk fitted at the narrow throat, while the
     upper-stage nozzle band at the stage seam is neutral dark gray.
     Both fin sets use symmetric aerofoil sections with rounded leading edges,
     maximum thickness near the forward third, and sharp trailing edges. The
     three rear fins retain their tall-aft profile, short flat crown, steep
     shoulder, long shallow forward strake, tapered root fairings, 218 mm radial
     envelope, and original axial attachment range without raised
     surface reinforcement panels. The booster body uses the upper stage's light
     neutral-gray family, with charcoal aft and seam-colored forward bands.
    - Halberd export groups are body / intakes / sustainer fins / hardware /
      sustainer nozzle / booster body and integrated tail shroud / booster fins /
      recessed booster nozzle / dark nozzle throat disk. The body
     renderer and `SustainerFins` child remain on the missile root after stage
     separation. Booster body, fins, nozzle, and collider all remain below the
     direct `Booster` child required by runtime jettison.
    - Build the source with
      `python cad/halberd/generate_halberd_detailed.py`, validate it with
      `python cad/halberd/check_halberd_detailed.py`, then export Unity groups with
      `python cad/halberd/export_halberd_unity_mesh.py`. The exporter rejects changed
      part counts, unclassified labels, empty groups, incorrect bounds or seam,
      off-axis body geometry, and exports above the triangle budget.
      Build `cad/halberd/generate_halberd_intake_review.py` and
      `cad/halberd/generate_halberd_mount_review.py` for isolated intake/fin and dorsal
      hardware review STEPs. Build `cad/halberd/generate_halberd_nozzle_review.py` for
      full and sectioned booster-nozzle review;
      `cad/halberd/generate_halberd_booster_fin_review.py` isolates one rear-fin module;
      `cad/halberd/halberd_detailed_snapshot_job.json` renders their diagnostic views
      alongside the full missile.
   - Kris's CAD source is the 2898.25 mm Kris/PL-10 hybrid STEP. The exporter midpoint-centers the full envelope and maps CAD `+Z` directly to game `+Z`, then applies a uniform 0.990802 scale to match the MMR-S3's measured 2.871592 m mesh length. The Unity model has a 0.143667 m body diameter, a 0.444464 m maximum deployed span, and its tail/nose at -1.435796/+1.435796 m. All 270 CAD parts are retained in body / hardware / dark / grid-fin-and-TVC / seeker meshes. Five deterministic URP materials reproduce the STEP palette; the dark seeker uses Complex Lit clearcoat.
   - The rack uses the vanilla-compatible `pylon/aam1` hierarchy. Its mounted missile is rolled 45 degrees around `+Z`, centering the pylon between the four cardinal strakes, and offset vertically to keep 9 mm clearance above the rotated strake-tip envelope.
   - Build the hybrid with `python cad/kris/generate_kris_hybrid.py`, validate it with `python -u cad/kris/check_kris_hybrid.py`, then export the Unity groups with `python cad/kris/export_kris_unity_mesh.py`. The exporter rejects changed part counts, unknown palette colors, empty groups, incorrect bounds, body scale, or off-axis geometry.

## Halberd CAD approval candidate

### Selected Shoulder hybrid authoring candidate

The selected 19-part `cad/halberd/Halberd_Shoulder_Hybrid.step` is a separate candidate
from the historical 41-part detailed RC1 below. `cad/halberd/export_halberd_hybrid_unity.py`
maps CAD `(X,Y,Z)` millimetres to Unity `(Y,Z,X)` metres and writes only
`Assets/Blueprinter/Mods/HalberdHybrid/Models/HalberdHybridMeshData.json`.
`HalberdHybridTextureBuilder.BuildAndPreview` creates the dedicated, script-free
`Erenaldi.AAM44.HybridCandidate.prefab`, materials, meshes, and preview scene.

Fresh authoring validation passes at 41,950 triangles / 19 renderers, centered
±1.6835 m bounds, identity root, complete UVs, sRGB albedo, linear packed maps,
and direct `Booster` ownership. The five Unity review renders were visually
reviewed. This candidate deliberately has no colliders, rack prefab, bundle,
loader contract, plugin install, or runtime evidence; do not substitute it for
`Erenaldi.AAM44` until those production gates are explicitly approved and run.

The detailed AAM-44 Halberd RC1 is documented in
[`HALBERD_UNITY_DELIVERY.md`](HALBERD_UNITY_DELIVERY.md): 41 labels with
zero-failure master/upper-stage/booster checks, nine export groups with
exact label-to-hierarchy mapping, fixed datums, the blind sustainer
recess, and the pending material/runtime/payload-contact gates. The
source is RC1; assistant CAD visual review is complete and user approval is pending.

**Candidate staging only.** `cad/halberd/export_halberd_unity_mesh.py` now writes
OBJ groups and `Halberd_Export_Report.json` to
`cad/candidates/halberd/` and refuses to write under the production Unity
`Assets` tree. The candidate report (`cad/candidates/halberd/
Halberd_Export_Report.json`) is staged at 30,716 triangles; it is not an
approved Unity asset. The older
`cad/halberd/Halberd_Export_Report.json` is the **baseline** and is preserved
as-is (21,106 triangles, 0.218082553 m maximum radius) — do not overwrite
or treat it as the current candidate.

No Unity integration has been done for this candidate: no prefab,
bundle, or plugin work, and no candidate runtime proof. The existing
runtime dumps are from the old revision. Pylon contact is not validated.
Deterministic CAD checks, STEP solid validation, and 22 exporter unit tests pass.
The 47-image CAD review packet does not establish imported/runtime appearance.

## Ballista CAD approval candidate

The reference-driven AGM-110 Ballista RC1 is documented in
[`BALLISTA_UNITY_DELIVERY.md`](BALLISTA_UNITY_DELIVERY.md): centered millimeter
masters, stowed/deployed wings, label-to-group mapping, pivot datums, materials,
tessellation targets, and outstanding carriage/FX measurements. Both primary
STEP files pass CAD checks; Unity prefab and gameplay integration await geometry
approval. This candidate is not yet an asset loaded by the plugin.

## Export and embedding

1. Build the AssetBundle (Blueprinter Editor `.nobp` output or a custom
   `BuildPipeline.BuildAssetBundle` editor script — either produces a Unity asset
   bundle; Blueprinter's format additionally embeds `patch_manifest`, which the
   loader does not require).
2. Copy the bundle into `src/Erenaldi.MunitionsPackage/` as a private `.bundle`
   resource so Blueprinter does not mistake it for a standalone `.nobp` mod, then embed it:
   ```xml
   <ItemGroup>
      <EmbeddedResource Include="erenaldi_munitions.geometry.bundle" />
   </ItemGroup>
   ```
3. Rebuild the plugin — the bundle ships inside `Erenaldi.MunitionsPackage.dll`
   (single-file distribution, same mechanism Blueprinter uses for embedded mods).
## Palisade CAD candidate

The HKP-1 Palisade interceptor CAD candidate is **Gate-2 only** — it is a design-review artifact, not an approved Unity asset.

- **Candidate files** under `cad/`: `palisade_geometry.py`, generate/check/review/snapshot scripts, `HKP-1_Palisade_Interceptor.step`, separated review STEP, 10 PNG review views, and `Palisade_Review.png`.
- **Candidate dimensions:** centered X −600…600 mm, body radius 70 mm, near-hemisphere nose 70 mm long, cap 170 mm long, four diagonal tiny fins, four cardinal hollow cap nozzles, recessed main nozzle.
- **Validation:** 11 valid closed solids, exact 1200 mm length, radial envelope ≤85 mm, symmetry/contact/no-intersection/nozzle probe checks pass.
- **Main-agent visual review:** found no remaining asymmetry, collision, or blocked opening; the silhouette reads as requested.
- **User approval is required** before Unity export, prefab creation, or bundle generation.

## Validation checklist

- `[Phase 3] Loaded geometry bundle '...'` in `LogOutput.log`
- `[Phase 3] Custom geometry applied to 'Erenaldi.AAM44'/'Erenaldi.AAM44_single': 2 of 2 prefabs transplanted`
- `[Phase 3] Custom geometry applied to 'Erenaldi.IRMS4'/'Erenaldi.IRMS4_single': 2 of 2 prefabs transplanted`
- In game: custom missile on wing pylon, correct alignment to the hardpoint;
  launch produces vanilla motor FX anchored to the new hull
- With the bundle removed from the csproj: `[Phase 3] No embedded geometry bundle
  found; using vanilla geometry.` and no errors
