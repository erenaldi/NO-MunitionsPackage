# Setup Status

Checked on 2026-09-03.

## Ready

- Nuclear Option 0.34.x is installed.
- BepInEx 5.4.23.5 is installed and launches.
- Blueprinter 2.0.1 is installed under the game's BepInEx plugins directory.
- NOMM is installed and already manages local mods.
- Unity Hub 3.21.1 is installed.
- Unity Editor 2022.3.62f2, revision `7670c08855a9`, is installed at
  `C:\Users\erena\Unity\Hub\Editor\2022.3.62f2` and registered with Hub.
- Blueprinter Editor template 0.1.0 is extracted at
  `C:\Users\erena\NO-Modding\Blueprinter-Editor`.
- AssetRipper 2.0.0 x64 is extracted at
  `C:\Users\erena\NO-Modding\AssetRipper-2.0.0`.
- Downloaded Blueprinter and AssetRipper archives matched the SHA-256 digests
  published in their GitHub releases.
- The Unity editor installer has a valid Unity Technologies Authenticode
  signature.
- The local Git repository is initialized on `main` and linked to the existing,
  empty `Erenaldi/NO-MunitionsPackage` GitHub repository. Nothing has been
  committed or pushed.

## Manual Gate

Unity project initialization currently exits with `No valid Unity Editor
license found`. Open Unity Hub, sign into a Unity account, and activate a free
Unity Personal license. After activation, initialize the project by opening:

```text
C:\Users\erena\NO-Modding\Blueprinter-Editor
```

## After Activation

1. Confirm the project opens without compile or Package Manager errors.
2. Complete the AssetRipper export and Blueprinter Project Setup steps in
   `BUILD.md`.
3. Import Blueprinter's bundled `myfirstmod.source.zip` example to confirm the
   authoring pipeline.
4. Stop before creating `Assets/Blueprinter/Mods/MunitionsPackage` until the
   runtime mapping choices in `PHASE1_FINDINGS.md` are resolved.
