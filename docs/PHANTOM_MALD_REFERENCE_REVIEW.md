# RDM-9 Phantom MALD Reference Review

Date: 2026-09-14

> **Current direction (2026-09-23):** The user reopened the RDM-9 silhouette
> and chose a clean-sheet TALD/Kh-69/GBU-39-inspired paired-state design.
> `plans/2026-09-23-rdm9-phantom-visual-reboot.md` and `MUNITIONS.md` section 5
> govern new concept work. The R5 context and scores below are historical
> evidence, not approval of the new exterior; no new concept has been selected.

## Active context

- **Current state:** `cad-review`. R5 remains the committed design of record; the
  later R6 tucked-wing candidate was rejected and does not supersede it. Final
  texture, Unity, rack-fit, and runtime acceptance remain pending.
- **Authoritative source:** `MUNITIONS.md` section 5 and the committed R5 family
  defined by `cad/phantom/phantom_r2_lib.py` and its R5 artifacts. Untracked R6 files are
  rejected diagnostic evidence, not a release master.
- **Approved concept / review packet:** R5 is the design of record: R4's sharp
  upward wedge and swept wing language with thinner deployed panels and an
  internal dorsal-bay retracted state. The latest adversarial review retained R5
  after rejecting R6.
- **Coordinate system and scale:** centered 2,800 mm length; CAD +X nose, +Z
  dorsal, +Y starboard; configuration-specific appendage envelopes are documented
  below.
- **Preserve:** broad shallow body, high sharp wedge nose, recognizable swept
  MALD-like wing planform, four-fin tail, recessed exhaust, and sparse game-scale
  detail.
- **Avoid:** pencil or rounded nose readings, board-like wings, hidden geometry
  presented as visible folding, floating roots, proud nozzle lips, and checks that
  only prove the model agrees with itself.
- **Emphasize:** the upward wedge, thin visibly aerodynamic wings, compact carriage
  logic, and a clear relationship between deployed and retracted states.
- **Rejected interpretations:** the original narrow/tall body, needle or blunt
  nose, near-square R3 wings, and R6's barely visible tucked strips with no valid
  state correspondence to the deployed wing.
- **Hard constraints:** user-specified dimensions and axes, source identity,
  attachment and pylon zones, configuration-specific envelopes, and no
  runtime-owned components in geometry.
- **Open decisions:** final user CAD/material review of R5, texture parity, Unity
  delivery, actual rack fit, state swap, and runtime acceptance. Reopen concept
  selection only if the user requests another folding direction.
- **Files required for the next gate:** this review, `MUNITIONS.md` section 5, the
  committed R5 source/artifacts, its review boards, and the applicable texture or
  Unity delivery files. Do not load unrelated weapon histories. If concept work is
  reopened, first create a contrastive board for external fold, visible tuck, and
  internal stow.

### Lifecycle evidence

| Boundary | State and evidence |
|---|---|
| Intent / concept | R5 is the committed design of record. R6 was reviewed and rejected without changing that authority. |
| CAD | R5 deterministic and visual-review evidence exists; final workflow-format user CAD approval is not recorded, so the current state remains `cad-review`. |
| Export | No source-bound production export is recorded for the active R5 delivery boundary. |
| Engine | R5 Unity delivery and representative engine review are not established. |
| Runtime | Rack fit, state swap, and current packaged behavior remain unverified for R5. |

### Workflow regression criteria

Use this history to verify `ASSET_DESIGN_WORKFLOW.md`:

- Detailed references and valid topology cannot substitute for a visual north star.
- The primary multimodal model must inspect the actual board; an image-blind review
  cannot pass.
- Shape-language checks must reject a technically pointed nose that still reads
  blunt or pencil-like, and mathematically valid wings that do not read as wings.
- "Folding," "visibly tucked," and "internally stowed" are separate concepts.
  Show them contrastively before changing CAD; R5 remains authoritative unless the
  user explicitly reopens that decision.
- A user correction reopens the owning visual gate and every dependent boundary,
  even when the previous candidate passed deterministic checks.

## Fidelity Brief

This is the 2026-09-14 baseline brief. The active context and later R3-R5 sections
record superseding decisions, including the sharp upward wedge and deployed wing
language; do not use this baseline alone as the current visual authority.

