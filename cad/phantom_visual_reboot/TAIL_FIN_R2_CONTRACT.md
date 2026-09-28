# Rear fin R2 — selected clipped planform, 80 mm aft

2026-09-27 follow-up: user clarified recessed mounting, flush folded panel and a shallow visible pocket when deployed. Current candidate is `TAIL_FIN_R3_RECESS_CONTRACT.md` / `STEP/Q_Tail_R3_Recessed_*`; selected clipped outline and80 mm aft station retained. R2 remains the above-skin mounting comparison.

2026-09-27. State: `cad-review` for revised placement. User selected the Tall clipped R1 option and requested moving it80 mm back. Planform selection is approved; the revised one-corner placement is presented before fourfold propagation.

- Source `src/tail_fin_r2.py`; three saved `STEP/Q_Tail_R2_Clipped_{Stowed,Midfold,Deployed}.step`.
- All four Tall fin/hinge parts translate exactly(-80,0,0). Shape,110 mm span,240 mm root,3 mm thickness,135-degree fold and hingeY82/Z88.5 unchanged. Moving rootX-1325..-1085; complete hardwareX-1336..-1074. Body tail endsX-1400, leaving64 mm behind the aftmost pin cap.
- Every A5 component remains exact and unchanged. No body edit or foot extension was needed: measured saved-body contact remains positive for both feet.
- Fresh bounded `checks/probe_tail_fin_r2.py` PASS; primary built source/three outputs; separate fresh saved-validation worker added/executed `src/check_tail_fin_r2.py`. Report `reviews/tail_fin_r2_checks.json`: no failures,17 valid single-solid parts per state,39 A5 and12 tail-state comparisons zero Boolean difference, exact saved mid/deployed inverse fold identity.
-31 fold samples pass with minimum clearance0.25 mm; stationary-hardware/A5 clearance1.36542 mm. Feet overlap194.79427 mm3 each as explicit attachments; isolated knuckle/body overlap0. Pin fit0.25 mm; cap gaps0.3 mm. Stowed conservative radius124.88895 mm<125. No continuous-sweep, four-fin-interaction, strength/tolerance or rack claim.
- Primary directly inspected four `reviews/Q_Tail_R2_*` views from `review_tail_fin_r2.json`, using matching R1 cameras. The fin visibly sits nearer the tail end; stowed panel and mounting feet remain readable. Earlier R1 options retained.

Next: user accepts revised placement, then propagate selected assembly to four corners with full cross-fin packing/motion checks. Current prototype remains one corner only.
