# Build Workflow

## Supported Environment

- Nuclear Option: 0.34.x
- Unity: 2022.3.62f2
- Blueprinter runtime: 2.0.1 or newer
- Blueprinter Editor template: 0.1.0

The game installation used for development is expected at:

```text
C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option
```

Keep the Blueprinter Unity project and AssetRipper export outside this Git
repository. They contain generated data and local game-derived placeholders
that must not be distributed.

## One-Time Setup

1. Install Unity Hub and sign in with a Unity account.
2. Install Unity Editor 2022.3.62f2 through Unity Hub.
3. Use the staged AssetRipper and Blueprinter Editor template under
   `C:\Users\erena\NO-Modding`.
4. In AssetRipper, set `Script Content Level` to `Level 1` and
   `Script Export Format` to `Decompilation`.
5. Open `NuclearOption.exe` in AssetRipper and export all files to a dedicated
   output directory with `Create Subfolder` enabled.
6. Add the Blueprinter template project to Unity Hub and open it with
   2022.3.62f2.
7. Run `Blueprinter > Project Setup` in order: enter game version, import game
   assemblies, import the exported assets, refresh op references, and build
   `_donotship`.

The `_donotship` directory is local-only. Do not copy it into this repository
or any release artifact.

This machine installs the editor at
`C:\Users\erena\Unity\Hub\Editor\2022.3.62f2`. Unity Hub must be signed in and
a Personal license activated before the project can initialize.

## Content Authoring

This stage starts only after the choices in `CONTENT_DECISIONS.md` are made.

1. Import or create a mod at
   `Assets/Blueprinter/Mods/MunitionsPackage`.
2. Create each mod-owned `WeaponMount`, weapon information asset, projectile
   definition, and prefab with a globally unique JSON key under
   `Erenaldi.MunitionsPackage`.
3. Reference `_PLACEHOLDER` assets for any reused game mesh, material, sound,
   effect, or component.
4. Add each mount to the encyclopedia and use `OpAddWeaponToHardpoint` for
   explicitly selected aircraft and hardpoint indices.
5. Run `Blueprinter > Tools > Validate references` on each prefab.

Do not guess hardpoint indices. Record inspected indices and their constraints
before adding any weapon option.

## Build

1. Open `Blueprinter > Mod Builder`.
2. Select the `MunitionsPackage` mod folder.
3. Enter a semantic version such as `0.1.0`.
4. Build to this repository's `build` directory.
5. Export a source ZIP to `src` for reproducible future editing.
6. Install the bundle locally with `tools/install_local.ps1`.
7. Launch the game and run `tools/check_log.ps1` after reaching the main menu.

During Phase 1, install the diagnostic BepInEx plugin instead:

```powershell
.\tools\install_plugin.ps1 -PluginPath .\src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll
```

## Runtime Verification

For each included weapon, verify all of the following before release:

- Blueprinter logs no manifest, resolution, duplicate-key, or op warnings.
- The mount appears only on intended aircraft and hardpoints.
- Display name, description, icon, cost, mass, drag, and radar signature render.
- Launch, guidance, propulsion, fuzing, damage, and effects work in a mission.
- AI can select and employ it where intended.
- Save/load and multiplayer behavior are tested with matching client/server mods.
