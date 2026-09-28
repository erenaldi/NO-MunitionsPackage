---
id: "002"
title: Backfill active asset contracts with visual-intent state
type: feature
status: done
blocked-by: ["001"]
---

## Slice

Apply the workflow to Halberd, Ballista, and Phantom using current disk evidence so a later session can identify each asset's authority, visual intent, gate state, and pending boundaries without reading the whole repository. Preserve verified work and do not alter asset geometry.

## Acceptance

- `docs/HALBERD_UNITY_DELIVERY.md`, `docs/BALLISTA_UNITY_DELIVERY.md`, and `docs/PHANTOM_MALD_REFERENCE_REVIEW.md` contain a compact context packet and lifecycle-state table.
- Each contract names the authoritative source, records the visual north star or points to existing fidelity evidence, and distinguishes deterministic, visual, export, engine, and runtime status.
- Pending and invalidated approvals are represented without converting historical assistant review into user approval.
- Contradictory or stale state statements are identified and normalized only when current disk evidence supports the correction.
- RDM-9 failure patterns become regression criteria; no RDM-9 redesign occurs.
- Existing geometry, checks, images, Unity assets, bundles, and gameplay code remain untouched.

## Test notes

- Cross-check every new status claim against current files, reports, and session journal entries.
- Search each contract for the required context and gate-state sections.
- Verify no executable or generated asset changed as part of the slice.
