# V1.1 Plan — Performance, Ground Vehicles, Large-Scale Operations

Planning document for the V1.1 milestone. Approved roster and design decisions
are recorded here; the V1.1 build starts only after V1 is complete (12
unimplemented weapons, the HKP-1 Palisade hard-kill system, the water-phase
spike, and proving-ground validation).

## Phase V1.1-0 — Performance evidence spike

No optimization code is written before this phase produces measurements.

- Build a dedicated stress mission: large IADS network, maximum AI-aircraft
  engagement, and mass-saturation events (ALBM-3 Trebuchet [C] bomblet
  carpets, HKP-1 Palisade engagements, heavy furballs).
- Instrument with BepInEx timing patches (ProfilerMarkers, frame-time and
  allocation logging). Measure: frame time, GC allocations, physics ticks,
  draw calls, worst-frame analysis across the stress scenarios.
- Deliverable: `docs/PERF_FINDINGS.md` — a quantified hot-spot list with the
  measured scenario, hardware, and settings recorded for reproducibility.

## Phase V1.1-1 — Performance systems

Content-serving optimizations come first; general game fixes only for items
present in `docs/PERF_FINDINGS.md`.

- Content-serving (mandatory):
  - Object pooling for submunitions (ALBM-3 Trebuchet [C]) and HKP-1
    Palisade interceptors.
  - Per-weapon FX/particle budgets with LOD fade.
  - LOD groups on custom geometry (AAM-44 Halberd, IRM-S4 Kris, AGM-110
    Ballista).
- General game fixes (candidates to verify against PERF_FINDINGS):
  - AI update throttling / distance culling for ground units.
  - Off-screen or far-range missile simulation LOD.
  - `Wreckage`/`WreckCollector` lifecycle tuning exposed as BepInEx config.
- Rules:
  - All general fixes are config-gated with conservative defaults.
  - No duplication of installed community mods (frame limiter, AI aircraft
    limit, time smoothing, QoL fast loading).

## Phase V1.1-2 — Ground vehicles

Architecture is proven and roster-agnostic; the vehicle roster and role mix
are deferred to a separate design session.

- Pipeline (same clone-and-relink philosophy as weapons): clone
  `UnitDefinition`/`VehicleDefinition` and the unit prefab, relink
  parts/armor/turrets, append `Encyclopedia.vehicles` and `Lookup`, and append
  `IndexLookup` with an explicit `LookupIndex` (append-only; indices are
  network-serialized and must not shift existing entries).
- Author friendly/hostile/map icons; register `weaponMounts` for the
  vehicle's armament.
- Config-gate AI-faction access per unit; validate mission-editor spawn.
- Deliverable: reusable vehicle-clone tooling plus the roster from the
  vehicle design session (assumed small first batch of 2-4 units).

## Phase V1.1-3 — Missions: 1-3 large-scale operations

- Large combined-arms operations on vanilla maps, playable single-player and
  multiplayer (`SingleAndMultiplayer`), published as mission folders like
  `Erenaldi.ProvingGround`.
- Faction supply lists feature the new vehicles; objective chains use the
  known v6 mission schema (labels, reveals, waypoints), with a decompile pass
  inventoring deeper objective types at execution time.
- Approach: design all three operations, build in priority order — ship two
  (one new-vehicle showcase, one combined-arms arsenal operation) and treat
  the third as stretch, adjusting at design time.

## Phase V1.1-4 — Release

- Finalize `nomnom/Erenaldi.MunitionsPackage.json` (update stale
  `gameVersion 0.34.1` to the current buildid; fill the artifact hash after
  build).
- Bundle custom geometry as `.nobp` add-ons; package plugin and mission
  folders.
- Workshop publication per `docs/PROVING_GROUND.md`; description must state
  the plugin requirement on every multiplayer peer.
- Document all BepInEx config entries and the multiplayer version-locking
  rules in the README.
