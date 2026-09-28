# R18 — surface-composition proposal

Date: 2026-09-27. State: **`concept-approved`** for the annotated access-feature
distribution: after opening both sheets, the user requested continuing. Local
geometry/appearance checks remain required. The uncertain root/intake/stage
interface treatments still need their own fit and visual gates.

## Authorized next implementation — individual access features

Build all seven individually drawn access assemblies from
`reviews/R18_layout_manifest.json`, retaining their face, position, outline
and hardware differences. Use true circles/arcs for the round cap, keyed cap and
D-ended door; diagram polygon samples are not intended as faceted CAD edges.
Retain the R16 nose joint and the useful R17 nozzle-rim assemblies. Do not carry
over R17's repeated panel matrix, seam ticks or rectangular fin badges.

- Main body/booster skin receive only localized shallow seats. Nominal new
  pocket depth0.8 mm, cover setback0.18–0.2 mm, fine perimeter gap about0.3 mm.
  Curved shoulder hatch must follow the actual skin and have backed seats.
- Use body-tone cover faces and restrained metallic terminal/ring pieces;
  no heavy dark perimeter around every hatch. Slotted fasteners stay standard.
- F05 has one central strip and two individually shaped terminal pieces, with
  the two end fasteners from the drawing. F03A has a fine ring, disc and paired
  heads; F03B is a keyed disc with a real shallow central slot, not another copy.
- Standard heads may reuse the checked shortened R17 local hardware, seated
  to actual local skin normals with opening countersinks, support and clearance.
  Exact counts follow the design, not a quota.
- All older sources/artifacts remain preserved. New access-detail geometry
  must be checked against the saved28-part planning base; retained nozzle
  details/cutters must match their saved/pilot source and correct stage ownership.
- F06/F07/F08/F09/F12 interface routes and new hardware are later local passes,
  not silently claimed complete by this access-feature implementation.

## Review packet

### F02 curved-shoulder feasibility checkpoint

`src/halberd_r18_access_shapes.py` now measures native skin points/normals and
clips/extrudes the actual shoulder faces to create the conformal pocket and
cover. The original whole-body translated-shell Boolean produced an incorrect
large pocket and was replaced; slow fixed-step wall probing was replaced by
native ray/face intersections. Neither was accepted as successful geometry.

`checks/check_halberd_r18_access_preflight.py` reports `F02_SAVED_PROBE_PASS` in
`reviews/halberd_r18_f02_probe_checks.json`: six saved focus parts, actual skin
radius96.192–99.014 mm across the footprint,0.8 mm pocket,0.18 mm setback,
0.30 mm actual perimeter inset, supported slotted heads and zero new overlaps.
Primary directly inspected `R18_F02_probe_oblique.png` and `_grazing.png` and
selected the construction for continuation of the reviewed access-feature set.
This is a local feasibility/visual checkpoint, not user acceptance of final CAD.

- `reviews/R18_Surface_Layout.png`: four cardinal faces and a visible-face whole
  composition, annotated on actual saved-STEP renders.
- `reviews/R18_Feature_Designs.png`: enlarged individual access-feature outline
  studies with proposed hardware layouts; fit-to-cell, not equal scale.
- Individual face maps: `reviews/R18_layout_{upper,lateral_positive,lower,lateral_negative}.png`.
- Whole view: `reviews/R18_layout_whole.png`.
- Reproducible composition source: `reviews/compose_r18_layout.py`.
- `reviews/R18_layout_manifest.json`: base document hash, proposed outlines,
  face clocks, axial/tangential placements and image calibration.

Teal outlines represent individual access designs. Amber identifies repeated or
shared assembly-related interfaces. Green brackets mark intentional quiet skin.
Colors and leader dots are diagram annotations, not proposed final paint or extra
hardware. Interface leaders show intended regions, not completed seam paths.

## Seven individual access assemblies

Axial coordinates and footprints below are proposal guides in millimeters, not
approved construction dimensions. +X noseward; face names are body coordinates.

