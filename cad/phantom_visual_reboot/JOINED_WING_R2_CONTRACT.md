# Joined-wing R2 — doubled-chord local study

Date: 2026-09-25. State: `cad-review`; user acceptance pending.

## Active context

- User accepted continuing the joined architecture and requested approximately twice the panel chord, then authorized execution of the inward-biased proposal.
- Source: `src/joined_wing_r2.py`; output family `STEP/M_JoinedWing_R2_*`. L/R1 remains the comparison baseline; J/R7 supplies the unchanged body/nose.
- Units mm; +X forward, +Y starboard, +Z dorsal. Preserve 2800 mm length, 250 mm circular stowed envelope, existing links, roots, housing, panel heights, hardware and motion law.
- One joined side only. No approval to repeat it or infer production GBU-39 kinematics.
- Broad forward sections: 120/88 mm; rear: 88/68 mm. Keep the old negative local-Y edge, extending the positive edge inward in stow. Joint-end tabs and bores retain their original dimensions.
- Symmetric doubling was rejected at feasibility: forward outline conservative radial bound 139.482 mm exceeds 125 mm. Inward growth avoids changing the hinges or stacking.

## Verified evidence

Builder ran `src/check_joined_wing_r2.py` successfully against six saved STEPs; primary inspected the checker and saved report `reviews/joined_wing_r2_checks.json`.

- Seven valid single solids per body assembly; six per module. Body Boolean-identical to saved J/R7, 2800 mm overall length.
- Hardware identical to saved L; all parts correspond after inverse pose transforms. Root/common-joint bore alignment and 900/600 mm link distances preserved.
- Thin-slab measurements verify doubled broad sections within 0.05 mm tolerance; endpoint geometry checked separately.
- Conservative stowed radial bounds: body 121.6224 mm (study maximum), forward panel 121.0249 mm, rear panel 110.8950 mm; all components below 125 mm.
- Twenty-one sampled poses: no checked panel intersections; minimum clearance 0.2500 mm with original >0.2 mm threshold retained. Carriage travel 449.9931 mm.
- These are sampled geometric checks, not continuous sweep, actuator, lock, opposite-side, tail or actual donor-rack validation.

## Visual review and handoff

Matched comparison job: `src/joined_review_r2_cameras.py` generates `src/render_joined_review_r2.json`; explicit shared cameras and `tightFrame:false` preserve scale within old/new pairs. Board: `reviews/M_JoinedWing_R2_Review.png`.

Primary directly inspected the board and full-resolution deployed top and stowed envelope-end images. Both panels read substantially broader; the joined triangular opening remains clear. Stowed end view exposes both layers and their inward extension across the body centreline. This makes opposite-side packaging a future design gate, not an automatic mirror operation. The existing narrow joint ends now sit visibly off-centre across the broader chord.

Next: user accepts or revises this local chord/planform before opposite-side packaging or tail work. Whole-airframe concept selection and real rack clearance remain open.
