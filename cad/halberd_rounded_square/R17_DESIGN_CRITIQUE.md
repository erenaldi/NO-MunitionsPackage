# R17 versus Kris — surface-design critique

Date: 2026-09-27. **R17's full surface layout is rejected by the user.** Its
saved-geometry checks remain valid technical evidence; they do not pass the
visual-design gate. All CAD artifacts are retained unchanged for comparison.

## Review evidence and ownership

The user explicitly requested an independent critique after identifying excessive
repetition and degraded appearance. A bounded independent general-agent critique
read the R17 contract/builders/check report, the two selected Kris generators,
and seven named local comparison/detail images. It reported direct image access.
Primary independently re-inspected the whole-model comparison and Kris close-up,
and read the cited Kris placement source. Final design interpretation remains
with the primary and user.

## Verdict

The count-driven layout materially weakens Halberd. It reaches 223 detail objects
without reproducing Kris's regional composition, varied interfaces or deliberate
quiet regions. Merely varying rectangle lengths does not break the repeated
two-fastener-cover pattern. The next pass needs a whole-body surface design.

## Ranked findings

1. **Critical — repeated axial matrix dominates the asset.**
   R17's cover-station list and four cardinal rotations populate the long body
   with synchronized rows. The independent fourfold seam array reinforces this
   pattern. Evidence: `src/halberd_r17_shapes.py:43-55`, `:296-338`;
   `reviews/R17_whole.png`, `R17_opposite.png`. Randomizing offsets would retain
   the same failed placement logic.
2. **Important — detail density lacks regional hierarchy.**
   R17 has gaps between objects but little distinction between busy assemblies
   and quiet skin. Kris's forward cluster, intervening quiet body, strake-related
   hardware and concentrated tail each read differently in
   `reviews/R17_Kris_whole.png`. Kris source ties joints to selected landmarks
   (`cad/kris/generate_pl10_stencil.py:85-93`) and paired attachments to strake roots
   (`:148-161`), rather than treating every axial station as equivalent.
3. **Important — dark borders amplify repetition.**
   R17's nominal 2 mm dark cover borders remain prominent at whole-model scale
   after small hardware becomes indistinct (`src/halberd_r17_shapes.py:113-124`).
   The visual result is rows of dark boxes. Kris's repeated service panels have
   less emphatic metallic borders (`cad/kris/generate_pl10_stencil.py:233-237`;
   `reviews/Kris_detail_oblique.png`).
4. **Important — features do not sufficiently respond to their host forms.**
   The isolated 50 mm seam ticks with one nearby screw do not organize meaningful
   body regions. Fin strips are geometrically conformal but use essentially the
   same rectangular patch on distinct fin/fairing shapes. Kris's paired shoes
   follow strakes, its seams define sections, and its tail housings are shaped
   around the actual fin (`cad/kris/generate_kris_hybrid.py:240-254`, `:276-281`).
5. **Important — numerical completion displaced design review.**
   The R17 contract fixed a 223-object budget before a whole-body layout existed.
   Local prototype review tested fit and appearance of one detail, but not the
   effect of its extensive repetition. Primary's final assessment understated
   the visible matrix as merely "more regularly patterned." That assessment is
   superseded: the layout fails the user's intended design quality.

## What the Kris comparison actually supports

Kris also repeats panels, bolts and tail stations. Its advantage is the relation
between repetition and identifiable local assemblies. It combines rectangular
and round panels, longitudinal covers, collars, discrete fittings and small
marks, with different placement rules and density by region. One-face fittings
are explicit at `cad/kris/generate_pl10_stencil.py:182-192`; round covers and distinct
surface marks at `:193-207`; rail/access-cover treatment at `:209-222`.

Kris is still an authored art reference. Its generator labels obscured placements
artistic approximations (`:224-226`); neither asset proves physical functionality.
Surface design should be explained by visible forms and reference evidence,
without inventing unsupported internal mechanisms.

## Corrective direction — planning only

- **Keep as a foundation:** approved body/intake/fin silhouette, R14 booster
  junction cleanup, accepted nose joint, restrained nozzle-rim treatment and
  reusable pocket/fastener construction. Existing files remain intact.
- **Remove from the next proposed layout:** blanket cover rows and isolated
  seam ticks. Do not replace every removed object merely to retain the count.
- **Redesign:** a few intentionally dense regions linked to visible interfaces,
  with explicit quiet spans; selected cover shapes/orientations should relate
  to their region. Fin-root details must articulate the actual junction rather
  than decorate the fin face with a generic badge.
- Symmetry is retained where the larger form supports it. Every feature need
  not be copied to all four faces. Irregularity alone is not a design solution.
- **Next deliverable:** an annotated four-face surface-layout proposal plus
  whole-model comparison. Explain each cluster's relationship to the existing
  shape and mark areas intentionally left quiet. Review that composition before
  another detailed CAD propagation pass.
- The earlier 222/223 count is a descriptive metric, not an acceptance quota.
  Count may be reported after layout design but cannot determine placement.

No geometry was changed for this critique. No redesign has been approved or
built. Current full-layout progression is blocked on the revised composition.
