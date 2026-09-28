# R18 — proposed surface-feature catalogue

Date: 2026-09-27. State: **`concept-review`**. User requested an actual feature
list first, followed by deliberate distribution on Halberd, then authorized
continuation with an explicit anti-copy/paste constraint. The annotated
[R18 surface-layout proposal](R18_SURFACE_LAYOUT.md) is now ready for review.
New detailed features are not yet modeled. R17 remains preserved rejected
surface-layout evidence; the approved silhouette and useful local treatments
remain the foundation.

## Design rule

Select complete visual assemblies and their placement logic before counting
their constituent CAD objects. Each feature must articulate an existing form,
define a local access region, or clarify an actual visible interface. Exact
dimensions and fit are a later geometry gate. The names below describe exterior
game-art features, not verified internal functions or manufacturing provisions.

## Proposed catalogue

### Explicit repetition constraint — user correction, 2026-09-27

- Identical radial features around a seam, collar or nozzle are acceptable when
  the assembly itself calls for a repeated pattern. Common small fasteners may
  retain a consistent design.
- Hatches and caps are individually composed for their locations. Do not
  automatically copy them around all four faces or along axial rows.
- A change of length, size or rotation alone does not establish a new hatch
  design. Consider its outline, relationship to the surrounding form, edge
  treatment, fastener arrangement and grouping together.
- An identical hatch/cap counterpart requires a clear relationship to a genuinely
  repeated assembly; otherwise omit it or design the local feature deliberately.
- Do not replace mechanical repetition with arbitrary variation. The annotated
  layout must distinguish **intentional repeated hardware** from **individually
  designed access features**, with a placement reason for each access feature.

| ID | Feature | Concrete visual treatment | Proposed occurrence and placement rule |
|---|---|---|---|
| F01 | Nose/body joint collar | Existing fine recessed ring with small slotted heads; low contrast. | Retain the accepted R16 assembly at the existing nose boundary. |
| F02 | Conformal shoulder hatch | One broad, clipped-corner tapered cover following the round-to-square shoulder; a few perimeter fasteners. | One upper-face focal feature, behind the nose joint and ahead of the intake mouths. Its outline follows the taper. |
| F03 | Circular inspection caps | Shallow circular disc, fine annular lip, a small paired-fastener arrangement. | Two local accents: one in the forward service region, one aft. Different regions justify placement; no ring of identical circles. |
| F04 | Main-body access doors | Two or three larger rounded or clipped-corner panels with restrained perimeter joints and fasteners located at corners/ends. | Group on a selected lateral face around forward and aft service regions; different panel proportions respond to available skin. Replace the blanket small-cover rows. |
| F05 | Longitudinal service cover | One narrow flush strip following a body/intake edge, with two shaped terminal pieces and localized fasteners. | One lower-face assembly aligned with an existing longitudinal form. It provides a long secondary line without repeating panel boxes along every face. |
| F06 | Intake-housing edge joints | Fine inset seam following the actual housing-to-core boundary, with a short access break only where the exterior has room. | One related treatment per intake, justified by the four existing housing forms. Preserve mouths, channel depth and stage ownership. No seam across an open passage. |
| F07 | Main-fin root attachment seats | Paired small, shaped seats adjacent to the actual root, with compact recessed hardware. | One assembly per main fin. Seats follow the root footprint rather than placing a rectangular badge on the fin face. Exact construction requires a local fit study. |
| F08 | Booster-fin root collar detail | Narrow shaped inset/parting line following the existing curved fairing-to-fin transition. | One assembly per booster fin. Retain the R14 clean union; the visible curve dictates the outline. Distinct from the main-fin treatment. |
| F09 | Stage-joint segments | Restrained segmented collar/seam aligned to the existing stage split, with localized hardware on its own stage. | One coherent interface assembly. Detail stops at the actual split and remains correctly owned during separation. Replace unrelated seam ticks. |
| F10 | Booster access hatch | One compact polygonal or rounded-ended cover shaped to the available flat between the aft fins. | One chosen booster face. Separate from the main-body access-door layout, with space around the repaired fairings. |
| F11 | Nozzle rim assemblies | Existing recessed annular rim, sparse evenly spaced heads, neutral lip and dark inner funnel. | Retain the useful R17 local treatment on both stage nozzles. Pattern belongs to the circular rim, not a whole-body decoration rule. |
| F12 | Joint alignment marks | Small paired engraved ticks or short index marks with very low contrast. | A few selected existing interfaces, such as nose and stage joints. Marks relate to a boundary; they are never spread along empty skin to increase count. |

