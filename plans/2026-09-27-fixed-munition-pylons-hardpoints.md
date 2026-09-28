# Fixed-munition pylon and hardpoint program

Date: 2026-09-27

## Problem statement

Halberd, Kris, Ballista and Phantom now have fixed carriage sizes, but their
mounting geometry and aircraft availability are still inherited from vanilla
donors. The Unity rack prefabs use simple box pylons, and runtime registration
adds each custom mount wherever one or more donor mounts appear. Donor presence
does not prove that the larger or differently shaped custom weapon clears the
aircraft, neighboring stores, doors, landing gear or its own moving appendages.

Ballista exposes the most serious mismatch: one external single-rack prefab is
currently offered through external multi-round and internal-bay donor keys even
though no Ballista-specific twin, triple or internal carriage has been designed.
Phantom also replaces a roughly 1.62 m donor with a fixed 2.8 m decoy, so its
donor stations require fresh evidence rather than assumed compatibility.

## Solution

Create a coherent family of four weapon-specific pylons around the fixed
munition envelopes, then replace donor-mirrored availability with an explicit,
evidence-backed aircraft/hardpoint compatibility table. A donor option only
makes a hardpoint a candidate. A configuration becomes available in game only
after its rack variant, mounted pose, static clearance and release path have
been measured and validated.

The common visual language is a tapered aircraft-side spine, a weapon-side load
beam, visible fore/aft suspension or ejector stations, chamfered side faces,
restrained fasteners and darker separation hardware. Each lower interface is
specific to its weapon. External single, internal-bay, twin and triple carriage
are separate configurations with separate prefab identities and evidence.

The first deliverable is measurement infrastructure and a compatibility ledger,
not a registration change. Existing runtime options remain untouched until a
validated table can replace them without guessing.

## User stories

1. As a player, I see a pylon whose size and mechanism visually suit the carried
   munition rather than a generic rectangular block.
2. As a player configuring an aircraft, I can select each munition only on
   hardpoints where its fixed-size mounted and release states have been checked.
3. As a player launching a weapon, I see clean separation without clipping the
   aircraft, rack, neighboring stores or weapon appendages.
4. As an asset author, I can inspect one compatibility record to understand the
   aircraft, hardpoint-set index, rack variant, pose, clearances, release path and
   evidence behind every enabled option.
5. As a maintainer, I can add a later internal or multi-round carriage without
   weakening the evidence required for existing configurations.
6. As a multiplayer user, I receive the same deterministic mount registration
   and prefab identity as every other peer running the package.

## Implementation decisions

- **Compatibility policy:** validated fits only. Donor parity supplies candidate
  sets but never authorizes a configuration by itself.
- **Size policy:** Halberd, Kris, Ballista and Phantom munition dimensions stay
  fixed. Pylons and eligibility adapt around them; missile geometry is not scaled
  to rescue a failed fit.
- **Change sequencing:** measure first, design second, change registration only
  after the replacement table is complete enough for the affected weapon.
- **Pylon family:** use a shared Erenaldi visual language, but retain four
  weapon-specific lower interfaces and proportions.
- **Variant identity:** external single, internal, twin and triple racks are
  distinct mount/prefab variants. A `_single` prefab cannot stand in for them.
- **Runtime ownership:** preserve cloned `MountedMissile`, launch behavior,
  networking and visibility handling. Custom assets own geometry, materials,
  deliberate colliders and mounted transforms only.
- **Concept gate:** each weapon receives three contrastive pylon directions:
  vanilla-adjacent tapered rail, exposed ejector/mechanism beam, and
  semi-conformal cradle or recessed adapter. User selection precedes detailed
  rack CAD.
- **Registration:** replace broad `AddToMirroredHardpoints` calls for these four
  weapons with an explicit aircraft-definition and hardpoint-set table after fit
  approval. Registration remains append-only and does not change existing
  encyclopedia indices.

## Fixed envelopes and design briefs

| Weapon | Fixed carriage basis | Recommended starting architecture | Hard constraints |
|---|---|---|---|
| AAM-44 Halberd | 3370 mm length; 200 mm rounded-square body; current selected appendage span measured from the approved CAD revision | Long mechanism beam with fore/aft suspension housings | Follow the dorsal mounting corridor and actual shoe datums; remain clear of upper intakes, stage joint and booster separation |
| IRM-S4 Kris | 3158.8 mm length; 158.0 mm body; about 489 mm deployed span | Compact tapered rail | Preserve the established 45-degree mounted roll and 9 mm pylon-to-strake clearance; clear all strakes and grid fins |
| AGM-110 Ballista | 2594.424 mm length; 322.805 mm stowed width/height | Heavy dual-lug ejector beam | Seat against the authored forward/aft shoes; clear folded wings and their mechanisms; do not reuse the external single rack for internal or multi-round carriage |
| RDM-9 Phantom | 2800 mm length; 250 mm maximum stowed envelope | Low-profile semi-conformal ejector | Avoid joined-wing covers and pin exits, tail-fin pockets, belly intake and future RF regions; complete release before appendage deployment |

