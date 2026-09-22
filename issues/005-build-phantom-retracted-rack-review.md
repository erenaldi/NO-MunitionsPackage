---
id: "005"
title: Add the R5 Phantom retracted rack candidate and final review packet
type: feature
status: done
blocked-by: []
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

## Review notes

- Tests-first review found no completion blocker. The final exporter suite runs
  38 Phantom tests, including pinned-hash end-to-end exports of both approved R5
  STEP masters into temporary outputs; deployed and retracted totals remain
  18,846 and 25,192 triangles.
- Both `dart5` and `dart5r` deterministic checks pass, and strict every-placement
  STEP validation reports zero failures for both source masters.
- Unity candidate validation passes for `Erenaldi.RDM9` and
  `Erenaldi.RDM9_single`, including state-specific groups, UVs, bounds, shared
  materials, colliders, the 9 mm candidate rack clearance, source exclusions,
  and a derived 3 mm nozzle-lip recess that removes the source's coplanar render
  overlap without changing either approved STEP.
- Primary-model inspection of all seven GPU captures passes the engine-review
  boundary. The deployed planform and neutral-gray/charcoal/amber hierarchy read
  at full and combat distances; the pylon-free retracted view exposes the dorsal
  slot, stack, and fairing; the rack view preserves clear mounting separation;
  and the corrected aft view shows a clean recessed exhaust without flicker.
- The result remains an authoring candidate. Actual donor-rack alignment,
  runtime lighting, retracted-to-deployed swapping, bundle inclusion, game
  installation, and multiplayer/in-game behavior are unverified and require a
  later user-approved integration gate.
