# RDM-9 Phantom R5 Unity Texture Candidate

## Problem statement

The RDM-9 Phantom has an approved R5 CAD design in deployed and retracted states, but it has no Unity mesh pipeline, no vanilla-compatible original textures, and no representative material review. The current CAD placeholder colors cannot establish whether the weapon fits Nuclear Option's visual language at loadout and combat distances.

## Solution

Import the approved R5 deployed and retracted STEP masters through a deterministic CAD-to-Unity exporter. Build candidate Unity prefabs named `Erenaldi.RDM9` and `Erenaldi.RDM9_single`, using the deployed state for flight and the retracted internal-bay state for the rack display. Apply original procedural URP Lit textures derived from the measured AGM1/`Missiles1` family and the established custom-munition texture rules: neutral gray value blocks, charcoal hardware and exhaust, restrained amber service accents, thin seams, sparse geometric service marks, subtle wear, low metallic response, mirrored major motifs, and no stencil text. Produce GPU-rendered deployed, retracted, rack-context, opposed-view, and same-scale vanilla comparison images for visual approval before any bundle or runtime integration.

## User stories

1. As a player viewing the loadout screen, I can recognize the retracted Phantom as a deliberate vanilla-compatible decoy rather than an untextured generic dart.
2. As a player seeing the Phantom in flight, I can read its deployed wing planform and major material groups at combat distance without relying on fine text.
3. As an asset maintainer, I can rebuild both Phantom Unity candidates deterministically from the approved R5 STEP files without manual mesh or material edits.
4. As a reviewer, I can compare Phantom directly with actual game references under matched scale and lighting before approving runtime integration.

## Implementation decisions

- **Release masters:** `cad/RDM-9_Phantom_R5_Dart.step` for flight and `cad/RDM-9_Phantom_R5_Dart_Retracted.step` for the rack display. R6 remains rejected and is not an input.
- **State ownership:** Deployed and retracted states are separate candidate prefabs. This texture pass does not implement the runtime state swap.
- **Coordinate transform:** CAD `(X, Y, Z)` millimeters maps to Unity `(Y, Z, X)` meters, preserving handedness and the centered runtime pivot.
- **Texture authority:** Use `reference/vanilla_textures/`, runtime `missile-geometry.json`, and `docs/TEXTURE_STYLE_FINDINGS.md`; prioritize AGM1/`Missiles1`, then similarly sized missile families for missing panel-language evidence.
- **Original work only:** Vanilla textures remain reference-only and must not become prefab or bundle dependencies.
- **Visual language:** Large neutral-gray panel fields, charcoal aft/nozzle and hardware, one restrained amber service accent, thin seams/rivets, sparse geometric service marks, subtle grunge, and baked seam shading.
- **Markings:** No stencil text, consistent with the established user preference for the other custom munitions.
- **Microsurface:** Painted-composite values near the measured vanilla family, generally metallic `0.05-0.10` and smoothness `0.40-0.50`; higher values are limited to appropriate hardware.
- **Symmetry:** Major texture motifs must satisfy the existing cylindrical mirror/roll conventions; stochastic low-amplitude wear may remain asymmetric within the measured tolerance.
- **Review gate:** Candidate prefabs and renders require direct visual approval before bundle inclusion, plugin changes, installation, or game launch.

## Data model and modules

- `cad/export_phantom_unity_mesh.py`: deep export module that classifies every R5 label, tessellates both states, applies the single documented basis/scale transform, emits material-grouped OBJ files, and writes a bounds/triangle/label manifest.
- `cad/test_export_phantom_unity_mesh.py`: exporter contract tests for source identities, labels, transforms, bounds, groups, triangle budgets, and state-specific parts.
- `unity/.../Assets/Editor/PhantomMeshBuilder.cs`: imports grouped OBJ files, creates UVs, materials, colliders, and the deployed/retracted candidate prefabs.
- `unity/.../Assets/Editor/PhantomTexturedMaterialBuilder.cs`: encapsulates procedural albedo and packed metallic/smoothness generation for body and wing/fin surfaces.
- `unity/.../Assets/Editor/PhantomPreviewBuilder.cs`: renders the required review packet using a real graphics device.
- `unity/.../Assets/Blueprinter/Mods/PhantomMod/`: generated candidate models, materials, textures, meshes, and prefabs.
- Existing `MunitionsGeometryBundleBuilder`, `CustomGeometryLoader`, and `PhantomCloner` are not modified in this pass.

## Testing decisions

- Restore a callable `dart5r` specification in `cad/check_phantom_r2.py` if needed so both approved R5 states can be freshly validated without weakening existing gates.
- Run `check_phantom_r2.py dart5` and `dart5r`, plus `cadgen step inspect validate` on both source STEPs.
- Test exporter label classification, state-specific label sets, axis conversion, millimeter-to-meter scaling, centered pivot, expected bounds, material groups, nonempty watertight meshes, and triangle budget.
- Unity builder validation must reject missing/unclassified groups, unexpected bounds, missing UVs/materials, incorrect colliders, reference-asset dependencies, and prefab-name/state mismatches.
- Texture validation must check albedo sRGB, packed map linearity, low-metallic ranges, full UV coverage, and major-motif mirror/roll symmetry.
- Render with GPU graphics enabled; verify nonblank output programmatically, then visually inspect all supplied views. Final material quality remains a human visual gate and is not replaced by pixel statistics.

## Out of scope

- R6 repair or promotion.
- Changes to R5 CAD silhouette or dimensions.
- AssetBundle inclusion or embedded plugin bundle replacement.
- Runtime retracted-to-deployed swapping.
- Changes to `CustomGeometryLoader`, `PhantomCloner`, gameplay behavior, or networking.
- Plugin build/install, game launch, or in-game validation.
- LODs, final collision tuning, normal-map authoring, and runtime effects-anchor work.