| ID | Face / axial center | Proposed design and local relationship |
|---|---|---|
| F02 | +Z / X=900 | A tapered, clipped shoulder hatch with four corner heads, narrowing with the shoulder toward the nose. Approximate footprint140×44. |
| F04A | +Y / X=440 | Broad forward access door with an asymmetric clipped end and six perimeter heads, in the forward intake/service region. Approximate180×44. |
| F04B | +Y / X=−790 | Aft access door with one rounded end and four heads; a separate local region ahead of the main-fin roots. Approximate130×40. |
| F05 | −Z / X=140, tangent offset14 | One narrow longitudinal cover with two differently shaped terminal pieces and terminal hardware. Approximate500×16; the other faces do not receive counterparts. |
| F03A | −Y / X=590, tangent offset−5 | A forward circular cap with a retaining lip and paired heads. Approximate36 diameter. |
| F03B | −Y / X=−1390 | A smaller keyed aft cap with a flattened edge and central slot. Approximate24 overall; distinct construction language from the forward circular cap. |
| F10 | +Z / X=−1450 | One offset-ended booster hatch with a three-point fastener arrangement, fitted between the existing aft forms. Approximate96×34. |

No access feature is copied to another face. F04A/F04B differ in outline and
fastener layout; F03A/F03B differ in retaining treatment, outline and hardware.
Variation is tied to the region, not random offsets or length-only changes.

## Shared/interface detailing

- F01: retain the accepted fine nose joint.
- F06: develop fine intake-edge seams against the actual housing boundaries;
  routes need a local fit study, especially at the stage seam.
- F07: paired small seats adjacent to the actual main-fin roots. The diagram
  identifies the region; it does not reuse the rejected R17 rectangular badges.
- F08: shape booster-root collar details around the preserved R14 fairing curve.
- F09: one coherent stage interface, expressed on the appropriate faces and
  owned by its respective stage. No isolated axial seam-tick array.
- F11: carry forward the useful R17 nozzle-rim treatment at the later CAD gate.
  These R17 parts are not embedded in the planning-base STEP.
- F12: only localized joint index marks; the upper-face diagram illustrates the
  nose pair. They are not scattered over empty skin.

Quiet skin is explicitly reserved through the central body. The lower-face
longitudinal feature is one controlled exception, not a four-face rail array.
The clean ogive is preserved. Further hardware is concentrated at visible root,
joint and nozzle assemblies rather than placed to recover an object quota.

## Planning-base evidence and limitations

`src/halberd_r18_layout_base.py` creates a separate28-part presentation base from
saved R16/R12. It hides the16 old service-cover parts and restores only their
body seat cuts within X=[−420,−220], retaining all other27 R16 parts including
the accepted nose joint and clean booster fin/fairing unions. Older artifacts
are preserved. This base is not the new detailed candidate.

`checks/check_halberd_r18_layout_base.py` passes on the saved STEP: independent
comparison against R12 minus the R16 nose-joint cuts, all27 unchanged peers,
all28 valid positive closed single solids/no self-intersections, material hash
and finishes,3370mm length and preserved301.793mm transverse envelope.
Evidence: `reviews/halberd_r18_layout_base_checks.json`.

The five raw snapshots were generated from that saved base. Primary authored the
feature map, projected visible-face outlines onto the sampled native skin,
composed both boards and directly inspected them. Label collisions in the first
board were corrected and the final maps re-inspected. Four-face locations use
orthographic silhouette calibration; the whole view uses sampled native edges
and the camera basis. This is visual placement evidence, not a check of pocket
depth, fastener support or physical construction for the proposed features.

[3D planning base](http://127.0.0.1:3247/?file=STEP/halberd_r18_layout_base.step)
contains the preserved geometry only; the proposed overlays are in the PNGs.

## Next gate

User approves or corrects distribution and feature identities on the two boards.
Then build a local forward cluster and the uncertain root/interface treatments,
check fit and appearance, and extend the accepted designs. No R18 detailed
feature geometry, final count, engine export or runtime acceptance is claimed.
