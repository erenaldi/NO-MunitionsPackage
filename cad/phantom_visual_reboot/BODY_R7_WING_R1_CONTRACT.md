# R7 mirrored lower shoulders / first folding-wing prototype

2026-09-23 22:56 -05:00. Body state: `cad-review`. Wing state: `blocked`.

**Subsequent user correction:** K/Wing R1 is rejected as an inaccurate GBU-39
mechanism reference. Do not propagate it. Research confirms MBDA's joined
tandem-wing architecture, which this single-panel swivel omitted. See
`GBU39_WING_REFERENCE_RESEARCH.md`; the historical checks below remain evidence
only for this rejected experiment, not approval or GBU-39 fidelity.

## Active context and authority

User requested equality of two circled lower shoulder areas and to start other
features. This accepts the current body/nose direction as the basis for appendage
studies, conditional on correcting those transitions; it is not whole-airframe
approval. The inline screenshot was inspected directly; no persistent path claimed.

- Body source: `src/symmetric_body_r7.py`; J full-body and close-up STEPs.
- Wing source: `src/wing_prototype_r1.py`; K deployed, midfold and stowed STEPs.
- Axes: +X nose, +Z up, +Y starboard; mm, total length 2800.
- Retain: square barrel, cleaned upper shoulders, 20 mm horizontal wedge with
  4 mm radius centered at (1400,0,40), reduced nose belly.
- Next decision: first wing planform/placement/fold before opposite-side
  propagation. Tail-fin and flush RF studies follow; three whole-airframe
  directions and actual donor-rack fit remain pending.

## Symmetry correction

The inherited lower loft had an extra short strip on the port side. R7 uses
the cleaner starboard half and its exact reflection, then unifies the seam.
Exported whole-body mirror difference is zero. Three paired lower-shoulder
face areas match: 3792.235280, 15769.304680 and 29051.735680 mm2 per side.
Exact Boolean comparisons retain the barrel, entire nose beyond X=1010 and
upper shoulder above Z=50. Lighting may shade equivalent sides differently.

## First wing — reversible assumptions

- One starboard panel: 650 mm hinge-to-tip span, 140 mm chord at Y=15,
  90 mm tip chord, modest aft sweep, 4 mm constant thickness.
- Vertical hinge at X=-160/Y=0; deployed 0 degrees, midfold -45, stowed -90.
  Panel remains visibly external along the roof when stowed.
- Integral 22 mm-radius root with 4.1 mm-radius bore; actual 4 mm-radius pin
  and retaining cap. Saddle overlaps the body; pin seats into saddle.
- Panel Z=89.5..93.5; roof Z=86; saddle top Z=89; cap starts Z=94.
  These are visual packaging assumptions, not engineering certification.
- GBU-39 cue: identifiable folded/deployed external wing. This original
  single-pivot study does not reproduce its precise linkage. TALD/ITALD's
  aircraft-like character is a later whole-silhouette judgement. Kh-69 cues
  remain in the body and later tail study. No new source-photo fidelity claim.

## Verification

`src/check_body_and_wing_r1.py` PASS on serialized exports:

- Two body artifacts valid single solids; whole-body mirror difference zero,
  paired lower face areas equal, retained regions match R6.
- Four labeled valid solids in each wing pose; identical body/hardware;
  inverse hinge transforms yield identical panel geometry; length 2800 mm.
- Conservative stowed radial bounds: body 121.6224 mm, wing 116.8000 mm,
  pin/cap 96.3328 mm, saddle 92.4446 mm, all below 125 mm.
- Nineteen poses at 5-degree steps: zero wing/body/hardware overlap; clearances
  3.5 mm to body, 0.5 mm to saddle, 0.1 mm to pin. Constant height and coaxial
  bore support clearance between samples. Second wing, tail, rack, actuator
  and lock are not included in this result.
- Initial checker hit `None` for an empty intersection; explicit empty handling
  fixed the API case without relaxing overlap thresholds. Exploratory import
  timed out at 20 seconds; a progress-logged 60-second retry succeeded.

Evidence: `reviews/body_wing_r1_checks.json`. All thirteen snapshots from
`review_JK.json` directly inspected; composed and inspected
`reviews/JK_Symmetry_OneWing_Review.png`. Lower seams match; stowed wing and
pin are legible. Side-on wing is thin; whole-airframe game-distance identity
and contrast remain open. All five paths exist; viewer port 3245 returned
HTTP 200 for each. Next: user reviews first wing before repetition and tail study.
