# Nuclear Option Munitions Package — AGENTS.md

Local instructions for agents working in this repo. These may override the global `~/.config/opencode/AGENTS.md` except its **Boundaries** section, which always applies.

## Purpose & stack
- BepInEx 5 plugin (netstandard2.1, C#) that adds 15 custom munitions to Nuclear Option by runtime-cloning vanilla ScriptableObjects/prefabs and re-registering them.
- Game: Nuclear Option 0.34.2 (Steam buildid 24724372), Unity 2022.3.62f2 (Mono), Mirage networking, Blueprinter 2.0.1 for `.nobp` asset bundles; NOMM distribution is a later phase. Beware: the installed `QoL` mod rewrites `Application.version` to a stale `0.34.1_qol-...` string — never use it as the game version; read the Steam `appmanifest_2168680.acf` buildid instead.
- Design authority: `MUNITIONS.md` (15-weapon roster, specs, phase decisions); `docs/PHASE1_FINDINGS.md` (validated analogs); `docs/BUILD.md` (build/install workflow).

## Layout
- `src/Erenaldi.MunitionsPackage/` — plugin source: `Plugin.cs` (entry, config, encyclopedia wait), `HalberdCloner.cs` (runtime clone + registration), `WeaponSchemaDumper.cs` (schema/hardpoint dumps), `HardpointSpawnMountPatch.cs` (Harmony postfix), `CustomGeometryLoader.cs` (embedded-bundle geometry transplant).
- `tools/` — `install_plugin.ps1` (guarded DLL installer), `check_log.ps1` (post-launch log validation).
- `docs/` — phase findings + `GEOMETRY_PIPELINE.md` (custom art contract); `V1_PLAN.md` (implementation roadmap, incl. the Palisade plan); `V1_1_PLAN.md` (post-V1 milestone plan); `SESSION_LOG.md` (append-only session journal — mandatory reading and writing, see "Session records & handoff"); `nomnom/` — schema validation assets; `unity/` — Unity project for geometry authoring (created by Unity Hub).
- Decompiled reference source (read-only, outside repo): `C:\Users\erena\AppData\Local\Temp\opencode\no-assembly-decompiled` and `...\mirage-decompiled` (via `dotnet tool run ilspycmd`, manifest in `.config/dotnet-tools.json`).

## Commands
- Build: `dotnet build -c Release` in `src\Erenaldi.MunitionsPackage` (references local game assemblies; game DLLs stay un-copied via `Private=false`).
- Install: `tools\install_plugin.ps1 -PluginPath src\Erenaldi.MunitionsPackage\bin\Release\netstandard2.1\Erenaldi.MunitionsPackage.dll` (refuses while the game runs; verify installed hash matches build output).
- Validate: launch the game to the main menu, then `tools\check_log.ps1`; runtime dumps land in `<Game>\BepInEx\config\Erenaldi.MunitionsPackage\`.
- Game path: `C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option`.

## Conventions
- Never modify vanilla ScriptableObjects/prefabs — clone and relink; all new keys prefixed `Erenaldi.` (jsonKeys are saved into mission JSON).
- Encyclopedia registration is append-only (`missiles`/`weaponMounts` lists, `Lookup`/`WeaponLookup`, `IndexLookup` + explicit `LookupIndex`) — existing indices are network-serialized and must not shift.
- Mirage `PrefabHash`: deterministic FNV-1a over a stable seed string, collision-checked against all loaded `NetworkIdentity` hashes at runtime.
- Reflection access: use `HalberdCloner`'s `GetField`/`SetField`/`SetNestedField` helpers; nested `[Serializable]` structs (e.g. `TargetRequirements`, `RadarParams`) require `SetNestedField` (boxed-copy trap).
- Clone GameObjects dormant via `CloneInactive` (prevents `Awake` at menu); spawned racks are activated by the `Hardpoint.SpawnMount` Harmony postfix.
- Error handling: clone/registration failures are logged and must never block plugin startup or the schema dump; validation scripts fail loudly with clear messages.
- New weapons are config-gated in BepInEx config (`Phase 2`, `Phase 3`, ...); log lines carry a `[Phase n]` prefix.
- Build must stay error-free; the only tolerated warning is the known transitive `System.IO.Compression` MSB3277 from `Mirage`/`Assembly-CSharp`.

## Session records & handoff

Sessions can end abruptly or corrupt their own context (this has happened: on 2026-09-13 a session was found to have fabricated paths and tool outputs). The repo — never a conversation — is the only durable state:

- `docs/SESSION_LOG.md` is the append-only session journal. At session start, read its newest entries plus `git log --oneline -10`, and treat them as claims to re-verify against disk, not as truth.
- Update the journal at every verified milestone AND before ending a session, newest entry first. Each entry records: date/time, what changed, what was verified with evidence (file:line, command results, log excerpts), what is in-flight and its exact state (files touched, build status, open decisions), and the next step. A session that stops early must still leave this entry — the journal entry is the deliverable, not a nice-to-have.
- Material decisions belong in the authority docs (`MUNITIONS.md`, `docs/*.md`) with their date. A decision that exists only in chat does not exist.
- Commit at every verified milestone (build green, validations pass, journal updated). Push and history changes require an explicit request.
- Never carry assumptions across sessions via conversation memory; only the journal, git history, and files on disk carry over.
- Self-corruption protocol: if you notice invented paths, tool outputs you cannot reproduce, or duplicated-token artifacts in your own context, stop generating analysis immediately, write a recovery note from disk-verifiable state only, and end the session. Never fabricate a handoff.

## Project-specific notes
- Multiplayer requires the plugin on all peers (IndexLookup index sync); flying missiles activate client-side via Mirage `SendActive: ForceEnable`, so only mount visuals need explicit activation.
- `P_` variant definitions are Blueprinter-generated and can have broken materials/transforms (they ship on zero aircraft) — prefer vanilla sources unless proven; the Halberd base was switched `P_AAM2` → `AAM4` for this reason.
- Custom geometry ships via the Path-A transplant (`docs/GEOMETRY_PIPELINE.md`): pure-geometry bundle embedded in the plugin DLL, visuals swapped onto clones, vanilla components preserved, fallback to vanilla geometry when the bundle is absent.
- Unity authoring toolchain (Unity Hub sign-in done; Editor 2022.3.62f2 + Blueprinter Editor install in progress by the user); no Blender installed yet.
- Git: checkpoint commits at verified milestones are expected and pre-authorized (see "Session records & handoff"); push and any history rewrite still require an explicit request.
