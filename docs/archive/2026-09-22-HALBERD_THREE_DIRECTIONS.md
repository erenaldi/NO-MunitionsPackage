# AAM-44 Halberd — three Blender silhouette demos (2026-09-22)

> Archived unapproved study: after reviewing the first production and references, the user was dissatisfied with these directions and requested a return to the earlier CAD skill workflow. The `.blend` and review renders remain available as historical evidence, not as an approved source master.

## Historical context

- **State when archived:** unapproved `concept-review`. These were three geometry-only blockouts for user comparison; none was selected or approved.
- **Authoritative source for this packet:** `cad/Halberd_Three_Directions.blend` (scene `Halberd | three silhouette demos`). The older Shoulder hybrid and four-intake STEP studies are separate historical candidates, not geometry donors for these demos.
- **Review packet:** `cad/Halberd_Three_Directions_{Side,Top,Iso,FrontIso,Front,Rear,Separated}.png` and `cad/Halberd_Demo_B_Intake_Close.png`. In side, top, isometric, and separated views the top row is C, center B, bottom A. The end-on views place the models diagonally, so use the `.blend` collection names to identify them.
- **Coordinate system and scale:** metres; local +X forward, +Z dorsal, +Y lateral. All three assembled missile bodies run from X = -1.6835 to +1.6835 m. The booster occupies X = -1.6835 to -1.1223333333 m: 0.5611666667 m, exactly one-sixth of the 3.367 m body length. Each assembly is translated for the comparison layout, but its local component coordinates retain these datums.
- **Preserve:** pointed radar nose, heavily filleted square body, four diagonal intake stations, separate compact booster and upper-stage fin/nozzle identities, and a clear dorsal mounting lane. Keep reference borrowing visual and attributable; the Buk M3 image motivates a small forward-fin option and later surface/paint explorations, not a copied missile.
- **Avoid:** promoting a sketchy mouth into a claim of working intake flow; assuming aircraft fit, accepting color as a substitute for silhouette, or changing the current production candidate from this concept file.
- **Reference correction (user, 2026-09-22):** the red details in the supplied long-strake missile image are **intake coverings**. Read the reference as a covered inlet at the forward end of each long, body-integrated intake/strake assembly. The existing Blender demos' short open boxy scoops do not reproduce that relationship; revise the intake architecture before using this reference to approve a silhouette. The red finish itself belongs to the later palette/detail pass.
- **Open decisions:** select, reject, or hybridize A/B/C; whether forward fins and long strakes survive; improve intake-mouth visibility at full-view scale and verify carrier clearance before detailed modeling; after shape selection, explore Buk-inspired palettes and surface detail. Gameplay motor retuning remains after concept approval.
- **Former next gate (superseded):** selection or hybridization of A/B/C. The user instead returned to the former CAD skills; any future design needs a new brief and review before production work.

## Three assemblies

| Collection | Silhouette premise | Forward surfaces | Upper-stage tail | Booster tail |
| --- | --- | --- | --- | --- |
| A — long integrated strakes | Long swept flank surfaces rise toward the stage seam; shoulder builds gradually into the intake band. | Small fins | Long integrated swept set ending ahead of the seam | Compact swept set |
| B — segmented canards and tails | The rounded-square body necks subtly behind a stronger intake shoulder; separated fin stations give an explicit front-to-back rhythm. | Large compact Buk-inspired fins | Distinct broad aft set | Distinct aft set |
| C — clean compact tails | Continuous restrained body and tapered forward shoulder; appendages stay close to the two aft stages. | Very low finlets | Short clipped aft set | Tight compact set |

All three use neutral clay materials. The shell has four Boolean-carved corner channels per assembly with individual hollow open-mouth cowl and recessed-throat pieces. The visual studies do not establish viable ramjet ducts, aerodynamic performance, launcher compatibility, or final topology for export.

## Review and verification

- Reopened the saved `.blend` in Blender 4.5.14 LTS: two scenes (including the unchanged original default scene), six review cameras, and three named concept collections with 26 mesh objects each.
- Blender mesh readback: each booster part group spans precisely X = -1.6835..-1.1223333333 m, ratio 1/6; each upper-stage group has four open cowl and four recessed-throat objects; all three Boolean-carved sustainer bodies have zero non-manifold edges.
- Direct image inspection: matched side, top, two obliques, front/rear, separated, and B intake end-on views. A has the strongest long-strake read, B the clearest forward-fin station, C the cleanest restrained forebody. The narrow intake mouths are conspicuous end-on but still subtle at assembled-missile scale. The end-on shot also stacks several fin sets into a busy outline; that is a concept-review issue, not an approval.
- The separated image is a temporary 0.31 m aft translation of booster-owned objects. The saved `.blend` restores all three assemblies to the assembled position; their named booster parts can be moved as a group for further staging studies.
- **Unverified:** exact rack/pylon clearance, functional intake interiors, aerodynamic or propulsion claims, materials/palette, export, Onshape, Unity, and in-game behavior.
