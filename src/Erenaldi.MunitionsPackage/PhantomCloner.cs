using System;
using BepInEx.Logging;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class PhantomCloner
    {
        private const string SourceMountJsonKey = "AGM1_single";
        private const string SourceMissileJsonKey = "AGM1";
        internal const string MissileJsonKey = "Erenaldi.RDM9";
        internal const string MountJsonKey = "Erenaldi.RDM9_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.RDM9";

        private const string WeaponName = "RDM-9 Phantom";
        private const string ShortName = "RDM-9";
        private const string WeaponDescription =
            "An expendable radar decoy with a Luneburg lens and active repeater. The unarmed Phantom " +
            "boosts to Mach 2, then glides along a threat-like penetration profile to draw air-defense fire.";

        internal const float MissileMassKg = 180f;
        internal const float MissileLength = 2.8f;
        internal const float MissileDiameter = 0.25f;
        internal const float MaxRange = 30000f;
        internal const float RadarSize = 1f;
        internal const float MotorThrust = 20000f;
        internal const float MotorBurnTime = 3.44f;
        internal const float MotorFuelMass = 30f;
        internal const float MotorTopSpeed = 650f;
        internal const float MaxFlightTime = 60f;

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
                logger.LogWarning("[Phase 2F] RDM-9 Phantom already registered; skipping clone.");
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
            if (sourceMount.info == null || sourceMount.info.weaponPrefab == null || sourceMount.prefab == null)
            {
                throw new InvalidOperationException("Source AGM-48 mount is missing its weapon info, missile, or rack prefab.");
            }

            var missileClone = HalberdCloner.CloneInactive(sourceMount.info.weaponPrefab, MissileJsonKey);
            var missile = missileClone.GetComponent<Missile>();
            var seeker = missileClone.GetComponent<OpticalSeeker>();
            if (missile == null || seeker == null)
            {
                throw new InvalidOperationException("Cloned Phantom prefab is missing its Missile or OpticalSeeker component.");
            }

            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = MissileMassKg;
            }
            HalberdCloner.SetField(missile, "mass", MissileMassKg);
            HalberdCloner.SetField(missile, "blastYield", 0f);
            HalberdCloner.SetField(missile, "pierceDamage", 0f);

            var warhead = HalberdCloner.GetField(missile, "warhead");
            if (warhead == null)
            {
                throw new InvalidOperationException("Cloned Phantom missile has no warhead state to disarm.");
            }
            HalberdCloner.SetField(warhead, "Armed", false);
            HalberdCloner.SetField(seeker, "armDelay", float.MaxValue);
            HalberdCloner.SetField(seeker, "timeFuse", MaxFlightTime);

            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length < 1)
            {
                throw new InvalidOperationException("Cloned Phantom missile has no motor.");
            }
            var single = Array.CreateInstance(motors.GetType().GetElementType() ?? typeof(object), 1);
            single.SetValue(motors.GetValue(0), 0);
            HalberdCloner.ApplyMotor(single.GetValue(0), MotorThrust, MotorBurnTime, MotorFuelMass, MotorTopSpeed);
            HalberdCloner.SetField(missile, "motors", single);
            HalberdCloner.NormalizePartMasses(missileClone, MissileMassKg);

            var definitionClone = UnityEngine.Object.Instantiate(sourceDef);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = WeaponName;
            definitionClone.description = WeaponDescription;
            definitionClone.radarSize = RadarSize;
            definitionClone.length = MissileLength;
            definitionClone.width = MissileDiameter;
            definitionClone.height = MissileDiameter;
            definitionClone.unitPrefab = missileClone;
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiSurface", 0f);
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiAir", 0f);
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiMissile", 0f);
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiRadar", 0f);
            missileClone.GetComponent<Unit>().definition = definitionClone;
            definitionClone.CacheMass();

            var infoClone = UnityEngine.Object.Instantiate(sourceMount.info);
            infoClone.name = MissileJsonKey + "_info";
            infoClone.weaponPrefab = missileClone;
            infoClone.weaponName = WeaponName;
            infoClone.shortName = ShortName;
            infoClone.description = WeaponDescription;
            infoClone.blastDamage = 0f;
            infoClone.pierceDamage = 0f;
            infoClone.SetMassPerRound(MissileMassKg);
            HalberdCloner.SetField(infoClone, "maxSpeed", -1f);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetField(missile, "info", infoClone);

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            var mountedMissile = rackClone.GetComponentInChildren<MountedMissile>(true);
            if (mountedMissile == null)
            {
                throw new InvalidOperationException("Cloned Phantom rack prefab has no MountedMissile.");
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

            int hardpointSets = HalberdCloner.AddToMirroredHardpoints(mountClone, SourceMountJsonKey);
            ReportRange(logger);
            logger.LogInfo(
                $"[Phase 2F] RDM-9 Phantom registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), " +
                $"mass {definitionClone.mass:F0} kg, radar size {RadarSize:F2}, range {MaxRange / 1000f:F0} km, " +
                $"motor {MotorThrust / 1000f:F0} kN/{MotorBurnTime:F2} s, {MaxFlightTime:F0} s maximum flight, " +
                $"lock-free intercept priority enabled, " +
                $"added to {hardpointSets} hardpoint sets.");
        }

        internal static bool IsPhantom(Missile missile)
        {
            return missile != null && missile.definition != null && missile.definition.jsonKey == MissileJsonKey;
        }

        private static void ReportRange(ManualLogSource logger)
        {
            try
            {
                const float benchmarkAltitude = 5000f;
                float launchSpeed = LevelInfo.GetSpeedOfSound(benchmarkAltitude) * 0.8f;
                var definition = (MissileDefinition)Encyclopedia.Lookup[MissileJsonKey];
                var missile = definition.unitPrefab.GetComponent<Missile>();
                float range = missile.CalcRange(
                    launchSpeed,
                    benchmarkAltitude,
                    benchmarkAltitude,
                    MaxRange,
                    0f,
                    out _);
                logger.LogInfo(
                    $"[Phase 2F] Range estimate at 5 km/Mach 0.8: RDM-9 {range / 1000f:F1} km kinematic " +
                    $"before its {MaxFlightTime:F0} s lifetime cap vs {MaxRange / 1000f:F0} km design range.");
                if (range < MaxRange * 1.1f)
                {
                    logger.LogWarning(
                        "[Phase 2F] RDM-9 lacks a 10 percent kinematic reserve over its 30 km design range; retune the motor or glide profile.");
                }
            }
            catch (Exception exception)
            {
                logger.LogWarning($"[Phase 2F] RDM-9 range estimate failed: {exception.GetType().Name}: {exception.Message}");
            }
        }
    }
}
