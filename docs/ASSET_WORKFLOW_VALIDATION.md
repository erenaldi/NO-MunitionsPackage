# Visual-Intent Workflow Validation

Date: 2026-09-21

## Scope

This report validates the project-local workflow contract without changing or
claiming new approval of any asset. It uses the RDM-9 history as a regression case;
R5 remains the committed design of record and R6 remains rejected.
Fresh-session image generation and visual judgment remain pending because no
concept-image generator is configured or approved.

## Static contract checks

| Requirement | Evidence | Result |
|---|---|---|
| Primary model reads visual evidence directly | `ASSET_DESIGN_WORKFLOW.md` operating rules and every visual gate | Pass |
| Image-blind review cannot approve appearance | Workflow operating rules; project `AGENTS.md` | Pass |
| Three contrastive concepts precede detailed CAD | Workflow intent and CAD silhouette gates; project `AGENTS.md` | Pass |
| User constraints outrank concept, references, and inference | Workflow authority hierarchy | Pass |
| Ambiguity is surfaced rather than silently resolved | Workflow operating rules, feasibility gate, and change contract | Pass |
| CAD, export, engine, and runtime evidence remain separate | Workflow states; `GEOMETRY_PIPELINE.md` evidence boundaries | Pass |
| Design and broad repository delegation are disabled by default | Workflow operating rules; project `AGENTS.md` | Pass |
| Concept generator requires comparison and approval | Workflow intent-discovery gate | Pass |
| Active assets carry compact context and lifecycle evidence | Halberd, Ballista, and Phantom contracts | Pass |

## RDM-9 bounded dry run

### Input

"Make the wings thinner as they should be for a folding concept, and show the
retracted design."

### Required interpretation board

For a newly opened design decision, the workflow must not turn that sentence
directly into CAD. It must first produce three visually distinct directions:

1. **Externally folded:** the deployed panels rotate around visible hinges and lie
   along a feasible exterior surface. The board must show hinge axis, folded
   thickness, overlap, and carriage consequences.
2. **Visibly tucked:** recognizable wing panels remain externally readable while
   nesting tightly against or partly into the body. The board must show what stays
   visible and how the deployed planform is preserved.
3. **Internally stowed:** panels disappear into a bay with only slot, door, stack,
   or hinge evidence visible. The board must state that this changes the visual
   reading from folded to internally retracted.

Each direction must identify infeasible dimensions or motion, but feasibility does
not choose the art direction. The primary multimodal model must inspect the actual
generated board against the visual north star, and the user must select or
hybridize a direction before CAD changes.

### Expected stop behavior

With no approved generator, no generated board, and no user selection, a newly
opened concept decision is `blocked` at concept review. R5 is not invalidated by
this dry run. Producing another R6-style replacement directly would fail the
workflow even if its topology and dimensions passed.

### Current result

The documentation produces the required interpretations and hard stop. A genuine
fresh-session visual run is **pending**, not passed: no concept-image generator is
configured, and adding one requires the comparison and approval below.

## Concept-generator setup gate

Use one fixed RDM-9 reference packet and prompt to compare a small candidate set.
Report, without adding credentials or configuration:

- adherence to supplied reference images
- ability to hold silhouette across multiple views
- control over specific features and prohibited interpretations
- repeatability or usable seed/version controls
- privacy and retention terms relevant to supplied assets
- measured cost for the fixed packet and one revision

The user selects the tool after seeing this comparison. External generation and
rough-CAD silhouette boards remain supported fallbacks. Tool selection, account
setup, credentials, dependencies, and OpenCode configuration are not authorized by
this remediation.

## Context and cost check

A future RDM-9 concept session should load only:

- `docs/PHANTOM_MALD_REFERENCE_REVIEW.md`
- the relevant `MUNITIONS.md` section
- the selected reference packet or concept board
- the one active source candidate only after concept approval

It should not load other weapon histories, all CAD outputs, the full session
database, or a broad subagent. Any exception requires explicit user approval and a
bounded prompt.

## Remaining validation

- Restart or open a fresh project session so the revised `AGENTS.md` is loaded.
- Select a concept-image generator or provide an external board.
- Run the visual RDM-9 scenario and record the selected interpretation, direct
  primary-model findings, user approval, packet identity, and cost.
