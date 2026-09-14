using System;
using System.Collections.Generic;
using BepInEx.Logging;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class PalisadeCloner
    {
        private const string SourceMountJsonKey = "AGM2_6Pod";
        private const string SourceMissileJsonKey = "SAM_Radar1";
        internal const string MissileJsonKey = "Erenaldi.HKP1_int";
        internal const string MountJsonKey = "Erenaldi.HKP1_Palisade";
        private const string HashSeed = "Erenaldi.MunitionsPackage.HKP1.Interceptor";

        private const string WeaponName = "HKP-1 Palisade";
        private const string InterceptorName = "HKP-1 Interceptor";
        private const string Description =
            "Four-round aircraft hard-kill defense pod. Its compact radar-guided interceptors automatically engage incoming missiles according to the selected Palisade mode.";

        private const float InterceptorMassKg = 35f;
        private const float InterceptorLength = 1.2f;
        private const float InterceptorDiameter = 0.14f;
        private const float InterceptorThrust = 18000f;
        private const float InterceptorBurnTime = 2.5f;
        private const float InterceptorFuelMass = 15f;
        private const float InterceptorTopSpeed = 1050f;
        private const float BlastYield = 5f;
        internal static float MinRange { get; set; } = 300f;
        internal static float MaxRange { get; set; } = 4000f;
        internal static int RoundsPerPod { get; set; } = 4;

        private static readonly string[] CompatibleMountAnchors =
        {
            "Rocket2_4Pod",
            "JammingPod1"
        };

        internal static ManualLogSource Logger { get; private set; }
        internal static WeaponInfo InterceptorInfo { get; private set; }
        internal static PalisadeCountermeasure.PalisadeMode InitialMode { get; set; }
        internal static float RefireCooldown { get; set; } = 0.75f;
        internal static float ReengageClearance { get; set; } = 100f;
        internal static float SoftKillLeadTime { get; set; } = 2f;
        internal static int MinimumFlareReserve { get; set; } = 2;
        internal static float MinimumCapacitorReserve { get; set; } = 0.25f;
        internal static HashSet<string> PlatformWhitelist { get; set; } =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "Multirole1", "EW1" };

        internal static void Clone(ManualLogSource logger)
        {
            Logger = logger;
            var encyclopedia = Encyclopedia.i;
            if (encyclopedia == null || Encyclopedia.Lookup == null || Encyclopedia.WeaponLookup == null)
            {
                throw new InvalidOperationException("Encyclopedia lookups are not initialized.");
            }
            if (Encyclopedia.WeaponLookup.ContainsKey(MountJsonKey) || Encyclopedia.Lookup.ContainsKey(MissileJsonKey))
            {
                logger.LogWarning("[Phase 4] Palisade already registered; skipping clone.");
                return;
            }
            if (!Encyclopedia.WeaponLookup.TryGetValue(SourceMountJsonKey, out var sourceMount) || sourceMount == null)
            {
                throw new InvalidOperationException($"Source pod mount '{SourceMountJsonKey}' was not found.");
            }
            if (!Encyclopedia.Lookup.TryGetValue(SourceMissileJsonKey, out var sourceObject) ||
                !(sourceObject is MissileDefinition sourceDefinition) || sourceDefinition.unitPrefab == null)
            {
                throw new InvalidOperationException($"RAM-45 definition '{SourceMissileJsonKey}' was not found.");
            }

            var missileClone = HalberdCloner.CloneInactive(sourceDefinition.unitPrefab, MissileJsonKey);
            var missile = missileClone.GetComponent<Missile>();
            if (missile == null)
            {
                throw new InvalidOperationException("Cloned RAM-45 prefab has no Missile component.");
            }
            ConfigureMissile(missileClone, missile);

            var definitionClone = UnityEngine.Object.Instantiate(sourceDefinition);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = InterceptorName;
            definitionClone.description = Description;
            definitionClone.length = InterceptorLength;
            definitionClone.width = InterceptorDiameter;
            definitionClone.height = InterceptorDiameter;
            definitionClone.value = 0.08f;
            definitionClone.unitPrefab = missileClone;
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiAir", 0f);
            HalberdCloner.SetNestedField(definitionClone, "roleIdentity", "antiMissile", 1f);
            missileClone.GetComponent<Unit>().definition = definitionClone;
            definitionClone.CacheMass();

            var infoClone = UnityEngine.Object.Instantiate(sourceMount.info);
            infoClone.name = MissileJsonKey + "_info";
            infoClone.weaponPrefab = missileClone;
            infoClone.weaponName = InterceptorName;
            infoClone.shortName = "HKP-1 INT";
            infoClone.description = Description;
            infoClone.fireInterval = RefireCooldown;
            infoClone.maxSpeed = -1f;
            infoClone.pK = 0.35f;
            infoClone.blastDamage = BlastYield;
            infoClone.pierceDamage = 50f;
            infoClone.missile = true;
            infoClone.boresight = false;
            HalberdCloner.SetNestedField(infoClone, "effectiveness", "antiSurface", 0f);
            HalberdCloner.SetNestedField(infoClone, "effectiveness", "antiAir", 0f);
            HalberdCloner.SetNestedField(infoClone, "effectiveness", "antiMissile", 1f);
            HalberdCloner.SetNestedField(infoClone, "effectiveness", "antiRadar", 0f);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "lineOfSight", false);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minRange", MinRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxSpeed", 100000f);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minAlignment", 180f);
            HalberdCloner.SetField(missile, "info", infoClone);
            InterceptorInfo = infoClone;

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            ConfigureRack(rackClone, infoClone);

            var mountClone = UnityEngine.Object.Instantiate(sourceMount);
            mountClone.name = MountJsonKey;
            mountClone.jsonKey = MountJsonKey;
            mountClone.info = infoClone;
            mountClone.prefab = rackClone;
            mountClone.mountName = WeaponName;
            mountClone.countermeasure = true;
            mountClone.colorable = true;
            mountClone.emptyMass = Mathf.Max(250f - RoundsPerPod * InterceptorMassKg, 0f);
            mountClone.emptyDrag = 0.15f;
            mountClone.drag = 0.15f;
            mountClone.emptyRCS = 0.01f;
            mountClone.RCS = 0.01f;
            mountClone.Initialize();
            mountClone.mountName = WeaponName;
            mountClone.mass = 250f;

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

            int hardpointSets = AddToWhitelistedHardpoints(mountClone);
            logger.LogInfo(
                $"[Phase 4] HKP-1 Palisade registered: interceptor '{MissileJsonKey}' (index {definitionIndex}, hash {prefabHash:X8}), " +
                $"mount '{MountJsonKey}' (index {mountIndex}), {mountClone.ammo} rounds, {MinRange / 1000f:F1}-{MaxRange / 1000f:F1} km envelope, " +
                $"RAM-45 SARH runtime spike, added to {hardpointSets} whitelisted hardpoint sets.");
        }

        private static void ConfigureMissile(GameObject missileClone, Missile missile)
        {
            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = InterceptorMassKg;
            }
            HalberdCloner.SetField(missile, "mass", InterceptorMassKg);
            HalberdCloner.SetField(missile, "blastYield", BlastYield);
            HalberdCloner.SetField(missile, "pierceDamage", 50f);
            HalberdCloner.SetField(missile, "gLimit", 35f);
            HalberdCloner.SetField(missile, "maxTurnRate", 360f);
            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length != 2)
            {
                throw new InvalidOperationException($"Cloned RAM-45 expected two motors but found {motors?.Length ?? 0}.");
            }
            // RAM-45 motor 0 is its brief launcher impulse; motor 1 is the flight motor.
            object boostMotor = motors.GetValue(motors.Length - 1);
            HalberdCloner.ApplyMotor(boostMotor, InterceptorThrust, InterceptorBurnTime, InterceptorFuelMass, InterceptorTopSpeed);
            HalberdCloner.SetField(boostMotor, "delayTimer", 0f);
            HalberdCloner.NormalizePartMasses(missileClone, InterceptorMassKg);

            var seeker = missileClone.GetComponent<SARHSeeker>();
            if (seeker == null)
            {
                throw new InvalidOperationException("Cloned RAM-45 has no SARHSeeker for the runtime spike.");
            }
            HalberdCloner.SetField(seeker, "tangibleDelay", 0f);
            HalberdCloner.SetField(seeker, "armDelay", 0.05f);
            HalberdCloner.SetField(seeker, "guidanceDelay", 0f);
            HalberdCloner.SetField(seeker, "seekerAngle", 180f);
            HalberdCloner.SetField(seeker, "selfDestructAtSpeed", 100f);
        }

        private static void ConfigureRack(GameObject rackClone, WeaponInfo infoClone)
        {
            var launchers = rackClone.GetComponentsInChildren<MountedMissile>(true);
            if (launchers.Length < RoundsPerPod)
            {
                throw new InvalidOperationException($"Source pod has only {launchers.Length} MountedMissile components.");
            }
            for (int i = launchers.Length - 1; i >= RoundsPerPod; i--)
            {
                UnityEngine.Object.DestroyImmediate(launchers[i].gameObject);
            }
            launchers = rackClone.GetComponentsInChildren<MountedMissile>(true);
            foreach (var launcher in launchers)
            {
                launcher.info = infoClone;
            }
            var countermeasure = rackClone.AddComponent<PalisadeCountermeasure>();
            countermeasure.Configure(InitialMode, infoClone.weaponIcon);
            rackClone.AddComponent<PalisadeDefense>();
        }

        private static int AddToWhitelistedHardpoints(WeaponMount mount)
        {
            int added = 0;
            foreach (var definition in Encyclopedia.i.aircraft)
            {
                if (definition == null || definition.unitPrefab == null || !PlatformWhitelist.Contains(definition.jsonKey))
                {
                    continue;
                }
                var manager = definition.unitPrefab.GetComponentInChildren<WeaponManager>(true);
                if (manager == null || manager.hardpointSets == null)
                {
                    continue;
                }
                foreach (var set in manager.hardpointSets)
                {
                    if (set == null || set.weaponOptions == null || set.weaponOptions.Contains(mount))
                    {
                        continue;
                    }
                    bool compatible = false;
                    foreach (var option in set.weaponOptions)
                    {
                        if (option != null && Array.IndexOf(CompatibleMountAnchors, option.jsonKey) >= 0)
                        {
                            compatible = true;
                            break;
                        }
                    }
                    if (compatible)
                    {
                        set.weaponOptions.Add(mount);
                        added++;
                    }
                }
            }
            return added;
        }
    }
}
