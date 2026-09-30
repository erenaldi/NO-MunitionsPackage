# R19 surface-detail handoff (next-session pickup)

Written 2026-09-28 at the end of the R19 prototype session. Treat every claim
below as something to re-verify against disk before acting (AGENTS.md,
"Session records & handoff").

## Workspace and runtime

- Repo root: `C:\Users\erena\Desktop\Nuclear Option Munitions Package`
- CAD study (run all CAD commands from here): `cad\halberd_rounded_square`
- Python: `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe`
  (cadgen 0.6.6). Set `CADGEN_DAEMON=0`; run builds/checks serially.
- Viewer: `http://127.0.0.1:3247/` serving the study dir (relaunch with
  `python -m cadgen.viewer --host 127.0.0.1 --json` from the study dir if down).
- Read first: repo `AGENTS.md`, `docs/ASSET_DESIGN_WORKFLOW.md`,
  `R19_SURFACE_DETAIL_DIRECTION.md` (decisions), `R17_DESIGN_CRITIQUE.md`
  (why the R17 layout was rejected), `~/.claude/domain/cad.md` section
  "Surface detailing construction", newest `docs/SESSION_LOG.md` entries.

## Decisions (user, 2026-09-28; recorded in R19_SURFACE_DETAIL_DIRECTION.md)

1. Surface detailing = physical radial screws and paneling (not paint/stencils).
2. Radial screw rings at section joints only: nose/body joint (X=1085), main/
   booster stage joint (X=-1123.3), booster aft joint.
3. Dense paneling similar to the Kris model, placement varied per section; the
   R17 lessons still apply (no synchronized four-fold matrix, no heavy dark
   borders, no count quota).
4. Round details required alongside rectangular panels.
5. Forward prototype approved; user said "Approved, propagate to the full
   body." **Propagation has NOT started** - no full-body geometry exists.

## Current verified state (forward section only, X=690-1100)

- Source: `src/halberd_r19_surface_proto.py`, built on saved
  `STEP/halberd_r18_access.step` (R18 access pass, still awaiting its own
  user visual acceptance; unchanged by R19).
- Output: `STEP/halberd_r19_surface_proto_forward.step` + `.step.json`
  sidecar; metadata `reviews/halberd_r19_surface_proto.json`.
- Content: 24-screw nose-joint ring at 15 deg (4 accepted R16 heads kept, 20
  identical added), 0.40x0.40 mm circumferential seam groove at X=1060,
  9 engraved chamfered-rectangle panels + 4 round panels (C01-C04, different
  hardware each), 0.40 mm wide x 0.40 mm deep grooves, 32 R17 slotted heads.
  F02 unchanged.
- Check: `checks/check_halberd_r19_surface_proto.py` -> PASS,
  `reviews/halberd_r19_surface_proto_checks.json`, 64 parts, doc hash
  `129c3297a88e3bc74d8fcd78a998480ee68dc9cc35883ec11e6cd0f0b0ae314a`.
- Renders (primary-inspected): `reviews/R19_proto_{iso,opposite,lower,side_pos,joint}.png`
  from job `reviews/R19_proto_snapshot_job.json`.
- Timings: build ~40-61 s, checker ~107 s, renders ~37 s.

## Reusable construction (use these; do not reintroduce the slow path)

- `cad/shared/surface_detail.py`: `clock_frame`, `skin_point` (single ray/face
  hit), `backing_depth`, `checked_cut`, `seated_hardware`. Imported from the
  study via `sys.path.insert(0, .../cad/shared)`; cadgen tracks it as an input.
- Clock convention: +X axis, clock 0 = +Z, 90 = +Y.
- Known OCC pitfalls (details in the SESSION_LOG entries of 2026-09-28):
  - Seat cuts near the nose-joint pocket silently no-op on the long host; cut
    on a local slab (box overrunning the crop end) and rejoin; the rejoin plane
    is the X=1060 seam groove. Do the slab work before other Booleans touch
    the host.
  - A single multi-tool cut over-removed material; keep sequential
    `checked_cut`.
  - R18 `measured_skin_point` is correct but 3-10 s per call; do not use it
    for many sites.

## Next step (needs a fresh plan in the new session)

- Plan full-body placement per section before building: main body aft of
  X=690, stage joint ring, booster, booster aft joint ring. Respect the seven
  R18 access features (F02, F04A, F04B, F05, F03A, F03B, F10), intakes, main
  fins and booster fin fairings; see `reviews/R18_layout_manifest.json` and
  `reviews/halberd_r18_access_layout.json` for their exact locations.
- Measure section shapes first (the main body is not round everywhere; check
  with `skin_point` at several clocks before assuming a radius).
- Build as a new full-body R19 model (keep the forward prototype files), write
  an independent checker (extend the prototype checker's approach), render a
  whole-body packet plus section close-ups, and present it for user visual
  approval. Primary inspects every image; no completion claim before approval.

## Housekeeping

- Nothing staged or committed. Uncommitted R19 files: the source/check/STEP/
  reviews listed above, `R19_SURFACE_DETAIL_DIRECTION.md`, this handoff,
  `cad/shared/surface_detail.py`, `cad/README.md` edit, `docs/SESSION_LOG.md`.
  Other unrelated modified files in the tree (palisade_pod, phantom) predate
  this work; leave them alone.
- Preserve all older artifacts (R12-R18, prototype renders).
