# Pylon concept briefs — issues 021 and 022

Date: 2026-09-30. Status: **draft briefs for the CAD sessions**, written without CAD tooling. They collect fixed constraints, measured evidence and the three-architecture comparison each packet must show. They make no design selection and approve nothing. Authority: `plans/2026-09-27-fixed-munition-pylons-hardpoints.md`; evidence: `docs/ISSUE_020_FINDINGS.md`, `docs/compatibility-ledger.json`. Re-verify every number against disk before a packet cites it.

## Common packet contract (issues 021 and 022)

Each weapon packet compares three architecturally different pylons around the fixed munition:

| Direction | Idea | Must read as different because |
|---|---|---|
| A. Tapered rail | Vanilla-adjacent blade pylon, aircraft-side spine narrowing to a rail | one continuous blade; load path is the blade itself; negative space only at lugs |
| B. Exposed ejector beam | Slim spine plus a visible weapon-side beam with fore/aft ejector housings | mechanism is the silhouette; two housings connected by an open beam |
| C. Semi-conformal cradle | Low adapter or recessed cradle hugging the munition and/or aircraft belly | the store nests into the rack; minimal standoff; cradle wraps a fraction of the body |

Every concept states: aircraft-side spine, weapon-side load path, fore/aft suspension or ejector stations, deliberate negative spaces, intended material regions, release direction, and which details are speculative. Every packet has opposed isometrics, side/top/front/rear, mounted-context, critical dimensions and representative-distance views. The primary model inspects every final board; the user selects, rejects or hybridizes one direction per weapon. A selection moves the pylon to `concept-approved` at most.

Evidence labels for packet annotations: **measured** (from the issue-020 dump or saved CAD checks), **contract** (fixed by an asset contract), **assumed** (stated, unverified), **speculative** (artistic).

## Measured donor context (issue 020, aircraft-root space, metres)

Reconstruction assumes the mount spawns at the hardpoint transform; the dump does not prove that, so label positions "reconstructed".

| Weapon | Donor | Sample station | Mount-local missile offset | Reconstructed missile pos | Rail |
|---|---|---|---|---|---|
| Halberd | AAM4_single | Fighter1 set 2 Wing Pylons (idx 0/1, X mirrored) | (0, -0.287, 0.187) | (∓3.58263, -1.00961, 0.66996), identity rot | Forward |
| Kris | AAM1_single | AttackHelo1 set 3 Left Stub Tip Pylon | (0, -0.2114, 0.134) | (-3.331, -0.90503, 0.08467), rot (-0.008726,0,0,0.999962) | Down |
| Phantom | AGM1_single | COIN set 2 Fuselage Pylons | (0, -0.219, 0.006783) | (∓1.09744, -1.17398, 0.67125), roll quaternion z ±0.271482 (about ±31.5°) | Forward |
| Ballista | AGM_heavy_single | CAS1 set 2 Inner Fuselage Pylons | (0, -0.309, 0.006783) | (∓0.412885, -1.53199, 0.092759), pitch quaternion x 0.022687 (about 2.6°) | Forward |

Rail length, speed and delay are 0 for all four donors, so donor data says nothing about release travel. Fighter1 has no collider bounds in the dump, and the 769 door/bay/gear candidates are name-heuristic only.

Representative-context rule: use these stations as *review context*, not shipped geometry. Every packet also states which other sets share the donor key (Halberd 6, Kris 17, Phantom 9, Ballista 11 external-single sets) and that sibling stations are unmeasured.

---

## Issue 021 — Halberd (AAM-44)

