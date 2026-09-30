# cad/ index

Work in ONE asset folder per session; do not load all of `cad/`.

Scripts locate their inputs/outputs with `Path(__file__)`, so each folder is self-contained: run scripts from inside their own folder
(`cd cad/halberd && python check_halberd_detailed.py`). Use the cadgen venv Python (see `~/.claude/domain/cad.md`).

| Folder | Contents |
|---|---|
| `halberd/` | AAM-44 Halberd: flat legacy set (Detailed, Hybrid, Concept/B/C/Shoulder variants, reviews, Unity export) |
| `halberd_rounded_square/` | Halberd rounded-square reboot (R5-R18); own `src/ checks/ reviews/ STEP/` layout |
| `phantom/` | RDM-9 Phantom R2-R6 darts, lens variants, MALD hybrid, Unity export |
| `phantom_visual_reboot/` | Phantom visual reboot (A/B configs); own layout |
| `kris/` | IRM-S4 Kris + PL-10 stencil/hybrid, Unity export |
| `ballista/` | AGM-110 Ballista stowed/deployed, Unity export |
| `palisade/` | HKP-1 Palisade flat set; `palisade_interceptor/` and `palisade_pod/` are the redesign studies |
| `shared/` | Asset-agnostic helpers (`inspect_step.py`, `diff_step.py`, `surface_detail.py` for fast conformal skin points, seated fasteners and checked cuts) and cross-weapon comparison images |
| `candidates/` | Unity-candidate export output (`candidates/halberd`) |
| `stencil/`, `texture_dump/`, `pipeline-validation/` | Reference stencils, dumped textures, pipeline calibration |

## Moved files (2026-09-28)

Everything that used to sit flat in `cad/` moved to the family folder above. `cad/<file>` is now `cad/<family>/<file>`; the family is
the weapon named in the file (Halberd/AAM-44, Phantom/RDM-9, Kris/IRM-S4/PL-10, Ballista/AGM-110, Palisade/HKP-1). Older records
(`docs/SESSION_LOG.md`, `issues/`, `plans/`, `docs/archive/`, `docs/PALISADE_FINDINGS.md` etc.) still cite the old flat paths; that is historical.
Scripts that resolve the repo root (`*_unity_mesh.py`) now use `parents[2]`; Halberd's candidate output stays in `cad/candidates/halberd`.
