---
id: "018"
title: Build and review the first Palisade pod U-frame housing study
type: feature
status: done
blocked-by: []
---

## Slice

Deliver one end-to-end, visible pod-housing direction: labeled parametric U-frame and paired sensor-end forms, bare and with four simple flush cassette placeholders, saved STEP checks, and directly inspected review views. Establish the four-place envelope method before multiplying directions. Follow `plans/2026-09-27-palisade-pod-housing-concepts.md` and `docs/ASSET_DESIGN_WORKFLOW.md`.

## Ownership and evidence

- Own a new `cad/palisade_pod/` housing-only workspace and scoped journal update. Preserve `cad/palisade_interceptor/STEP/Spear_ACMWrap.step`, donor assets, plugin runtime, and concurrent asset work.
- Use the approved Spear as a measured envelope datum; the historical 400×400 two-by-two packing case is illustrative and is not the new two-across × two-fore/aft, single-tier layout. The primary model directly reviews every CAD view and records visual weaknesses; no assistant review constitutes user silhouette approval.

## Acceptance

1. One distinct long inverted-U frame has a dorsal bridge and two side rails, integrated front/rear sensor ends with outward-facing apertures and accessible underside; the bare state shows four seating regions without exposed hardware in the filled state.
2. One companion state uses exactly four equivalent simple cassette volumes at two Y positions × two X positions in one underside tier. Installed skins align with the frame and sensor ends as a coherent outer shell; no box detailing or split shutters are modeled.
3. Labeled editable source emits both saved STEP states; checks on saved geometry verify valid positive-volume parts, shared housing identity, four unique/equivalent placeholders, actual bounds/thicknesses, no unintended frame/placeholder or placeholder/placeholder overlap, and four open downward exits.
4. Re-measure the selected interceptor's 1,200 mm length / 158.013 mm maximum fin-envelope diameter from its saved STEP, compare it to each placeholder and the proposed axial/transverse spacing with stated example margins. Record unverified actual AGM2 launcher poses, door sweeps, pylon and aircraft clearance separately.
5. Generate opposed isometrics, side/top/front/rear, underside and bare/filled matched views from saved artifacts. Primary directly inspects them and provides review paths/viewer links and honest tradeoffs; no detail or production approval is implied.

## Test notes

- Check serialized outputs independently, including identical housing placements across states and source-independent Spear envelope. Use strict native STEP validation where available, then inspect matched images directly at both full-pod and underside scale.
- Keep study dimensions (~2.8–3.0 m × 400 mm × 220–260 mm) provisional; if a proposed volume cannot safely fit the measured round, report the conflict rather than reduce the fin envelope.

## Result — 2026-09-27

Built `cad/palisade_pod/STEP/A_Bridge_{Bare,Filled}.step` from labeled `src/housing.py` and paired entrypoints. `checks/check_a.py` PASS on both serialized artifacts and the approved Spear: 11/15 valid closed solids, 2,980 × 400 × 223 mm assembled envelope, four unique 1,310 × 180 × 180 mm placeholders at X ±664/Y ±95/Z −133, no frame/cell or cell/cell volume intersections, common flush underside Z −223, and unchanged bare/filled housing solids. Measured Spear 1,200 mm × 158.013 mm conservative diameter; an **illustrative** 6 mm inset per cassette side/end gives 4.994 mm half-side transverse and 49 mm end margins. Bottom views show the four separate exit faces and the empty U bay. Primary inspected both opposed underside isometrics, top-view isometrics, side, end and bottom review PNGs; A reads as a severe straight-sided bridge-and-rails direction, with little character visible from above. `cadgen step inspect` is removed in this installed version; independent saved-step checks include topology and closed-shell tests. Live CAD Viewer serves the study at port 3248. No actual launcher/door/pylon/aircraft clearance verified.
