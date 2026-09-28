---
id: "001"
title: Establish the project-local visual-intent workflow
type: feature
status: done
blocked-by: []
---

## Slice

Make one reference-driven asset session able to discover, preserve, and gate visual intent without broad repository or subagent analysis. Add the project workflow, connect it from the project instructions and geometry pipeline, and include an RDM-9-derived example that demonstrates how ambiguous visual language is surfaced before CAD.

## Acceptance

- `docs/ASSET_DESIGN_WORKFLOW.md` defines the per-asset context packet, visual north star, three-direction concept board, direct primary-model visual review, approval invalidation, lifecycle states, and hard boundaries.
- `AGENTS.md` routes reference-driven game assets through the existing CAD skills and the project workflow.
- Project instructions prohibit design, visual, retrospective, and broad repository delegation by default; exceptions require explicit user approval and a bounded scope.
- `docs/GEOMETRY_PIPELINE.md` links to the workflow and distinguishes CAD, export, engine, and runtime evidence.
- An RDM-9 regression section demonstrates that "folding," "tucked," and "internally stowed" are separate interpretations requiring visual resolution.
- No global skill, OpenCode configuration, geometry, Unity asset, bundle, or gameplay file changes.

## Test notes

- Read back every changed section and verify links resolve.
- Search for the required lifecycle states, authority hierarchy, delegation rule, and image-blind-review prohibition.
- Confirm the diff is limited to project workflow/instruction documentation plus planning artifacts.
