# Release Workflow

## Local Package

Build the `.nobp` file in Blueprinter, then prepare release metadata:

```powershell
.\tools\prepare_release.ps1 -BundlePath .\build\MunitionsPackage_0.1.0.nobp -Version 0.1.0
```

The command verifies the version, copies the bundle to `dist`, calculates its
SHA-256 digest, and writes `dist/release.json`. It does not publish anything.

## Local Installation

```powershell
.\tools\install_local.ps1 -BundlePath .\dist\MunitionsPackage_0.1.0.nobp
```

After launching Nuclear Option and reaching the main menu:

```powershell
.\tools\check_log.ps1
```

## GitHub Release

After tests pass, create a tag exactly matching the version (for example,
`0.1.0`, not `v0.1.0`) and attach the `.nobp` file to a release in
`Erenaldi/NO-MunitionsPackage`. Publishing tags, releases, or other remote
changes is intentionally not automated without explicit approval.

## NOMM / NOMNOM

1. Replace the placeholder version, file name, download URL, game version, and
   hash in `nomnom/Erenaldi.MunitionsPackage.json` with release values.
2. Validate the manifest against NOMNOM's current `ValidationSchema.json`.
3. Confirm the documented `addOn` type and `extends` convention against the
   current NOMNOM repository before submission.
4. Fork `KopterBuzz/NOMNOM` and add the manifest under `modManifests`.
5. Open a pull request to NOMNOM's `main` branch.
6. After merge, install the addon in a clean NOMM-managed setup and rerun the
   runtime verification checklist.
