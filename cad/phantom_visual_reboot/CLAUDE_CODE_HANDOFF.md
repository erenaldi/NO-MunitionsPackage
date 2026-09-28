# Claude Code handoff prompt

Paste everything below this line into Claude Code as the first message.

---

Continue the RDM-9 Phantom visual-reboot CAD work. This is a Nuclear Option game-mod asset (BepInEx plugin repo), currently at the **aft-exhaust / donor-rack fit** stage.

Workspace: `C:\Users\erena\Desktop\Nuclear Option Munitions Package`
CAD root for this work: `cad\phantom_visual_reboot\` (all paths below are relative to it unless marked)

## Read first (verify on disk; treat every doc as a claim, not truth)

1. `AGENTS.md` at the repo root (project rules), plus newest entries of `docs/SESSION_LOG.md` (the 2026-09-27 Phantom entries and the 2026-09-28 cad-reorganization entry).
2. `cad/README.md` — cad/ was reorganized 2026-09-28; run scripts from inside their own folder.
3. `IMPLEMENTATION_CHECKLIST.md` — the ordered work map (P01–P08) and current baseline.
4. `AFT_EXHAUST_R1_BRIEF.md` — latest built candidate and its evidence.
5. `DONOR_RACK_FINDINGS.md` — recovered actual donor geometry and the measured fit failure.
6. Feature contracts for what is already accepted: `INTERLEAVED_A5_COVER_CONTRACT.md`, `TAIL_FIN_R4_FOUR_CONTRACT.md`, `RAMP_INTAKE_R3_CONTRACT.md`.
7. Design authority: `plans/2026-09-23-rdm9-phantom-visual-reboot.md` and `MUNITIONS.md` section 5 (repo root). `~/.claude/domain/cad.md` covers CAD tooling conventions.

Do not mistake historical journal entries for current files (e.g., the failed provisional "R3 support probe" predates the accepted N/R3 wing work; old `a_*.py`/`b_*.py` are whole-airframe studies). Docs may cite pre-reorganization flat `cad/...` paths; those are historical.

## Current verified state (committed at a9deb1b; folder was clean)

Coordinates: mm, +X forward, +Y starboard, +Z dorsal; body X −1400..+1400; complete stowed assembly must stay inside radius 125 mm (250 mm envelope). Baseline = `src/aft_exhaust_r1.py` → `STEP/S_AftExhaust_R1_{Stowed,Midfold,Deployed}.step`, 34 parts per full state.

| Feature | Status |
|---|---|
| Rounded-square body + selected nose | locally accepted |
| Two-set joined main wings, 5.5 mm offset, recessed, side-specific exits, calculated pin openings, flush cover | locally accepted (A5) |
| Four clipped tail fins, 80 mm aft, flush stowage in shaped shallow pockets | locally accepted (TailR4) |
| Belly ramp intake, aft-hinged, nested cheeks | **35 mm lip travel is a checked trial (IntakeR3) — user acceptance still pending** |
| Aft exhaust: recessed rounded-square liner (124×124 r14 opening, 6 mm recess) + visual passage connecting the former blind intake stub | built and checked (`reviews/aft_exhaust_r1_checks.json` PASS, 0 failures; 66-pose liner/peer clearance proven by conservative AABB lower bounds ≥18 mm) — **user visual review pending** |
| Actual donor rack fit | **FAILS at unchanged donor placement** (see below) |

Key checks/evidence: `reviews/aft_exhaust_r1_checks.json`, `reviews/ramp_intake_r3_checks.json`, `reviews/agm1_reference_fit.json`. Older STEPs/revs are comparison evidence — never edit them. The `LEVELLING_B_FEASIBILITY.md` wing-levelling study is blocked/deferred and is NOT part of the baseline.

## Donor-rack facts (recovered, read-only)

- Donor is `AGM1_single`/`AGM1` (game buildid 24724372). The visible pylon mesh `launchpylon1` (pathID 3857, 848 verts) and the composed mounted-missile transform were extracted from installed `NuclearOption_Data/resources.assets` via `checks/extract_agm1_mount_reference.py` (hashes in `reference/agm1_mount/manifest.json`).
- `checks/check_agm1_reference_fit.py` exits nonzero **by design**: at the unchanged donor missile-local origin the actual pylon surface intersects body (≈20,003 mm²), top cover (≈13,752 mm²) and port front wing (≈701 mm²), with strict interior witnesses. Vertical bounds overlap ≈8.574 mm; lowering ≈9.574 mm would give only a 1 mm bounding-box gap and has NOT been applied or approved.
- Extracted meshes / `reference/agm1_mount/*.step` are reference-only. They must never be shipped as mod geometry, and no game/config/propulsion change is authorized by any of this.

## Next gates (in order; do not skip approval boundaries)

1. **P01** — Have the user accept or revise the 35 mm intake travel, then record one selected integrated baseline.
2. **Mounting interface study** — using the actual pylon keep-outs from `DONOR_RACK_FINDINGS.md`, propose and check a supported mounting position/interface (≥1 mm bounding-box gap is a starting bound, not an attachment design). This is the recommended next geometry gate and needs the user's explicit approval before any offset is applied.
3. **P04** — flush RF-panel layout once keep-outs are settled; then P05 visible interfaces, P06 surface detailing, P07 integrated regression/review, P08 whole-airframe approval (see `IMPLEMENTATION_CHECKLIST.md`).
4. Export/Unity/runtime milestones are separately authorized later work — do not start them.

## Tooling

- CAD Python: `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe` (build123d/cadgen). Use full path in commands; 300 s tool timeouts.
- UnityPy exists ONLY in the system Python 3.12 (`C:\Users\erena\AppData\Local\Programs\Python\Python312\python.exe`), not in the CAD venv. The extractor is read-only against the game install.
- Run scripts from inside `cad\phantom_visual_reboot\`. Review images: write/refresh a JSON job, then `cadgen step snapshot --job <job>.json`. Viewer: `cadgen viewer --host 127.0.0.1 --json` from the CAD dir (recently reused port 3245).
- Performance gotcha: exact nearest-distance queries on lofted solids time out (seen in `checks/probe_aft_exhaust_r1.py`). Prove the >0.2 mm threshold with conservative AABB distance lower bounds and fall back to exact distance only for pairs whose bounds cannot prove it; report bounds as bounds, never as exact minima.
- Existing saved checkers are the regression suite. Never weaken thresholds, skip coverage, or declare a pass from a failed run. `check_agm1_reference_fit.py` exiting 1 is expected until the fit is fixed.

## Boundaries

- 250 mm stowed envelope, 2800 mm length, and all accepted exterior geometry outside the already-approved pocket cuts are locked.
- No engine/airflow/thermal performance claims from visual geometry; no propulsion or gameplay tuning changes.
- Visual review gates belong to the user; present packets, state limitations honestly, and never self-approve. A technically passing check is not user acceptance.
- Nothing is committed/pushed without an explicit request from me. Preserve unrelated work in the repo.

## First message back

Verify the state above against disk (git log/status, file existence, spot-read one checker report), then summarize: current baseline, the two pending user decisions (intake travel; mounting-offset approach), and your recommended first concrete step. Do not start new geometry before I choose.
