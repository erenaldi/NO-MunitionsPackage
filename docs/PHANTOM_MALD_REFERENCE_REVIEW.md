# RDM-9 Phantom MALD Reference Review

Date: 2026-09-14

## Fidelity Brief

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

The round-2 candidates replace the hybrid on a shared repaired airframe (`cad/phantom_r2_lib.py`):

- Ruled, station-densified loft clamped to exactly 200 × 154 mm. A measured probe showed a plateau pin destabilizing the non-ruled interpolator to a 779 mm bulge; ruled lofting between the elliptical stations is deterministic and lands on spec.
- Nozzle bore shrunk to 64 mm with a 96 mm flush lip fully inside the tail face; a checker gate requires `(nozzle_lip - smooth_body)` to be empty, so the ring can never stand proud again.
- Upward wedge nose per the 2026-09-20 user direction (rounded body, upward wedge nose facilitating the radar emitters): the ventral line climbs from −77 to +24 mm across the forward 800 mm and the 70 × 12 mm cap blade rides at +30 mm; from x=1300 to the tip no body material lies below the centerline (measured).
- Every appendage root must overlap the body wall by ≥500 mm³ (round 1 only asserted contact, which is how the tailplane root gap shipped), and no part may enter a 700 × 80 mm dorsal pylon-pad mockup zone.
- Candidates: **Sled** (long stowed-panel wings with raised emitter insets, low dorsal spine), **Rails** (heavier mid-body slivers, tail surfaces, tall dorsal fin), **Dart** (clean body, four real-span tail fins).
- Verification per candidate: `cad/check_phantom_r2.py` PASS; `cadgen step inspect validate` ok=true with zero failures; `refs --facts` reports centered 2800.0000002 mm; eight-view boards plus comparison and pylon-context mockups under `cad/Phantom_R2_*.png`; two independent image-capable review passes (second pass: wedge reads, bore proportionate, no floating parts or cracks).
- Known residuals: faint ruled-loft tangent seams at station junctions (read as panel lines at game scale); Dart fins intentionally minimal; rack fit remains unverified pending runtime integration; colors are the round-1 placeholder palette pending the texture-parity pass.
