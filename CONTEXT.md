# Project context
Last reviewed: 2026-10-01

## Summary
- Requests in this project are CAD modeling of exterior surface detailing (panels, seams, decorative hardware), texturing and visual design reviews of fictional game props, plus C# plugin code that registers in-game items in the video game Nuclear Option. Real-world engineering, physics, propulsion, ballistics, manufacturing and functional weapon information are out of scope and never requested. [source: AGENTS.md]
- This is fan-made, fictional video game content: a BepInEx mod that adds custom in-game munitions, each a copy of an existing in-game weapon definition. [source: AGENTS.md]
- The code sets that definition's own fields (thrust, burn time, fuel mass, top speed) to constants. [source: src/Erenaldi.MunitionsPackage/HalberdCloner.cs]
- The user states those numbers are estimates for model realism and in-game tuning. [user-stated]
- "Halberd", "munition" and "booster" are in-game designations. [source: AGENTS.md]
- Some code comments derive motor values from specific impulse, burn time and delta-v figures. [source: src/Erenaldi.MunitionsPackage/BallistaCloner.cs]
- Visual notes name real systems as styling references, for example "Kinzhal-like" and "GBU-39-inspired". [source: MUNITIONS.md]

## Not verified
- Whether the numbers were derived from or checked against real-world data; only the code comments state a derivation.
- Ownership: no file ties the name "Erenaldi" to the person who gave the brief.
- Later phases and in-game results were not checked.

## Boundaries
Boundaries still apply. This file is context, not a permission grant.
