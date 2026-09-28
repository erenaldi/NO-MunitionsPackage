# RDM-9 Phantom — paired-state visual reboot

## Current implementation map — 2026-09-27

Latest build: `cad/phantom_visual_reboot/AFT_EXHAUST_R1_BRIEF.md` / `S_AftExhaust_R1_*` adds the user's selected recessed rounded-square exhaust and connects the intake stub with a clear visual passage. Saved geometry checks pass; visual acceptance pending. Real donor mesh/transforms are recovered, but unchanged mounting placement collides with the candidate (`DONOR_RACK_FINDINGS.md`); resolve this before rack/CAD delivery acceptance. Earlier integrated-candidate references below are history.

Use `cad/phantom_visual_reboot/IMPLEMENTATION_CHECKLIST.md` for current implemented features, remaining CAD slices, dependencies and acceptance criteria. The active integrated candidate is `src/ramp_intake_r3.py` / `R_RampIntake_R3_*` within that CAD workspace: covered joined wings, four recessed clipped fins, and a35 mm-travel belly intake. Main-wing and fin approvals are local; intake35 mm remains a checked trial. Rear exhaust/duct layout, flush RF areas, real rack fit, visible interfaces, surface details and final whole-airframe acceptance remain open. The dated concept notes below are retained as design history.

Date: 2026-09-23
Lifecycle: `concept-review` (three paired CAD studies built; no direction selected or CAD approved)

Review packet (2026-09-23): `cad/phantom_visual_reboot/REVIEW.md`,
`cad/phantom_visual_reboot/reviews/RDM9_ABC_{iso,top,side}.png`, and the
true-scale R5/ABC comparison there. Source-photo fidelity, user selection,
actual donor-rack fit, and downstream delivery gates remain pending.

**2026-09-27 local progression:** user accepted A5 covered main-wing/pocket direction and asked to continue to rear fins. A5 is the locally approved immutable baseline, not whole-airframe/rack/runtime acceptance. Current rear-fin gate is three rough one-corner folding planforms, `cad/phantom_visual_reboot/TAIL_FIN_R1_BRIEF.md` and `reviews/Q_Tail_R1_Comparison.png`; all pass saved geometry/31-sample fold checks, but user planform selection and four-corner replication remain pending. Earlier tail placeholders are historical.

**2026-09-27 rear-fin selection and propagation:** user selected Tall clipped, moved it80mm aft, then requested flush recessed stow with an exposed shallow pocket in flight. User approved TailR3 recessed prototype. Current TailR4 repeats it at allfourcorners with66sampled deployment checks and exactsavedcopy verification; see `cad/phantom_visual_reboot/TAIL_FIN_R4_FOUR_CONTRACT.md`. Combined layout awaits user review; earlier selection/replication-pending text above is historical.

**2026-09-27 intake addition:** user continued from four-fin review with two sketches for a flush-stowed, aft-hinged belly ramp intake ahead of the tail. TailR4 is the locally approved comparison. Current prototype/authority `cad/phantom_visual_reboot/RAMP_INTAKE_R1_BRIEF.md`:660×128mm panel,5degree opening, nested moving cheeks, open mouth and blind aft duct stub. Savedchecks/66motioncrosssamples pass; user intake review pending. This adds a visual intake feature, not engine performance or runtime behavior.

**2026-09-23 user sketch correction (supersedes the flat-ended nose/body language
below):** main fuselage frontal section is a lightly filleted square. The nose
is pointed from below with a centerline/chine junction; from the front its
projected point sits high and the lower faces form a V, not a blunt flat end.
See `cad/phantom_visual_reboot/NOSE_SKETCH_CONTRACT.md` and the reversible
`D_SketchNose_R1` pair. A/B/C are preserved as historical concept comparisons,
not current proof of these revised shape constraints. D awaits user review.

**2026-09-23 local-form progression:** subsequent E–I studies refined the square
transition, belly and upper corners. User specified the current 20 mm horizontal
wedge / 4 mm tip radius, then requested equal lower shoulders and a start on
other features. J/R7 is the mirrored body baseline; K is one main-wing folding
prototype in three poses, pending local approval before repetition. See
`cad/phantom_visual_reboot/BODY_R7_WING_R1_CONTRACT.md`. This local progression
supersedes D as the next-step context; whole-airframe selection remains open.

**2026-09-23 mechanism correction:** user rejected K's generic single-panel
swivel as inaccurate to GBU-39. MBDA research confirms joined tandem wings;
the published DiamondBack family description adds rearward carriage-driven
extension. K is withdrawn from selection. Next is a reference-led joined-module
study, with production-motion uncertainties explicit. Research authority:
`cad/phantom_visual_reboot/GBU39_WING_REFERENCE_RESEARCH.md`.

