using System;
using System.Reflection;
using BepInEx.Logging;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class BallistaCloner
    {
        private const string SourceMountJsonKey = "AGM_heavy_single";
        private const string SourceMissileJsonKey = "AShM2";
        internal const string MissileJsonKey = "Erenaldi.AGM110";
        internal const string MountJsonKey = "Erenaldi.AGM110_single";
        private const string HashSeed = "Erenaldi.MunitionsPackage.AGM110";

        private const string WeaponName = "AGM-110 Ballista";
        private const string ShortName = "AGM-110";
        private const string WeaponDescription =
            "Heavy standoff weapon with an electro-optical cruise seeker, terrain-following approach, " +
            "evasive terminal jink, and a terminal sprint motor. Carries a 45 kg shaped-charge " +
            "warhead against hardened ground targets at ranges up to 20 km.";

        // Calibrated from the approved CAD masters: 0.131369 m3 enclosed volume
        // at the AGM-68/AGM-48 density anchors (1332 / 1304 kg/m3) -> 175 kg.
        internal const float MissileMassKg = 175f;
        internal const float MissileLength = 2.594424f;
        internal const float MissileDiameter = 0.24f;
        internal const float MaxRange = 20000f;
        // Terminal-dash drag: the folded airframe runs nearly clean; the donor
        // curve and its 0.5 supersonic penalty bled the sprint to a crawl.
        internal const float SupersonicDrag = 0.05f;
        internal const float CruiseThrust = 2800f;
        internal const float CruiseTopSpeed = 300f;
        // 8 kg over 80 s = 24 km cruise endurance: covers a 20 km engagement
        // (cruise ~9.5 km, loft, sprint) with reserve, freeing mass to the
        // 70 kg-class warhead per the 175/73/8/24 budget build-up.
        internal const float CruiseBurnTime = 80f;
        internal const float CruiseFuelMass = 8f;
        internal const float CruiseIgnitionDelay = 1f;
        // Terminal motor profile, derived from the 49 kg propellant mass at
        // Isp 250 s (high-energy composite solid): exhaust velocity 2452 m/s,
        // mass flow 5.71 kg/s at 14 kN -> 8.6 s burn, 120 kNs total impulse,
        // and a rocket-equation delta-v of ~850 m/s (167 -> 118 kg). The
        // 168 kNs "doubled impulse" figure was a game-model artifact; 120 kNs
        // is the physical number for this propellant mass.
        //
        // Terminal energy retention: what bleeds speed is drag (the 0.05
        // folded drag above) and off-axis burn geometry. The motor effect for
        // the terminal burn is therefore modeled as four levers set below:
        //   1. FoldDelaySeconds 2 s / FoldRange 7.5 km - wings fold before the
        //      burn so the drag cut lands first, not mid-sprint.
        //   2. Fold time/range trigger - fold at the time OR range gate so the
        //      fold always precedes ignition (time trigger at the 9.5 km fold,
        //      range trigger on a late loft).
        //   3. FoldDelay Ignition - ignition after the fold (drag low, wings
        //      gone) rather than during, so the sprint energy lands on a clean
        //      airframe.
        //   4. Donor gear cleanup - gear, gear doors, and wings are destroyed
        //      at the fold, so the donor's drag-cut gear curve cannot bleed
        //      the sprint after ignition.
        internal const float SprintThrust = 14000f;
        internal const float SprintBurnTime = 8.6f;
        internal const float SprintFuelMass = 49f;
        internal const float SprintReserveDelay = 3600f;
        // Sprint velocity ceiling, Mach 2.4-ish at terminal altitude. The
        // motor's delta-v would reach Mach 3+; the engine's per-motor topSpeed
        // cap trims the dash the way a real grain tail-off would.
        internal const float SprintTopSpeed = 780f;
        internal const float TerminalRange = 10000f;
        internal const float FoldRange = 7500f;
        internal const float FoldDelaySeconds = 2f;
        // Aero reference area after the wing fold. Missile.ApplyAero scales
        // drag AND lift by currentFinArea; the donor deploys it to 2.5 m2 and
        // never re-folds it, so the sprint paid sea-skimmer drag. 0.12 m2 is
        // the Ballista's actual folded tail-control area.
        internal const float TerminalFinArea = 0.12f;
        internal const float CruiseAltitude = 110f;
        internal const float TerminalMaxTargetSpeed = 50f;
        internal const float TargetMaxAltitude = 100000f;
        internal const float TargetMinValue = 0f;
        internal const float TargetMaxSpeed = 50f;

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
                logger.LogWarning("[Phase 2D] Ballista already registered; skipping clone.");
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
            if (sourceMount.prefab == null || sourceDef.unitPrefab == null)
            {
                throw new InvalidOperationException("Source mount rack or missile unit prefab is missing.");
            }

            // AGM_heavy's weaponPrefab is its carriage (MountedMissile), not a missile;
            // the Ballista body must come from the AShM2 missile unit prefab.
            var missileClone = HalberdCloner.CloneInactive(sourceDef.unitPrefab, MissileJsonKey);
            var missile = missileClone.GetComponent<Missile>();
            var seeker = missileClone.GetComponent<OpticalSeekerCruiseMissile>();
            if (missile == null || seeker == null)
            {
                throw new InvalidOperationException("Cloned Ballista prefab is missing its Missile or OpticalSeekerCruiseMissile component.");
            }
            RemoveVlsBooster(missileClone, seeker, missile);

            var rigidbody = missileClone.GetComponent<Rigidbody>();
            if (rigidbody != null)
            {
                rigidbody.mass = MissileMassKg;
            }
            HalberdCloner.SetField(missile, "mass", MissileMassKg);
            // The folded-wing terminal dash must not bleed its speed; the donor
            // sea-skimmer carries a 0.5 supersonic penalty sized for its wings.
            HalberdCloner.SetField(missile, "supersonicDrag", SupersonicDrag);

            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            if (motors == null || motors.Length == 0)
            {
                throw new InvalidOperationException("Cloned Ballista missile has no cruise motor.");
            }
            motors = CreateMotorProfile(motors);
            HalberdCloner.SetField(missile, "motors", motors);
            ConfigureCruiseMotor(motors.GetValue(0));
            ConfigureSprintMotor(motors.GetValue(1));
            HalberdCloner.NormalizePartMasses(missileClone, MissileMassKg);

            // Terrain-following cruise altitude, terminal loft trigger at 10 km,
            // and the terminal target-speed ceiling. The stock top attack is
            // forced to 100 percent probability so every shot pitches up. The
            // donor's vanilla TerminalBoost is zeroed: the 14 kN sprint stage
            // is the sole terminal rocket, so the dash no longer double-thrusts
            // inside 8 km.
            HalberdCloner.SetField(seeker, "altitudeTarget", CruiseAltitude);
            HalberdCloner.SetField(seeker, "terminalRange", TerminalRange);
            HalberdCloner.SetField(seeker, "maxTargetSpeed", TerminalMaxTargetSpeed);
            HalberdCloner.SetNestedField(seeker, "topAttack", "probability", 1f);
            HalberdCloner.SetNestedField(seeker, "terminalBoost", "Amount", 0f);

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
            HalberdCloner.SetField(infoClone, "maxSpeed", -1f);
            HalberdCloner.SetField(infoClone, "overHorizon", true);
            HalberdCloner.SetNestedField(infoClone, "effectiveness", "antiSurface", 0.814f);
            infoClone.SetMassPerRound(MissileMassKg);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxRange", MaxRange);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxAltitude", TargetMaxAltitude);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "maxSpeed", TargetMaxSpeed);
            HalberdCloner.SetNestedField(infoClone, "targetRequirements", "minValue", TargetMinValue);
            HalberdCloner.SetField(missile, "info", infoClone);

            var rackClone = HalberdCloner.CloneInactive(sourceMount.prefab, MountJsonKey);
            var mountedMissile = rackClone.GetComponentInChildren<MountedMissile>(true);
            if (mountedMissile == null)
            {
                throw new InvalidOperationException("Cloned Ballista rack prefab has no MountedMissile.");
            }
            mountedMissile.info = infoClone;

            var mountClone = UnityEngine.Object.Instantiate(sourceMount);
            mountClone.name = MountJsonKey;
            mountClone.jsonKey = MountJsonKey;
            mountClone.info = infoClone;
            mountClone.prefab = rackClone;
            mountClone.mountName = WeaponName;
            mountClone.Initialize();

            bool geometryApplied = EnableCustomGeometry && CustomGeometryLoader.TryApply(
                Logger,
                HalberdCloner.GeometryResourceName,
                missileClone,
                rackClone,
                MissileJsonKey,
                MountJsonKey);
            if (geometryApplied)
            {
                AlignCruiseFx(missileClone.transform);
            }
            SetupSprintFx(missileClone, sourceMount);

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
            // Mirror every AGM-68 carriage variant so the Ballista is offered
            // wherever the AGM-68 is, including internal-bay Multirole fits.
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_internal");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_internalx2");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_internalx4");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_internalx6");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_internalx8");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavy_triple");
            hardpointSets += HalberdCloner.AddToMirroredHardpoints(mountClone, "AGM_heavyx2");
            logger.LogInfo(
                $"[Phase 2D] AGM-110 Ballista registered: missile '{MissileJsonKey}' (index {definitionIndex}, " +
                $"hash {prefabHash:X8}), mount '{MountJsonKey}' (index {mountIndex}), " +
                $"mass {definitionClone.mass:F0} kg, cost {infoClone.costPerRound:F2}, range {MaxRange / 1000f:F0} km, " +
                $"cruise {CruiseThrust / 1000f:F1} kN to Mach {CruiseTopSpeed / 340f:F2} after {CruiseIgnitionDelay:F1} s drop delay, " +
                $"loft at {TerminalRange / 1000f:F0} km, wing fold + {SprintThrust / 1000f:F0} kN sprint by {FoldDelaySeconds:F1} s or {FoldRange / 1000f:F1} km, " +
                $"added to {hardpointSets} hardpoint sets.");
        }

        private static void RemoveVlsBooster(GameObject missileClone, OpticalSeekerCruiseMissile seeker, Missile missile)
        {
            // The donor's VLSBooster self-destructs only when missile.owner is
            // already an Aircraft at initialize time, which is not guaranteed;
            // remove it outright so the Ballista always drops clean and lights
            // its jet after the delay.
            var booster = missileClone.GetComponentInChildren<VLSBooster>(true);
            if (booster != null)
            {
                HalberdCloner.SetField(seeker, "booster", null);
                if (booster.gameObject != missileClone)
                {
                    UnityEngine.Object.DestroyImmediate(booster.gameObject);
                }
                else
                {
                    UnityEngine.Object.DestroyImmediate(booster);
                }
                Logger?.LogInfo("[Phase 2D] Removed donor VLS booster; Ballista drops clean and ignites its cruise jet.");
            }
            missile.boosterIsAttached = false;
        }

        private static Array CreateMotorProfile(Array sourceMotors)
        {
            object cruise = sourceMotors.GetValue(0);
            Type motorType = sourceMotors.GetType().GetElementType() ?? cruise.GetType();
            MethodInfo cloneMethod = typeof(object).GetMethod(
                "MemberwiseClone",
                BindingFlags.Instance | BindingFlags.NonPublic);
            if (cloneMethod == null)
            {
                throw new MissingMethodException(typeof(object).FullName, "MemberwiseClone");
            }
            object sprint = cloneMethod.Invoke(cruise, null);
            var profile = Array.CreateInstance(motorType, 2);
            profile.SetValue(cruise, 0);
            profile.SetValue(sprint, 1);
            return profile;
        }

        private static void ConfigureCruiseMotor(object motor)
        {
            HalberdCloner.ApplyMotor(motor, CruiseThrust, CruiseBurnTime, CruiseFuelMass, CruiseTopSpeed);
            HalberdCloner.SetField(motor, "delayTimer", CruiseIgnitionDelay);
            HalberdCloner.SetField(motor, "activated", false);
            HalberdCloner.SetField(motor, "burnRate", 0f);
        }

        private static void ConfigureSprintMotor(object motor)
        {
            HalberdCloner.ApplyMotor(motor, SprintThrust, SprintBurnTime, SprintFuelMass, SprintTopSpeed);
            HalberdCloner.SetField(motor, "delayTimer", SprintReserveDelay);
            HalberdCloner.SetField(motor, "activated", false);
            HalberdCloner.SetField(motor, "burnRate", 0f);
        }

        private static void SetupSprintFx(GameObject missileClone, WeaponMount carriageMount)
        {
            // The sprint stage was MemberwiseClone'd from the cruise jet, so it
            // referenced the SAME already-playing jet plume objects: igniting
            // it re-"Plays" FX that are already live and nothing visibly
            // changes. The sprint instead gets the carriage donor's (AGM-68)
            // own rocket plume, cloned from the Encyclopedia prefab and
            // configured for the engine's Play-on-Activate / Stop-on-burnout
            // lifecycle. The cruise jet plume is also stabilized: burnout only
            // stops looping systems, and a looping BURST-based emitter pulses
            // flare-and-fade every duration cycle, so bursts convert to a
            // steady rate.
            var missile = missileClone.GetComponent<Missile>();
            var motors = HalberdCloner.GetField(missile, "motors") as Array;
            if (motors == null || motors.Length < 2)
            {
                Logger?.LogWarning("[Phase 2D] No sprint motor for FX setup.");
                return;
            }
            var sprint = motors.GetValue(1);

            var cruiseFx = HalberdCloner.GetField(motors.GetValue(0), "particleSystems") as Array;
            if (cruiseFx != null)
            {
                var stabilized = new System.Collections.Generic.List<string>();
                foreach (var value in cruiseFx)
                {
                    if (value is ParticleSystem jetPlume)
                    {
                        stabilized.Add(StabilizeForBurn(jetPlume));
                    }
                }
                if (stabilized.Count > 0)
                {
                    Logger?.LogInfo($"[Phase 2D] Cruise plume stabilized: {string.Join("; ", stabilized)}");
                }
            }

            var rocketPrefab = carriageMount != null && carriageMount.info != null
                ? carriageMount.info.weaponPrefab
                : null;
            var rocketMissile = rocketPrefab == null ? null : rocketPrefab.GetComponent<Missile>();
            var rocketMotors = rocketMissile == null
                ? null
                : HalberdCloner.GetField(rocketMissile, "motors") as Array;
            var source = rocketMotors != null && rocketMotors.Length > 0
                ? HalberdCloner.GetField(rocketMotors.GetValue(0), "particleSystems") as Array
                : null;
            if (source == null || source.Length == 0)
            {
                Logger?.LogWarning("[Phase 2D] AGM-68 rocket FX unavailable; sprint plume skipped.");
                return;
            }

            var tailZ = -MissileLength * 0.5f;
            var clones = new System.Collections.Generic.List<ParticleSystem>();
            foreach (var value in source)
            {
                if (!(value is ParticleSystem original))
                {
                    continue;
                }
                var copy = UnityEngine.Object.Instantiate(
                    original.gameObject, missileClone.transform, false).GetComponent<ParticleSystem>();
                copy.gameObject.name = "Sprint" + original.gameObject.name;
                var position = copy.transform.localPosition;
                position.z = tailZ;
                copy.transform.localPosition = position;
                StabilizeForBurn(copy);
                copy.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                clones.Add(copy);
            }
            if (clones.Count == 0)
            {
                Logger?.LogWarning("[Phase 2D] No AGM-68 rocket FX cloned for the sprint plume.");
                return;
            }
            HalberdCloner.SetField(sprint, "particleSystems", clones.ToArray());

            var rocketTrails = HalberdCloner.GetField(rocketMotors.GetValue(0), "trailEmitters") as Array;
            if (rocketTrails != null && rocketTrails.Length > 0)
            {
                var trails = new System.Collections.Generic.List<TrailEmitter>();
                foreach (var value in rocketTrails)
                {
                    if (!(value is TrailEmitter trail) || trail.gameObject == rocketPrefab)
                    {
                        continue;
                    }
                    var trailCopy = UnityEngine.Object.Instantiate(
                        trail.gameObject, missileClone.transform, false).GetComponent<TrailEmitter>();
                    trailCopy.gameObject.name = "Sprint" + trail.gameObject.name;
                    var trailPosition = trailCopy.transform.localPosition;
                    trailPosition.z = tailZ;
                    trailCopy.transform.localPosition = trailPosition;
                    trailCopy.StopTrail();
                    trails.Add(trailCopy);
                }
                if (trails.Count > 0)
                {
                    HalberdCloner.SetField(sprint, "trailEmitters", trails.ToArray());
                }
            }

            // The cloned motor also shares the jet's audio and lights; silence
            // them so the sprint lights only its own plume.
            HalberdCloner.SetField(sprint, "audioSources", Array.Empty<AudioSource>());
            HalberdCloner.SetField(sprint, "lights", Array.Empty<Light>());
            Logger?.LogInfo(
                $"[Phase 2D] Sprint FX: {clones.Count} AGM-68 rocket plume system(s), " +
                $"cruise jet plume stabilized.");
        }

        private static string StabilizeForBurn(ParticleSystem plume)
        {
            // Burnout(forceStopEffects: false) only stops looping systems, so
            // the plume must loop. But a looping BURST emitter pulses
            // flare-and-fade every duration cycle; convert bursts to an
            // equivalent steady rate. A sparse converted rate (or a short
            // particle lifetime) still reads as flicker, so the rate is
            // floored and lifetime extended until particles overlap into a
            // continuous flame.
            var main = plume.main;
            main.loop = true;
            var emission = plume.emission;
            float rate = emission.rateOverTime.mode == ParticleSystemCurveMode.Constant
                ? emission.rateOverTime.constant
                : 0f;
            int bursts = emission.burstCount;
            if (bursts > 0)
            {
                float duration = Mathf.Max(main.duration, 0.01f);
                float total = 0f;
                for (int i = 0; i < bursts; i++)
                {
                    var burstCurve = emission.GetBurst(i).count;
                    total += burstCurve.mode == ParticleSystemCurveMode.Constant
                        ? burstCurve.constant
                        : burstCurve.constantMax;
                }
                rate += total / duration;
                emission.SetBursts(Array.Empty<ParticleSystem.Burst>());
            }
            rate = Mathf.Max(rate, 40f);
            emission.rateOverTime = rate;
            float lifetime = main.startLifetime.constantMax > 0f
                ? main.startLifetime.constantMax
                : 0.3f;
            main.startLifetimeMultiplier = 1.6f;
            return $"{plume.gameObject.name}: bursts {bursts} -> rate {rate:F0}/s, " +
                   $"lifetime {lifetime:F2} -> {lifetime * 1.6f:F2} s";
        }

        private static void AlignCruiseFx(Transform missileTransform)
        {
            var tailWorld = missileTransform.TransformPoint(0f, 0f, -MissileLength * 0.5f);
            int moved = 0;
            foreach (var particleSystem in missileTransform.GetComponentsInChildren<ParticleSystem>(true))
            {
                var name = particleSystem.gameObject.name;
                if (name.IndexOf("Booster", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    continue;
                }
                if (name.IndexOf("Fire", StringComparison.OrdinalIgnoreCase) < 0 &&
                    name.IndexOf("smoke", StringComparison.OrdinalIgnoreCase) < 0 &&
                    name.IndexOf("trail", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    continue;
                }
                particleSystem.transform.position = tailWorld;
                moved++;
            }
            if (moved == 0)
            {
                Logger.LogWarning("[Phase 2D] No cruise FX transforms found for exhaust alignment.");
            }
            else
            {
                Logger.LogInfo($"[Phase 2D] Aligned {moved} cruise FX transform(s) to the exhaust datum.");
            }
        }
    }
}
