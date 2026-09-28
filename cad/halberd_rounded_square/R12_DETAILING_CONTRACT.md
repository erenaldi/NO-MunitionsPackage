# R12 propagation and first detailing pass

**Superseding design direction (2026-09-27):** user rejected R17's repetitive
full-body layout. See `R17_DESIGN_CRITIQUE.md`. The next pass must establish
regional surface design before propagation; numerical parity with Kris is not
an acceptance criterion. No CAD was removed during the critique.

Date: 2026-09-24; updated 2026-09-27. R12 propagation is verified. Current **`cad-review`** candidate is [R17 full surface-detail pass](R17_FULL_DETAIL_CONTRACT.md): 223 detail instances, carrying the approved R16 joint and existing R15 covers while preserving R14 booster-junction geometry outside new shallow detail pockets.

User accepted the approximate 80–120 detail-object / 20–30 meaningful-group
planning range, then prioritized the booster taper/fin clipping repair before
further surface detailing. This range does not substitute for visual quality.

## Selected Kris object inventory — 2026-09-27

Direct `read_scene` inventory of `cad/kris/IRM-S4_Kris_PL10_Hybrid.step` reports
**270 placed objects**. Conservative label-based classification excludes48
primary body/aerodynamic forms, structural mounts, optical and exhaust-back
faces, leaving **222 surface-detail objects**:114 fasteners,55 panels/covers/
borders,24 small attachment plates,29 seams/rims/bands/fittings/marks.
Reproduce with `checks/count_kris_details.py`. This counts instances, not unique
designs, faces or grid-fin cells. The source document hash is
`c35d10d58c4529c0d492b9516b17bb9c850e4dcf0f94e917f1eebfbae9a986ca`.
The earlier80–120 Halberd planning range was an estimate, not a measured Kris
count; it is materially lower than this reference inventory. No automatic target
change or equal-count quality claim follows from the inventory.

Subsequent user direction explicitly raised Halberd to Kris-scale detail count.
R17 now has223 verified detail instances; the earlier80–120 estimate is superseded
for this task. See `R17_FULL_DETAIL_CONTRACT.md` for actual family inventory,
verification and remaining user-review boundary.

## Approved decisions

- User approved R11 ("Perfect") and explicitly authorized copying it to the
  other three stations, then beginning detailing.
- All four stations use the exact approved continuous intake taper, ridge-aligned
  endpoint, 80 mm rear fin, unchanged intake height and booster-owned aft section.
- User explicitly selected `cad/kris/IRM-S4_Kris_PL10_Hybrid.step` as the target
  quality reference. It supplies detailing quality, not Halberd's silhouette.
- Preserve the approved rounded-square body, ogive, lengths, intake mouths,
  channels, fin placement, dark backs and clean stage separation.
- The primary model owns direct visual inspection and the detailing decisions.
- New uncertain repeated details require a one-feature review before propagation.

## Files and next gates

- Propagation source: `src/halberd_r12_shapes.py`.
- Outputs: `STEP/halberd_r12.step`, `halberd_r12_separated.step`.
- First inspect the selected Kris STEP and its authored details. Establish a
  bounded first-detail region from that evidence, build it, and offer visual
  review before extending the treatment to other regions. This packet is now
  available for R13; approval remains pending.
- This is a CAD/art-detailing gate; engine delivery remains a later boundary.

## Reference evidence and first pass

The actual Kris hybrid STEP was imported into a read-only service-panel crop,
`STEP/kris_detail_reference.step`; fresh `reviews/Kris_detail_{oblique,top}.png`
were directly inspected. Source evidence: `cad/kris/generate_pl10_stencil.py:246-258`
uses 0.35 mm skin relief, 0.8 mm borders, two small slotted fasteners per panel,
and fine section seams. `cad/kris/generate_kris_hybrid.py:240-254,310-322` supplies
blended housings and small metallic hardware. These are quality cues, not new
shape requirements or a mandate to copy the grid fins.

First region: one dorsal service cover on the flat skin between the corner
intakes, centered at X=-320 mm. A 124 x 30 mm shallow rounded seat contains a
120 x 26 mm cover with a 0.35 mm rim bevel, a recessed dark-gray border, and two
small slotted/countersunk cosmetic fasteners. The cover top is 0.15 mm below the
original skin. No visible part protrudes beyond the approved skin envelope.
This begins the panel/hardware treatment; it is not a claim of whole-model
detailing parity with Kris. First local review precedes panel propagation,
body-joint layout, fin-root hardware and nozzle detail passes.

Source/outputs: `src/halberd_r13_shapes.py`, `STEP/halberd_r13.step`,
`halberd_r13_separated.step`, `halberd_r13_focus.step`.

## R13 verification and local review — 2026-09-26

- `checks/check_halberd_r13.py` passes on saved artifacts: 31 assembled,
  31 separated and five focused placements pass single-solid, positive-volume,
  topology, closed-shell and self-intersection checks. Report:
  `reviews/halberd_R13_checks.json`.
- Measured seat depth is 1.2 mm; cover and fastener tops are recessed 0.15 and
  0.35 mm. All four added parts contact the body within the seat, slots are open,
  and fastener/cover intersections are absent. All 26 unaffected R12 parts,
  stage transforms, channels and approved outer envelope are preserved.
- Initial material-ID assertion failed because composed inherited definitions
  receive `local/` IDs. The checker now resolves assignments and compares
  metalness, roughness and name against R12/source authority while retaining
  document-hash binding and every geometry check. No geometry repair was needed.
- Primary directly inspected `reviews/R13_detail_{oblique,top,grazing}.png`,
  `R13_whole.png`, `R13_separated.png`, and `R13_Kris_Detail_Comparison.png`,
  alongside existing saved-Kris oblique/top and R12 iso/opposite/front/separated
  images. R13 images are newly rendered; Kris/R12 comparison inputs are the
  preserved prior packet, not newly rendered this session.
- Visual assessment: clean inset cover, readable small slots, restrained
  whole-model presence. The dark rounded perimeter is visibly heavier than
  Kris's fine square-corner border; approval should explicitly settle this
  treatment before propagation. The comparison is qualitative, not equal-scale
  metrology. Whole-model detailing parity remains pending.
- Verified viewer on port 3247:
  [focus](http://127.0.0.1:3247/?file=STEP/halberd_r13_focus.step),
  [assembled](http://127.0.0.1:3247/?file=STEP/halberd_r13.step),
  [separated](http://127.0.0.1:3247/?file=STEP/halberd_r13_separated.step).
- Next gate: user approves or corrects this single cover treatment before any
  panel repetition, body-joint layout, fin-root hardware or nozzle detailing.
