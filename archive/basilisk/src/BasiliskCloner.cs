using System;
using System.Reflection;
using BepInEx.Logging;
using Mirage;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class BasiliskCloner
    {
        private const string SourceMountJsonKey = "P_AAM1_single";
        private const string SourceMissileJsonKey = "P_AAM1";
        private const string HardpointMirrorJsonKey = "AAM2_single";
        private const string IrTuningMissileJsonKey = "AAM1";
        private const string RadarTuningMissileJsonKey = "AAM2";
        internal const string MissileJsonKey = "Erenaldi.AAM41";
        internal const string MountJsonKey = "Erenaldi.AAM41_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.AAM41";

        private const string WeaponName = "AAM-41 Basilisk";
        private const string ShortName = "AAM-41";
        private const string WeaponDescription =
            "Compact medium-range air-to-air missile with sequential active-radar and infrared guidance. " +
            "Defeating the radar stage triggers an infrared fallback that must be defeated separately.";

        private const float MissileMassKg = 130f;
        private const float MissileLength = 2.9f;
        private const float MissileBodyDiameter = 0.21f;
        private const float BoosterThrust = 18000f;
        private const float BoosterBurnTime = 4f;
        private const float BoosterFuelMass = 25f;
        private const float SustainerThrust = 10000f;
        private const float SustainerBurnTime = 10f;
        private const float SustainerFuelMass = 25f;
        private const float TopSpeed = 1100f;
        private const float BlastYield = 25f;
        private const float PierceDamage = 400f;
        private const float MaxRange = 25000f;
        private const float MinRange = 1500f;
        private const float SeekerRange = 25000f;

        internal static ManualLogSource Logger { get; private set; }
        internal static bool EnableCustomGeometry { get; set; }

        internal static void Clone(ManualLogSource logger)
        {
            Logger = logger;
            var encyclopedia = Encyclopedia.i;
            if (encyclopedia == null || Encyclopedia.Lookup == null || Encyclopedia.WeaponLookup == null)
            {
                throw new InvalidOperationException("Encyclopedia is not loaded.");
            }
            if (Encyclopedia.WeaponLookup.ContainsKey(MountJsonKey) || Encyclopedia.Lookup.ContainsKey(MissileJsonKey))
            {
                logger.LogWarning("[Phase 2B] Basilisk already registered; skipping clone.");
                return;
            }
            if (!Encyclopedia.WeaponLookup.TryGetValue(SourceMountJsonKey, out var sourceMount) || sourceMount == null)
            {
                throw new InvalidOperationException($"Source mount '{SourceMountJsonKey}' was not found.");
            }
            var sourceDef = RequireMissileDefinition(SourceMissileJsonKey);
            var irSource = RequireMissileDefinition(IrTuningMissileJsonKey).unitPrefab.GetComponent<IRSeeker>();
            var radarSource = RequireMissileDefinition(RadarTuningMissileJsonKey).unitPrefab.GetComponent<ARHSeeker>();
            if (sourceMount.info == null || sourceMount.info.weaponPrefab == null || irSource == null || radarSource == null)
            {
                throw new InvalidOperationException("Basilisk source assets are incomplete.");
            }

            var missileClone = HalberdCloner.CloneInactive(sourceMount.info.weaponPrefab, MissileJsonKey);
            var missile = missileClone.GetComponent<Missile>();
            if (missile == null)
            {
                throw new InvalidOperationException("Cloned Basilisk prefab has no Missile component.");
            }
            foreach (var staleSeeker in missileClone.GetComponents<MissileSeeker>())
            {
                UnityEngine.Object.DestroyImmediate(staleSeeker);
            }

            var infraredHost = new GameObject("BasiliskIRSeeker");
            infraredHost.transform.SetParent(missileClone.transform, false);
            var infrared = infraredHost.AddComponent<IRSeeker>();
            CopySerializedFields(irSource, infrared);
            HalberdCloner.SetField(infrared, "missile", missile);

            var radarHost = new GameObject("BasiliskARHSeeker");
            radarHost.transform.SetParent(missileClone.transform, false);
            var radar = radarHost.AddComponent<ARHSeeker>();
            CopySerializedFields(radarSource, radar);
            HalberdCloner.SetField(radar, "missile", missile);
            HalberdCloner.SetNestedField(radar, "radarParameters", "maxRange", SeekerRange);
            HalberdCloner.SetField(radar, "loftAmount", 0f);
            HalberdCloner.SetNestedField(radar, "jinkEvasion", "amount", 0f);

            var composite = missileClone.AddComponent<BasiliskSeeker>();
            composite.Configure(missile, infrared, radar);

            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = MissileMassKg;
            }
            HalberdCloner.SetField(missile, "mass", MissileMassKg);
            HalberdCloner.SetField(missile, "blastYield", BlastYield);
            HalberdCloner.SetField(missile, "pierceDamage", PierceDamage);
            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length < 2)
            {
                throw new InvalidOperationException("Cloned Basilisk missile has fewer than two motors.");
            }
            HalberdCloner.ApplyMotor(motors.GetValue(0), BoosterThrust, BoosterBurnTime, BoosterFuelMass, TopSpeed);
            HalberdCloner.ApplyMotor(motors.GetValue(1), SustainerThrust, SustainerBurnTime, SustainerFuelMass, TopSpeed);
            HalberdCloner.NormalizePartMasses(missileClone, MissileMassKg);

            var definitionClone = UnityEngine.Object.Instantiate(sourceDef);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = WeaponName;
            definitionClone.description = WeaponDescription;
            definitionClone.length = MissileLength;
            definitionClone.width = MissileBodyDiameter;
            definitionClone.height = MissileBodyDiameter;
            definitionClone.unitPrefab = missileClone;
            missile.definition = definitionClone;
            definitionClone.CacheMass();

            var infoClone = UnityEngine.Object.Instantiate(sourceMount.info);
            infoClone.name = MissileJsonKey + "_info";
            infoClone.weaponPrefab = missileClone;
            infoClone.weaponName = WeaponName;
            infoClone.shortName = ShortName;
            infoClone.description = WeaponDescription;
            infoClone.maxSpeed = -1f;
            infoClone.SetMassPerRound(MissileMassKg);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minRange", MinRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minIR", 0f);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minRadar", 0f);
            HalberdCloner.SetField(missile, "info", infoClone);

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            var mountedMissile = rackClone.GetComponentInChildren<MountedMissile>(true);
            if (mountedMissile == null)
            {
                throw new InvalidOperationException("Cloned Basilisk rack prefab has no MountedMissile.");
            }
            mountedMissile.info = infoClone;

            var mountClone = UnityEngine.Object.Instantiate(sourceMount);
            mountClone.name = MountJsonKey;
            mountClone.jsonKey = MountJsonKey;
            mountClone.info = infoClone;
            mountClone.prefab = rackClone;
            mountClone.mountName = WeaponName;
            mountClone.Initialize();

            if (EnableCustomGeometry)
            {
                if (CustomGeometryLoader.TryApply(
                    Logger,
                    HalberdCloner.GeometryResourceName,
                    missileClone,
                    rackClone,
                    MissileJsonKey,
                    MountJsonKey))
                {
                    AlignEffectsToTail(missile, missileClone.transform);
                }
            }

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

            int hardpointSets = HalberdCloner.AddToMirroredHardpoints(mountClone, HardpointMirrorJsonKey);
            logger.LogInfo(
                $"[Phase 2B] AAM-41 Basilisk registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), mass {MissileMassKg:F0} kg, " +
                $"length {MissileLength:F1} m, range {MaxRange / 1000f:F0} km, added to {hardpointSets} hardpoint sets.");
        }

        private static void AlignEffectsToTail(Missile missile, Transform missileTransform)
        {
            var effectsTransform = (Transform)HalberdCloner.GetField(missile, "effectsTransform");
            if (effectsTransform != null)
            {
                effectsTransform.position = missileTransform.TransformPoint(0f, 0f, -MissileLength * 0.5f);
            }
        }

        private static MissileDefinition RequireMissileDefinition(string jsonKey)
        {
            if (!Encyclopedia.Lookup.TryGetValue(jsonKey, out var value) || !(value is MissileDefinition definition) ||
                definition == null || definition.unitPrefab == null)
            {
                throw new InvalidOperationException($"Source missile definition '{jsonKey}' was not found.");
            }
            return definition;
        }

        private static void CopySerializedFields(Component source, Component target)
        {
            for (var type = source.GetType(); type != null && type != typeof(MonoBehaviour); type = type.BaseType)
            {
                foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance |
                    BindingFlags.DeclaredOnly))
                {
                    if (field.IsStatic || field.IsInitOnly || field.IsNotSerialized || field.Name == "missile" ||
                        (!field.IsPublic && !Attribute.IsDefined(field, typeof(SerializeField))))
                    {
                        continue;
                    }
                    field.SetValue(target, field.GetValue(source));
                }
            }
        }
    }
}
