# R14 — clean booster fin/fairing junctions

Date: 2026-09-26. State: **`cad-review`**. Geometry checks pass; primary visual
review passed the clipping-cleanup objective. User subsequently requested
resuming detailing; [R15](R15_DETAILING_CONTRACT.md) carries this repair unchanged.

## User direction and preserved intent

- User accepted the approximate 80–120 surface-detail-object / 20–30 group
  planning range, then prioritized repairing the sloppy/clipping taper-to-fin
  junction. The count is a visual planning range, not a quality metric or an
  instruction to populate arbitrary detail.
- User identified **booster fins**, supplying a screenshot marking the ragged
  light/dark strip where the tapered fairing intersects the fin root.
- Preserve R11's ridge-aligned endpoint, intake heights and original cubic
  taper, the approved 80 mm fin silhouette and placement, and stage ownership.
- R13 service-cover geometry is carried forward unchanged. This repair adds
  no new repeated detail style and does not claim whole-model detailing parity.

## Diagnosis and repair

R13 kept each booster fin and fairing as separate intersecting solids. Saved
geometry measures 15,303.037 mm³ of fin/fairing overlap at each station. The
before snapshots reproduce the jagged boundary marked by the user.

For each of four stations, R14 computes `(fin + fairing) - booster_body`.
This creates one contiguous solid and removes only buried body overlap. The
outer union of body, fin and fairing is preserved: saved-artifact comparisons
measure **0 mm³ added and 0 mm³ missing** at every station (0.05 mm³ tolerance).
This is a surface/topology cleanup, not a new taper or fillet design.

Eight original fin/fairing parts become four `booster_fin_fairing_1..4` parts,
giving 27 parts in each full state. Each joined piece uses the existing fin gray
`#929DA5`; the booster fairing therefore changes from its former body gray to
fin gray. The other 23 R13 parts, including the booster body and service-cover
assembly, retain exact geometry and colors.

## Evidence

- Source: `src/halberd_r14_shapes.py`; entrypoints `src/halberd_r14.py`,
  `halberd_r14_separated.py`, `halberd_r14_focus.py`.
- Artifacts: `STEP/halberd_r14{,_separated,_focus}.step`. Full-state material
  sidecars accompany their STEPs. The focused crop uses STEP colors and has no
  custom-material sidecar.
- Preserved comparison: `src/halberd_r13_booster_focus.py` generates
  `STEP/halberd_r13_booster_focus.step`; original R13 artifacts remain intact.
- `checks/check_halberd_r14.py` passes after primary additions checking that
  both review crops match their saved full models and that merged colors match
  the original fins. All 61 placements (27 assembled + 27 separated + 3 repaired
  focus + 4 baseline focus) pass positive single-solid, topology, closed-shell
  and self-intersection checks.
- Union identity, zero cleaned-piece/body and main-stage overlap, flush body
  contact, fourfold equivalence, 340 mm separated transforms, nozzle clearance,
  3370 mm total length, 23 unchanged parts and full-state material/hash checks
  pass. Report: `reviews/halberd_R14_checks.json`.
- Primary inspected `reviews/Halberd_R14_Booster_Junction.png` (matched
  before/after side, top and oblique), full-resolution before/after oblique,
  opposite oblique, whole and separated views. The formerly ragged strip is
  replaced by a clean intersection curve; the fin silhouette and taper remain.

## Review links and next gate

- [Cleaned junction](http://127.0.0.1:3247/?file=STEP/halberd_r14_focus.step)
- [Whole model](http://127.0.0.1:3247/?file=STEP/halberd_r14.step)
- [Separated stages](http://127.0.0.1:3247/?file=STEP/halberd_r14_separated.step)

Viewer launcher reused this study root on port 3247; all three page URLs returned
HTTP 200. Subsequent work resumes the service-cover family in R15. Engine export,
runtime and physical engineering remain outside this CAD review gate.