Screws, borders, liners and small seams are subcomponents of these assemblies.
Use the established slotted-head language consistently. Any alternate head,
paint or marking language would need a reason rather than variety for its own sake.

## Kris evidence supporting the vocabulary

- `cad/kris/generate_pl10_stencil.py:85-93`: section joints anchored to selected
  landmarks; `:111-133`: conformal nose covers, collars and small bezel hardware.
- `:148-161`: root strips and paired attachment shoes tied to strake geometry.
- `:182-207`: one-face fittings, localized marks and circular cosmetic covers.
- `:209-222`: distinct access-cover proportions and one longitudinal cover with
  terminal bands; `:240-244`: selected opposite-side counterparts.
- `:254-265`: small joint hardware, fine seams and restrained aft rim layers.
- `cad/kris/generate_kris_hybrid.py:240-254,276-281`: shaped housings and actual local
  interfaces. These support F07/F08's form-led approach, not copying grid fins.

F02's exact outline, F06's seam path, F07/F08's local fit and all Halberd-specific
placements are proposed adaptations. Kris's artistic approximations do not turn
these into measured real-world construction details.

## Proposed distribution — region and face roles

This establishes relationships, not final coordinates or a committed part count.

| Region | Composition | Deliberately quiet |
|---|---|---|
| Nose/shoulder | F01 retained; F02 as one main hatch; a nearby F03 cap or F12 mark only if it improves the grouping. | The ogive remains clean; no all-face hatch replication. |
| Forward intake/service region | Selected F04 doors and F03 cap; F06 joints track existing intake edges. | Intake mouths and surrounding lips stay visually legible. |
| Long central body | F05 supplies one controlled longitudinal accent. | Broad skin on the other faces; no recurring axial stations or seam punctuation. |
| Main-fin/stage interface | F07 groups explain root locations; F09 expresses the real stage boundary. | Flat gaps between unrelated root/interface groups. |
| Booster/aft | F08 responds to the repaired fairing curves; F10 supplies one access region; F11 concentrates hardware at the nozzle. | Booster flats without a chosen feature stay plain. |

Proposed face roles (body coordinates, not aircraft-side labels):

- **+Z:** main shoulder hatch and a restrained forward service cluster.
- **+Y:** selected larger access doors, grouped rather than evenly repeated.
- **−Z:** the longitudinal service-cover assembly and a quieter surrounding field.
- **−Y:** circular inspection accents and an aft access region, with broad gaps.
- **Diagonal stations:** intake boundaries and fin-root interfaces may repeat
  because the underlying assemblies repeat. Their details remain subordinate
  to those shapes and need not be copied onto every adjacent flat.

The exact assignment of individual caps/doors is provisional and should be
tested on the annotated layout. A feature may be omitted if it crowds an
existing form; empty skin is an intentional part of the design.

## Next gate

1. User selects or amends the catalogue.
2. Produce an annotated four-face layout plus a whole-model view using this
   vocabulary, with actual region boundaries and explicit quiet spans.
3. Review composition before detailed CAD. Prototype uncertain interfaces,
   verify skin/support/clearance, then distribute only the selected instances.
4. Count detail objects after composition. Do not restore the 223-object quota
   or duplicate assemblies merely to match Kris's raw inventory.

The original catalogue was documentation-only. Subsequent work produced a
separate checked planning-base STEP and annotated PNGs, documented in
`R18_SURFACE_LAYOUT.md`; no new detailed-feature CAD is claimed.
