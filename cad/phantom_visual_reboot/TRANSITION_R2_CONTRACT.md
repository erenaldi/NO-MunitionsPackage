# RDM-9 first square / transition / nose CAD

Date: 2026-09-23. Lifecycle: `cad-review` (local prototype; visual checks pending).
User authorized the first CAD after requesting a distinct transition between
the lightly filleted square body and the sketch-led nose. No shape is approved.

## Active context

- Source: `src/transition_nose_r2.py`; historical D is not the new master.
- Scope: local body/transition/nose prototype; appendages await this local gate.
- Axes: +X forward, +Z up, millimetres. Total length 2800 mm.
- Body: 172 mm square with 10 mm corner radii, ending at X=760.
- Transition: 250 mm long, square at X=760 to a five-sided nose root at X=1010.
- Nose: broad upper edge, narrowed lower sides and central lower V at the root;
  actual point at (1400, 0, 40). This uses the whole-nose front-projection
  interpretation of the reattached drawing. Interpretation remains unapproved.
- Dimensions apart from total length/envelope are reversible visual assumptions.
- Preserve: pointed bottom outline, connected chine relationships, modest body
  corner rounding. Avoid abrupt square-to-nose butt joint and round-dart reading.
- Open: does the actual front projection convey the drawing's Y? Does the
  five-sided nose introduce excess projected ridges? Is the shoulder too long?
- No claim of folding, donor-rack clearance, or whole-airframe approval.

## Artifacts and evidence

- `STEP/E_Transition_Nose_R2.step`: full body; build succeeded.
- `STEP/E_Transition_Nose_R2_Close.step`: same shape cut at X=550 for review;
  build succeeded. The cut end is presentation geometry, not a vehicle seam.
- `src/check_transition_r2.py` passed on both serialized STEPs: each is one
  valid solid; lengths 2800/850 mm; 172 mm body width/height; exact elevated
  apex; positive section areas and decreasing area through shoulder/nose.
- Conservative bounding-box radial limit for the body is 121.6224 mm, below
  125 mm. This is body-only evidence, not a stowed-vehicle envelope pass.
- Machine evidence: `reviews/transition_r2_checks.json`.
- Strict cadgen validation and nine-view snapshot packet were attempted but
  failed before execution with `ModuleNotFoundError: No module named cadgen.cli`.
  The CLI had worked earlier this session. A subsequent import probe confirmed
  `cadgen.__file__` and `find_spec('cadgen.cli')` were both None. Cause unknown;
  no environment repair attempted. No PNGs generated or visual approval claimed.
- Viewer launcher earlier reused http://127.0.0.1:3247/ for this directory;
  initial HTTP checks for both artifacts failed to connect. On user-requested
  retry, the restored CLI (viewer 0.6.6) launched independently on port 3245.
  Both STEP paths exist and both artifact page URLs returned HTTP 200.
  Live viewer handoff is restored; snapshots and strict validation remain pending.

## Resume

After the shared CAD runtime is restored, run from this directory:

```text
cadgen step inspect validate STEP/E_Transition_Nose_R2.step --every-placement
cadgen step inspect validate STEP/E_Transition_Nose_R2_Close.step --every-placement
cadgen step inspect refs STEP/E_Transition_Nose_R2.step --facts --planes --positioning
cadgen step snapshot --job review_E.json
cadgen viewer --host 127.0.0.1 --json
```

Directly inspect the nine images; label front as full projection and rear as
the square body end. Present the shoulder/nose views before requesting approval
to propagate this form to three whole-airframe directions.
