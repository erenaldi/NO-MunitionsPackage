using System;
using BepInEx.Logging;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class AradCloner
    {
        private const string SourceMountJsonKey = "ARM1_single";
        private const string SourceMissileJsonKey = "ARM1";
        internal const string MissileJsonKey = "Erenaldi.ARAD80";
        internal const string MountJsonKey = "Erenaldi.ARAD80_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.ARAD80";

        private static readonly string[] MirroredMounts =
        {
            "ARM1_single",
            "ARM1_double",
            "ARM1_internalx2",
            "ARM1_internalx4"
        };

        private const string WeaponName = "ARAD-80";
        private const string ShortName = "ARAD-80";
        private const string WeaponDescription =
            "A lightweight high-speed anti-radiation missile. The ARAD-80 burns its full propellant charge " +
            "in a single boost, sprinting off the rail to strike active emitters at ranges up to 35 km at Mach 3+.";

        private const float MissileMassKg = 210f;
        private const float BlastYield = 30f;
        private const float DefinitionValue = 0.55f;
        private const float MaxRange = 35000f;
        private const float MissileLength = 3.6f;
        private const float MissileWidth = 0.26f;
        private const float TopSpeed = 1172.5f;
        private const float BoosterThrust = 50000f;
        // Single burn: full 82 kg charge at 50 kN = 188 kNs (booster 100 +
        // former pulse 88), same solid chemistry (ve ~2293 m/s, Isp ~234 s).
        private const float BoosterBurnTime = 3.76f;
        private const float BoosterFuelMass = 82f;

        internal static ManualLogSource Logger { get; private set; }

        internal static void Clone(ManualLogSource logger)
        {
            Logger = logger;
            var encyclopedia = Encyclopedia.i;
            if (encyclopedia == null)
            {
                throw new InvalidOperationException("Encyclopedia is not loaded.");
            }
            if (Encyclopedia.Lookup == null || Encyclopedia.WeaponLookup == null)
            {
                throw new InvalidOperationException("Encyclopedia lookups are not initialized.");
            }
            if (Encyclopedia.WeaponLookup.ContainsKey(MountJsonKey) || Encyclopedia.Lookup.ContainsKey(MissileJsonKey))
            {
                logger.LogWarning("[Phase 2E] ARAD-80 already registered; skipping clone.");
                return;
            }
            if (!Encyclopedia.WeaponLookup.TryGetValue(SourceMountJsonKey, out var sourceMount) || sourceMount == null)
            {
                throw new InvalidOperationException($"Source mount '{SourceMountJsonKey}' was not found.");
            }
            if (!Encyclopedia.Lookup.TryGetValue(SourceMissileJsonKey, out var sourceDefObject) ||
                !(sourceDefObject is MissileDefinition sourceDef) || sourceDef == null)
            {
                throw new InvalidOperationException($"Source missile definition '{SourceMissileJsonKey}' was not found.");
            }
            if (sourceMount.info == null || sourceMount.info.weaponPrefab == null)
            {
                throw new InvalidOperationException("Source mount has no weapon info or weapon prefab.");
            }

            var missileClone = HalberdCloner.CloneInactive(sourceMount.info.weaponPrefab, MissileJsonKey);
            var missile = missileClone.GetComponent<Missile>();
            if (missile == null)
            {
                throw new InvalidOperationException("Cloned missile prefab has no Missile component.");
            }
            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = MissileMassKg;
            }
            HalberdCloner.SetField(missile, "mass", MissileMassKg);
            HalberdCloner.SetField(missile, "blastYield", BlastYield);
            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length < 1)
            {
                throw new InvalidOperationException("Cloned missile has no motors.");
            }
            // Single continuous burn: the boost motor carries the full charge,
            // the second stage is removed entirely.
            var single = Array.CreateInstance(motors.GetType().GetElementType() ?? typeof(object), 1);
            single.SetValue(motors.GetValue(0), 0);
            HalberdCloner.ApplyMotor(single.GetValue(0), BoosterThrust, BoosterBurnTime, BoosterFuelMass, TopSpeed);
            HalberdCloner.SetField(missile, "motors", single);
            HalberdCloner.NormalizePartMasses(missileClone, MissileMassKg);

            var definitionClone = UnityEngine.Object.Instantiate(sourceDef);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = WeaponName;
            definitionClone.description = WeaponDescription;
            definitionClone.length = MissileLength;
            definitionClone.width = MissileWidth;
            definitionClone.height = MissileWidth;
            definitionClone.value = DefinitionValue;
            definitionClone.unitPrefab = missileClone;
            missileClone.GetComponent<Unit>().definition = definitionClone;
            definitionClone.CacheMass();

            var infoClone = UnityEngine.Object.Instantiate(sourceMount.info);
            infoClone.name = MissileJsonKey + "_info";
            infoClone.weaponPrefab = missileClone;
            infoClone.weaponName = WeaponName;
            infoClone.shortName = ShortName;
            infoClone.description = WeaponDescription;
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetField(missile, "info", infoClone);

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            var mountedMissile = rackClone.GetComponentInChildren<MountedMissile>(true);
            if (mountedMissile == null)
            {
                throw new InvalidOperationException("Cloned rack prefab has no MountedMissile.");
            }
            mountedMissile.info = infoClone;

            var mountClone = UnityEngine.Object.Instantiate(sourceMount);
            mountClone.name = MountJsonKey;
            mountClone.jsonKey = MountJsonKey;
            mountClone.info = infoClone;
            mountClone.prefab = rackClone;
            mountClone.mountName = WeaponName;
            mountClone.Initialize();

            int prefabHash = HalberdCloner.AssignUniquePrefabHash(missileClone, HashSeed);

            encyclopedia.missiles.Add(definitionClone);
            Encyclopedia.Lookup.Add(MissileJsonKey, definitionClone);
            int definitionIndex = encyclopedia.IndexLookup.Count;
            ((INetworkDefinition)definitionClone).LookupIndex = definitionIndex;
            encyclopedia.IndexLookup.Add(definitionClone);

            encyclopedia.weaponMounts.Add(mountClone);
            Encyclopedia.WeaponLookup.Add(MountJsonKey, mountClone);
            int mountIndex = encyclopedia.IndexLookup.Count;
            ((INetworkDefinition)mountClone).LookupIndex = mountIndex;
            encyclopedia.IndexLookup.Add(mountClone);

            int hardpointSets = 0;
            foreach (var mirror in MirroredMounts)
            {
                hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, mirror);
            }

            ReportRange(logger);

            logger.LogInfo(
                $"[Phase 2E] ARAD-80 registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), " +
                $"mass {definitionClone.mass:F0} kg, cost {infoClone.costPerRound:F2}, " +
                $"range {MaxRange / 1000f:F0} km, single burn {BoosterThrust / 1000f:F0} kN/{BoosterBurnTime:F1} s " +
                $"({BoosterFuelMass:F0} kg propellant), added to {hardpointSets} hardpoint sets.");
        }

        private static void ReportRange(ManualLogSource logger)
        {
            try
            {
                // Kinematic range dwarfs the lock envelope for this airframe
                // family (donor: ~115 km kinematic vs a 60 km envelope), so
                // the check references the donor instead of an absolute band.
                const float benchmarkAltitude = 1000f;
                float launchSpeed = LevelInfo.GetSpeedOfSound(benchmarkAltitude);
                float donorRange = CalculateRange(SourceMissileJsonKey, launchSpeed, benchmarkAltitude, 60000f);
                float aradRange = CalculateRange(MissileJsonKey, launchSpeed, benchmarkAltitude, MaxRange);

                logger.LogInfo(
                    $"[Phase 2E] Range estimate at 1 km/Mach 1: ARAD-116 {donorRange / 1000f:F1} km, " +
                    $"ARAD-80 {aradRange / 1000f:F1} km kinematic vs {MaxRange / 1000f:F0} km lock envelope.");
                if (aradRange > donorRange)
                {
                    logger.LogWarning(
                        "[Phase 2E] ARAD-80 kinematic range exceeds the ARAD-116 airframe despite its smaller single burn; retune fuel mass/burn time.");
                }
                else if (aradRange < MaxRange * 1.2f)
                {
                    logger.LogWarning(
                        "[Phase 2E] ARAD-80 kinematic range cannot comfortably reach its 35 km lock envelope; increase fuel mass/burn time.");
                }
            }
            catch (Exception exception)
            {
                logger.LogWarning($"[Phase 2E] ARAD-80 range estimate failed: {exception.GetType().Name}: {exception.Message}");
            }
        }

        private static float CalculateRange(string jsonKey, float launchSpeed, float altitude, float targetDistance)
        {
            if (!Encyclopedia.Lookup.TryGetValue(jsonKey, out var definitionObject) ||
                !(definitionObject is MissileDefinition definition) || definition.unitPrefab == null)
            {
                throw new InvalidOperationException($"Range reference missile '{jsonKey}' was not found.");
            }
            var missile = definition.unitPrefab.GetComponent<Missile>();
            if (missile == null)
            {
                throw new InvalidOperationException($"Range reference missile '{jsonKey}' has no Missile component.");
            }
            return missile.CalcRange(launchSpeed, altitude, altitude, targetDistance, 0f, out _);
        }
    }
}
