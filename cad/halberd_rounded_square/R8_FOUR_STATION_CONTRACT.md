# R8 — four approved sets, booster fins shifted forward

Date: 2026-09-23. User authorized moving the new booster fin forward 170 mm and copying the complete approved set to the remaining three stations. This authorizes fourfold propagation of the intake housing/channel, housing-mounted main fin, dark intake lining/back, and shifted trapezoidal booster fin.

## Invariants

- Forward is +X. Booster fin root moves from [-1655,-1360] to **[-1485,-1190] mm**. Its 295 mm root, centered 220 mm tip, 53 mm height and section remain unchanged.
- Stations: **45, 135, 225, 315 degrees**, measured from +Z toward +Y.
- Preserve R6's late cubic intake taper, straight entry, existing side-height profile and channel depth; replicate the exact approved shapes rather than refitting profiles.
- Preserve black back faces and existing side/nozzle materials. Nozzle liners and their backs remain single axial components, not four copies.
- Preserve nose, core, booster body, nozzle geometry, 3370 mm overall length and one-sixth booster allocation.
- Intake housing, channels, main fins and their dark backs belong to the main stage. Shifted booster fins and booster nozzle parts remain with the booster.

## Construction and checks

Build the new main body by adding three rotated copies of the approved **housing-only delta** to the existing one-intake body. Never union four complete bodies, which would refill the channels. Verify core preservation, four enclosed channels, exact replicated feature geometry/materials, rotated housing deltas, fin attachments and inter-station/nozzle clearance.

All four shifted fin roots now lie ahead of the boattail transition, on the constant-section booster body; verify contact rather than assuming it from the 170 mm move. The root leading edge remains 66.667 mm behind the main/booster seam.

Outputs: `STEP/Selected_Halberd_R8.step` and `Selected_Halberd_R8_Separated.step`, authored by explicit source entrypoints. R7 remains the preserved prototype baseline. Full-assembly visual review follows propagation; no engine/runtime approval is implied.

## Delivered four-station CAD assembly

- [Assembled R8](http://127.0.0.1:3247/?file=STEP/Selected_Halberd_R8.step)
- [Separated R8](http://127.0.0.1:3247/?file=STEP/Selected_Halberd_R8_Separated.step)
- [Overview](reviews/Halberd_R8_Overview.png)
- [Fourfold end views](reviews/Halberd_R8_Ends.png)
- [Booster placement and separated stages](reviews/Halberd_R8_Stages.png)

Viewer port 3247 serves this study workspace on the updated runtime. Earlier port-3245 links in historical handoffs must not be assumed to serve Halberd now.

## Verified results

`checks/check_halberd_r8.py` passes against both saved STEP documents:

| Requirement | Result |
|---|---|
| Four complete sets | Four housing/channel deltas exactly match rotated copies of the approved one-station artifact; four main fins, four shifted booster fins and four intake lining/back pairs match their prototypes. |
| Clocking | 45/135/225/315 degrees, measured from part centers and verified by inverse-transform geometry comparisons. |
| Booster shift | Exactly +170 mm X; root range [-1485,-1190] mm on every booster fin. Leading root remains 66.667 mm aft of the stage seam. |
| Attachment | Booster contact approximately 5009.30 mm3 per fin; main-fin contact approximately 1561.80 mm3 per fin. Three root samples per booster fin are inside the constant-section booster body and fin. |
| Clearance | Booster fin to nozzle liner: 147.289 mm minimum; to nozzle back: 149.571 mm. Main/booster fin gap: 118.248 mm. Inter-station fin/recess clearances are positive. |
| Channel and stage preservation | All four channels remain open to the retained back plane X=-444.973923 mm. Housing reaches the main-stage seam, original core is preserved, overall length stays 3370 mm and booster stays one sixth. |
| Components and materials | Nose, booster body and both nozzle assemblies match R7. Colors match the prototypes, including all black intake backs. Twelve named finish assignments per state match the STEP-bound sidecar and intended material. |
| Native geometry | Every one of 46 saved placements (23 per state) has one positive-volume solid, valid topology, closed shell boundaries and zero reported self-intersections. Both separated and assembled geometry match after reversing the display offset. |

Reports: `reviews/halberd_R8_checks.json` includes the document hashes and per-occurrence native results. `reviews/halberd_R8_manifest.json` identifies the STEP files, material sidecars and eight snapshots. The primary model directly inspected all eight views through the three boards; the final booster-placement framing was corrected and read again.

## Runtime transition during this task

The shared cadgen installation became temporarily unavailable after the first assembled build: its `__init__.py` was absent and Python found only a namespace package. On continuation, `cadgen doctor` reported **0.6.6**, matching the updated installed skill pin. No shared installation or configuration was modified by this task.

R8 was rebuilt on 0.6.6. This runtime removes dynamic `cad_material` authoring and the inspect CLI. R8 therefore declares equivalent named finishes in both model decorators, removes the retired attributes only from its returned derived occurrences, and validates artifacts through native Python `cadgen.geometry` checks. Historical source files are not globally migrated. Snapshot jobs use the current display/output schema; image dimensions belong to each output. The material sidecars must accompany these STEP files when retaining finish metadata.

## Reproduce

Using the dedicated CAD Python interpreter from the repository root:

```text
cad/halberd_rounded_square/src/halberd_r8.py
cad/halberd_rounded_square/src/halberd_r8_separated.py
cad/halberd_rounded_square/checks/check_halberd_r8.py
cad/halberd_rounded_square/reviews/render_r8.py
```

The full assembly is at `cad-review`. Requested shift and propagation are implemented and checked; user review of the full layout is the next gate before production/engine delivery.
