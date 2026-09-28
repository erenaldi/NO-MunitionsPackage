# O / A — interleaved wing-set candidate

2026-09-26. State: `cad-review`; user acceptance pending. User selected “Try A and B.”

Follow-up 2026-09-26: user responded positively but identified insufficient elevated-track supports. A is preserved as pre-reinforcement comparison; current support revision is `INTERLEAVED_A2_SUPPORT_CONTRACT.md` / `STEP/O_Interleaved_A2_*`. Only the support gate reopened; A2 user review is pending.

- Source: `src/interleaved_wing_a.py`. Exact J/R7 body and M/R2 panel geometry retained; matching root X/Y stations, no longitudinal staggering. N/R3 preserved.
- Rear/front bottom heights: starboard 88.75/99.25 mm; port 94.25/104.75 mm. Corresponding front AND rear offset 5.5 mm (N:10.5); within-set separation increases from 5 to 10.5 mm, requiring longer joint pins. Fixed-root/front cap and outer-pin cap levels differ 5.5 mm between sides too.
- Shelf Z93..93.5; upper guides93.5..94; existing side beam shortened. Four-layer end view exposes the changed order. Deployed planform and negative spaces remain the same; oblique full-body views alone understate the offset difference.
- Saved artifacts: `STEP/O_Interleaved_A_{Stowed,Module_Stowed,Midfold,Deployed}.step`.
- Primary executed `checks/probe_interleaved_a.py`: stowed in-memory pass. Initial feasibility worker returned empty/no files; primary ran this gate. Separate fresh builder successfully implemented/exported A; another added checker/views.
- Primary reran `src/check_interleaved_a.py` after adding module/full identity checks: PASS, no failures. Body and four inverse-transformed R2 panels have zero Boolean difference; saved mid/deployed match rigid transforms; 12 full/11 module valid single solids; maximum stowed conservative radius124.270643 mm; minimum panel clearance0.25 mm across21 simultaneous poses; supports remain seated; no unexpected checked pair overlap.
- Reports: `reviews/interleaved_a_feasibility.json`, `reviews/interleaved_a_checks.json`. Limits remain sampled motion, conceptual supports, no continuous sweep, strength, tolerances, captive retention, bearings, actuation, locks or donor-rack proof.
- Canonical review job: `review_interleaved_a.json`; PNGs `reviews/O_A_*.png`; matched N/A board `reviews/O_A_vs_N_Comparison.png`. `tightFrame:false`, matching N camera scale. Primary directly inspected the eight initial A views; subsequent canonical-name snapshots use unchanged geometry/cameras.
- Naming repair: delegated renderer initially overwrote historical `review_A.json`, `A_deployed_top.png` and `A_deployed_iso.png`. Restored original manifest from worker's pre-edit read and regenerated historical A_Facet top/iso from its unchanged STEP. Top camera is original; original iso camera was unavailable, so iso is an explicitly regenerated default-iso view, not byte-identical recovery. Recovery job uses current `output` schema; historical manifest retained as recorded. New candidate uses O_A names to prevent recurrence.

Next: user reviews A; B is a separate supported-mechanism investigation. No production/engine acceptance implied.
