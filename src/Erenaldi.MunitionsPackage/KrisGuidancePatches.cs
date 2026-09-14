using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class KrisGuidance
    {
        private const float SearchInterval = 0.25f;
        private const float SearchDuration = 8f;
        private const float JHookMinHorizontal = 50f;

        internal static bool JHookEnabled { get; set; }
        internal static float JHookLoftAltitude { get; set; } = 2762f;
        internal static float JHookDiveRange { get; set; } = 2550f;
        internal static float JHookBlendRange { get; set; } = 3825f;
        internal static float JHookTerminalFade { get; set; } = 2f;
        internal static float JHookTerminalShare { get; set; } = 0.4f;

        private const float MaxLeadTime = 5f;
        private const float MaxTerminalLeadTime = 12f;
        private const float MinClosingSpeed = 50f;
        private const float TargetAccelerationSmoothingTime = 0.15f;
        private const float TargetAccelerationPredictionTime = 1.25f;
        private const float MaximumTargetAcceleration = 100f;

        internal static bool LeadGuidanceEnabled { get; set; }
        internal static float LeadGain { get; set; } = 1f;
        internal static float MaxCommandedAngle { get; set; } = 40f;

        private static readonly FieldInfo SeekerIRTargetField = AccessTools.Field(typeof(IRSeeker), "IRTarget");
        private static readonly FieldInfo DriftErrorField = AccessTools.Field(typeof(IRSeeker), "driftError");
        private static readonly FieldInfo ErrorOffsetField = AccessTools.Field(typeof(IRSeeker), "errorOffset");
        private static readonly FieldInfo DazzleAmountField = AccessTools.Field(typeof(IRSeeker), "dazzleAmount");
        private static readonly FieldInfo PositionalErrorField = AccessTools.Field(typeof(IRSeeker), "positionalError");
        private static readonly FieldInfo KnownAccelerationField = AccessTools.Field(typeof(IRSeeker), "knownAccel");

        private sealed class SearchState
        {
            internal Unit Target;
            internal float StartedAt;
            internal float LastScanAt;
        }

        private static readonly Dictionary<int, SearchState> Searches = new Dictionary<int, SearchState>();
        private static readonly Dictionary<int, Vector3> SmoothedTargetAccelerations =
            new Dictionary<int, Vector3>();
        private sealed class TerminalTelemetryState
        {
            internal float LastLoggedAt;
            internal float ClosestRange = float.MaxValue;
        }
        private static readonly Dictionary<int, TerminalTelemetryState> TerminalTelemetry =
            new Dictionary<int, TerminalTelemetryState>();

        internal static bool IsKris(Missile missile)
        {
            return missile != null && missile.definition != null &&
                string.Equals(missile.definition.jsonKey, KrisCloner.MissileJsonKey, StringComparison.Ordinal);
        }

        internal static void BeginSearch(Missile missile, Unit target)
        {
            Searches[missile.GetInstanceID()] = new SearchState
            {
                Target = target,
                StartedAt = Time.timeSinceLevelLoad,
                LastScanAt = 0f
            };

            // Keep the selected target and warning synchronized while the seeker waits for a usable IR source.
            missile.SetTarget(target);
            WriteSearchAimpoint(missile, target);
        }

        private static void WriteSearchAimpoint(Missile missile, Unit target)
        {
            GlobalPosition knownPosition;
            if (missile.NetworkHQ == null || !missile.NetworkHQ.TryGetKnownPosition(target, out knownPosition))
            {
                // Rail-exit drift guard: the HQ lookup can lag at spawn; fall back
                // to the target's live transform instead of the stale forward aim.
                knownPosition = target.transform.GlobalPosition();
            }
            missile.SetAimpoint(knownPosition, target.rb != null ? target.rb.velocity : Vector3.zero);
        }

        internal static void UpdateSearch(IRSeeker seeker, Missile missile)
        {
            int id = missile.GetInstanceID();
            if (!Searches.TryGetValue(id, out var state))
            {
                return;
            }
            if (missile.disabled || state.Target == null || state.Target.disabled ||
                Time.timeSinceLevelLoad - state.StartedAt > SearchDuration)
            {
                Searches.Remove(id);
                return;
            }

            WriteSearchAimpoint(missile, state.Target);

            if (Time.timeSinceLevelLoad - state.LastScanAt < SearchInterval)
            {
                return;
            }
            state.LastScanAt = Time.timeSinceLevelLoad;

            Vector3 toTarget = state.Target.transform.position - missile.transform.position;
            if (toTarget.magnitude > missile.GetWeaponInfo().targetRequirements.maxRange ||
                Vector3.Angle(missile.transform.forward, toTarget) > KrisCloner.MaxAlignment ||
                !state.Target.HasIRSignature() ||
                Physics.Linecast(seeker.transform.position, state.Target.transform.position, PhysicsLayers.StaticsMask))
            {
                return;
            }

            // IRCCM acquisition only accepts a visible non-flare source from the selected aircraft.
            IRSource source = KrisIrccm.SelectNonFlareSource(state.Target, missile);
            if (source == null || source.transform == null)
            {
                return;
            }

            HalberdCloner.SetField(seeker, "IRTarget", source);
            HalberdCloner.SetField(seeker, "targetUnit", state.Target);
            HalberdCloner.SetField(seeker, "driftError", Vector3.zero);
            HalberdCloner.SetField(seeker, "dazzleAmount", 0f);
            HalberdCloner.SetField(seeker, "achievedLock", false);

            if (!source.flare)
            {
                var flareMethod = AccessTools.Method(typeof(IRSeeker), "IRSeeker_OnTargetFlare");
                if (flareMethod != null)
                {
                    var flareHandler = (Action<IRSource>)Delegate.CreateDelegate(
                        typeof(Action<IRSource>), seeker, flareMethod);
                    state.Target.onAddIRSource -= flareHandler;
                    state.Target.onAddIRSource += flareHandler;
                }
            }

            missile.SetTarget(source.flare ? null : state.Target);
            Searches.Remove(id);
            KrisCloner.Logger?.LogDebug(
                $"[Phase 2C] Kris acquired selected target '{state.Target.unitName}'" +
                (source.flare ? " through a flare source." : "."));
        }

        internal static void Remove(Missile missile)
        {
            if (missile != null)
            {
                Searches.Remove(missile.GetInstanceID());
                SmoothedTargetAccelerations.Remove(missile.GetInstanceID());
                if (TerminalTelemetry.TryGetValue(missile.GetInstanceID(), out TerminalTelemetryState telemetry))
                {
                    KrisCloner.Logger?.LogDebug(
                        $"[Phase 2C] Kris terminal guidance ended; closest sampled range {telemetry.ClosestRange:F1} m.");
                    TerminalTelemetry.Remove(missile.GetInstanceID());
                }
                KrisFlightController.Remove(missile.GetInstanceID());
                KrisDualPulseController.Remove(missile.GetInstanceID());
                KrisIrccm.Remove(missile);
            }
        }

        internal static void DeployFinArea(Missile missile)
        {
            // Vanilla holds missiles at 10% fin area until the seeker's guidance delay
            // elapses; the Kris needs full aerodynamic grip from the first physics frame.
            HalberdCloner.SetField(missile, "currentFinArea", HalberdCloner.GetField(missile, "finArea"));
            var seeker = missile.GetComponent<IRSeeker>();
            if (seeker != null)
            {
                HalberdCloner.SetField(seeker, "guidanceDelay", 0f);
            }
        }

        internal static GlobalPosition ReadAimpoint(Missile missile)
        {
            return (GlobalPosition)HalberdCloner.GetField(missile, "aimPoint");
        }

        internal static Vector3 ReadTargetVelocity(Missile missile)
        {
            return (Vector3)HalberdCloner.GetField(missile, "targetVel");
        }

        internal static GlobalPosition ComputeLeadAim(Missile missile, GlobalPosition seekerAim)
        {
            if (!LeadGuidanceEnabled || LeadGain <= 0f)
            {
                return seekerAim;
            }

            // During an IRCCM suspension the seeker is blind, but guidance must
            // keep steering on the frozen inertial prediction; skipping the lead
            // instead lets the intercept solution rotate away and grows an
            // unrecoverable command error.
            bool suspended = KrisIrccm.TryGetPredictedTarget(
                missile,
                out GlobalPosition baseAim,
                out Vector3 targetVelocity,
                out Vector3 suspendedAcceleration);

            var seeker = missile.GetComponent<IRSeeker>();
            bool flareLocked = false;
            if (!suspended)
            {
                var irTarget = seeker != null ? SeekerIRTargetField?.GetValue(seeker) as IRSource : null;
                bool seekerTracking = irTarget != null && irTarget.transform != null;
                flareLocked = seekerTracking && irTarget.flare;
                if (seekerTracking)
                {
                    // Guide on the locked IR source (aircraft source or decoy flare)
                    // rather than the aircraft unit itself; the seeker only knows
                    // what it can see.
                    baseAim = irTarget.transform.GlobalPosition();
                }
                if (flareLocked && KrisIrccm.TryGetFlareVelocity(missile, out Vector3 flareVelocity))
                {
                    targetVelocity = flareVelocity;
                }
                else
                {
                    targetVelocity = ReadTargetVelocity(missile);
                }
            }

            var missilePosition = missile.GlobalPosition();
            float dx = baseAim.x - missilePosition.x;
            float dy = baseAim.y - missilePosition.y;
            float dz = baseAim.z - missilePosition.z;
            float range = Mathf.Sqrt(dx * dx + dy * dy + dz * dz);
            if (range < 1f)
            {
                return seekerAim;
            }

            GlobalPosition aim;
            if (KrisDualPulseController.IsTerminalPhase(missile))
            {
                Vector3 targetAcceleration = suspended
                    ? suspendedAcceleration
                    : flareLocked
                        ? Vector3.zero
                        : SmoothTargetAcceleration(missile, seeker);
                Vector3 relativePosition = new Vector3(dx, dy, dz);
                float timeToGo = ComputeTerminalInterceptTime(
                    missile,
                    relativePosition,
                    targetVelocity,
                    targetAcceleration);
                float accelerationTime = Mathf.Min(timeToGo, TargetAccelerationPredictionTime);
                Vector3 lead = targetVelocity * timeToGo +
                    targetAcceleration * (
                        0.5f * accelerationTime * accelerationTime +
                        accelerationTime * Mathf.Max(timeToGo - accelerationTime, 0f));
                aim = baseAim + lead * LeadGain;
                LogTerminalTelemetry(
                    missile,
                    baseAim,
                    aim,
                    range,
                    timeToGo,
                    targetVelocity,
                    targetAcceleration);
            }
            else
            {
                Vector3 missileVelocity = missile.rb != null ? missile.rb.velocity : Vector3.zero;
                float closing = (
                    dx * (missileVelocity.x - targetVelocity.x) +
                    dy * (missileVelocity.y - targetVelocity.y) +
                    dz * (missileVelocity.z - targetVelocity.z)) / range;
                float timeToGo = Mathf.Clamp(range / Mathf.Max(closing, MinClosingSpeed), 0f, MaxLeadTime);
                aim = baseAim + targetVelocity * (timeToGo * LeadGain);
            }

            if (!suspended && seeker != null)
            {
                Vector3 drift = DriftErrorField != null ? (Vector3)DriftErrorField.GetValue(seeker) : Vector3.zero;
                Vector3 errorOffset = ErrorOffsetField != null ? (Vector3)ErrorOffsetField.GetValue(seeker) : Vector3.zero;
                float dazzle = DazzleAmountField != null ? (float)DazzleAmountField.GetValue(seeker) : 0f;
                float positional = PositionalErrorField != null ? (float)PositionalErrorField.GetValue(seeker) : 0f;
                aim += drift + errorOffset * (dazzle + positional);
            }

            if (aim.y < 0f)
            {
                aim = new GlobalPosition(aim.x, 0f, aim.z);
            }
            return aim;
        }

        private static Vector3 SmoothTargetAcceleration(Missile missile, IRSeeker seeker)
        {
            Vector3 measured = seeker != null && KnownAccelerationField != null
                ? (Vector3)KnownAccelerationField.GetValue(seeker)
                : Vector3.zero;
            measured = Vector3.ClampMagnitude(measured, MaximumTargetAcceleration);

            int id = missile.GetInstanceID();
            if (!SmoothedTargetAccelerations.TryGetValue(id, out Vector3 smoothed))
            {
                smoothed = measured;
            }
            else
            {
                float blend = 1f - Mathf.Exp(-Time.fixedDeltaTime / TargetAccelerationSmoothingTime);
                smoothed = Vector3.Lerp(smoothed, measured, blend);
            }
            SmoothedTargetAccelerations[id] = smoothed;
            return smoothed;
        }

        private static float ComputeTerminalInterceptTime(
            Missile missile,
            Vector3 relativePosition,
            Vector3 targetVelocity,
            Vector3 targetAcceleration)
        {
            float missileSpeed = Mathf.Max(missile.speed, 200f);
            float time = SolveInterceptTime(relativePosition, targetVelocity, missileSpeed);
            float turnRate = Mathf.Max(KrisFlightController.EstimateAvailableTurnRate(missile), 0.1f);
            Vector3 velocityDirection = missile.rb != null && missile.rb.velocity.sqrMagnitude > 1f
                ? missile.rb.velocity.normalized
                : missile.transform.forward;

            for (int i = 0; i < 3; i++)
            {
                float accelerationTime = Mathf.Min(time, TargetAccelerationPredictionTime);
                Vector3 futureOffset = relativePosition + targetVelocity * time +
                    targetAcceleration * (
                        0.5f * accelerationTime * accelerationTime +
                        accelerationTime * Mathf.Max(time - accelerationTime, 0f));
                if (futureOffset.sqrMagnitude < 1f)
                {
                    return 0f;
                }

                float travelTime = futureOffset.magnitude / missileSpeed;
                float turnAngle = Vector3.Angle(velocityDirection, futureOffset) * Mathf.Deg2Rad;
                float turnPenalty = 0.5f * turnAngle / turnRate;
                time = Mathf.Clamp(travelTime + turnPenalty, 0f, MaxTerminalLeadTime);
            }
            return time;
        }

        private static void LogTerminalTelemetry(
            Missile missile,
            GlobalPosition targetPosition,
            GlobalPosition aim,
            float range,
            float timeToGo,
            Vector3 targetVelocity,
            Vector3 targetAcceleration)
        {
            int id = missile.GetInstanceID();
            if (!TerminalTelemetry.TryGetValue(id, out TerminalTelemetryState telemetry))
            {
                telemetry = new TerminalTelemetryState();
                TerminalTelemetry.Add(id, telemetry);
            }
            telemetry.ClosestRange = Mathf.Min(telemetry.ClosestRange, range);

            float now = Time.timeSinceLevelLoad;
            if (now - telemetry.LastLoggedAt < 0.5f)
            {
                return;
            }
            telemetry.LastLoggedAt = now;

            Vector3 missilePosition = missile.GlobalPosition().AsVector3();
            Vector3 toTarget = targetPosition.AsVector3() - missilePosition;
            Vector3 missileVelocity = missile.rb != null ? missile.rb.velocity : Vector3.zero;
            float closing = range > 1f
                ? Vector3.Dot(missileVelocity - targetVelocity, toTarget / range)
                : 0f;
            Vector3 command = aim.AsVector3() - missilePosition;
            float commandAngle = missileVelocity.sqrMagnitude > 1f && command.sqrMagnitude > 1f
                ? Vector3.Angle(missileVelocity, command)
                : 0f;
            float leadDistance = FastMath.Distance(targetPosition, aim);
            float turnRate = KrisFlightController.EstimateAvailableTurnRate(missile) * Mathf.Rad2Deg;
            float thrust = KrisFlightController.GetCurrentThrust(missile);
            KrisCloner.Logger?.LogDebug(
                $"[Phase 2C] Kris terminal guidance: range {range:F0} m, tgo {timeToGo:F2} s, " +
                $"speed {missile.speed:F0} m/s, closing {closing:F0} m/s, lead {leadDistance:F0} m, " +
                $"target accel {targetAcceleration.magnitude / 9.81f:F1} g, command {commandAngle:F1} degrees, " +
                $"turn {turnRate:F0} deg/s, thrust {thrust / 1000f:F1} kN.");
        }

        private static float SolveInterceptTime(Vector3 relativePosition, Vector3 targetVelocity, float missileSpeed)
        {
            float a = targetVelocity.sqrMagnitude - missileSpeed * missileSpeed;
            float b = 2f * Vector3.Dot(relativePosition, targetVelocity);
            float c = relativePosition.sqrMagnitude;
            if (Mathf.Abs(a) < 1e-5f)
            {
                return b < -1e-5f
                    ? Mathf.Clamp(-c / b, 0f, MaxTerminalLeadTime)
                    : Mathf.Min(relativePosition.magnitude / missileSpeed, MaxTerminalLeadTime);
            }

            float discriminant = b * b - 4f * a * c;
            if (discriminant < 0f)
            {
                return Mathf.Min(relativePosition.magnitude / missileSpeed, MaxTerminalLeadTime);
            }

            float root = Mathf.Sqrt(discriminant);
            float first = (-b - root) / (2f * a);
            float second = (-b + root) / (2f * a);
            float time = float.MaxValue;
            if (first > 0f)
            {
                time = first;
            }
            if (second > 0f)
            {
                time = Mathf.Min(time, second);
            }
            return time < float.MaxValue
                ? Mathf.Clamp(time, 0f, MaxTerminalLeadTime)
                : Mathf.Min(relativePosition.magnitude / missileSpeed, MaxTerminalLeadTime);
        }

        internal static GlobalPosition LimitCommandedAngle(Missile missile, GlobalPosition aim)
        {
            float commandedAngle = KrisDualPulseController.GetCommandedAngleLimit(missile);
            if (commandedAngle <= 0f || missile.rb == null)
            {
                return aim;
            }

            Vector3 missilePosition = missile.GlobalPosition().AsVector3();
            Vector3 desired = new Vector3(aim.x - missilePosition.x, aim.y - missilePosition.y, aim.z - missilePosition.z);
            float range = desired.magnitude;
            Vector3 velocity = missile.rb.velocity;
            if (range < 1f || velocity.sqrMagnitude < 100f)
            {
                return aim;
            }

            Vector3 desiredDirection = desired / range;
            Vector3 velocityDirection = velocity.normalized;
            if (Vector3.Angle(velocityDirection, desiredDirection) <= commandedAngle)
            {
                return aim;
            }

            Vector3 limited = Vector3.RotateTowards(
                velocityDirection,
                desiredDirection,
                commandedAngle * Mathf.Deg2Rad,
                0f);
            return new GlobalPosition(missilePosition + limited * range);
        }

        internal static GlobalPosition ComputeJHookAim(Missile missile, GlobalPosition originalAim)
        {
            if (!JHookEnabled || JHookLoftAltitude <= 0f)
            {
                return originalAim;
            }

            var missilePosition = missile.GlobalPosition();
            float horizontalDistance = Mathf.Sqrt(
                (originalAim.x - missilePosition.x) * (originalAim.x - missilePosition.x) +
                (originalAim.z - missilePosition.z) * (originalAim.z - missilePosition.z));
            if (horizontalDistance < JHookMinHorizontal)
            {
                return originalAim;
            }

            float loftFactor = Mathf.Clamp01(
                (horizontalDistance - JHookDiveRange) /
                Mathf.Max(JHookBlendRange - JHookDiveRange, 1f));
            if (loftFactor <= 0f)
            {
                return originalAim;
            }

            // Hybridize the lofted arc with the terminal intercept across the
            // pulse-two ignition: the loft tapers to a residual share over the
            // fade window instead of vanishing, keeping the trajectory lofted
            // until the dive-range taper takes over near the target.
            if (KrisDualPulseController.TryGetPulseTwoElapsed(missile, out float pulseTwoElapsed))
            {
                float fade = JHookTerminalFade > 0f
                    ? Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(pulseTwoElapsed / JHookTerminalFade))
                    : 1f;
                loftFactor *= Mathf.Lerp(1f, JHookTerminalShare, fade);
                if (loftFactor <= 0f)
                {
                    return originalAim;
                }
            }

            // Fade the loft out when the target already sits above the missile.
            float altitudeDifference = originalAim.y - missilePosition.y;
            if (altitudeDifference > 0f)
            {
                loftFactor *= Mathf.Clamp01(1f - altitudeDifference / Mathf.Max(JHookLoftAltitude, 1f));
                if (loftFactor <= 0f)
                {
                    return originalAim;
                }
            }

            // Distance-proportional share of the loft keeps the climb angle near constant.
            float verticalBias = JHookLoftAltitude * loftFactor *
                Mathf.Clamp01(horizontalDistance / 8000f);
            return new GlobalPosition(originalAim.x, originalAim.y + verticalBias, originalAim.z);
        }
    }

    [HarmonyPatch(typeof(Missile), "Steering")]
    internal static class KrisJHookSteeringPatch
    {
        private static bool Prefix(Missile __instance)
        {
            if (!KrisGuidance.IsKris(__instance))
            {
                return true;
            }

            GlobalPosition seekerAim = KrisGuidance.ReadAimpoint(__instance);
            GlobalPosition guided = KrisGuidance.ComputeLeadAim(__instance, seekerAim);
            GlobalPosition biased = KrisGuidance.ComputeJHookAim(__instance, guided);
            GlobalPosition limited = KrisGuidance.LimitCommandedAngle(__instance, biased);
            Vector3 missilePosition = __instance.GlobalPosition().AsVector3();
            Vector3 commandDirection = new Vector3(
                limited.x - missilePosition.x,
                limited.y - missilePosition.y,
                limited.z - missilePosition.z);
            if (commandDirection.sqrMagnitude > 1e-6f)
            {
                KrisFlightController.SetCommandDirection(__instance, commandDirection);
            }
            return false;
        }
    }

    [HarmonyPatch(typeof(IRSeeker), "Initialize")]
    internal static class KrisSeekerInitializePatch
    {
        private static void Postfix(IRSeeker __instance, Unit target)
        {
            var missile = (Missile)HalberdCloner.GetField(__instance, "missile");
            if (!KrisGuidance.IsKris(missile) || target == null)
            {
                return;
            }

            var source = (IRSource)HalberdCloner.GetField(__instance, "IRTarget");
            if (source == null || source.transform == null)
            {
                KrisGuidance.BeginSearch(missile, target);
            }
        }
    }

    [HarmonyPatch(typeof(IRSeeker), "Seek")]
    internal static class KrisSeekerSeekPatch
    {
        private static bool Prefix(IRSeeker __instance)
        {
            return !KrisIrccm.HandleSeek(__instance);
        }

        private static void Postfix(IRSeeker __instance)
        {
            var missile = (Missile)HalberdCloner.GetField(__instance, "missile");
            if (!KrisGuidance.IsKris(missile))
            {
                return;
            }

            KrisIrccm.UpdateTrackRate(__instance, missile);
            KrisIrccm.UpdateFlareLock(__instance, missile);
            if (!KrisIrccm.IsSuspended(missile))
            {
                KrisGuidance.UpdateSearch(__instance, missile);
            }
        }
    }

    [HarmonyPatch(typeof(Missile), "StartMissile")]
    internal static class KrisTurnControlPatch
    {
        private static void Postfix(Missile __instance)
        {
            if (KrisGuidance.IsKris(__instance))
            {
                KrisGuidance.DeployFinArea(__instance);
            }
        }
    }

    [HarmonyPatch(typeof(Missile), nameof(Missile.UnitDisabled))]
    internal static class KrisGuidanceCleanupPatch
    {
        private static void Postfix(Missile __instance)
        {
            KrisGuidance.Remove(__instance);
        }
    }

    [HarmonyPatch(typeof(Unit), "OnDestroy")]
    internal static class KrisGuidanceDestroyCleanupPatch
    {
        private static void Postfix(Unit __instance)
        {
            if (__instance is Missile missile)
            {
                KrisGuidance.Remove(missile);
            }
        }
    }
}