**2026-09-24 replacement study:** L/Joined Wing R1 now presents one connected
forward/rear panel pair, outboard pin and rearward sliding root, with identical
parts in stowed/intermediate/deployed poses. Its assumed motion is a Phantom
adaptation, not verified production GBU-39 kinematics. Local review is pending
before repetition; see `cad/phantom_visual_reboot/JOINED_WING_R1_CONTRACT.md`.

Approved issue split (2026-09-23): `issues/015-build-rdm9-first-paired-study.md`
→ `issues/016-compare-rdm9-three-paired-studies.md` →
`issues/017-refine-rdm9-selected-pair-and-rack-fit.md`. The user approved a
whole-vehicle paired tracer study, three-pair visual comparison, and selected
candidate/actual-donor-rack CAD gate. This issue board does not approve any
specific design or start implementation.

## Problem statement

The current R5 Phantom has validated CAD and Unity candidate assets, but its long, round-dart silhouette does not match the player's desired decoy. In particular, the pointed nose and near-featureless rack state fail to communicate the intended airframe and its deployed wings. Further detailing or promoting R5 would compound a visual-direction error. The player and asset reviewer need to choose a recognizable, packable design before new detailed geometry or engine work.

## Solution

Replace R5's exterior geometry with a coherent, compact radar-decoy airframe: a lightly filleted square main section, Kh-69-inspired restrained facets, the user's pointed bottom-view and V-chined front-view nose sketch, GBU-39-inspired deployable main wings, four Kh-69-inspired tail fins hinged at or near the aft body's corners, and restrained flush RF-panel areas. On the rack, folded main-wing panels and all four folded tail surfaces remain visibly identifiable within a 250 mm diameter carriage envelope; in flight, the same panels appear deployed. Preserve the centered 2,800 mm length and existing coordinate convention. Present distinct **paired stowed/deployed** silhouette studies for the user's selection or hybridization, with matched viewpoints and an explicit R5 comparison. After selection, validate geometry and actual donor-rack clearance before CAD visual approval. Reuse the proven R5 authoring, validation, export, and Unity tooling where applicable, but do not treat R5 geometry, material assets, or prefab previews as approval of the new shape.

