# Halberd clean-sheet concept comparison

2026-09-14. User selected Option B (Shoulder). Five broader descendants with
matched booster outlines are recorded in `HALBERD_SHOULDER_VARIANTS.md`.
The comparison below preserves the initial two-concept review as historical evidence.
Neither imports or modifies the detailed Halberd master, prior model experiments,
production exporter, Unity assets, bundle, or gameplay. They share newly authored
primitive helpers and neutral presentation settings with each other.

## Brief and evidence

- User authority: two unrelated-to-previous-work designs, one three-intake and one
  four-intake, retaining tandem booster/sustainer architecture.
- Architecture interpretation: rear booster detaches; the forward sustainer keeps
  its own fins and exposes its nozzle. Both detached pieces have finished faces.
- Assistant comparison choices: identical 3367 mm overall length, centered pivot,
  CAD +X forward/+Z dorsal/+Y lateral, seam X=-336.7 mm, neutral palette. These
  datums make comparison fair; they do not imply adoption of production geometry.
- Presentation gap in separated models: 350 mm, display only.
- New form choices below are artistic proposals, not measured real-world designs.
- AAM4 comparison uses the game's actual `AAM4.geometry.obj`, selected through
  `BepInEx/config/Erenaldi.MunitionsPackage/missile-geometry.json` (dump timestamp
  2026-09-14T03:32:13.1842254Z). It is an unmounted mesh comparison, not a pylon or
  aircraft clearance test. No aerodynamic performance claims are made.

## A — Pod, three intakes

Round central body, separate pointed radome, three short oval-mouthed enclosed
housings at 60/180/300 degrees, and independent swept sustainer fins. The housings
end well before the fins. A slightly fuller booster cartridge has three clipped
tail blades, a recessed exhaust and a shallow dished forward closure. Two compact
shoes occupy the dorsal corridor without a long rail or service-strip network.

**Strengths:** readily countable three-lobed identity; actual forward-facing
mouths; clear separation between intake volume and tail fins; stronger recognition
in top silhouette than the flush four-intake alternative.

**Adversarial findings:**
1. From aft quarters, the long rounded housings resemble auxiliary tubes. If
   selected, their cross-section and leading rim deserve the next shape pass.
2. Neutral gray cavity backing looks like a cap head-on. The cavities are real,
   and volume probes pass, but depth readability remains a presentation weakness.
3. The ventral pod creates a deliberate bottom-heavy side silhouette. This is
   threefold symmetry, not a placement error; acceptance is an artistic choice.

## B — Shoulder, four intakes

Rounded-square sustainer body with four carved shoulder recesses at
45/135/225/315 degrees. These are integrated, flush scoop-like openings rather
than added pods. Four short sustainer fins and four swept booster fins repeat
that X-pattern. The round booster contrasts with the faceted upper body.

**Strengths:** cleaner side silhouette, strong end-on fourfold identity, integrated
housing construction, and a naturally clear dorsal centerline.

**Adversarial findings:**
1. Side views read the recesses as slots or vents more readily than intake mouths.
   A stronger mouth shoulder is the highest-value next refinement if selected.
2. In silhouette, the flush openings disappear: the pointed body and two fin sets
   carry recognition. This is less immediately distinctive than Pod.
3. The square-to-round transition is deliberately faceted and still concept-level;
   it needs a highlight-continuity pass before production surfacing.

## Shared review result

Neither is a production-ready hero asset. Both need more deliberate mounting
interfaces, edge treatment and stage-joint detailing after concept selection.
The existing detailed model's long cowls/strakes, shoulder-strake fins, stacked
collars and hardware network have not been reused.

The main agent reviewed the 26 matched snapshots using full-size feature images
and four comparison boards, plus actual AAM4 side/top silhouettes. A gray body-cap
overlap at the nozzle backing was found, removed in source, and guarded by new
contact/backing checks. The repaired upper-stage aft views were reviewed again.
Remaining tube/vent ambiguity is recorded above rather than hidden with paneling.

Recommendation: **Pod** for a more recognizable three-intake silhouette;
**Shoulder** for the cleaner, more integrated four-intake direction. These should
remain separate concepts through user selection, not be merged prematurely.

## Validation and artifacts

`python check_halberd_concepts.py` passes against the exported STEP files:
unique labels, one valid positive solid per part, 3367 mm length, stage ownership,
body/fin/intake/shoe contact, radius <=220 mm, 3+4 clear cavity probes, and
nozzle backing free from body-cap overlap. Report: `cad/halberd/Halberd_Concept_Checks.json`.

`cadgen step inspect validate` after the repair:

| Master | Occurrences | Prototypes | Failures |
|---|---:|---:|---:|
| `cad/halberd/Halberd_Concept_Pod.step` | 16 | 10 | 0 |
| `cad/halberd/Halberd_Concept_Shoulder.step` | 19 | 10 | 0 |

Self-intersection mode was default first-placement. Sampled reported radial
extents are approximately 216.02 mm (Pod), 211.01 mm (Shoulder); the <=220 mm
envelope check uses BREP subtraction rather than sampling alone.

Sources: `cad/halberd/halberd_concept_shapes.py`, `cad/halberd/generate_halberd_pod_concept.py`,
`cad/halberd/generate_halberd_shoulder_concept.py`, `cad/halberd/generate_halberd_concept_reviews.py`,
`cad/halberd/check_halberd_concepts.py`, `cad/halberd/compare_halberd_concepts.py`.

Each concept has `_Separated`, `_Upper`, `_Booster`, `_Intake` review STEP files.
The review generator writes `cad/halberd/halberd_concepts_snapshot_job.json`; render with
`cadgen step snapshot --job halberd_concepts_snapshot_job.json` from `cad/`.
PNG names: `Halberd_Concept_{Pod,Shoulder}_{iso,opposite,side,top,nose,tail,
separated,separated_opposite,intake,mouth,grazing,upper_aft,booster_face}.png`.
Comparison boards: `cad/halberd/Halberd_Concept_Comparison_1.png` through `_4.png`;
scale comparison: `cad/halberd/Halberd_Concept_AAM4_Silhouettes.png`.

Unity grouping, colliders, materials, LODs, aircraft mounts and runtime behavior
are not delivered or verified at this concept-selection boundary.