Current candidate hardpoint-set counts from the saved schema are six for
`AAM4_single`, seventeen for `AAM1_single`, nine for `AGM1_single`, and twenty-two
unique sets across Ballista's presently mirrored AGM-heavy keys. Only the eleven
sets containing `AGM_heavy_single` are candidates for Ballista's current external
single-rack architecture. The eight `AGM_heavyx2` sets, one
`AGM_heavy_triple` set and five internal sets require separate variant studies;
some sets contain more than one of those keys.

## Data model and modules

### Hardpoint evidence dump

Extend `WeaponSchemaDumper` with a compact hardpoint geometry record for each
physical `Hardpoint`, including:

- aircraft definition key and unit name
- hardpoint-set index/name and physical hardpoint index
- hardpoint hierarchy path
- local and aircraft-root-relative position, rotation and scale
- active state and relevant component identity
- nearby aircraft renderer/collider bounds in aircraft-root coordinates
- applicable door, gear or bay transforms where they can be identified
- source weapon-option keys

Extend mount-prefab records with explicit transform data, renderer/collider
bounds and `MountedMissile` local pose. The current generic serialized-field path
does not include `Transform` properties, so these values must be emitted
deliberately.

### Compatibility ledger

Add a repository-owned, reviewable data artifact with one record per proposed
configuration:

```text
weapon key
rack variant key
aircraft definition key
hardpoint-set index
physical hardpoint indices
mounted transform
minimum static clearances
release direction and checked travel
neighboring-store assumptions
door/gear constraints
evidence artifact identities
status: candidate | blocked | approved | rejected
reason
```

The ledger is design and validation authority. Runtime registration consumes a
small generated or hand-reviewed approved subset; it does not infer approval
from donor options at startup.

### Pylon CAD projects

Create one pylon project per weapon after its concept selection. Each project
owns parameterized source, saved STEP states, deterministic fit checks, review
views and its approval contract. Aircraft context geometry is evidence input,
not copied into the shipped rack.

### Runtime registration

Add one shared helper that accepts an explicit list of aircraft definition keys
and hardpoint-set indices, rejects missing or duplicate entries loudly, and logs
the exact registrations. Migrate the four weapons independently only after their
approved table and rack variant are available.

## Testing decisions

- Unit-test transform serialization and coordinate conversion with synthetic
  hierarchy fixtures where practical.
- Build the plugin after dump and registration changes; tolerate only the known
  transitive `System.IO.Compression` warning.
- Validate saved rack CAD for positive closed solids, correct bounds, contact at
  intended interfaces and absence of unintended rack/munition intersections.
- Check each approved station in both symmetric physical positions rather than
  assuming a set-level count proves symmetry.
- Check aircraft, rack, munition, neighboring-store, door and landing-gear
  clearances in every applicable mounted state.
- Check launch travel and moving appendages with swept geometry or targeted
  evidence appropriate to the mechanism; a few evenly spaced poses are not
  sufficient near narrow openings.
- Validate Unity prefab hierarchy, local transforms, materials, colliders and
  mounted-display visibility independently from CAD.
- Run in-game loadout, launch, AI, save/load and matching-peer multiplayer tests
  for every enabled configuration.
- Visual approval remains human: the primary model inspects every concept, CAD,
  engine and runtime packet, and the user approves the owning visual gate.

## Out of scope

- Changing missile dimensions, mass, guidance, damage, propulsion or balance.
- Designing pylons for ARAD-80, Palisade or the remaining roster in this pass.
- Treating structural appearance as a certified load calculation.
- Enabling a configuration solely because a vanilla donor uses the station.
- Building Ballista internal, twin or triple carriage before their own fit and
  concept gates.
- Production export, Unity integration or registration before the applicable
  weapon's CAD and compatibility evidence are approved.

## Open questions

- The exact minimum clearance thresholds will be set after the first current-game
  hardpoint and donor-rack measurement packet establishes the game's practical
  scale and animation tolerances.
- Aircraft-specific top-interface geometry may require more than one adapter
  family; this will be decided from measured station clusters rather than names.

## Issue board

The user approved the seven-slice split on 2026-09-27:

| Issue | Deliverable | Dependency |
|---|---|---|
| [020](../issues/020-dump-hardpoint-geometry-and-seed-compatibility-ledger.md) | Current-game physical hardpoint/mount dump and candidate ledger | Unblocked |
| [021](../issues/021-select-halberd-and-kris-pylon-concepts.md) | Halberd and Kris concept selections | 020 |
| [022](../issues/022-select-ballista-and-phantom-pylon-concepts.md) | Ballista and Phantom concept selections | 020 |
| [023](../issues/023-deliver-kris-validated-external-pylon.md) | Kris production tracer and shared explicit-registration helper | 020, 021 |
| [024](../issues/024-deliver-halberd-validated-external-pylon.md) | Halberd validated external delivery | 021, 023 |
| [025](../issues/025-deliver-ballista-validated-external-pylon.md) | Ballista external single delivery and availability correction | 022, 023 |
| [026](../issues/026-deliver-phantom-validated-external-pylon.md) | Phantom delivery against the approved reboot airframe | 017, 022, 023 |

Issues 021 and 022 can proceed in parallel after issue 020. Kris is the first
production slice because its mounted roll and local clearance contract already
exist; its shared registration boundary then supports the other three weapons.