- Asset: RDM-9 Phantom radar-decoy missile exterior.
- Intended use: sparse, vanilla-compatible Nuclear Option game asset viewed at aircraft-loadout and combat distances.
- Silhouette: recognizable ADM-160B/MALD-J language without claiming a scale replica; smooth broad-shallow body, rounded wedge nose, compact carriage appendages, angular RF emitter housings, and round recessed exhaust.
- Hard constraints: centered 2,800 mm length; every point inside a 125 mm radial carriage envelope; CAD +X nose, +Z dorsal, +Y starboard; no runtime-owned components in geometry.
- Negative space: the exhaust mouth must remain visibly open with a dark blind backing surface.
- Detail density: sparse. Primary forms and appendages carry recognition; paired RF/lens panels provide the Phantom-specific role cue.
- Known adaptation: the public MALD deployed span cannot fit the 250 mm game envelope. Wings and tail surfaces are deliberately represented as compact fixed/stowed-form appendages, with steep sweep used to preserve a readable root chord inside the narrow span.

## Reference Images

1. Air Force Armament Museum ADM-160B underside oblique: <https://commons.wikimedia.org/wiki/File:ADM-160B_MALD_-_Air_Force_Armament_Museum.jpg>
   - Direct image: <https://upload.wikimedia.org/wikipedia/commons/b/be/ADM-160B_MALD_-_Air_Force_Armament_Museum.jpg>
   - Evidence: rounded wedge/ogive nose, broad shallow body, substantial swept wing and tail surfaces, underside aperture/fairing, and round aft exhaust. Perspective and display mounting prevent exact dimensional inference.
2. RTX MALD hero, close stowed group: <https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/sea/naval-air-missile/mald-decoy/2020-02/images/mald-decoy-hero.jpg?rev=672a98aaa2e64cfd9879f8919151daf0>
   - Source page: <https://www.rtx.com/raytheon/what-we-do/air/mald-decoy>
   - Evidence: broad rectangular/faceted fuselage, rounded wedge nose, long flush/folded appendage panels, compact tail surfaces, and top access/fairing forms.
3. RTX MALD-J underwing close view: <https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/sea/naval-air-missile/mald-decoy/2020-02/images/the-mald-j-decoy.jpg?rev=d8114b17537645f5bf8fc1b75c064342>
   - Source page: <https://www.rtx.com/raytheon/what-we-do/air/mald-decoy>
   - Evidence: blunt rounded wedge nose, broad flattened body, long stowed side/underside panel, short dorsal tail fin, compact side tailplane, and pylon relationship.
4. RTX development articles: <https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/sea/naval-air-missile/mald-decoy/2020-02/images/early-mald-decoys.jpg?rev=976d61fcda16491084bf236bac57fd71>
   - Source page: <https://www.rtx.com/raytheon/what-we-do/air/mald-decoy>
   - Evidence: repeated rounded wedge noses, broad body sections, longitudinal panel breaks, and test-article construction. Lower authority for production appendage details.
5. RTX deployed-flight side view: <https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/sea/naval-air-missile/mald-decoy/2020-02/images/the-mald-decoy-weighs.jpg?rev=b5c7de10424c491790648021d1137498>
   - Source page: <https://www.rtx.com/raytheon/what-we-do/air/mald-decoy>
   - Evidence: rounded nose, broad shallow fuselage, swept deployed wing, dorsal vertical surfaces, and exposed aft exhaust. Resolution limits small-detail interpretation.

The downloaded review copies live only in the temporary OpenCode workspace and are not shipped with the mod.

## Evidence Ledger

