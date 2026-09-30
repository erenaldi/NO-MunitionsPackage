# Handoff prompt — RDM-9 Phantom B2H baseline (paste into a fresh session)

## What this project is (please read first)

This is **fan-made, fictional video-game art** for the game *Nuclear Option* (an entertainment product). The repository holds a BepInEx game mod that registers fictional in-game items, plus CAD models of **fictional sci-fi props**. The current work is a purely **artistic and cosmetic** CAD asset: exterior shapes, panel seams, engraved grooves, fastener rings, vent slots, hinges and visible hardware, checked only for visual coherence (parts don't intersect, moving pieces don't collide, the model stays inside its size budget).

Explicitly **not** requested and not to be added: real-world engineering, physics, aerodynamics, propulsion, ballistics, manufacturing or any functional weapon information. The "engine", "nozzle", "intake" and "pylon" here are shapes for how a game prop looks; they carry no function. Names such as "munition", "halberd", "phantom", "nozzle" are game-art naming only. Nothing in this task involves real hardware. If any step seems to touch real-world function, say so and ask instead of guessing. (Project rules: repo-root `AGENTS.md`, section "Context for AI assistants".)

Workspace: `C:\Users\erena\Desktop\Nuclear Option Munitions Package`. CAD root for this asset: `cad\phantom_visual_reboot\` (paths below are relative to it unless marked). Coordinates in mm: +X forward, +Y starboard, +Z dorsal; body X -1400..+1400.

## Read first — and re-verify on disk (treat every doc as a claim, not truth)

1. Repo `AGENTS.md` and the newest entries of `docs/SESSION_LOG.md` (2026-09-29 Phantom entries: "B2F", "B2G", "B2H", "step 1", "mounting-interface study", "pylon fit decision"). Also `git log --oneline -10` and `git status` (Phantom work is **uncommitted** at handoff; HEAD is a Palisade commit; many unrelated dirty Halberd/Palisade/Unity files belong to other work — preserve them, don't clean up).
2. `ENGINE_BAY_B2H_CONTRACT.md` — the working baseline: feature status table, parameters, evidence, residual limits.
3. `IMPLEMENTATION_CHECKLIST.md` (P01–P08; the baseline note at the top was updated 2026-09-29) and `ENGINE_READ_STUDY.md` (history of the B1/B2/B2D–B2H studies, including a wording correction: the nozzle petals flare, they do not "converge").
4. `DONOR_RACK_FINDINGS.md` (recovered donor pylon reference and the mounting-interface study).
5. `~/.claude/domain/cad.md` for CAD tooling conventions.

## State at handoff (verified on disk 2026-09-29; re-check before relying on it)

- **Baseline = B2H**: `STEP/S_EngineBay_B2H_{Stowed,Deployed}_Full.step` (66 leaves each; Stowed sha256 begins `3d858398...`), built by the chain in the contract (`src/engine_bay_b2h.py` on top of `engine_bay_cosmetic.py`, `engine_bay_b2g.py`, `engine_bay_b2e.py`, `engine_bay_b2d.py`, `engine_bay_b2.py`, `engine_read_study.py`). Immutable inputs: `STEP/R_RampIntake_R3_*.step`. Older STEPs and studies are comparison evidence: never edit them.
- What B2H adds to the earlier accepted body/wings/fins/liner: an engine envelope carried on the main ramp (ramp now ~50 mm lip drop, 4.3424 deg — supersedes the earlier accepted 35 mm at the user's request), a 340 mm belly door with pocket, a straight bypass duct, a square rear nozzle (user chose square over circular), and restrained cosmetic engraving on the door, ramp underside, bay surround and intake frame.
- Evidence: `src/check_engine_bay_b2h_integrated.py` -> `reviews/engine_bay_b2h_integrated_checks.json` = **0 failures** (identity vs R3, pose sweeps, stowed radius 121.62 mm < 125, overlap list). Older checkers (`check_ramp_intake_r3`, `check_aft_exhaust_r1`, `check_tail_fin_r4`, `check_interleaved_a5`) exit 0; `checks/check_agm1_reference_fit.py` exits 1 **by design** at the unchanged donor placement.
- **Pylon fit decision (user, 2026-09-29):** straight lowering of **9.574 mm applied in the CAD asset frame**; game mount transform untouched. Verified: `reviews/pylon_lowering_verification.json` (8.1 mm still intersects, 9.1 and 9.574 mm clear). Artifacts: `STEP/S_EngineBay_B2H_Stowed_Placed.step`, reference-only `reference/agm1_mount/Phantom_DonorFit_Lowered_9574.step` (never ship the extracted pylon geometry).

## Open items and next gate

1. **P04 — flush RF-panel layout (recommended next):** produce an **annotated all-side layout for the user's review before cutting any pocket or border**; keep the stowed envelope and moving clearances; account for the pylon keep-out and the lowering. Do not cut geometry until the user approves the placement.
2. Remaining cosmetic detailing of nose, tail, flanks and top surface (user has not chosen those yet) and P05/P06/P07 items per the checklist; whole-airframe acceptance (P08) belongs to the user.
3. Residuals to keep visible: sampled-pose sweeps only; aircraft/bay clearance under the lowered model, release states and the hitbox/envelope reference point are not assessed; mount pads touch the engine flank by face contact only; door pocket/chamber/duct were not separately approved as exterior cuts.
4. Export, Unity and runtime milestones are separate, later, explicitly-authorized work — do not start them.

## Tooling and gotchas

- CAD Python: `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe` (build123d/cadgen). Run scripts from `src/` or the CAD root as their headers say. Review renders: write a JSON job, then `cadgen step snapshot --job <job>.json` (put `direction/up/target/orthographicHalfHeight` under `camera`; do not put `projection` there).
- **Long commands:** run anything longer than ~2 minutes as a background shell job writing to a log file (`run_in_background`); foreground long runs sometimes fail with a transient permission-classifier error and heavy CAD scripts can exceed the tool timeout.
- **CAD Viewer:** `cadgen viewer --host 127.0.0.1 --json` from `cad\phantom_visual_reboot\` (run it in the background — it stays alive). The port has changed between sessions (3245/3246); read the URL it prints. `cadgen viewer list` shows which folder each port serves — a stale port may serve another folder ("File does not exist"). Per the user's standing rule, whenever you mention a viewer-openable CAD file, confirm it exists and give a live `?file=` link.
- Exact nearest-distance queries on lofted solids time out; use AABB lower bounds and report them as bounds. Boolean symmetric-difference is unreliable on some complex solids (fan, face frame): use volume/centre-of-mass/bbox/vertex-set invariants as the identity test and report the unreliable boolean.
- Existing saved checkers are the regression suite: never weaken thresholds, skip coverage, or declare a pass from a failed run.

## Boundaries

- 250 mm stowed envelope, 2800 mm length, and accepted A5 wing/TailR4 fin/R1 liner geometry and the rounded-square rear opening are locked outside already-approved cuts.
- No engine/airflow/thermal performance claims from visual geometry; no game/config/propulsion changes.
- Visual approval gates belong to the user: present renders/packets, state limits honestly, never self-approve. A passing check is not user acceptance.
- Nothing is pushed or history-rewritten without an explicit request; checkpoint commits at verified milestones are pre-authorized by `AGENTS.md`, but leave unrelated dirty files alone (stage only Phantom paths if committing).
- Update `docs/SESSION_LOG.md` (newest first) at every verified milestone and before ending.

## First message back

Verify the state above against disk (git log/status, existence of the B2H STEPs, one spot-read of `reviews/engine_bay_b2h_integrated_checks.json`), then summarize: current baseline, the open decisions, and your recommended first step (annotated RF-panel layout for review). Do not cut geometry before the user approves a layout.
