using System;
using System.Collections;
using System.Reflection;
using BepInEx.Logging;
using Mirage;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class KrisCloner
    {
        private const string SourceMountJsonKey = "AAM1_single";
        private const string SourceMissileJsonKey = "AAM1";
        internal const string MissileJsonKey = "Erenaldi.IRMS4";
        internal const string MountJsonKey = "Erenaldi.IRMS4_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.IRMS4";

        private const string WeaponName = "IRM-S4 Kris";
        private const string ShortName = "IRM-S4";
        private const string WeaponDescription =
            "Compact high-agility infrared missile with four honeycomb lattice fins, longitudinal strakes, " +
            "a wide seeker aperture, and thrust-vector control. Optimized for close-range off-boresight " +
            "engagements out to approximately 8.5 km.";

        internal const float SizeScale = 1.1f;
        internal const float MissileMassKg = 110f * SizeScale * SizeScale * SizeScale;
        private const float PropellantMassKg = 44f * SizeScale * SizeScale * SizeScale;
        private const float MissileLength = 2.8715922f * SizeScale;
        private const float MissileDiameter = 0.14366694f * SizeScale;
        internal const float TopSpeed = 1190f;
        internal const float FirstPulseThrust = 20000f;
        internal const float FirstPulseBurnTime = 4f;
        internal const float FirstPulseFuelMass = PropellantMassKg * 0.5f;
        internal const float SecondPulseThrust = 10596.7f;
        internal const float SecondPulseBurnTime = 6f;
        internal const float SecondPulseFuelMass = PropellantMassKg * 0.5f;
        internal const float ThrustVectoring = 35f;
        private const float FinArea = 0.35f * SizeScale * SizeScale;
        internal const float SteeringTorque = 30f;
        internal const float AerodynamicMaxG = 60f;
        internal const float SteeringMaxTurnRate = 240f;
        internal const float CombinedMaxG = 130f;
        internal const float FirstPulseTvcG = 70f;
        internal const float PeakLiftCoefficient = 2.25f * SizeScale;
        private const float SupersonicDrag = 0.05f;
        private const float BlastYield = 11f;
        private const float MaxRange = 8500f;
        internal const float MaxAlignment = 72.1f;

        internal static ManualLogSource Logger { get; private set; }
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
                logger.LogWarning("[Phase 2C] Kris already registered; skipping clone.");
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
            if (missile == null || missileClone.GetComponent<IRSeeker>() == null)
            {
                throw new InvalidOperationException("Cloned Kris prefab is missing its Missile or IRSeeker component.");
            }

            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = MissileMassKg;
            }
            HalberdCloner.SetField(missile, "mass", MissileMassKg);
            HalberdCloner.SetField(missile, "finArea", FinArea);
            HalberdCloner.SetField(missile, "liftCurve", BuildLiftCurve());
            HalberdCloner.SetField(missile, "dragCurve", BuildDragCurve());
            HalberdCloner.SetField(missile, "blastYield", BlastYield);
            HalberdCloner.SetField(missile, "supersonicDrag", SupersonicDrag);
            HalberdCloner.SetField(missile, "torque", SteeringTorque);
            HalberdCloner.SetField(missile, "gLimit", AerodynamicMaxG);
            HalberdCloner.SetField(missile, "maxTurnRate", SteeringMaxTurnRate);
            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length == 0)
            {
                throw new InvalidOperationException("Cloned Kris missile has no motor.");
            }
            motors = CreateMotorProfile(motors);
            HalberdCloner.SetField(missile, "motors", motors);
            HalberdCloner.NormalizePartMasses(missileClone, MissileMassKg);

            var definitionClone = UnityEngine.Object.Instantiate(sourceDef);
            definitionClone.name = MissileJsonKey;
            definitionClone.jsonKey = MissileJsonKey;
            definitionClone.unitName = WeaponName;
            definitionClone.description = WeaponDescription;
            definitionClone.length = MissileLength;
            definitionClone.width = MissileDiameter;
            definitionClone.height = MissileDiameter;
            definitionClone.unitPrefab = missileClone;
            missileClone.GetComponent<Unit>().definition = definitionClone;
            definitionClone.CacheMass();

            var infoClone = UnityEngine.Object.Instantiate(sourceMount.info);
            infoClone.name = MissileJsonKey + "_info";
            infoClone.weaponPrefab = missileClone;
            infoClone.weaponName = WeaponName;
            infoClone.shortName = ShortName;
            infoClone.description = WeaponDescription;
            infoClone.maxSpeed = TopSpeed;
            infoClone.SetMassPerRound(MissileMassKg);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minAlignment", MaxAlignment);
            HalberdCloner.SetField(missile, "info", infoClone);

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            var mountedMissile = rackClone.GetComponentInChildren<MountedMissile>(true);
            if (mountedMissile == null)
            {
                throw new InvalidOperationException("Cloned Kris rack prefab has no MountedMissile.");
            }
            mountedMissile.info = infoClone;

            var mountClone = UnityEngine.Object.Instantiate(sourceMount);
            mountClone.name = MountJsonKey;
            mountClone.jsonKey = MountJsonKey;
            mountClone.info = infoClone;
            mountClone.prefab = rackClone;
            mountClone.mountName = WeaponName;
            mountClone.Initialize();

            if (EnableCustomGeometry && CustomGeometryLoader.TryApply(
                Logger,
                HalberdCloner.GeometryResourceName,
                missileClone,
                rackClone,
                MissileJsonKey,
                MountJsonKey))
            {
                AlignEffectsToTail(missile, missileClone.transform);
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

            int hardpointSets = HalberdCloner.AddToMirroredHardpoints(mountClone, SourceMountJsonKey);
            logger.LogInfo(
                $"[Phase 2C] IRM-S4 Kris registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), " +
                $"mass {definitionClone.mass:F0} kg, cost {infoClone.costPerRound:F2}, range {MaxRange / 1000f:F0} km, " +
                $"off-boresight {MaxAlignment:F0} degrees, dual pulse {FirstPulseThrust / 1000f:F0} kN/{FirstPulseBurnTime:F1} s -> adaptive coast -> " +
                $"{SecondPulseThrust / 1000f:F0} kN/{SecondPulseBurnTime:F2} s, TVC {ThrustVectoring:F0} degrees, " +
                $"added to {hardpointSets} hardpoint sets.");
        }

        private static Array CreateMotorProfile(Array sourceMotors)
        {
            object firstPulse = sourceMotors.GetValue(0);
            Type motorType = sourceMotors.GetType().GetElementType() ?? firstPulse.GetType();
            MethodInfo cloneMethod = typeof(object).GetMethod(
                "MemberwiseClone",
                BindingFlags.Instance | BindingFlags.NonPublic);
            if (cloneMethod == null)
            {
                throw new MissingMethodException(typeof(object).FullName, "MemberwiseClone");
            }
            object secondPulse = cloneMethod.Invoke(firstPulse, null);
            var profile = Array.CreateInstance(motorType, 2);

            ConfigurePulse(firstPulse, FirstPulseThrust, FirstPulseBurnTime, FirstPulseFuelMass);
            ConfigurePulse(secondPulse, SecondPulseThrust, SecondPulseBurnTime, SecondPulseFuelMass);
            profile.SetValue(firstPulse, 0);
            profile.SetValue(secondPulse, 1);
            return profile;
        }

        private static void ConfigurePulse(object motor, float thrust, float burnTime, float fuelMass)
        {
            HalberdCloner.ApplyMotor(motor, thrust, burnTime, fuelMass, TopSpeed);
            HalberdCloner.SetField(motor, "thrustVectoring", ThrustVectoring);
            HalberdCloner.SetField(motor, "activated", false);
            HalberdCloner.SetField(motor, "delayTimer", 0f);
            HalberdCloner.SetField(motor, "burnRate", 0f);
        }

        private static AnimationCurve BuildLiftCurve()
        {
            // Lift coefficients scale with SizeScale so the enlarged fin area and
            // mass keep the authored aerodynamic-G envelope.
            return new AnimationCurve(
                new Keyframe(0f, 0f),
                new Keyframe(0.087f, 0.389f * SizeScale),
                new Keyframe(0.175f, 0.772f * SizeScale),
                new Keyframe(0.26f, 1.118f * SizeScale),
                new Keyframe(0.35f, 1.449f * SizeScale),
                new Keyframe(0.44f, 1.734f * SizeScale),
                new Keyframe(0.52f, 1.94f * SizeScale),
                new Keyframe(0.61f, 2.113f * SizeScale),
                new Keyframe(0.7f, 2.217f * SizeScale),
                new Keyframe(0.79f, 2.25f * SizeScale),
                new Keyframe(0.87f, 2.218f * SizeScale),
                new Keyframe(1.05f, 1.942f * SizeScale));
        }

        private static AnimationCurve BuildDragCurve()
        {
            // Grid-fin axial relief: the low-AoA keys (the aligned-flight/coast
            // regime, where the missile spends every coast phase) are reduced
            // ~25-28 percent; the induced-drag keys above 25 degrees AoA stay
            // authored so hard maneuvers still bleed energy realistically.
            return new AnimationCurve(
                new Keyframe(0f, 0.025f),
                new Keyframe(0.087f, 0.034f),
                new Keyframe(0.175f, 0.063f),
                new Keyframe(0.26f, 0.104f),
                new Keyframe(0.35f, 0.19f),
                new Keyframe(0.44f, 0.2965f),
                new Keyframe(0.61f, 0.4869f),
                new Keyframe(0.79f, 0.6931f),
                new Keyframe(1.05f, 0.9395f));
        }

        private static void AlignEffectsToTail(Missile missile, Transform missileTransform)
        {
            var effectsTransform = (Transform)HalberdCloner.GetField(missile, "effectsTransform");
            if (effectsTransform != null)
            {
                effectsTransform.position = missileTransform.TransformPoint(0f, 0f, -MissileLength * 0.5f);
            }
        }

    }
}
