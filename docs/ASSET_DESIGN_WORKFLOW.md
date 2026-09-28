# Visual-Intent Asset Workflow

Use this workflow for reference-driven or high-fidelity munition assets. It is
a project-specific overlay on the global `cad` and `concept-asset-cad` skills.
Load `game-asset-cad` when approved CAD crosses into engine delivery, not for
CAD-only studies. The separate `3d-design` skill and MCP pipeline are archived,
not active routes for this work.

The purpose of this workflow is to discover and preserve the intended design
language before technically valid work commits the project to the wrong idea.

## Operating rules

- The primary multimodal model owns visual continuity and directly reads every
  concept board, CAD review packet, engine capture, and in-game capture.
- A text-only or image-blind report cannot pass a visual gate.
- A text-only worker may request bounded observations from `subagents/multimodal-analyst`
  for an exact accessible local image or file. This supplies evidence, not
  delegated design or visual acceptance; the primary still inspects every packet.
- Keep design, visual review, retrospective analysis, and broad repository
  exploration with the primary model by default. Delegating one of those
  activities requires explicit user approval, a fixed file list, a bounded
  investigation, and one narrow output.
- This does not restrict bounded implementation. Once the user approves the
  relevant concept or repeated-feature gate, a non-OpenRouter primary model
  defaults to `subagents/cad-builder` for a substantial, clear CAD build and
  deterministic checks. The worker returns actual views; the primary model
  inspects them and decides the next visual gate. No extra approval is needed
  merely to delegate an already approved build pass.
- Load the per-asset context packet and files required for the current gate, not
  the entire project history.
- Never treat a CAD check as export evidence, export evidence as Unity evidence,
  or Unity evidence as runtime/gameplay acceptance.
- Resolve material ambiguity visually. Do not silently choose an interpretation
  because it is easiest to model.

## Authority hierarchy

When evidence conflicts, apply this order:

1. Explicit user constraints and decisions
2. The approved concept board and visual-intent brief
3. Supplied references as evidence for specific features
4. Agent inference, clearly labeled as inference

A reference contributes only the features attributed to it. It does not become
unqualified authority for the entire asset.

## Per-asset context packet

Keep this compact section in the asset's delivery or reference contract:

```markdown
## Active context

- Current state:
- Authoritative source:
- Approved concept / review packet:
- Coordinate system and scale:
- Preserve:
- Avoid:
- Exaggerate or emphasize:
- Rejected interpretations:
- Hard constraints:
- Open decisions:
- Files required for the next gate:
```

The repository, not conversation memory, is authoritative. Re-verify paths,
artifact identities, and status against disk at the start of a session.

## Visual north star

Before generating concepts, record:

- the asset's role and the impression it should create
- silhouette family and dominant proportions
- shape language, feature hierarchy, and important negative spaces
- intended viewing distances and presentation states
- what must feel familiar, novel, aggressive, restrained, improvised, refined,
  or otherwise characteristic
- features to preserve, avoid, or deliberately exaggerate
- unacceptable readings and rejected prior interpretations
- deliberate deviations from references and why they exist

Prefer contrastive language: "broad and lifting, not pencil-like," "tucked against
the body, not absent," or "recessed opening, not a dark decal." These statements
carry more visual intent than feature counts alone.

## Lifecycle states

Use exactly these state names in per-asset contracts:

| State | Meaning |
|---|---|
| `intent-draft` | Context and visual north star are incomplete. |
| `concept-review` | Three contrastive directions exist and await selection. |
| `concept-approved` | The user approved a direction and its intent brief. |
| `cad-review` | CAD exists but visual approval is pending or reopened. |
| `cad-approved` | Applicable CAD checks pass and the user approved the CAD packet. |
| `export-validated` | The approved CAD source was exported and the serialized mesh passed its contract. |
| `engine-review` | The imported asset exists; engine appearance or integration remains pending. |
| `runtime-review` | Packaged runtime behavior is being tested. |
| `runtime-accepted` | The applicable in-game acceptance matrix passed and the user accepted the result. |
| `blocked` | A named missing decision, capability, artifact, or failed gate prevents progression. |

Do not use "complete," "final," or "approved" without naming the boundary. A
technically valid CAD candidate is not a completed game asset.

## Gates

