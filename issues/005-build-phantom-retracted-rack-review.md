---
id: "005"
title: Add the R5 Phantom retracted rack candidate and final review packet
type: feature
status: blocked
blocked-by: ["004"]
---

## Slice

Extend the approved deployed candidate with the R5 retracted internal-bay state as the rack-display prefab, reuse the same material system, and deliver the complete visual comparison packet needed for user approval.

## Acceptance

- A callable `dart5r` checker specification is present and both `check_phantom_r2.py dart5r` and STEP topology validation pass without weakening R5 gates.
- The exporter accepts only `RDM-9_Phantom_R5_Dart_Retracted.step` for the rack display, classifies `stowed_wing_stack` and `hinge_fairing`, and verifies the centered 2.8 m length and 250 mm carriage envelope.
- `PhantomMeshBuilder` creates `Assets/Blueprinter/Mods/PhantomMod/Erenaldi.RDM9_single.prefab` with a pylon-compatible candidate hierarchy and the retracted missile display, sharing the deployed candidate's material assets where appropriate.
- The retracted slot, stack, fairing, tail surfaces, nozzle, and major value groups remain readable without becoming visually noisy at loadout distance.
- Automated Unity validation covers both prefab identities, state-specific child sets, bounds, UVs, materials, colliders, reference-asset exclusion, and deployed/retracted material consistency.
- GPU rendering produces nonblank deployed, retracted, rack-context, opposed-view, and same-scale vanilla comparison images.
- Direct visual inspection confirms vanilla-compatible hierarchy and no obvious asymmetry, clipping, blank textures, missing surfaces, or state-incoherent material placement.
- The result remains a candidate: bundle inclusion, runtime swapping, plugin changes, installation, and game launch do not occur.

## Test notes

- Run the full Phantom exporter test suite and both R5 CAD checker paths.
- Run the Unity candidate build/validation and GPU preview methods.
- Inspect all rendered views against AGM1 plus similarly sized runtime missile meshes and the measured `Missiles1`/`Missiles3` texture language.
- Record unresolved rack-transform, runtime-lighting, and state-swap risks explicitly for the later integration gate.
