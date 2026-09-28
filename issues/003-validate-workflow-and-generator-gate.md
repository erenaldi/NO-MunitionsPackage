---
id: "003"
title: Validate the workflow and gate concept-generator setup
type: feature
status: done
blocked-by: ["001", "002"]
---

## Slice

Demonstrate that the documented workflow prevents the known RDM-9 failure modes and leaves concept-image tooling behind an explicit, cost-aware user decision. Close the remediation with a durable session handoff.

## Acceptance

- A bounded dry-run scenario demonstrates three contrastive directions, direct primary-model visual review, concept approval before detailed CAD, and explicit treatment of ambiguous folding-wing language.
- The verification confirms that no design subagent or broad repository audit is required.
- The workflow states that no concept-image service, dependency, credential, or configuration may be added until options are compared on reference conditioning, controllability, repeatability, privacy, and cost, then approved by the user.
- `docs/SESSION_LOG.md` records the evidence-backed remediation, files changed, checks run, remaining image-generator decision, and next step.
- Planning and issue documents reflect actual completion status.

## Test notes

- Run documentation link/readback and focused content searches.
- Use a fresh project session for behavioral validation when available; otherwise report that restart-dependent check as pending rather than simulating a pass.
- Run `opencode debug config` only if OpenCode configuration changes, which this issue does not require.