### 1. Intent discovery

Create three deliberately different visual directions. They must differ in
silhouette, proportion, or design language rather than only color, detail, or a
small parameter. For each direction, state what it emphasizes, what it gives up,
and which reference cues it uses.

The primary model reviews the actual board. The user may select one direction,
reject all three, or hybridize named features. Persist the reasons, including why
directions were rejected.

No concept-image generator is currently in the active CAD workflow. Before
adding one, compare a small fixed reference packet for conditioning,
controllability, repeatability, privacy, and cost. Adding a service,
dependency, credential, or OpenCode configuration requires explicit approval.

### 2. Feasibility

Before detailed CAD, check the approved concept against carriage envelope,
deployment, source and donor constraints, hierarchy, pivot, animation, materials,
and runtime ownership. A hard conflict returns to concept review; do not quietly
redesign the feature during implementation.

### 3. CAD silhouette

Build only the primary volumes and appendages needed to judge silhouette and
proportion. Produce the standard review packet:

- opposed isometrics
- side, top, front, and rear orthographic views
- critical dimensions and envelopes
- comparison with the approved concept and relevant references
- deliberate deviations and unresolved readings

The primary model reads the packet directly. User approval is required before
expensive detailing or repeated-feature propagation.

### 4. Primary forms and detail

For an ambiguous local edit, record a change contract:

```markdown
- Local axial / radial / tangential axes:
- Volume retained:
- Volume removed:
- Volume added:
- Hard boundaries:
- Acceptance views:
- Interpretations explicitly excluded:
```

Prototype one uncertain repeated feature, review it in context and isolation, and
obtain approval before mirroring or patterning. Add grazing, section, all-side,
and material views according to risk.

### 5. Export and engine presentation

Follow `game-asset-cad` for approved CAD delivery. Validate the approved source identity,
transform chain, serialized mesh, hierarchy, materials, colliders, anchors, and
stowed/deployed states independently. The primary model must inspect engine
captures under representative lighting before visual approval can advance.

### 6. Runtime and gameplay

Use the proving ground and asset-specific requirements. Check applicable rows:

| Area | Evidence |
|---|---|
| Loadout and rack | Visible, correctly scaled and aligned, correct hierarchy and clearance |
| Launch | Clean separation, correct visibility swap, collider behavior, and initial orientation |
| State transitions | Deployment, staging, burnout, jettison, and ownership occur in the intended order |
| Effects | Exhaust, trails, particles, audio, and anchors follow the correct stage and lifetime |
| Flight role | Representative guidance, control, range, and terminal cases match the weapon brief |
| Packaging and fallback | Packaged identity loads; declared fallback works without corrupting runtime state |

Only applicable rows are required, but untested rows must be marked unverified.

## Approval and invalidation

Record each approval with the date, packet identity, approving user, and scope.
Assistant visual review is evidence, not user approval.

A change invalidates the gate that owns it and every dependent gate. Preserve
unaffected approvals. Examples:

- silhouette or proportion change: reopen CAD visual approval and all later gates
- tessellation or group change: preserve CAD approval; reopen export and later gates
- material or importer change: reopen engine visual review and later gates
- guidance or FX change: preserve visual gates; reopen affected runtime rows

## RDM-9 regression case

Use these failures to test future workflow compliance; do not redesign RDM-9 as
part of this workflow:

- Detailed references and valid topology did not prevent a body and nose that
  contradicted the intended broad, wedge-like visual language.
- Self-consistency checks passed features that did not read correctly in images.
- Image-blind reviewers reported no visual blocker.
- "Thin for a folding concept" was resolved as internal retraction without first
  presenting external fold, visible tuck, and internal stow as distinct visual
  directions. A later tucked-wing attempt failed visual and semantic review, and
  R5 internal stow remains the design of record.

For a future folding-feature request, show at least the materially plausible
interpretations, such as externally folded, visibly tucked, and internally
stowed. Label feasibility constraints and obtain a visual selection before CAD.

## Completion report

Report these categories separately:

- deterministic evidence
- primary-model visual findings
- user-approved aesthetic decisions
- export evidence
- engine evidence
- runtime/gameplay evidence
- assumptions and unresolved items

The next state must follow from the weakest applicable category, not the strongest
check that happened to pass.
