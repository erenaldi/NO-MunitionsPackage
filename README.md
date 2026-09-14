# Nuclear Option Munitions Package

A planned collection of custom munitions for Nuclear Option, built as a
Blueprinter `.nobp` addon and packaged for installation through the Nuclear
Option Mod Manager (NOMM).

The approved 15-weapon handoff is recorded in `MUNITIONS.md`. Phase 1 provides
a BepInEx diagnostic plugin that inventories the live weapon catalog, resolves
the requested vanilla analogs, and dumps weapon and hardpoint schemas before
gameplay implementation begins.

## Requirements

- Nuclear Option 0.34.x
- BepInEx 5 for Windows x64
- Blueprinter 2.0.1 or newer
- Unity Editor 2022.3.62f2 for authoring
- AssetRipper for generating local placeholder game assets

## Repository Layout

- `docs/BUILD.md`: authoring and build workflow
- `docs/RELEASE.md`: local packaging and NOMM publication workflow
- `docs/CONTENT_DECISIONS.md`: original content checklist and handoff status
- `docs/PHASE1_FINDINGS.md`: evidence from the first runtime schema dump
- `docs/PROVING_GROUND.md`: install, test-zone, and Workshop mission workflow
- `missions/Erenaldi.ProvingGround/`: version 6 in-game test mission and 15-weapon lane manifest
- `nomnom/`: draft NOMNOM registry manifest
- `tools/`: local installation, log checking, and release preparation scripts
- `src/Erenaldi.MunitionsPackage/`: BepInEx plugin and schema dumper source

## Current Status

The Phase 1 diagnostic plugin builds, loads in Nuclear Option, and emits both
runtime reports. The schema results in `docs/PHASE1_FINDINGS.md` contain one
missing analog and several implementation gates that must be resolved before
weapon definitions are cloned. Unity still needs account activation before
geometry work; see `docs/SETUP_STATUS.md`.

## References

- [Blueprinter runtime](https://github.com/nikkorap/NOBlueprinter-Releases)
- [Blueprinter Editor](https://github.com/nikkorap/NOBlueprinter-Editor)
- [NOMNOM registry schema](https://github.com/KopterBuzz/NOMNOM/blob/main/SCHEMA.md)
- [Nuclear Option munitions wiki](https://nuclearoption.wiki.gg/wiki/Munitions)
