# Custom Geometry Pipeline (Path A — plugin-authoritative transplant)

The plugin remains the single registration/tuning authority. Custom art ships as a
pure-geometry AssetBundle; the plugin transplants visuals onto the runtime-cloned
prefabs. Component data (Missile, seeker, motors, Mirage networking) stays owned by
the clone pipeline — see `docs/PHASE2A_FINDINGS.md`.

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
4. Scale: `cad/generate_halberd_detailed.py` authors the Halberd directly at
   final game scale in millimeters. CAD +X is forward, +Z is dorsal, and +Y is
   lateral; `cad/export_halberd_unity_mesh.py` maps those axes to Unity +Z, +Y,
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
      `python cad/generate_halberd_detailed.py`, validate it with
      `python cad/check_halberd_detailed.py`, then export Unity groups with
      `python cad/export_halberd_unity_mesh.py`. The exporter rejects changed
      part counts, unclassified labels, empty groups, incorrect bounds or seam,
      off-axis body geometry, and exports above the triangle budget.
      Build `cad/generate_halberd_intake_review.py` and
      `cad/generate_halberd_mount_review.py` for isolated intake/fin and dorsal
      hardware review STEPs. Build `cad/generate_halberd_nozzle_review.py` for
      full and sectioned booster-nozzle review;
      `cad/generate_halberd_booster_fin_review.py` isolates one rear-fin module;
      `cad/halberd_detailed_snapshot_job.json` renders their diagnostic views
      alongside the full missile.
   - Kris's CAD source is the 2898.25 mm Kris/PL-10 hybrid STEP. The exporter midpoint-centers the full envelope and maps CAD `+Z` directly to game `+Z`, then applies a uniform 0.990802 scale to match the MMR-S3's measured 2.871592 m mesh length. The Unity model has a 0.143667 m body diameter, a 0.444464 m maximum deployed span, and its tail/nose at -1.435796/+1.435796 m. All 270 CAD parts are retained in body / hardware / dark / grid-fin-and-TVC / seeker meshes. Five deterministic URP materials reproduce the STEP palette; the dark seeker uses Complex Lit clearcoat.
   - The rack uses the vanilla-compatible `pylon/aam1` hierarchy. Its mounted missile is rolled 45 degrees around `+Z`, centering the pylon between the four cardinal strakes, and offset vertically to keep 9 mm clearance above the rotated strake-tip envelope.
   - Build the hybrid with `python cad/generate_kris_hybrid.py`, validate it with `python -u cad/check_kris_hybrid.py`, then export the Unity groups with `python cad/export_kris_unity_mesh.py`. The exporter rejects changed part counts, unknown palette colors, empty groups, incorrect bounds, body scale, or off-axis geometry.

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

## Validation checklist
- `[Phase 3] Loaded geometry bundle '...'` in `LogOutput.log`
- `[Phase 3] Custom geometry applied to 'Erenaldi.AAM44'/'Erenaldi.AAM44_single': 2 of 2 prefabs transplanted`
- `[Phase 3] Custom geometry applied to 'Erenaldi.IRMS4'/'Erenaldi.IRMS4_single': 2 of 2 prefabs transplanted`
- In game: custom missile on wing pylon, correct alignment to the hardpoint;
  launch produces vanilla motor FX anchored to the new hull
- With the bundle removed from the csproj: `[Phase 3] No embedded geometry bundle
  found; using vanilla geometry.` and no errors
