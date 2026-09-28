# B — clearance and supported-levelling investigation

2026-09-26. State: `blocked` at the supported-mechanism gate. This is a failed first support architecture, not proof that B is impossible. User authorized A/B exploration and changing hardware/root spacing/heights; exact body, R2 panels and250 mm stowed envelope remain locked. Current A heights were held fixed only for this initial support probe.

## Measured clearance

`checks/probe_levelling_b.py` reads the saved A deployed panels. It raises the starboard set5.5 mm to align both front and rear panels with port, without altering panel solids.

- At unchanged roots, front-panel intersection4830.197781 mm3. Rear-panel gap36 mm. Levelling directly fails.
- Equal outward travel of each whole set needs approximately21.064 mm per side for >0.2 mm panel clearance at equal heights (bisection bracket21.063995..21.064453). This is specific to the fully deployed pose and symmetric translation, not a global minimum across all mechanisms.
- Trial sequence: fully unfold as A; translate both sets22 mm outward; then raise starboard5.5 mm. The two extra phases passed21 panel-only samples each. Fully deployed width1318.588090 mm,44 mm wider than N/A's1274.588090 mm.
- Naively moving existing supports loses starboard housing contact: fixed-root gap4.5 mm, carriage gap5.385165 mm. Port zero-distance contact does not establish captured guidance or retention.
- Report: `reviews/levelling_b_clearance_probe.json`. Panel/body/hardware collision coverage, actual support paths, phase-transition continuity with new hardware, and all saved-pose checks remain pending for B. No B STEP or render was created: there is no supported candidate to present.

## First supported architecture screened out

Primary selected a longitudinal guide shoe + captive transverse tongue + telescoping rear pivot stem for the first bounded starboard-rear packaging probe. A fresh worker measured saved A; primary reviewed source/report and reran `checks/probe_b_rear_support.py` after clarifying assumption language.

- Housing top beneath rear root Z88; rear-panel underside Z88.75: **0.75 mm available**. Existing guides top Z88.5 leaves only0.25 mm above them.
- The trial serial stack assumed shoe0.5 + clearance0.25 + tongue1 + clearance0.25 + retracted stem2 = **4 mm**. It does not fit.
- The4 mm package is an explicit design assumption, not a validated universal minimum or a modeled/collision-checked mechanism. No stage solids or retention checks were built after this early failure.
- Report: `reviews/b_rear_support_probe.json`. It rejects only this under-panel stacked arrangement with unchanged A layers/base.

## Comparison / next gate

| Item | N/R3 | A interleaved | B target/probe |
|---|---:|---:|---:|
| Corresponding front/rear offset |10.5 mm|5.5 mm|0 mm panel target only|
| Stowed radius bound |123.8333 mm|124.2706 mm|No supported assembly bound|
| Deployed panel width |1274.5881 mm|1274.5881 mm|1318.5881 mm with trial translation|
| Hardware |Fixed side shelf|Lower shelf, longer joining pins|New lateral and lifting support stages required|
| Validation |Saved reports pass|Primary full saved checker passes|Panel-only motion passes; first support packaging fails|

Next B gate should explore a side-mounted or cam/linkage support layout that avoids placing all stages serially below the rear panel, or revised layer/root placement within the existing envelope. A wholesale raise by the3.25 mm package deficit is not authorized by this probe and needs renewed packing checks. No change to body/panels/envelope is proposed. Stop before full B build until a represented support path and its packaging pass. A remains available for user review independently.
