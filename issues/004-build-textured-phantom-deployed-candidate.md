---
id: "004"
title: Build a textured R5 Phantom deployed Unity candidate
type: feature
status: todo
blocked-by: []
---

## Slice

Deliver the approved R5 deployed Phantom as a deterministic Unity candidate with original vanilla-style textures and a GPU-rendered preview. This tracer bullet crosses CAD validation, mesh export, Unity import, UV generation, procedural material creation, prefab construction, automated checks, and a visible output before the retracted state is added.

## Acceptance

- `cad/check_phantom_r2.py dart5` and STEP topology validation pass without weakening existing checks.
- `cad/export_phantom_unity_mesh.py` accepts only `RDM-9_Phantom_R5_Dart.step`, classifies every label exactly once, applies CAD `(X,Y,Z)` mm to Unity `(Y,Z,X)` m, and emits material-grouped OBJ files plus a manifest under the Phantom candidate asset root.
- Exporter tests cover source identity, labels, basis/scale, centered pivot, expected bounds, watertight nonempty groups, and triangle budget.
- `PhantomMeshBuilder` creates `Assets/Blueprinter/Mods/PhantomMod/Erenaldi.RDM9.prefab` with the body renderer on the root, semantic wing/fin/nozzle children, an approximate candidate collider, and no runtime-owned components.
- `PhantomTexturedMaterialBuilder` creates original URP Lit albedo and packed metallic/smoothness assets using the established vanilla rules: AGM1/`Missiles1`-led neutral gray panels, charcoal hardware/exhaust, restrained amber accent, thin seams/rivets, geometric service marks, subtle wear, low metallic response, mirrored major motifs, and no stencil text.
- Unity-side validation rejects missing meshes, unexpected bounds, missing UVs/materials, wrong color-space settings, out-of-range microsurface values, symmetry failures, or reference-asset dependencies.
- `PhantomPreviewBuilder` renders a nonblank deployed full view, opposed view, and representative combat-distance view with a real graphics device.
- No bundle, plugin, runtime, install, or game files are changed.

## Test notes

- Run targeted Python exporter tests and both CAD checks.
- Run the Unity editor method that builds and validates the deployed candidate.
- Run the GPU preview method without `-nographics`; inspect the generated images directly.
- Compare palette/value/detail decisions against `reference/vanilla_textures/`, runtime AGM1 data, and `docs/TEXTURE_STYLE_FINDINGS.md`.
