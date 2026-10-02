# Pickup brief: Halberd work, new workflow session

Written 2026-10-02 by the workflow-setup session. Treat every claim below as a claim to re-verify against disk (repo `AGENTS.md`, "Session records & handoff"). This file is context, not a task: your first job is to verify and then ask the user what to do next.

## Where this comes from

- Source session: "Halberd R18 access-feature CAD pass (fork 3)" (id `local_3358e4e4-99a9-4d7d-ba48-fd26e8ec5208`). It began as "pick up the interrupted Halberd R18 access-feature pass" on 2026-09-28 and ran to 2026-09-30 (UTC 02:04), moving through the R18 access build into full-body R19 surface detailing.
- Its raw transcript is a 45 MB file at `C:\Users\erena\.claude\projects\C--Users-erena-Desktop-Nuclear-Option-Munitions-Package\3358e4e4-99a9-4d7d-ba48-fd26e8ec5208.jsonl`. Reference only: do not load it whole; search it for a specific question if the repo files do not answer it.
- A sibling session, "Palisade handoff continuation (fork)" (`local_a5f91386-...`), worked on Palisade sensors (A12 to A14) and is separate. Do not act on Palisade unless the user asks.

## State at the end of the Halberd session (from its last messages and the journal)

- The user reviewed the R19 full-body surface build and approved it ("Looks good to me"): one transverse panel per face (P03 top 16x44 mm, P02 +Y 20x50 mm, Z10 underside 14x36 mm, B02 -Y 18x50 mm) and even 3.0 mm inlet side walls. Then asked "commit and push".
- Committed and pushed as `2bad5ba` "Halberd R19: one transverse panel per face and even inlet side walls" to `origin/main`. Its checker passed: no failures, 335 leaves, 250 screw heads, 58 panels. Sources: `cad/halberd_rounded_square/src/halberd_r19_surface.py` and `halberd_r19_intake_walls.py`; checker `checks/check_halberd_r19_surface.py`; model `STEP/halberd_r19_surface.step`.
- The session left uncommitted, as not its own: Palisade A12 to A13 studies, `cad/halberd_rounded_square/checks/measure_top_centerline_span.py` (another session's Halberd +Z clear-span measurement for a pylon contact patch, with its own journal entry) and `tmp/viewer.log`.

## Repo state when this brief was written (verify)

- Branch `main` at `aea6b05`, ahead of `origin/main` by 2 (`7bab3cf` Palisade sensors, `aea6b05` pickup-handoff record). `core.autocrlf` is true (system Git setting).
- The working tree is NOT clean: other sessions' Palisade STEP files, `AGENTS.md` (modified), `CONTEXT.md`, `measure_top_centerline_span.py`, plus the setup changes below.

## Known unknowns (do not assume)

- Whether the R18 access pass (F02, F04A, F04B, F05, F03A, F03B, F10) was ever visually accepted by the user: the 2026-09-28 handoff says it was still awaiting acceptance. Check `docs/SESSION_LOG.md` and `R19_SURFACE_DETAIL_DIRECTION.md`.
- `cad/halberd_rounded_square/HANDOFF_R19_SURFACE_DETAIL.md` is STALE: it says propagation had not started. The full-body R19 was built afterwards (journal entries dated 2026-09-29).
- Later gates the original brief called separate and unbuilt: F06 to F09 and F12 (intake seams, fin-root seats, booster collars, stage interface, marks), production export, Unity integration. Nothing here is the user's next request.

## Project rules that matter most (from `AGENTS.md` and the original brief)

- Fictional game-asset context: cosmetic CAD and plugin work for the game Nuclear Option; "Halberd", "munition", "booster" are in-game names. Read `CONTEXT.md`.
- CAD runtime: `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe` (cadgen), `CADGEN_DAEMON=0`, builds and checks serial, 600000 ms timeouts, run from `cad\halberd_rounded_square`. CAD Viewer `http://127.0.0.1:3247/` (relaunch with `python -m cadgen.viewer --host 127.0.0.1 --json` from the study dir). When a viewable CAD file is mentioned, give a live `?file=` viewer link (cad-viewer skill).
- Hard rules: no object-count quota, never copy-paste hardware, never weaken a checker, preserve older artifacts (R12 to R19), do not modify the shared CAD runtime or unrelated files, no commit or push unless asked, append a dated entry to `docs/SESSION_LOG.md` (newest first) at every verified milestone and before ending.
- The primary model must inspect every render itself; visual quality is judged by the user, never self-approved.

## What was configured for the new workflow (2026-10-02)

- `CLAUDE.md` now imports `@AGENTS.md` and `@CONTEXT.md` (it only imported `CONTEXT.md` before, so Claude sessions did not see the project rules). Previous content: the single line `@CONTEXT.md`.
- `.workflow/` created: `STATUS.md` (coordinator's status board), `reports/`, `tmp/`; `.gitignore` gained `.workflow/tmp/`. Committed locally on `main` (see the commit "Configure orchestrated workflow and add Halberd pickup brief"); not pushed. The commit exists so git worktree sessions inherit `CLAUDE.md`, `CONTEXT.md` and `.workflow/`; a worktree created before it needs `git merge --ff-only main` to get them.
- Global setup: Claude defaults to Sonnet 5.5 at medium effort (the coordinator); the Orca hooks were removed from `~/.claude/settings.json`.
- Workflow files: `C:\Users\erena\agent-workflow\` (read `skills\orchestrate\SKILL.md` and `skills\orchestrate\roster.md`); the `/orchestrate` skill is the entry point.

## How to work here under the new workflow

- You are the coordinator: talk to the user, plan, write briefs, audit, decide. Delegate bounded work; do one-step tasks yourself.
- CAD builds go to the `cad-builder` agent (Opus 5.5, medium). They are always REVIEW: the user judges the images. Builds are serial (OCC pitfalls, daemon off), so batch parallelism does not help CAD builds. Retrieval and read-only digging can go to `explorer` or `summarizer` (Luna) and checks to `checker`. Code work (the C# plugin) goes to `implementer`/`tester` (Sol); reviews go to `reviewer` (Sol).
- `dispatch.mjs` (batch dispatcher) refuses a dirty tree, and this tree is dirty with other sessions' files. Use `run-worker.mjs` for single tasks, or ask the user before committing or cleaning anything.
- `AGENTS.md` still mentions the old OpenCode setup (`~/.config/opencode/AGENTS.md`, `subagents/cad-builder`, `subagents/multimodal-analyst`). The roster agents replace those; do not edit `AGENTS.md` without asking.

## First steps for the new session

1. Read `CONTEXT.md`, `AGENTS.md`, the newest 6 entries of `docs/SESSION_LOG.md`, and run `git status --short` and `git log --oneline -10`.
2. Verify the Halberd claims above against disk (the commit, the R19 STEP file and its checker JSON).
3. Report in 10 lines or fewer: verified state, discrepancies, and open questions. Then ask the user what to do next. Do not start CAD work first.
