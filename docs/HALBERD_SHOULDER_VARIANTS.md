# Halberd Shoulder — five broad variants

2026-09-14. User selected Option B (Shoulder), requested five substantially
different whole-model studies, and required each booster to continue the
sustainer's cross-section without a stepped or circular transition.

## Designs and dimensions

Dimensions are millimeters. Body width/height are measured at the stage joint,
not the overall fin envelope. These are aesthetic studies, not approved game scale.

| Variant | Length | Joint width × height | Corner radius | Nose length | Character |
|---|---:|---:|---:|---:|---|
| B1 Needle | 3600 | 170 × 170 | 47 | 740 | Slender, long nose, narrow recessed slots, compact swept fins |
| B2 Broadhead | 3000 | 250 × 250 | 65 | 400 | Short and full-bodied, broad intakes, large cropped blades, single broad saddle |
| B3 Chisel | 3360 | 208 × 208 | 12 | 570 | Tight corners, planar nose, angular recesses and forward-offset fin tips |
| B4 Manta | 3200 | 320 × 144 | 36 | 590 | Flattened body/nose, widely spread upper/lower fin pairs, broad saddle |
| B5 Sculpted | 3500 | 226 × 226 | 85 | 650 | Softly squared body, curved nose loft, fuller smooth recesses and swept fins |

All retain four diagonal shoulder recesses, independent sustainer/booster fins,
a pointed nose, centered X-axis pivot and +Z dorsal direction. Manta's fins are
clocked 70/110/250/290 degrees to spread them laterally; the other fin sets use
45/135/225/315 degrees. The neutral palette is shared for fair visual comparison.
The rear booster remains 40% of total length in these studies. Length, body
aspect/corner shape, nose proportion, recess dimensions, fin span/chord/sweep,
mount arrangement and aft taper vary; stage fraction is a controlled commonality.

## Continuous booster transition

The booster and sustainer use the same rounded-rectangle profile at each joint,
including Manta's flattened section. Both have constant external cross-section
next to the seam. The booster only tapers near its aft exhaust; the sustainer
only narrows toward its nose. No external collar or circular waist spans the joint.
The circular sustainer nozzle is recessed **inside** that matching outer outline.

`check_halberd_shoulder_variants.py` compares 60 mm BREP bands on each side,
translated to a common origin. A central cylindrical region is excluded because
the nozzle and booster dish intentionally differ internally. Outer bands match
in both subtraction directions: **0.0 mm³ difference** for all five. Half-band
comparisons and matching to a constant-section extrusion also return zero,
establishing equal outline and zero axial taper on both sides of the seam.
This verifies the outer junction itself; no global surface-smoothness claim is made.

## Adversarial visual assessment

- **Needle:** strongest slender-dart extreme, but its shallow intakes disappear
  at small scale and may look like service grooves. Compact fins make it restrained.
- **Broadhead:** clearest substantial/compact alternative, with the most obvious
  fin area in side view. Risk: it reads heavier than the original medium-range AAM.
- **Chisel:** strongest planar/faceted direction. It can look extruded and boxy;
  a selected version needs careful nose-to-body and intake-mouth surface treatment.
- **Manta:** largest departure in cross-section and side-versus-top silhouette.
  Its wide body/fins need aircraft-specific clearance checks. Circular exhaust
  within the flattened aft face is visually small; deliberate alternate surround
  treatment is a possible next art decision, not a validated integration change.
- **Sculpted:** closest to a rounded missile while retaining Shoulder identity.
  Less radical than Manta/Chisel. The nose and recesses are smooth lofts; fin-root
  blending and final surface detailing remain future work, not completed features.

The main agent reviewed 60 generated snapshots via four labeled boards, the
same-scale silhouette plate, and full-size Manta/Sculpted feature views. No broken
solid or disconnected attachment was identified. The recessed intakes remain
concept-level open shoulder scoops; mouth/lip definition and depth readability
need refinement on the selected design. No paneling was used to disguise similarity.

Suggested shortlist: **Broadhead** for a substantial conventional direction,
**Chisel** for an angular direction, **Manta** for the most unconventional direction.
Needle and Sculpted retain useful slender/rounded alternatives.

## Validation and delivery boundary

Fresh deterministic checks pass all five: unique labels; valid positive solids;
length and stage ownership; matching section width/height and outer junction;
fin/mount/nozzle contact; four clear inlet probes; no body intrusion into nozzle
backings. `cadgen step inspect validate` passes with zero failures:

| Model | Occurrences | Prototypes |
|---|---:|---:|
| B1 | 15 | 8 |
| B2 | 14 | 8 |
| B3 | 15 | 8 |
| B4 | 14 | 8 |
| B5 | 15 | 8 |

Default first-placement self-intersection checks were used. Report:
`cad/halberd/Halberd_Shoulder_Variant_Checks.json`.

Five complete, five separated (350 mm display gap), five seam and five intake
review STEPs are generated in `cad/`: `Halberd_B1_Needle.step` through
`Halberd_B5_Sculpted.step`, plus `_Separated`, `_Seam`, `_Intakes` suffixes.
Snapshots: `cad/halberd/halberd_shoulder_variants_snapshot_job.json` (60 views).
Boards: `cad/halberd/Halberd_B_Variants_Board_1.png` through `_4.png`.
True-scale reference: `cad/halberd/Halberd_B_Variants_TrueScale.png`, projected from the
actual dumped AAM4 OBJ and concept STEP tessellation. It is not a mounted test.

Sources: `cad/halberd/halberd_shoulder_variants.py`,
`cad/halberd/generate_halberd_shoulder_variants.py`,
`cad/halberd/review_halberd_shoulder_variants.py`,
`cad/halberd/compare_halberd_shoulder_variants.py`,
`cad/halberd/check_halberd_shoulder_variants.py`.

No variant is integrated into Unity. Different lengths and seams require a
revised delivery/FX/collider contract after selection. Existing production CAD,
Unity prefabs/materials, embedded bundle and gameplay were not edited for this task.
