# Visual-Intent Asset Workflow

## Problem statement

Reference-driven munition work repeatedly produces technically valid geometry that misses the user's implied art direction. Text instructions and detailed references do not reliably communicate shape language, emphasis, negative space, or prohibited interpretations, so incorrect concepts can survive deterministic CAD checks and become expensive to repair after detailing, export, Unity integration, or gameplay work. Broad subagent reviews also load too much of this dense repository, add cost, lose visual continuity, and have sometimes reported on appearance without image access.

## Solution

Add a project-local visual-intent workflow that treats concept discovery, CAD, export, Unity presentation, and gameplay as separate evidence boundaries. Each reference-driven asset begins with a compact per-asset context packet and a durable visual north star, then explores three deliberately different concept directions before detailed CAD begins. The primary multimodal model directly reviews every visual packet, while the user approves the costly transitions; design and broad repository work are not delegated by default. Existing global CAD skills remain authoritative for geometry and engine-delivery mechanics, while this workflow supplies the project's art-direction, context, status, and acceptance discipline.

## User stories

1. As the art director, I can choose among three meaningfully different concept directions so that preferences I cannot fully express in text become visible before expensive modeling begins.
2. As the art director, I can record what an asset must feel like, must not feel like, preserve, exaggerate, and avoid so that later sessions retain the spirit of the approved design.
3. As the art director, I see ambiguous instructions represented as competing visual interpretations rather than having the agent silently choose the wrong meaning.
4. As the modeler, I know the authoritative source, coordinate system, approved visual state, and unresolved decisions without reading the entire repository or conversation history.
5. As the integrator, I can distinguish CAD validity, visual approval, exported-mesh validity, Unity presentation, and runtime/gameplay acceptance so that success at one boundary is never overstated as completion of another.
6. As the project owner, I avoid expensive broad subagent investigations while retaining direct multimodal review by the primary model at every visual gate.
7. As a later session, I can determine which approval was invalidated by a change and reopen only that gate and its dependents.

## Implementation decisions

- **Primary problem:** Optimize for latent art-direction capture, not merely conflict reduction. The recurring failure is self-consistent execution of the wrong visual interpretation.
- **Lifecycle scope:** Cover concept generation through CAD, export, Unity presentation, and gameplay acceptance.
- **Concept discovery:** Begin with three contrastive concept directions. Variants must differ in silhouette or design language, not only dimensions or decoration.
- **Visual evaluation:** The active primary multimodal model inspects concept boards, CAD renders, engine captures, and in-game captures directly. A text-only or image-blind report cannot satisfy a visual gate.
- **Concept-image tooling:** Select the generator during setup by comparing reference conditioning, control, repeatability, privacy, and cost on one fixed RDM-9 packet. Adding a service, dependency, credential, or configuration requires separate user approval.
- **CAD start:** Detailed CAD begins only after concept approval and a quick feasibility check. Reversible rough studies may support that check.
- **Approval gates:** Gates are hard at costly propagation boundaries: repeated-feature expansion, detailed modeling after silhouette selection, production export, Unity integration, and completion claims.
- **Review packet:** Use opposed isometrics, orthographic and end views, dimensions, reference comparison, and a list of deliberate deviations. Add isolated, grazing, material, engine, or gameplay views according to the current risk.
- **Authority hierarchy:** Explicit user constraints first, approved concept and intent brief second, supplied references as feature evidence third, and agent inference last.
- **Durable authority:** Store the approved board and intent brief in the asset's existing delivery or reference contract. Record preserve/avoid/exaggerate cues and rejected interpretations with reasons.
- **Approval invalidation:** A dependent change reopens the affected gate and downstream gates, while unrelated approved regions remain approved.
- **Status vocabulary:** Distinguish intent draft, concept review, concept approved, CAD review, CAD approved, export validated, engine review, runtime review, runtime accepted, and blocked.
- **Context control:** Use per-asset context packets and load only the authority document, active source, current artifacts, and files needed for the current gate.
- **Delegation:** No design, visual, retrospective, or broad repository subagents by default. Any exception requires explicit user approval and a fixed file list, bounded investigation, and narrow deliverable.
- **Placement:** Prefer project-local instructions and documents. Do not duplicate or weaken the global `cad`, `concept-asset-cad`, or `game-asset-cad` contracts.
- **Backfill:** Normalize Halberd, Ballista, and Phantom in their existing contracts using current disk evidence. Do not reopen verified work unnecessarily or modify geometry as part of this feature.
- **RDM-9:** Use its history as a regression case for the workflow. Redesigning the asset is outside this feature.
- **Historical fixes:** Verify and preserve safeguards that already work; add no duplicate rule solely because an old session predates the safeguard.

## Data model and modules

No runtime data or database changes are required.

### Project workflow module

`docs/ASSET_DESIGN_WORKFLOW.md` will encapsulate the project-specific process behind a small interface:

- Inputs: asset authority document, active source identity, references, user constraints, and current gate.
- Outputs: visual north star, three-direction concept board, gate-specific review packet, approval record, and next permitted transition.
- Invariants: no image-blind visual pass, no silent resolution of material visual ambiguity, no later-boundary completion claim, and no broad design delegation.

### Per-asset contract sections

Each active asset contract will carry:

- context packet and authoritative source identity
- visual north star and authority hierarchy
- selected concept and rejected interpretations
- gate-status table with evidence and approval provenance
- invalidation triggers and unresolved items
- boundary-specific acceptance evidence

Existing modules modified:

- `AGENTS.md` for mandatory routing, context, and delegation rules
- `docs/GEOMETRY_PIPELINE.md` for lifecycle handoff and status semantics
- Halberd, Ballista, and Phantom delivery/reference documents for backfilled state
- `docs/SESSION_LOG.md` for verified handoff

## Testing decisions

- Verify documentation links and required sections by repository search and readback.
- Start a fresh project session and run an RDM-9-derived dry run that creates three concept directions but does not begin detailed CAD before approval.
- Test an ambiguous folding-wing direction and verify distinct external-fold, tucked, and internal-stow interpretations are surfaced rather than silently collapsed.
- Verify the primary model directly reads each visual packet and that no subagent session is created during the dry run.
- Verify each backfilled contract separates deterministic checks, visual approval, export state, engine state, and runtime state without claiming unperformed validation.
- Run `opencode debug config` only if implementation ultimately changes OpenCode configuration; project documentation changes alone do not require it.
- Run CAD, Unity, or plugin checks only if executable geometry, tooling, or runtime files change. This feature does not require those changes.

Visual quality and whether a concept captures the intended spirit remain human approval decisions. The workflow can make those decisions earlier and better informed, but cannot automate the user's aesthetic judgment.

## Out of scope

- Redesigning RDM-9, Halberd, Ballista, or another munition
- Modifying CAD, textures, Unity assets, gameplay code, bundles, or generated artifacts
- Changing global CAD skills or global OpenCode configuration without a separately evidenced gap and approval
- Selecting or configuring an image-generation dependency without a comparison and user approval
- Re-auditing all 189 historical project sessions
- Treating deterministic geometry checks as substitutes for visual or runtime acceptance
