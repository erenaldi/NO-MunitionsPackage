using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using BepInEx.Logging;
using Mirage;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class HalberdCloner
    {
        private const string SourceMountJsonKey = "AAM4_single";
        private const string SourceMissileJsonKey = "AAM4";
        internal const string MissileJsonKey = "Erenaldi.AAM44";
        internal const string MountJsonKey = "Erenaldi.AAM44_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.AAM44";

        private const string WeaponName = "AAM-44 Halberd";
        private const string ShortName = "AAM-44";
        private const string WeaponDescription =
            "Medium-range air-to-air missile pairing a solid-fuel booster with a ramjet sustainer. " +
            "The AAM-44 reaches Mach 3.5 with performance between the AAM-29 and AAM-36, and carries a 22 kg continuous-rod warhead.";

        private const float MissileMassKg = 180f;
        private const float BoosterThrust = 21000f;
        private const float BoosterBurnTime = 6f;
        private const float BoosterFuelMass = 55f;
        private const float SustainerThrust = 14000f;
        internal const float SustainerBurnTime = 30f;
        internal const float SustainerFuelMass = 30f;
        internal const float SustainerAccelerationTime = 10f;
        internal const float BoosterTopSpeed = 837.5f;
        internal const float SustainerTopSpeed = 1172.5f;
        private const float BoosterNozzleLocalZ = -1.6835f;
        private const float SustainerNozzleLocalZ = -0.3367f;
        internal const float BoosterSupersonicDrag = 0.5f;
        internal const float SustainerSupersonicDrag = 0.25f;
        internal const float CoastSupersonicDrag = 0.25f;
        private const float BlastYield = 22f;
        private const float PierceDamage = 400f;
        private const float MaxRange = 70000f;
        private const float MinRange = 3500f;
        private const float SeekerRange = 15000f;
        private const float CruiseLoftAmount = 0.3f;
        private const float DefinitionValue = 1.5f;
        private const float Pk = 1.75f;
        private const float MountDragPerRound = 0.25f;
        private const float MountRcs = 0.06f;

        internal static ManualLogSource Logger { get; private set; }

        internal const string GeometryResourceName = "erenaldi_munitions.geometry.bundle";

        internal static bool EnableCustomGeometry { get; set; }

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
                logger.LogWarning("[Phase 2A] Halberd already registered; skipping clone.");
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

            var missileClone = CloneInactive(sourceMount.info.weaponPrefab, MissileJsonKey);
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
            SetField(missile, "mass", MissileMassKg);
            SetField(missile, "blastYield", BlastYield);
            SetField(missile, "pierceDamage", PierceDamage);
            var motors = (Array)GetField(missile, "motors");
            if (motors == null || motors.Length < 2)
            {
                throw new InvalidOperationException("Cloned missile has fewer than two motors.");
            }
            ApplyMotor(motors.GetValue(0), BoosterThrust, BoosterBurnTime, BoosterFuelMass, BoosterTopSpeed);
            ApplyMotor(motors.GetValue(1), SustainerThrust, SustainerBurnTime, SustainerFuelMass, SustainerTopSpeed);
            SetMotorParticlesLooping(motors.GetValue(0));
            SetMotorParticlesLooping(motors.GetValue(1));
            SetField(missile, "supersonicDrag", BoosterSupersonicDrag);
            NormalizePartMasses(missileClone, MissileMassKg);
            var seeker = missileClone.GetComponent<ARHSeeker>();
            float cruiseLoft = 0f;
            if (seeker != null)
            {
                SetNestedField(seeker, "radarParameters", "maxRange", SeekerRange);
                SetField(seeker, "loftAmount", CruiseLoftAmount);
                cruiseLoft = (float)GetField(seeker, "loftAmount");
            }

            var definitionClone = UnityEngine.Object.Instantiate(sourceDef);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = WeaponName;
            definitionClone.description = WeaponDescription;
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
            infoClone.maxSpeed = -1f;
            infoClone.pK = Pk;
            SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            SetNestedField(infoClone, "targetRequirements", "minRange", MinRange);

            var rackClone = CloneInactive(sourceMount.prefab, MountJsonKey);
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
            mountClone.drag = MountDragPerRound;
            mountClone.RCS = MountRcs;
            mountClone.Initialize();

            if (EnableCustomGeometry)
            {
                bool geometryApplied = CustomGeometryLoader.TryApply(Logger, GeometryResourceName, missileClone, rackClone);
                if (geometryApplied && missileClone.transform.Find("Booster") != null)
                {
                    AlignMotorEffects(missileClone);
                }
            }

            int prefabHash = AssignUniquePrefabHash(missileClone, HashSeed);

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

            int hardpointSets = AddToMirroredHardpoints(mountClone, SourceMountJsonKey);

            ReportRelativeRange(logger);

            logger.LogInfo(
                $"[Phase 2A] AAM-44 Halberd registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), " +
                $"mass {definitionClone.mass:F0} kg, cost {infoClone.costPerRound:F2}, " +
                $"range {MaxRange / 1000f:F0} km, cruise loft {cruiseLoft:F2}, added to {hardpointSets} hardpoint sets.");
        }

        private static void ReportRelativeRange(ManualLogSource logger)
        {
            try
            {
                const float benchmarkAltitude = 1000f;
                const float benchmarkTargetDistance = 50000f;
                float launchSpeed = LevelInfo.GetSpeedOfSound(benchmarkAltitude);
                float scytheRange = CalculateRange("AAM2", launchSpeed, benchmarkAltitude, benchmarkTargetDistance);
                float halberdRange = CalculateRange(MissileJsonKey, launchSpeed, benchmarkAltitude, benchmarkTargetDistance);
                float scimitarRange = CalculateRange(SourceMissileJsonKey, launchSpeed, benchmarkAltitude, benchmarkTargetDistance);
                float gap = scimitarRange - scytheRange;
                float position = Mathf.Abs(gap) > 0.01f ? (halberdRange - scytheRange) / gap : 0f;

                logger.LogInfo(
                    $"[Phase 2A] Relative range estimate at 1 km/Mach 1: Scythe {scytheRange / 1000f:F1} km, " +
                    $"Halberd {halberdRange / 1000f:F1} km, Scimitar {scimitarRange / 1000f:F1} km; " +
                    $"Halberd is {position * 100f:F0}% across the Scythe-to-Scimitar gap.");
                if (position < 0.53f || position > 0.63f)
                {
                    logger.LogWarning($"[Phase 2A] Halberd relative range is outside the accepted 53-63% of the Scythe-to-Scimitar gap.");
                }
            }
            catch (Exception exception)
            {
                logger.LogWarning($"[Phase 2A] Halberd relative range estimate failed: {exception.GetType().Name}: {exception.Message}");
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

        internal static GameObject CloneInactive(GameObject source, string name)
        {
            var holder = new GameObject("Erenaldi.CloneHolder");
            holder.SetActive(false);
            var clone = UnityEngine.Object.Instantiate(source, holder.transform);
            clone.name = name;
            clone.SetActive(false);
            clone.transform.SetParent(null, false);
            UnityEngine.Object.Destroy(holder);
            UnityEngine.Object.DontDestroyOnLoad(clone);
            return clone;
        }

        internal static void ApplyMotor(object motor, float thrust, float burnTime, float fuelMass, float? topSpeed)
        {
            SetField(motor, "thrust", thrust);
            SetField(motor, "burnTime", burnTime);
            SetField(motor, "fuelMass", fuelMass);
            if (topSpeed.HasValue)
            {
                SetField(motor, "topSpeed", topSpeed.Value);
            }
        }

        private static void AlignMotorEffects(GameObject missileClone)
        {
            SetEffectLocalZ(missileClone.transform, "Effects/FireParticlesBooster", BoosterNozzleLocalZ);
            SetEffectLocalZ(missileClone.transform, "Effects/RamjetConesBlue", SustainerNozzleLocalZ);
        }

        private static void SetMotorParticlesLooping(object motor)
        {
            var particleSystems = (Array)GetField(motor, "particleSystems");
            if (particleSystems == null)
            {
                return;
            }

            foreach (var value in particleSystems)
            {
                if (value is ParticleSystem particleSystem)
                {
                    var main = particleSystem.main;
                    main.loop = true;
                }
            }
        }

        private static void SetEffectLocalZ(Transform missileRoot, string path, float localZ)
        {
            var effect = missileRoot.Find(path);
            if (effect == null)
            {
                Logger?.LogWarning($"[Phase 2A] Halberd motor effect '{path}' was not found for nozzle alignment.");
                return;
            }

            var position = effect.localPosition;
            position.z = localZ;
            effect.localPosition = position;
        }

        internal static void NormalizePartMasses(GameObject missileClone, float totalMass)
        {
            var parts = missileClone.GetComponentsInChildren<UnitPart>(true);
            float sum = 0f;
            foreach (var part in parts)
            {
                sum += part.mass;
            }
            if (sum <= 0f)
            {
                return;
            }
            float scale = totalMass / sum;
            foreach (var part in parts)
            {
                part.mass *= scale;
            }
        }

        internal static int AssignUniquePrefabHash(GameObject missileClone, string hashSeed)
        {
            var identity = missileClone.GetComponent<NetworkIdentity>();
            if (identity == null)
            {
                throw new InvalidOperationException("Cloned missile prefab has no NetworkIdentity.");
            }
            var taken = new HashSet<int>();
            foreach (var other in Resources.FindObjectsOfTypeAll(typeof(NetworkIdentity)))
            {
                var networkIdentity = other as NetworkIdentity;
                if (networkIdentity != null && networkIdentity.PrefabHash != 0)
                {
                    taken.Add(networkIdentity.PrefabHash);
                }
            }
            var seed = hashSeed;
            int hash = ComputeFnv1a(seed);
            while (hash == 0 || taken.Contains(hash))
            {
                seed += "#";
                hash = ComputeFnv1a(seed);
            }
            identity.PrefabHash = hash;
            return hash;
        }

        private static int ComputeFnv1a(string text)
        {
            uint hash = 2166136261u;
            foreach (var character in text)
            {
                hash ^= character;
                hash *= 16777619u;
            }
            return unchecked((int)hash);
        }

        internal static int AddToMirroredHardpoints(WeaponMount mountClone, string sourceMountJsonKey)
        {
            if (!Encyclopedia.WeaponLookup.TryGetValue(sourceMountJsonKey, out var mirror) || mirror == null)
            {
                return 0;
            }
            var aircraft = Encyclopedia.i.aircraft;
            if (aircraft == null)
            {
                return 0;
            }
            int added = 0;
            foreach (var definition in aircraft)
            {
                if (definition == null || definition.unitPrefab == null)
                {
                    continue;
                }
                var weaponManager = definition.unitPrefab.GetComponentInChildren<WeaponManager>(true);
                if (weaponManager == null || weaponManager.hardpointSets == null)
                {
                    continue;
                }
                foreach (var set in weaponManager.hardpointSets)
                {
                    if (set == null || set.weaponOptions == null)
                    {
                        continue;
                    }
                    if (set.weaponOptions.Contains(mirror) && !set.weaponOptions.Contains(mountClone))
                    {
                        set.weaponOptions.Add(mountClone);
                        added++;
                    }
                }
            }
            return added;
        }

        private static FieldInfo FindField(Type type, string name)
        {
            for (var current = type; current != null && current != typeof(object); current = current.BaseType)
            {
                var field = current.GetField(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (field != null)
                {
                    return field;
                }
            }
            return null;
        }

        internal static object GetField(object target, string name)
        {
            if (target == null)
            {
                throw new ArgumentNullException(nameof(target));
            }
            var field = FindField(target.GetType(), name);
            if (field == null)
            {
                throw new MissingFieldException(target.GetType().Name, name);
            }
            return field.GetValue(target);
        }

        internal static void SetField(object target, string name, object value)
        {
            if (target == null)
            {
                throw new ArgumentNullException(nameof(target));
            }
            var field = FindField(target.GetType(), name);
            if (field == null)
            {
                throw new MissingFieldException(target.GetType().Name, name);
            }
            field.SetValue(target, value);
        }

        internal static void SetNestedField(object container, string containerFieldName, string fieldName, object value)
        {
            if (container == null)
            {
                throw new ArgumentNullException(nameof(container));
            }
            var field = FindField(container.GetType(), containerFieldName);
            if (field == null)
            {
                throw new MissingFieldException(container.GetType().Name, containerFieldName);
            }
            var boxed = field.GetValue(container);
            if (boxed == null)
            {
                throw new InvalidOperationException($"Field '{containerFieldName}' on {container.GetType().Name} was null.");
            }
            SetField(boxed, fieldName, value);
            field.SetValue(container, boxed);
        }
    }
}