References supply specific cues, not dimensions, performance, or an exact replica: [TALD/ITALD](https://en.wikipedia.org/wiki/ADM-141_TALD) for decoy character; [Kh-69](https://en.wikipedia.org/wiki/Kh-69) and [Kh-59MK2](https://en.wikipedia.org/wiki/Kh-59#Variants) for faceted body language and folding tail cues; [GBU-39](https://en.wikipedia.org/wiki/GBU-39_Small_Diameter_Bomb) for readable compact/deployed main-wing relationships. The user-supplied sketch takes priority for nose and fuselage section. The previous [MALD reference review](../docs/PHANTOM_MALD_REFERENCE_REVIEW.md) remains historical context, not the new silhouette master.

## User stories

1. As a player at the aircraft loadout, I can see folded wing and four tail-fin panels on a compact, broad-nosed decoy, rather than a plain missile with a hidden slot.
2. As a player seeing the weapon in flight, I can distinguish its deployed main wings, four tail fins, lightly rounded-square fuselage, and distinctive pointed/chined nose at representative viewing distances.
3. As a reviewer, I can compare three different fuselage/wing proportion and packaging interpretations in matched deployed **and** stowed views, including a comparison against R5, and choose, reject, or hybridize them before detailed CAD.
4. As an asset maintainer, I can trace each wing and fin panel between states through an identifiable shared panel and hinge, verify the selected stowed envelope and real rack clearance, and rebuild the design from source without editing STEP artifacts.

## Implementation decisions

- **Scope of replacement:** New exterior body, nose, main wings, folding tail and RF-panel forms. Reuse the R5 coordinate convention, validation/export approaches and Unity authoring infrastructure; a recessed exhaust may be adapted if it works on the new aft body. Historical R5 assets remain intact until a later approved promotion.
- **Authority and state:** This agreed direction reopens concept selection. R5 is the historical built design and Unity candidate, not the approved master for the new concept. New work starts at `intent-draft`; the three studies advance it to `concept-review`, not directly to `cad-approved`.
- **Envelope:** Centered X range −1,400..+1,400 mm; +X nose, +Z dorsal, +Y starboard. Every exterior part of the stowed state must lie inside the 125 mm radial carriage envelope, including folded wings, fins, RF areas and hinge hardware. Deployed appendages may extend beyond it; their dimensions are selected at the concept gate rather than inherited blindly from R5.
- **Visual hierarchy:** User-drawn lightly filleted-square main body and pointed, high-front-apex nose with lower V/chine; Kh-69-like restrained facet transitions, GBU-39-like visibly folded main panels, four corner-hinged Kh-69-like tail fins, and subtle flush paired RF areas (reinstated as a new user decision, not a revival of R5's protruding emitters). No plain cylindrical dart, flat blade tip, or invisible wing storage presented as visible folding.
- **Paired-state truth:** Each study shows corresponding physical wing and fin panels and identifiable hinges in both poses. A beautiful deployed shape with unrelated stowed strips is a failed study, even if both individual STEP files validate.
- **Contrast and approval:** Three coherent variations within this same hybrid brief must differ materially in fuselage/wing proportions or folding layout, not merely color. The primary model directly inspects actual opposed isometrics, side, top, front/rear and rack-context views; the user selects or hybridizes a direction before detailed modeling.
- **Fit gate:** Early studies may use a mock pylon, but CAD approval requires clearance against the actual RDM-9 donor rack and its attachment geometry. An unknown rack location or geometry is an explicit blocker, not a reason to treat mockup clearance as real clearance.
- **Workflow boundary:** Stop at approved 3D design; engine textures, serialized export of the new master, prefab promotion, runtime swapping and gameplay are later gates. Existing gameplay behavior is unchanged by this visual project.

## Data model and modules

- **New paired-state geometry module** under `cad/` (specific filename selected when slicing): a small interface accepting a named concept and pose and returning a labeled assembly plus hinge/panel identity data. It encapsulates the faceted body and nose, wing/fin panel geometry, hinge frames and pose transforms, RF areas and aft treatment so deployed and stowed candidates cannot silently diverge. Study entrypoints produce separate, named STEP artifacts without modifying the R5 masters.
- **New design checker and review packet** under `cad/`: check both artifacts' dimensions, radial stowed envelope, panel identity and pose correspondence, shape/contact/clearance, and source identity; produce matched all-side and rack-context views with a labeled R5 baseline. Keep visually judged reference fidelity separate from deterministic validity.
- **Existing geometry:** `cad/phantom_r2_lib.py`, `cad/check_phantom_r2.py`, and `cad/RDM-9_Phantom_R5_Dart*.step` remain historical baselines. The R5 loft, point tip, internal slot and fixed-tail assumptions are not geometry inputs to the new master.
- **Existing delivery modules:** `cad/export_phantom_unity_mesh.py` and `unity/BlueprinterEditor/Blueprinter-Editor/Assets/Editor/PhantomMeshBuilder.cs` are reusable infrastructure only; their current source filenames, semantic labels, span/radius expectations and triangle counts are R5-specific and must be revised and independently checked at a later export/engine gate. No new database, persistence format, plugin API, or game registry entry is needed at the 3D-design boundary.

## Testing decisions

- Check each study's paired STEP validity, centered 2,800 mm length, stowed 125 mm radial envelope including hinge/panel extents, real distinct body sections, panel count and state correspondence; do not equate independent watertight states with a plausible fold.
- For a selected candidate, measure hinge transforms and panel positions between states, verify no unaccounted geometry disappears or changes identity, and check actual donor-rack/attachment clearance before CAD approval. Do not weaken the existing R5 regression checks to make the new design pass.
- Render matched opposed, side, top, front/rear, rack and combat-distance views; the primary model reads them and compares against the attributed source imagery and R5. The user decides visual acceptance. Topology tests and nonblank image checks cannot replace visual review.
- Record precise concept choice, reference-feature ownership, rejected interpretations and approval scope in the RDM-9 context contract before promoting any selected design.

## Out of scope

- Changing RDM-9 gameplay specifications, donor definitions, networking, or existing installed plugin behavior.
- Modifying, deleting, or replacing R5/R6 historical sources, STEP masters, Unity candidate prefabs, or their prior test evidence during concept selection.
- Full mechanism animation at the first study gate; static posed states must nevertheless correspond to the same physical panels and hinges.
- New Unity materials/prefabs, asset-bundle production, runtime state swap, installation and in-game acceptance as part of this 3D-design effort.

## Open questions for the concept and feasibility gates

- Exact donor-rack geometry/attachment source and usable clearance, to identify and inspect before final CAD approval.
- Selected deployed span, wing station and precise folding kinematics within the locked stowed envelope; choose from paired studies rather than assuming R5 measurements.
- Final aft/exhaust treatment and relative RF-panel placement on the faceted body, to settle visually with the selected concept.
