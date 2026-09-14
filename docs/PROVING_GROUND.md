# Erenaldi Munitions Proving Ground

`Erenaldi.ProvingGround` is a deterministic, non-ending Nuclear Option mission
for package development. It is a normal version 6 mission folder and is
published separately from the BepInEx plugin. Its custom loadouts still require
the plugin to be installed.

## Current Use

Install the plugin and mission while Nuclear Option is closed:

```powershell
dotnet build -c Release .\src\Erenaldi.MunitionsPackage
.\tools\install_plugin.ps1 -PluginPath .\src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll
.\tools\install_test_mission.ps1
```

Start `Erenaldi.ProvingGround` in single player. The mission joins Boscali,
pauses, and opens the North Boscali Airbase aircraft selector. Choose an
aircraft, configure every hardpoint, and press `Fly`; simulation resumes and
the aircraft air-spawns about 5 km above North Boscali Airbase facing
toward `AIR-CLOSE` with forward speed rather than rolling out of a hangar
or runway. Halberd and Kris appear
on compatible aircraft exactly like normal loadout options.

Multiplayer cannot globally pause while each player chooses independently. It
uses the normal faction, airbase, aircraft, and loadout selection flow instead.

Restart the mission to restore destroyed targets and ammunition. The mission
does not end automatically. The four `AIR-CLOSE` fighters are gun-only with a
persistent local patrol and high bravery, so they dogfight the player rather than
departing. Each fighter is locally anchored and provides repeated dogfight/IR
engagements without restarting after one kill.

## Test Zones

| Zone | Named targets | Roles |
|---|---|---|
| `AIR-CLOSE` | Four spaced gun-only high-bravery fighters | Repeated dogfight/IR engagements, off-boresight, LOAL, flare, and maneuver testing |
| `AIR-BVR` | Radar target near the southwest map corner, about 85 km from `AIR-CLOSE` | ARH, LOAL, notch, and long-range air testing |
| `GROUND-AREA` | Three spaced IFVs | Cluster, rocket dispersion, and soft/armored area effects |
| `IADS-HARD` | Search radar, radar SAM, pillboxes, fixed radar | SEAD, decoy, ECM, penetration, fixed-coordinate, hard-kill, and terminal-defense testing |
| `NAVAL-WATER` | Corvette | Ship strike, water entry, and torpedo testing |

Each zone has a persistent, matching objective label on the tactical map.

The complete 15-weapon mapping is in
`missions/Erenaldi.ProvingGround/lane-manifest.json`. A `live` lane has a
registered package mount. Reserved lanes describe the target environment and
vanilla fallback but are not embedded as nonexistent custom keys.

## Adding A Weapon

1. Register the weapon and mount through the plugin.
2. Launch to the main menu and regenerate `weapon-schema.json`.
3. Verify the intended aircraft, hardpoint-set index, and mount key from the
   generated schema; do not infer them from the projectile key.
4. Update the manifest lane to `live` and set its carrier, index, and mount key.
5. Add a verified player aircraft or replace a verified loadout entry in the
   mission JSON.
6. Run `tools/validate_test_mission.ps1`, install, launch, and run the role test.

## Known Limits

- The default map has about 100 km of usable diameter. Vesper, Tusko-D, and
  both Trebuchets can exercise launch, cruise/loft, interception, and terminal
  behavior here, but their full 150-400 km design ranges need another test.
- Halcyon and Barracuda remain blocked until water-phase physics and networking
  exist. The naval zone supplies valid deep-water targets for that spike.
- Static targets do not respawn. Restarting gives a clean, repeatable range.
- The plugin suppresses the vanilla join menu while the proving-ground loadout
  selector is open. `Testing > MapDiagnostics` (config, default on) logs every
  map maximize/minimize with its caller and dumps the Map action's key
  bindings at mission start. A fullscreen map toggling during flight is a
  stray Map-keypress issue (this install had Map bound to Return), not a
  plugin effect; rebind the Map action in Options > Controls if it interferes.
- Multiplayer requires the same plugin build on every peer because weapon
  definition indices are network serialized.

## Workshop Publication

The in-game Workshop uploader publishes the installed mission folder. Supply a
preview image smaller than 1 MB, select the Mission type, and select
`Erenaldi.ProvingGround`. The description must state that the Nuclear Option
Munitions Package is required on every multiplayer peer. The game creates
`workshop.json` after publication; that machine-specific file does not belong
in source control.
