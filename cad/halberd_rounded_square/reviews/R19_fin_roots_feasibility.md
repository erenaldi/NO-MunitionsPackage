# R19 F07/F08 fin-root feasibility (measurement only, 2026-10-02)

Source: `checks/measure_fin_roots_r19.py` on saved `STEP/halberd_r19_surface.step` -> `reviews/halberd_r19_fin_roots.json`. No model geometry changed; not a visual gate.

| Fin | Root X range / chord | Max root thickness | Adjacent skin (30 mm) | Nearest existing detail / seam | Verdict |
|---|---|---|---|---|---|
| main_fin_1..4 (clocks 45/135/225/315) | -1075.0..-859.8 / 215.2 mm | 7.6 mm (tapers to edges) | curved: rounded body corner, turns 63-67 deg within 30 mm; first 5.5-11 mm near-flat | RMA ring heads 39.4 mm; panels >= 60 mm from any seat; RMA seam 21 mm aft of root | 20x8 seat fits on both sides, any centre X -1062.5..-872.5 |
| booster_fin_fairing_1..4 (same clocks) | -1482.9..-1203.6 / 279.3 mm | 7.7 mm | fairing flank X -1350..-1204 (turns up to 158 deg); body corner cylinder aft of -1352 | RBA ring heads 31-32 mm from band; RBA seam 25.6 mm, RBF 53.6 mm | 3 mm collar band fits over full root |

All 16 fin sides have 100% free band area (no detail within 2 mm). No fin needs relocation.

Recommended forms (for the next approved build pass):
- F07 main: one seat each side of the root (paired), its root edge an offset of the measured root outline at 2 mm. Taper the ends to follow the blade's thinning leading/trailing edges, so it is not a rectangle. Place it about 20 mm long near mid-chord (thickest root, X ~ -970). Seats are on the curved corner, so cut conformally from the native skin (the F02 method), not as a planar pocket.
  Pocket 0.6 mm (<= 0.8), cover setback 0.18-0.2 mm. Hardware: 2 R17 slotted heads per seat, 4 per fin, 16 total.
- F08 booster: a 2.5-3 mm inset parting band that follows the blade root over the fairing curve and continues down onto the body corner aft of X -1352. Depth 0.4 mm (matches the R19 seam groove). No heads in the band (an R17 countersink is ~3.6 mm wide). Optional: 2 heads at the band's forward end on the fairing nose, so it reads differently from F07.

Risks:
- OCC silent no-op cuts (R19 notes): every future seat/band cut must use `checked_cut` and assert removed volume > 0, ideally per piece. Cut on a local slab if the long host skips cuts.
- The R17 seat-rim issue (rim 0.02 mm above skin) recurs on curved corners. Use the extended countersink.
- The booster band crosses the fairing-to-body step at X -1352 (two tiny step faces). The band must stay valid across it.
- Main fins embed 2817 mm3 into the body. Seats must offset from the visible root line, not from the fin solid.
- The measurement is sampled (2 mm stations, 0.5 mm arc steps). Panel outlines are re-projected from plan metadata. No images were rendered.