**Fixed:** length 3370 mm (CAD contract 3.367 m; the plan quotes 3370, use the approved revision's value and record both); rounded-square body about 200 mm (BODY_RADIUS 100.5 mm in the detailed model); stage seam and FX datums; open intake language; dorsal mounting corridor kept clear; booster-separation path; intake clearance. Unity mounted display is `pylon/aam4`; the donor mount's missile node sits at (0, -0.204, 0.187) under a pylon at (0, -0.083, 0), so any custom rack keeps that mounted placement until contact is measured (`docs/HALBERD_UNITY_DELIVERY.md`).

**Attachment evidence (corrected 2026-09-30):** the current R17-R19 rounded-square model has **no lugs** (`cad/halberd_rounded_square/R18_REAL_MISSILE_DETAIL_SURVEY.md` marks hardpoint/lug studs "Missing", conflicting with the +Z F02/F10 features), and the survey notes lugs would be appearance-only because the game carries the missile on its own mount. The older values are model constants, not game measurements: -75/+410 mm (`MOUNT_LUG_STATIONS`, `cad/halberd/generate_halberd_detailed.py:51`, the Unity-delivery model) and 0/480 mm (`MOUNT_STATIONS`, `cad/halberd/halberd_four_intake_concepts.py:20`, fixed pads of the older four-intake study; other `cad/halberd/` files reuse it, not opened). Neither applies to the current model. Packets must not cite lug stations as measured: take pylon attachment stations from the pylon design, and see the decision below. Game evidence: the vanilla `AAM4_single` pylon spans z -1.09 to +0.99 m with the missile node at z +0.187 m, which shows where the vanilla pylon sits, not a lug station.


**Halberd attachment decision (2026-09-30, user):** attachment is purely visual. No lugs, studs or hanger block are added to the missile; the approved R18 +Z access features (F02, F10) stay untouched. The pylon carries all attachment detail (hooks, saddle, ejector housings); the missile side gets at most one explicit, measured contact patch on the top centerline clear of F02/F10, which packets must dimension. Concept-level only: no CAD, export or runtime approval. Acceptance 021 #4 is met on the pylon side, and packets label the missile-end load path as visual.

**Starting architecture (plan):** long mechanism beam with fore/aft suspension housings, i.e. direction B is the recommended start but must still be compared with A and C.

**Halberd-specific points per direction:**
- A: rail must stay within the dorsal corridor and not shadow the upper intakes; taper toward the aft lug so the stage joint band stays visible.
- B: the beam carries fore/aft ejector housings (stations set by the pylon design) ahead of and behind the stage joint; open gap under the beam clears the dorsal conduit and umbilical run.
- C: cradle may not wrap the dorsal corridor or upper-intake apertures; keep the cradle forward of the booster fin plane.

**Show:** intake clearance, stage joint, booster-separation path, dorsal corridor, and how the beam meets the donor mount frame at the Fighter1 wing-pylon station.

**Acceptance link (issue 021 #1, #3-#5):** none of the three moves the missile, changes the joint, or hides a corridor obstruction behind renderer state.

## Issue 021 — Kris (IRM-S4)

**Fixed:** length 3158.8 mm (3.158751 m); body 158.0 mm; about 489 mm deployed span; four honeycomb grid fins and strakes; mounted display rolled 45 degrees so the pylon occupies the gap between adjacent strakes; mount offset solved to hold a 9 mm local pylon-to-strake clearance at the larger radius (MUNITIONS.md). `Kris_Unity_RackAlignment.png` is the existing visual reference. Donor rack scale detail: `AAM1_single/pylon` is scaled (0.67, 0.9, 0.8) and `pylon/aam1` (1.4925, 1.1111, 1.25), and the rail direction is Down, so a Kris rack cannot assume the donor's proportions.

**Starting architecture (plan):** compact tapered rail (direction A).

**Kris-specific points per direction:**
- A: blade width must fit the strake gap with the measured 9 mm on each face; taper up toward the aircraft spine.
- B: ejector housings sit only in the 45-degree gaps, so the beam is offset around the strake roots; show the roll explicitly.
- C: a cradle risks reaching the strakes; it must be shallow and end above the strake tips, or the concept is rejected.

**Show:** every strake and all four grid fins in the mounted view; the 45-degree roll; the 9 mm gap dimensioned in section for each concept; and Kris on the AttackHelo1 stub-tip station as one context (helicopter wingtip, roll and Down rail are unusual).

**Acceptance link (issue 021 #2, #5):** every 9 mm claim is measured from saved CAD, not from a render.

## Issue 021 closing steps

Record the user's selected/rejected/hybrid direction per weapon with a dated decision and exact packet identity in the weapon's asset context and `MUNITIONS.md`, without implying CAD, export or runtime approval. Kris production (023) starts after the Kris selection; Halberd production (024) waits on 023.

---

## Issue 022 — Ballista (AGM-110)

**Fixed:** length 2594.424 mm; stowed envelope 322.805 mm (body 240 x 240 mm, wings folded, stowed bounds 2594.424 x 322.805 x 322.805 mm); forward shoe top center at CAD (155, 0, 170.99) mm and aft at (-330, 0, 170.99) mm (Unity 0.155 / -0.330 m along the length, 0.170991 m up); wing pivots at CAD (395, ±63.65, -119.20) mm, stowed 0 degrees, deployed ±40 degrees. Datums come from `docs/BALLISTA_UNITY_DELIVERY.md`.

**Starting architecture (plan):** heavy dual-lug ejector beam (direction B).

**Ballista-specific points per direction:**
- A: a heavy blade with dual lugs; broad enough to read as carrying 175 kg (avoid a Kris-like thin blade).
- B: two ejector housings on the authored shoe datums with the beam visibly bridging them; load path readable from housings up through the spine.
- C: recessed adapter that stays clear of the folded wing recess and root mechanism.
- All three: keep clear of folded wings and their mechanism, and show the release direction.

**Deferred variants panel (required):** a clearly labeled panel showing that x2 (8 sets), triple (1 set) and internal (5 sets) carriage are different future racks that the external single concept does not cover. Keep their context out of the external silhouettes; the ledger already blocks those 14 rows and the 11 `AGM_heavy_single` rows remain candidate only.

**Show:** the CAS1 inner fuselage pylon station (roll about 2.6 degrees pitch), the dual-lug/ejector load path, folded-wing clearance in the stowed state and a release-direction view.

## Issue 022 — Phantom (RDM-9)

**Fixed:** length 2800 mm; 250 mm maximum stowed envelope, with every folded external part inside a 125 mm radius (stowed envelope max conservative radius 121.62 mm on the B2H baseline); baseline is the visual-reboot chain `S_EngineBay_B2H_Stowed_Full.step` (sha256 `3d85839829219d4d0bafe05c825d8e363351a0d6632cc944b7bea11431d24def`), not the historical R5 Unity candidate. Reserved regions: joined main-wing covers and pin exits, tail-fin pockets (four fins), belly intake and ramp/second-belly-door, and RF regions (P04 layout study is open, so leave the RF zones clear).

**Known blocker and prior decision:** at the unchanged donor placement the stowed candidate fails against the actual donor pylon (`reviews/agm1_reference_fit.json`). The 2026-09-29 user decision resolves it by a straight lowering of 9.574 mm in the asset frame (game mount transform untouched); the pylon-surface check at that value passes with a 1.00 mm bbox gap. The actual donor pylon mesh is `launchpylon1`, reference-only. A custom Phantom pylon concept must be consistent with that lowering or state clearly that it changes it.

**Whole-airframe acceptance (P08) is not given.** A pylon direction can be approved, but production (026) stays blocked on the whole-airframe decision and on issue 017.

**Starting architecture (plan):** low-profile semi-conformal ejector (direction C), but compare A and B.

**Phantom-specific points per direction:**
- A: a short blade only if it never contacts a wing cover or pin exit.
- B: an exposed beam risks the belly door and ramp; show it clear of both.
- C: low semi-conformal adapter; keep attachment on surfaces that issue 020 found (no invented attachment geometry).

**Release-before-deployment must be legible:** show stowed and immediate-release context. Deployed wings alone do not establish carriage fit; no pylon contact over a moving cover.

**Show:** the COIN fuselage-pylon station (about ±31.5 degrees roll), the stowed-on-rack view with the 9.574 mm lowering, every reserved region marked, and release direction.

## Issue 022 closing steps

Record the user's selections and exact approval boundaries. Neither weapon advances beyond `concept-approved` for its pylon. Ballista production (025) needs 022 and 023; Phantom production (026) also needs 017.

---

## Unresolved evidence (do not fill in from the briefs)

- Static clearance to the airframe, ground, wing and neighboring stores at any station.
- Door, bay and landing-gear relationships (769 candidates are name-heuristic only).
- Release travel: donor rail data is zero.
- The mount-spawns-at-hardpoint assumption.
- Sibling stations beyond the four sampled (Halberd 5 more sets, Kris 16, Phantom 8, Ballista 10).
- Halberd missile-side contact patch: location on the top centerline between/clear of F02 and F10 is unmeasured (attachment itself is decided as visual-only).

## Suggested split for CAD sessions

One session per weapon, in this order: Kris (first production slice), Halberd, Ballista, Phantom. Halberd and Kris share issue 021; Ballista and Phantom share 022. Each session starts from `AGENTS.md`, this file, its weapon's asset contract and `docs/ISSUE_020_FINDINGS.md`.
