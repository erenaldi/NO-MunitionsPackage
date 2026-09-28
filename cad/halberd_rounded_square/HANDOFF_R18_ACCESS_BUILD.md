# R18 access-feature build handoff (Claude Code pickup)

This file is the durable record of the interrupted R18 access pass. The
conversation prompt given to Claude Code mirrors it. Treat every claim below as
something to re-verify against disk before acting.

## Workspace and runtime

- Repo root: `C:\Users\erena\Desktop\Nuclear Option Munitions Package`
- CAD study (working dir for all CAD commands): `cad\halberd_rounded_square`
- Python: `C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe`
  (cadgen 0.6.6, build123d/OCP). Always set `$env:CADGEN_DAEMON='0'`, run
  checks/builds serially, allow 600000 ms timeouts.
- Viewer: `http://127.0.0.1:3247/` serving the study dir (re-run
  `python -m cadgen.viewer --host 127.0.0.1 --json` from the study dir if down).
- Read first: repo `AGENTS.md`, `docs/ASSET_DESIGN_WORKFLOW.md`, and the study
  contracts listed below.

## Design state

- R17's full surface layout was REJECTED (repetition; see
  `R17_DESIGN_CRITIQUE.md`). Do not restore its panel matrix, seam ticks or
  rectangular fin badges.
- R18 redesign: `R18_SURFACE_FEATURE_CATALOG.md` (12 families) and
  `R18_SURFACE_LAYOUT.md`. The annotated four-face layout is
  **concept-approved** for the seven individual access features.
- Seven unique access assemblies (see `reviews/R18_layout_manifest.json` →
  `individual_access_features`, exact outlines/screws/lines):
  F02 tapered shoulder hatch (+Z, X=900), F04A clipped forward door (+Y, 440),
  F04B D-ended aft door (+Y, −790), F05 longitudinal lower cover (−Z, X=140,
  tangent 14), F03A round cap (−Y, 590, tangent −5), F03B keyed cap (−Y, −1390),
  F10 booster hatch (+Z, −1450).
- Retain F01 (accepted nose joint, five `main_joint_*` parts) and the R17
  nozzle-rim assemblies (18 parts, both stages).
- F06 intake seams, F07 main-fin root seats, F08 booster collars, F09 stage
  interface, F12 marks are LATER local gates — not part of this pass.
- Hard rules: no object-count quota; never copy a hatch/cap; identical hardware
  only where the assembly repeats (nozzle rings); true arcs for F04B/F03A/F03B;
  F05 is one central strip + two shaped end pieces with fine gaps; F03B has a
  real central slot; body-tone covers (host color) with ~0.3 mm perimeter gap,
  0.8 mm pocket, 0.18–0.2 mm setback; NO heavy dark borders; standard short
  slotted fastener (R17 local, 1.02 mm seat) with ≥0.25 mm remaining wall and
  countersinks open through the skin; every new part inside the old host skin,
  zero owner overlap, nonzero support face area.

## Verified milestones (evidence on disk)

- 28-part planning base `STEP/halberd_r18_layout_base.step`
  (hash `aa33330e16ed78918032a76e3374a82439a9d2445c5bca3d61c158ccb454fd21`),
  checker `checks/check_halberd_r18_layout_base.py` PASS
  (`reviews/halberd_r18_layout_base_checks.json`).
- F02 conformal shoulder probe `STEP/halberd_r18_f02_probe.step`,
  `reviews/halberd_r18_f02_probe_checks.json` = `F02_SAVED_PROBE_PASS`
  (six parts, skin radii 96.192–99.014 mm, 0.8/0.18/0.30 mm recess stack,
  supported heads, zero overlaps). Primary inspected its two review PNGs.
- Kris reference link: `STEP/kris_full_reference.step` on the viewer
  (`?file=STEP/kris_full_reference.step`).

## Interrupted in-flight work — UNVERIFIED

The cancelled gate-2 worker wrote sources but built nothing and validated
nothing beyond F02:

- `src/halberd_r18_access_shapes.py` (346 lines — CHANGED since the F02 probe
  validation; may no longer match the validated construction).
- `src/halberd_r18_access_build.py` (797 lines; imports R17
  `nozzle_lip_interface`, holds locked nozzle parameters).
- Entrypoints: `src/halberd_r18_access.py`, `halberd_r18_access_separated.py`,
  `halberd_r18_access_F02_focus.py`, `halberd_r18_access_forward_F04A_F03A.py`,
  `halberd_r18_access_F04B_focus.py`, `halberd_r18_access_F05_focus.py`,
  `halberd_r18_access_booster_F10_F03B.py`.
- Missing: any `STEP/halberd_r18_access*.step` outputs and
  `reviews/halberd_r18_access_layout.json`.

## Next steps (in order)

1. Re-run `checks/check_halberd_r18_access_preflight.py`. If the reworked
   `halberd_r18_access_shapes.py` broke F02, repair minimally back to the
   validated construction (measured native points/normals, clipped-native-face
   extrusion pockets/covers) without changing the approved F02 footprint.
2. Review `halberd_r18_access_build.py` and the entrypoints; fix only evidenced
   defects. Design stays locked to the manifest. Nozzle rims must come from
   `halberd_r17_interface_shapes.nozzle_lip_interface` over saved native faces
   with the locked parameters (main mouth −1123.3333333333, cavity 65, ring
   70–73, screws r 91.5; booster mouth −1685, cavity 69, screws r 78.4; eight
   heads each), stage-prefixed labels.
3. Build full + separated + five focus crops (shoulder F02; forward F04A+F03A;
   aft F04B; lower F05; booster F10+F03B). Record exact crop bounds and labels;
   material sidecars for every output. Expected composition ≈ 77 parts per full
   state (28 base + 31 access + 18 nozzle) — report the actual count, never pad.
4. Write an independent saved-artifact checker `checks/check_halberd_r18_access.py`
   → `reviews/halberd_r18_access_checks.json`: every saved placement a single
   positive closed solid with clean topology and no self-intersections (all
   placements, no sampling); saved-vs-source identity for new parts; changed
   hosts equal original minus declared cutters with no gained volume; support
   contact with zero overlap; open slots; open nozzle bores and retained dark
   backs; F01 and the other baseline parts unchanged; booster parts moved
   −340 mm X in the separated state; 3370 mm length; sidecar hashes.
5. Render one review packet (single JSON snapshot job): oblique/grazing close-ups
   per focus, whole and separated states, plus a fresh F02 re-render. Use fine
   tessellation (`chordTolerance` 0.00005, `angleTolerance` 0.05) for macro views.
6. STOP for primary/user visual review. Do not start F06/F07/F08/F09/F12, do
   not claim whole-model completion, and do not touch engine/plugin files.

## Boundaries and failure protocol

- Preserve every older artifact (R12–R17, probes, review images). Never modify
  the shared CAD runtime, the plugin source, or unrelated concurrent work.
- If a feature cannot fit without changing its approved outline, position or
  hardware, stop and report measurements — no silent rescaling.
- Never weaken a checker to get a pass. A failed check is reported with evidence.
- Git: the study is tracked as of commit `a9deb1b`; unrelated repo changes exist
  in the working tree — stage nothing, commit/push nothing unless explicitly
  requested.
- Journal: append to `docs/SESSION_LOG.md` (newest first) at every verified
  milestone AND before ending the session. The journal entry is the deliverable.
- Example command form:
  `& "C:\Users\erena\.config\opencode\cadgen-venv\Scripts\python.exe" checks\check_halberd_r18_access_preflight.py`
  with `$env:CADGEN_DAEMON='0'` set first, from `cad\halberd_rounded_square`.