| Datum | Class | Confidence | Authority and uncertainty |
|---|---|---:|---|
| 2,800 mm centered length | User-specified | High | Locked RDM-9 game specification, intentionally close to public MALD length reports. |
| 125 mm maximum radial envelope | User-specified | High | Locked carriage constraint; overrides real deployed span. |
| Smooth broad-shallow body | User-specified | High | Supersedes the first faceted interpretation; the emitter housings remain deliberately angular. |
| Rounded wedge/ogive nose rather than needle tip | Visually inferred | High | Recurs across all five images and survives viewpoint changes. |
| Compact fixed/stowed-form appendages | User-specified | High | Hybrid adaptation required by the 250 mm envelope; not a claim about real deployed geometry. |
| No intake | User-specified | High | Supersedes the earlier dorsal-intake art direction on 2026-09-14. |
| Paired RF/lens side panels | User-specified | High | Phantom role cue, not copied MALD surface detail. |
| Round recessed exhaust | Visually inferred | High | Museum and flight imagery support an aft turbojet exhaust; exact diameters remain adapted. |
| Ventral keel | Speculative | Low | Compact Phantom stability/detail choice; not treated as a measured MALD feature. |

## Adversarial Review Resolution

The first hybrid passed topology, symmetry, contact, aperture, and envelope checks but those checks did not enforce the two most consistent reference forms. It used a 176 x 184 mm main section and tapered to a 4 x 4 mm needle tip. The reviewed revision changed the main body to 200 x 154 mm, ended in a 34 x 28 mm cap, re-proportioned adjacent loft stations, and reduced appendage tips to a 123.5 mm design radius. The subsequent user-directed revision removes both intake solids and replaces every octagonal section with a smooth elliptical loft while retaining angular emitter housings. Checks enforce the elliptical midbody area and absent angular shoulder material in addition to width over height, nose-cap material, the 124 mm design envelope, wing/emitter clearance, and full mirrored-geometry equivalence.

The paired RF panels, compact appendages, and ventral keel remain explicit hybrid choices. They are acceptable deviations because the goal is a recognizable Phantom derivative inside an incompatible carriage envelope, not a scale ADM-160 reproduction.

## Round-2 revision (2026-09-20)

