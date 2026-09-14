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
        // Supersonic drag restored to the earlier 0.15 tuning (user direction):
        // the sprint cap is raised and drag re-limits the dash naturally
        // instead of the hard topSpeed clamp doing it alone.
        internal const float SupersonicDrag = 0.15f;
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
        // Sprint velocity ceiling raised (user direction): with drag restored
        // to 0.15 the dash self-limits near Mach 3 at terminal altitude
        // instead of the hard 780 m/s clamp.
        internal const float SprintTopSpeed = 1050f;
        internal const float TerminalRange = 10000f;
        internal const float FoldRange = 7500f;
        // Loft duration: 4 s of aim-raised climb before the wing fold and
        // sprint ignition (user direction: 2 s longer than the prior pass).
        internal const float FoldDelaySeconds = 4f;
        // Aimpoint raise during the loft: the seeker's top attack is zeroed at
        // launch for every target inside its 10 km TooCloseRange (all our
        // shots), so the loft commands its own climb instead.
        internal const float LoftAimRise = 500f;
        // Aero reference area after the wing fold. Missile.ApplyAero scales
        // drag AND lift by currentFinArea; the donor deploys it to 2.5 m2 and
        // never re-folds it, so the sprint paid sea-skimmer drag. 0.12 m2 is
        // the Ballista's actual folded tail-control area.
        internal const float TerminalFinArea = 0.12f;
        internal const float CruiseAltitude = 110f;
        // Cruise plume size: the AGM-68 fire clone reduced by 80 percent from
        // the 0.8x first pass (user direction), keeping it discreet in chase
        // view while the sprint carries the full plume.
        internal const float CruisePlumeScale = 0.16f;
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
            SetupMotorFx(missileClone, sourceMount);

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

        private static void SetupMotorFx(GameObject missileClone, WeaponMount carriageMount)
        {
            // The donor's jet emitter is a 0.15 s three-burst ignition flash by
            // design; looping or rate-converting it always reads as flicker.
            // Both engine stages therefore get the carriage donor's (AGM-68)
            // own fire FX instead: a scaled-down clone as the continuous
            // cruise flame (the jet FX objects are disabled outright), and
            // full-scale fire + smoke + trail clones as the sprint plume. The
            // AGM-68 flame is a continuous rate emitter; the only change made
            // to it is clearing its one-shot ignition bursts (which would
            // replay every loop cycle) and looping it so burnout stops it.
            var missile = missileClone.GetComponent<Missile>();
            var motors = HalberdCloner.GetField(missile, "motors") as Array;
            if (motors == null || motors.Length < 2)
            {
                Logger?.LogWarning("[Phase 2D] No sprint motor for FX setup.");
                return;
            }

            var rocketPrefab = carriageMount != null && carriageMount.info != null
                ? carriageMount.info.weaponPrefab
                : null;
            var rocketMissile = rocketPrefab == null ? null : rocketPrefab.GetComponent<Missile>();
            var rocketMotors = rocketMissile == null
                ? null
                : HalberdCloner.GetField(rocketMissile, "motors") as Array;
            var rocketFx = rocketMotors != null && rocketMotors.Length > 0
                ? HalberdCloner.GetField(rocketMotors.GetValue(0), "particleSystems") as Array
                : null;
            if (rocketFx == null || rocketFx.Length == 0)
            {
                Logger?.LogWarning("[Phase 2D] AGM-68 rocket FX unavailable; plume setup skipped.");
                return;
            }

            var tailZ = -MissileLength * 0.5f;
            var cruiseFire = new System.Collections.Generic.List<ParticleSystem>();
            var sprintFire = new System.Collections.Generic.List<ParticleSystem>();
            foreach (var value in rocketFx)
            {
                if (!(value is ParticleSystem original))
                {
                    continue;
                }
                bool isFire = original.gameObject.name.IndexOf("Fire", StringComparison.OrdinalIgnoreCase) >= 0;
                var cruiseCopy = UnityEngine.Object.Instantiate(
                    original.gameObject, missileClone.transform, false).GetComponent<ParticleSystem>();
                cruiseCopy.gameObject.name = "Cruise" + original.gameObject.name;
                var cruisePosition = cruiseCopy.transform.localPosition;
                cruisePosition.z = tailZ;
                cruiseCopy.transform.localPosition = cruisePosition;
                cruiseCopy.transform.localScale = cruiseCopy.transform.localScale * CruisePlumeScale;
                StabilizeForBurn(cruiseCopy);
                cruiseCopy.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                if (isFire)
                {
                    cruiseFire.Add(cruiseCopy);
                }
                else
                {
                    cruiseCopy.gameObject.SetActive(false);
                }

                var sprintCopy = UnityEngine.Object.Instantiate(
                    original.gameObject, missileClone.transform, false).GetComponent<ParticleSystem>();
                sprintCopy.gameObject.name = "Sprint" + original.gameObject.name;
                var sprintPosition = sprintCopy.transform.localPosition;
                sprintPosition.z = tailZ;
                sprintCopy.transform.localPosition = sprintPosition;
                StabilizeForBurn(sprintCopy);
                sprintCopy.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                sprintFire.Add(sprintCopy);
            }

            // Retire the donor jet emitters: their objects are disabled so the
            // 0.15 s ignition flash can never play again.
            var cruiseMotor = motors.GetValue(0);
            var jetFx = HalberdCloner.GetField(cruiseMotor, "particleSystems") as Array;
            if (jetFx != null)
            {
                foreach (var value in jetFx)
                {
                    if (value is ParticleSystem jetPlume)
                    {
                        jetPlume.gameObject.SetActive(false);
                    }
                }
                HalberdCloner.SetField(cruiseMotor, "particleSystems", cruiseFire.ToArray());
                HalberdCloner.SetField(cruiseMotor, "audioSources", Array.Empty<AudioSource>());
                HalberdCloner.SetField(cruiseMotor, "lights", Array.Empty<Light>());
            }
            HalberdCloner.SetField(motors.GetValue(1), "particleSystems", sprintFire.ToArray());
            HalberdCloner.SetField(motors.GetValue(1), "audioSources", Array.Empty<AudioSource>());
            HalberdCloner.SetField(motors.GetValue(1), "lights", Array.Empty<Light>());

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
                    HalberdCloner.SetField(motors.GetValue(1), "trailEmitters", trails.ToArray());
                }
            }
            Logger?.LogInfo(
                $"[Phase 2D] Plume FX: {cruiseFire.Count} cruise flame(s) (AGM-68 fire, {CruisePlumeScale:F2}x), " +
                $"{sprintFire.Count} sprint system(s) (AGM-68 fire+smoke), donor jet emitters retired.");
        }

        private static string StabilizeForBurn(ParticleSystem plume)
        {
            // Burnout(forceStopEffects: false) only stops looping systems, so
            // the plume must loop. The one intervention allowed on the AGM-68
            // flame is clearing its one-shot ignition bursts: replayed every
            // loop cycle they read as pulses. Its own designed steady rate is
            // preserved untouched; only a purely burst emitter gets a derived
            // rate.
            var main = plume.main;
            main.loop = true;
            var emission = plume.emission;
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
                emission.SetBursts(Array.Empty<ParticleSystem.Burst>());
                if (emission.rateOverTime.mode == ParticleSystemCurveMode.Constant &&
                    emission.rateOverTime.constant <= 0.01f)
                {
                    emission.rateOverTime = Mathf.Max(total / duration, 25f);
                }
            }
            return $"{plume.gameObject.name}: bursts {bursts} cleared, loop on";
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
