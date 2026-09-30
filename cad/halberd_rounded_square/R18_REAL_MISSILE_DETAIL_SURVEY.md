# R18 — real-missile surface-detail survey

Date: 2026-09-28. State: evaluation only; no geometry changed. Purpose: decide what
"actual surface object detailing" should add to the R18 access pass, from
observed real hardware rather than the Kris art reference.

## Evidence and limits

Photos were viewed (not saved) in the browser pane from Wikimedia Commons at
1920 px; small features were inspected by cropping in-page. Limits: no photo is
close enough to resolve fastener head form; two Meteor images are trade-show
models, not flight hardware; AMRAAM photo shows the launcher rail more than the
missile. Findings below are what was visible, labelled by confidence.

| Reference (Commons file) | Type | Used for |
|---|---|---|
| `2019 Royal International Air Tattoo 1P4A8361 (48387229361).jpg` | Meteor, real display round | joint bands, stencils, dark data slot, top lug studs |
| `Meteor, MBDA, Madrid, 2015.jpg`, `Lenkrakete Meteor.jpg` | Meteor display models | slot layout, flag/roundel decals |
| `MBDA Brimstone (45372527695).jpg` | Brimstone, display round | fastener rows, seam step, hardpoint blocks, stencils |
| `AIM-120 AMRAAM B.jpg` | AMRAAM on carrier deck | color rings, weathering, rail hardware |
| `AGM-88 HARM in hangar.jpg` | HARM, display round | brass band, cable raceways, lug studs, tags |
| `AGM 88 - HARM.jpg` | HARM, museum | band placement, nose stencil |

## Details seen on real missiles

| # | Detail | Observed | Confidence | R18 status |
|---|---|---|---|---|
| 1 | Section-joint bands | Narrow full-circumference color bands (blue Meteor/AMRAAM/HARM, brass HARM, black Brimstone) exactly at section joints; the band is paint, not geometry | High | Missing (F09 joint + F12 marks not built) |
| 2 | Joint seams | Hairline circumferential seam, sometimes a small step where one section overlaps | High | F01 nose joint only; stage joint missing |
| 3 | Fastener rows | Rows of tiny dark dots parallel to joints, spacing uniform and close; read as dots, not as slotted heads, at any viewing distance | High (Brimstone), medium elsewhere | R18 uses few slotted heads at hatches only |
| 4 | Stencils | Manufacturer/type text, data blocks, warning marks, small pictograms, roughly along the top-side or near section joints; low-contrast, on flat paint | High | Missing (F12) |
| 5 | Dark rectangular data slots | Meteor: two thin dark rectangles ahead of the first joint; also seen on the display models | High | Missing |
| 6 | Hardpoint / lug studs | Two round studs (or a hanger block) on the top centerline, plus a slide/umbilical fairing | High | Missing; conflicts with F02/F10 on +Z (see below) |
| 7 | Cable raceways | Raised low tunnel along one side or top, ending in small ramps at fin roots (HARM, Brimstone) | High | Missing (F07 fin-root seats not built) |
| 8 | Access covers | Flush panels with hairline gap, mostly rectangular; small round caps; few per body | High | Seven built, consistent with this |
| 9 | Dielectric nose | Nose radome a different color/finish (white or pale) from the metal body | High | Present (white nose in renders) |
| 10 | Weathering | Paint chips at nose tip, fin edges and panel edges; streaks aft of joints; dirt/soot near the nozzle; fading of rings | High on AMRAAM deck photo | Missing |
| 11 | Removal tags, blanks | Orange/red pull tags and covers (HARM) | Medium | Out of scope (removable accessories) |
| 12 | Nozzle | Dark burnt metal inside, bolted retaining ring on the lip | Medium (Halberd's nozzle taken from R17) | Present |

## Assessment against the R18 seven

Present features agree with real practice on covers and nozzle rims. The largest
gaps are paint-level, not geometric: bands (1), stencils (4) and weathering (10)
cost no CAD parts and are the details most responsible for a real missile
reading as real. The other gap is fastener rows (3) at the joints, where real
hardware uses many small dots rather than a few slotted heads.

**Conflict to resolve before adding lugs (6):** on a real round the hanger studs
sit on the top centerline, which is F02's face (+Z, X=900) and F10's. Hanger
geometry would need to be placed between them, or +Z declared the carriage face.
Nuclear Option carries the round on its own mount, so lugs are appearance-only.

## Recommended next scope (needs your choice)

1. **Paint layer (low risk):** joint bands at F01 and the stage joint, stencil
   panels, weathering wear on nose/fins/nozzle. Implemented as material regions
   or thin decal solids, not fastener-scale geometry. Decision needed: bands via
   sidecar materials on split faces, or thin band solids.
2. **Joint fastener rows:** small dot heads spaced uniformly along F01 and the
   stage joint (F09), a distinct small-head design, not the slotted head.
3. **Lugs and one raceway:** only if +Z carriage is confirmed.
4. Skip removal tags and blanks.

No F06–F09 or F12 work starts without your selection; those remain separate
gates per `R18_SURFACE_LAYOUT.md`.