An adversarial review of the round-1 session found the shipped geometry drifting from its own claims and the art direction under-served: the non-ruled spline loft crowned the 200 × 154 mm spec midbody to 209.87 × 155.11 mm, the 60 mm nozzle lip stood ~4 mm proud of the 56 mm tail-face semi-minor (contradicting the recessed exhaust), the tailplane roots left a visible aft root gap, and the nose still read pencil-sharp. Reference provenance spot-checks passed (Wikimedia museum image verified; the RTX source page live with captions matching this review's four RTX image descriptions).

The round-2 candidates replace the hybrid on a shared repaired airframe (`cad/phantom/phantom_r2_lib.py`):

- Ruled, station-densified loft clamped to exactly 200 × 154 mm. A measured probe showed a plateau pin destabilizing the non-ruled interpolator to a 779 mm bulge; ruled lofting between the elliptical stations is deterministic and lands on spec.
- Nozzle bore shrunk to 64 mm with a 96 mm flush lip fully inside the tail face; a checker gate requires `(nozzle_lip - smooth_body)` to be empty, so the ring can never stand proud again.
- Upward wedge nose per the 2026-09-20 user direction (rounded body, upward wedge nose facilitating the radar emitters): the ventral line climbs from −77 to +24 mm across the forward 800 mm and the 70 × 12 mm cap blade rides at +30 mm; from x=1300 to the tip no body material lies below the centerline (measured).
- Every appendage root must overlap the body wall by ≥500 mm³ (round 1 only asserted contact, which is how the tailplane root gap shipped), and no part may enter a 700 × 80 mm dorsal pylon-pad mockup zone.
- Candidates: **Sled** (long stowed-panel wings with raised emitter insets, low dorsal spine), **Rails** (heavier mid-body slivers, tail surfaces, tall dorsal fin), **Dart** (clean body, four real-span tail fins).
- Verification per candidate: `cad/phantom/check_phantom_r2.py` PASS; `cadgen step inspect validate` ok=true with zero failures; `refs --facts` reports centered 2800.0000002 mm; eight-view boards plus comparison and pylon-context mockups under `cad/Phantom_R2_*.png`; two independent image-capable review passes (second pass: wedge reads, bore proportionate, no floating parts or cracks).
- Known residuals: faint ruled-loft tangent seams at station junctions (read as panel lines at game scale); Dart fins intentionally minimal; rack fit remains unverified pending runtime integration; colors are the round-1 placeholder palette pending the texture-parity pass.

### R3 Dart of record (2026-09-20)

User selection from the candidate board: the Dart silhouette, with the side RF/lens emitter panels removed and dorsal pop-out wings added, rendered deployed like the real ADM-160 spring-out wings. The wing roots stay buried in the dorsal crown inside the 125 mm carriage radius; the deployed span (~1.10 m) intentionally exceeds the 250 mm carriage envelope, so the wing pair is exempt from the radial envelope gates (bounded instead to 600 mm lateral / 200 mm height) and the rack visual shows deployed wings — an accepted tradeoff documented in `cad/phantom/Phantom_R3_Context_Board.png`. Wing geometry: 600 mm root chord, 240 mm tip chord, ±550 mm semi-span, 5° dihedral, 5 mm plate, hinge buried at z=68 in the dorsal crown. The paired RF/lens panel rows in the fidelity brief are retired for this design; recognition now rides on the deployed wing planform, the upward wedge nose, and the four-fin tail. Verification: `check_phantom_r2.py dart3` PASS (with the wing exemption and wing-limit gates), `cadgen step inspect validate` ok=true 0 failures for the candidate and its pylon-context compound, and the eight-view board `cad/phantom/Phantom_R3_Dart_Review.png`.

### R4 dart4 of record (2026-09-20)

User review of R3 rejected both the near-square wing planform ("don't even look like wings") and the blunt blade cap ("still rounded"). The R4 revision, per the follow-up decisions (wedge to a high sharp point; near-flat MALD wings):

- Wings: ±700 mm span (1.4 m total), 420 mm root chord → 110 mm tip chord (3.8:1 taper), 30° leading-edge sweep, raked tip corners, 4 mm plate, 2.5° dihedral, wing box centered near mid-body, root edge buried in the dorsal crown at z=66.
- Nose: the body converges monotonically to a sharp apex vertex at (1400, 0, +30) — the upward wedge's ventral line crosses the centerline near x=1300 and the tip carries zero material below it from there to the apex.
- Surface: one smooth non-ruled loft (the R3 ruled-station ring bands eliminated). Stability recipe found by measured probes: monotone tail stations without duplicates, equal-value plateau stations every 200 mm (an 800 mm equal-span cubic crowns ~1-3 mm mid-span), and — critically — a ruled single-segment tip cone (1380 → apex) fused to the smooth body, because a pure vertex-ended spline fails cadgen's strict topology check even after fix(); the ruled tip validates clean and adds no interior rings. Realized clamp 200.64 × 154.73 mm against the 201.5 × 155.5 gate.
- Verification: `check_phantom_r2.py dart4` PASS (apex material, empty centerline near the tip, tip section ≤ 60 mm², wing limits ±760/±160, plus all carried-over gates); `cadgen step inspect validate` ok=true 0 failures ×2; independent image review confirmed the point, the wing planform, and the absence of ring bands. Known cosmetic: the pylon-pad mockup renders near-black in the context board.

### R5 folding concept (2026-09-20)

User direction: thin the wings "as they should be for a folding concept" and produce the retracted configuration. Engineering note recorded with the design: with a 1.4 m span against the locked 250 mm carriage envelope, no external hinge fold fits — the span needs the 2.8 m body axis, but then the 420 mm chord lies across a 200 mm body (every fold direction overflows the envelope; measured reasoning in the journal). The retraction is therefore internal, Tomahawk-style:

- Deployed (`dart5`): identical swept planform, panel thinned 4.0 → 2.5 mm so it parks inside the fuselage.
- Retracted (`dart5r`): no deployed wings; the panels park inside a dorsal bay and deploy through a 6 mm × 700 mm spine slot (x −950..−250, floor z=71) cut into the crown. External evidence: the dark panel stack visible in the slot plus a hinge fairing (x −1000..−950, top +79) capping the slot's aft end — deliberately outside the pylon-pad mockup zone. The retracted model keeps the full 125/124 mm envelope gates with nothing exempt; measured bounds ±123.5 mm.
- Verification: `check_phantom_r2.py dart5` / `dart5r` PASS; `inspect validate` ok=true 0 failures ×3 (deployed, retracted, retracted-with-pad); independent image review — clean wingless read, slot reads as a panel seam (not a crack), fairing present; known cosmetic: the pylon-pad mockup renders near-black.
