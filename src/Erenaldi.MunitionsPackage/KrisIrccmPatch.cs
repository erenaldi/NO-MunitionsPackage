using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class KrisIrccm
    {
        private const float MaximumPredictionAcceleration = 20f * 9.81f;
        private const float AccelerationPredictionTime = 0.5f;
        private const float ReacquireInterval = 0.25f;
        private const int MaximumTrackedFlares = 8;
        private const float FatigueWindow = 4f;
        private const float MaximumFatiguedPause = 1f;
        private const float DriftWanderRate = 1.5f;
        private const float MinimumSweepRate = 5f;
        private const float TrackRateBlend = 0.35f;

        internal static float ProcessingPause { get; set; } = 0.4f;
        internal static float OpticalTrackFov { get; set; } = 3f;
        internal static float ReacquireWindow { get; set; } = 2f;
        internal static float FlareDecoyGain { get; set; } = 1f;
        internal static float GimbalSlewRate { get; set; } = 120f;
        internal static float FatigueStep { get; set; } = 0.15f;
        internal static float SuspensionDrift { get; set; } = 20f;
        internal static float BeamRejectHorizon { get; set; } = 0.25f;

        private static readonly FieldInfo MissileField = AccessTools.Field(typeof(MissileSeeker), "missile");
        private static readonly FieldInfo TargetUnitField = AccessTools.Field(typeof(MissileSeeker), "targetUnit");
        private static readonly FieldInfo IRTargetField = AccessTools.Field(typeof(IRSeeker), "IRTarget");
        private static readonly FieldInfo KnownPositionField = AccessTools.Field(typeof(IRSeeker), "knownPos");
        private static readonly FieldInfo KnownVelocityField = AccessTools.Field(typeof(IRSeeker), "knownVel");
        private static readonly FieldInfo KnownPreviousVelocityField = AccessTools.Field(typeof(IRSeeker), "knownVelPrev");
        private static readonly FieldInfo KnownAccelerationField = AccessTools.Field(typeof(IRSeeker), "knownAccel");
        private static readonly FieldInfo DriftErrorField = AccessTools.Field(typeof(IRSeeker), "driftError");
        private static readonly FieldInfo DazzleAmountField = AccessTools.Field(typeof(IRSeeker), "dazzleAmount");
        private static readonly FieldInfo IRSourcesField = AccessTools.Field(typeof(Unit), "IRSources");
        private static readonly MethodInfo LoseLockMethod = AccessTools.Method(typeof(IRSeeker), "LoseLock");
        private static readonly MethodInfo RangeCoefMethod = AccessTools.Method(typeof(IRSeeker), "RangeCoef");
        private static readonly MethodInfo AspectCoefMethod = AccessTools.Method(typeof(IRSeeker), "AspectCoef");
        private static readonly MethodInfo BackgroundBrightnessMethod =
            AccessTools.Method(typeof(IRSeeker), "BackgroundBrightness");

        private sealed class SuspensionState
        {
            internal Unit Target;
            internal GlobalPosition Position;
            internal Vector3 Velocity;
            internal Vector3 Acceleration;
            internal Vector3 SeekerLOS;
            internal Vector3 DriftDirection;
            internal Vector3 DriftError;
            internal float StartedAt;
            internal float PausedDuration;
            internal float NextReacquireAt;
            internal int ReacquireAttempts;
            internal bool ReacquireWindowLogged;
            internal string LastFailure;
            internal readonly List<IRSource> Flares = new List<IRSource>();
        }

        private sealed class FatigueState
        {
            internal float LastEndedAt = float.NegativeInfinity;
            internal int ConsecutiveCount;
        }

        private sealed class FlareTrackState
        {
            internal GlobalPosition LastPosition;
            internal bool HasLastPosition;
            internal Vector3 Velocity;
        }

        private sealed class TrackRateState
        {
            internal Vector3 LastDirection;
            internal float LastTime = -1f;
            internal float SmoothedRate;
        }

        private static readonly Dictionary<int, SuspensionState> Suspensions =
            new Dictionary<int, SuspensionState>();
        private static readonly Dictionary<int, FatigueState> Fatigues =
            new Dictionary<int, FatigueState>();
        private static readonly Dictionary<int, FlareTrackState> FlareTracks =
            new Dictionary<int, FlareTrackState>();
        private static readonly Dictionary<int, TrackRateState> TrackRates =
            new Dictionary<int, TrackRateState>();
        private static readonly Dictionary<int, float> LastRejectedFlareLogAt =
            new Dictionary<int, float>();

        internal static bool BeginOrExtend(IRSeeker seeker, IRSource flare)
        {
            Missile missile = GetMissile(seeker);
            if (!KrisGuidance.IsKris(missile) || flare == null || !flare.flare)
            {
                return false;
            }

            int id = missile.GetInstanceID();
            float now = Time.timeSinceLevelLoad;
            if (!Suspensions.TryGetValue(id, out SuspensionState state))
            {
                Unit target = TargetUnitField?.GetValue(seeker) as Unit;
                if (target == null || target.disabled)
                {
                    return false;
                }

                IRSource trackedSource = IRTargetField?.GetValue(seeker) as IRSource;
                if (trackedSource != null && trackedSource.flare)
                {
                    // Already decoyed onto a flare: further dispensing cannot blind
                    // a seeker that is no longer tracking the aircraft.
                    return true;
                }
                if (trackedSource != null && !trackedSource.flare && trackedSource.transform != null &&
                    flare.transform != null)
                {
                    Vector3 trackedDirection = trackedSource.transform.position - missile.transform.position;
                    Vector3 flareDirection = flare.transform.position - missile.transform.position;
                    float flareSeparation = trackedDirection.sqrMagnitude > 1e-6f && flareDirection.sqrMagnitude > 1e-6f
                        ? Vector3.Angle(trackedDirection, flareDirection)
                        : float.PositiveInfinity;
                    if (flareSeparation > OpticalTrackFov)
                    {
                        if (!LastRejectedFlareLogAt.TryGetValue(id, out float lastLoggedAt) ||
                            now - lastLoggedAt >= 0.5f)
                        {
                            LastRejectedFlareLogAt[id] = now;
                            KrisCloner.Logger?.LogDebug(
                                $"[Phase 2C] Kris IRCCM rejected flare at {flareSeparation:F1} degrees " +
                                $"outside {OpticalTrackFov:F1}-degree optical half-angle.");
                        }
                        return true;
                    }
                    if (IsFastSeparatingFlare(missile, trackedDirection, flareDirection, flareSeparation, out float sweepRate, out float exitTime))
                    {
                        if (!LastRejectedFlareLogAt.TryGetValue(id, out float lastFastLogAt) ||
                            now - lastFastLogAt >= 0.5f)
                        {
                            LastRejectedFlareLogAt[id] = now;
                            KrisCloner.Logger?.LogDebug(
                                $"[Phase 2C] Kris IRCCM rejected fast-separating flare, leaving the " +
                                $"{OpticalTrackFov:F1}-degree window in {exitTime:F2} s at {sweepRate:F0} deg/s sweep.");
                        }
                        return true;
                    }
                }

                Vector3 acceleration = KnownAccelerationField != null
                    ? (Vector3)KnownAccelerationField.GetValue(seeker)
                    : Vector3.zero;
                if (!IsFinite(acceleration))
                {
                    acceleration = Vector3.zero;
                }
                if (!Fatigues.TryGetValue(id, out FatigueState fatigue))
                {
                    fatigue = new FatigueState();
                    Fatigues.Add(id, fatigue);
                }
                if (now - fatigue.LastEndedAt <= FatigueWindow)
                {
                    fatigue.ConsecutiveCount++;
                }
                else
                {
                    fatigue.ConsecutiveCount = 0;
                }
                float pausedDuration = Mathf.Min(
                    ProcessingPause + fatigue.ConsecutiveCount * FatigueStep,
                    Mathf.Max(ProcessingPause, MaximumFatiguedPause));

                state = new SuspensionState
                {
                    Target = target,
                    Position = target.GlobalPosition(),
                    Velocity = target.rb != null ? target.rb.velocity : Vector3.zero,
                    Acceleration = Vector3.ClampMagnitude(acceleration, MaximumPredictionAcceleration),
                    SeekerLOS = SafeDirection(missile, trackedSource),
                    DriftDirection = UnityEngine.Random.onUnitSphere,
                    StartedAt = now,
                    PausedDuration = pausedDuration,
                    NextReacquireAt = now + pausedDuration
                };
                Suspensions.Add(id, state);
                string fatigueSuffix = fatigue.ConsecutiveCount > 0
                    ? $" (salvo #{fatigue.ConsecutiveCount + 1})"
                    : string.Empty;
                KrisCloner.Logger?.LogDebug(
                    $"[Phase 2C] Kris IRCCM suspended optical tracking on '{target.unitName}' " +
                    $"for {pausedDuration:F2} s{fatigueSuffix}.");
            }

            if (!state.Flares.Contains(flare) && state.Flares.Count < MaximumTrackedFlares)
            {
                state.Flares.Add(flare);
            }
            return true;
        }

        internal static bool HandleSeek(IRSeeker seeker)
        {
            Missile missile = GetMissile(seeker);
            if (missile == null || !Suspensions.TryGetValue(missile.GetInstanceID(), out SuspensionState state))
            {
                return false;
            }
            if (missile.disabled || state.Target == null || state.Target.disabled)
            {
                RecordSuspensionEnd(missile.GetInstanceID(), Time.timeSinceLevelLoad);
                Suspensions.Remove(missile.GetInstanceID());
                KrisCloner.Logger?.LogDebug(
                    $"[Phase 2C] Kris IRCCM ended before optical recovery after " +
                    $"{Mathf.Max(0f, Time.timeSinceLevelLoad - state.StartedAt):F2} s: " +
                    (missile.disabled ? "missile disabled." : "target unavailable."));
                return false;
            }

            for (int i = state.Flares.Count - 1; i >= 0; i--)
            {
                IRSource flare = state.Flares[i];
                if (flare == null || flare.transform == null || flare.intensity <= 0f)
                {
                    state.Flares.RemoveAt(i);
                }
            }

            float now = Time.timeSinceLevelLoad;
            float elapsed = Mathf.Max(0f, now - state.StartedAt);
            ComputePrediction(state, elapsed, out GlobalPosition predictedPosition, out Vector3 predictedVelocity);
            UpdateSuspensionDrift(state, elapsed);
            GlobalPosition sensedPosition = predictedPosition + state.DriftError;
            Vector3 predictedDirection = sensedPosition.AsVector3() - missile.GlobalPosition().AsVector3();
            if (predictedDirection.sqrMagnitude > 1e-6f)
            {
                predictedDirection.Normalize();
                state.SeekerLOS = GimbalSlewRate > 0f
                    ? Vector3.RotateTowards(
                        state.SeekerLOS,
                        predictedDirection,
                        GimbalSlewRate * Mathf.Deg2Rad * Time.fixedDeltaTime,
                        0f).normalized
                    : predictedDirection;
            }
            else
            {
                predictedDirection = state.SeekerLOS;
            }
            if (elapsed >= state.PausedDuration)
            {
                if (!state.ReacquireWindowLogged)
                {
                    state.ReacquireWindowLogged = true;
                    KrisCloner.Logger?.LogDebug(
                        $"[Phase 2C] Kris IRCCM opened {OpticalTrackFov:F1}-degree optical reacquisition window " +
                        $"with {state.Flares.Count} active flare(s).");
                }
                if (now >= state.NextReacquireAt)
                {
                    state.NextReacquireAt = now + ReacquireInterval;
                    state.ReacquireAttempts++;
                    if (TryReacquire(
                        seeker,
                        missile,
                        state,
                        predictedDirection,
                        out bool decoyedToFlare,
                        out float trackAngle,
                        out float range,
                        out string failure))
                    {
                        RecordSuspensionEnd(missile.GetInstanceID(), now);
                        Suspensions.Remove(missile.GetInstanceID());
                        if (!decoyedToFlare)
                        {
                            KrisCloner.Logger?.LogDebug(
                                $"[Phase 2C] Kris IRCCM reacquired '{state.Target.unitName}' after {elapsed:F2} s " +
                                $"at {trackAngle:F2} degrees/{range:F0} m ({state.ReacquireAttempts} attempt(s)).");
                        }
                        return false;
                    }
                    state.LastFailure = failure;
                }
                if (elapsed >= ReacquireWindow)
                {
                    RecordSuspensionEnd(missile.GetInstanceID(), now);
                    Suspensions.Remove(missile.GetInstanceID());
                    if (LoseLockMethod != null)
                    {
                        LoseLockMethod.Invoke(seeker, null);
                    }
                    else
                    {
                        IRTargetField?.SetValue(seeker, null);
                        missile.SetTarget(null);
                    }
                    KrisGuidance.BeginSearch(missile, state.Target);
                    KrisCloner.Logger?.LogDebug(
                        $"[Phase 2C] Kris IRCCM widened to gimbal search after {elapsed:F2} s and " +
                        $"{state.ReacquireAttempts} narrow attempt(s); last result: {state.LastFailure ?? "no candidate"}.");
                    return true;
                }
            }

            missile.SetAimpoint(sensedPosition, predictedVelocity);

            // Preserve vanilla rail-clearance tangibility while optical updates are suspended.
            if (!missile.IsTangible() && missile.timeSinceSpawn > 0.1f &&
                (missile.owner == null ||
                 (FastMath.OutOfRange(missile.owner.GlobalPosition(), missile.GlobalPosition(), 50f) &&
                  Vector3.Dot(missile.owner.GlobalPosition() - missile.GlobalPosition(), missile.rb.velocity) < 0f)))
            {
                missile.SetTangible(true);
            }
            return true;
        }

        private static void ComputePrediction(
            SuspensionState state,
            float elapsed,
            out GlobalPosition predictedPosition,
            out Vector3 predictedVelocity)
        {
            float accelerationTime = Mathf.Min(elapsed, AccelerationPredictionTime);
            float constantVelocityTime = elapsed - accelerationTime;
            predictedVelocity = state.Velocity + state.Acceleration * accelerationTime;
            predictedPosition = state.Position +
                state.Velocity * accelerationTime +
                state.Acceleration * (0.5f * accelerationTime * accelerationTime) +
                predictedVelocity * constantVelocityTime;
        }

        private static void UpdateSuspensionDrift(SuspensionState state, float elapsed)
        {
            if (SuspensionDrift > 0f && elapsed > 0f)
            {
                state.DriftDirection = Vector3.Slerp(
                    state.DriftDirection,
                    UnityEngine.Random.onUnitSphere,
                    Mathf.Clamp01(Time.fixedDeltaTime * DriftWanderRate)).normalized;
                state.DriftError = state.DriftDirection * (SuspensionDrift * Mathf.Sqrt(elapsed));
            }
            else
            {
                state.DriftError = Vector3.zero;
            }
        }

        internal static bool IsSuspended(Missile missile)
        {
            return missile != null && Suspensions.ContainsKey(missile.GetInstanceID());
        }

        internal static bool TryGetPredictedTarget(
            Missile missile,
            out GlobalPosition position,
            out Vector3 velocity,
            out Vector3 acceleration)
        {
            if (missile != null &&
                Suspensions.TryGetValue(missile.GetInstanceID(), out SuspensionState state) &&
                state.Target != null && !state.Target.disabled)
            {
                float elapsed = Mathf.Max(0f, Time.timeSinceLevelLoad - state.StartedAt);
                ComputePrediction(state, elapsed, out GlobalPosition predictedPosition, out Vector3 predictedVelocity);
                float driftMagnitude = SuspensionDrift * Mathf.Sqrt(Mathf.Max(0f, elapsed));
                position = predictedPosition +
                    (driftMagnitude > 0f ? state.DriftDirection * driftMagnitude : Vector3.zero);
                velocity = predictedVelocity;
                acceleration = state.Acceleration;
                return true;
            }

            position = default;
            velocity = default;
            acceleration = default;
            return false;
        }

        internal static IRSource SelectNonFlareSource(Unit target, Missile missile)
        {
            if (target == null || missile == null || IRSourcesField?.GetValue(target) is not List<IRSource> sources)
            {
                return null;
            }

            IRSource best = null;
            float bestIntensity = float.MinValue;
            for (int i = 0; i < sources.Count; i++)
            {
                IRSource source = sources[i];
                if (source == null || source.flare || source.transform == null || source.intensity <= 0f ||
                    !IsWithinGimbalAndVisible(missile, source.transform))
                {
                    continue;
                }
                if (source.intensity > bestIntensity)
                {
                    best = source;
                    bestIntensity = source.intensity;
                }
            }
            return best;
        }

        internal static void Remove(Missile missile)
        {
            if (missile != null && Suspensions.TryGetValue(missile.GetInstanceID(), out SuspensionState state))
            {
                Suspensions.Remove(missile.GetInstanceID());
                KrisCloner.Logger?.LogDebug(
                    $"[Phase 2C] Kris IRCCM ended before optical recovery after " +
                    $"{Mathf.Max(0f, Time.timeSinceLevelLoad - state.StartedAt):F2} s: missile removed.");
            }
            if (missile != null)
            {
                LastRejectedFlareLogAt.Remove(missile.GetInstanceID());
                FlareTracks.Remove(missile.GetInstanceID());
                Fatigues.Remove(missile.GetInstanceID());
                TrackRates.Remove(missile.GetInstanceID());
            }
        }

        private static bool TryReacquire(
            IRSeeker seeker,
            Missile missile,
            SuspensionState state,
            Vector3 headDirection,
            out bool decoyedToFlare,
            out float trackAngle,
            out float range,
            out string failure)
        {
            decoyedToFlare = false;
            trackAngle = float.PositiveInfinity;
            range = 0f;
            failure = "no live IR source";
            Unit target = state.Target;
            if (target == null || missile == null ||
                IRSourcesField?.GetValue(target) is not List<IRSource> sources)
            {
                return false;
            }

            Vector3 missilePosition = missile.transform.position;
            Vector3 missileGlobalPosition = missile.GlobalPosition().AsVector3();
            if (headDirection.sqrMagnitude <= 1e-6f)
            {
                failure = "invalid seeker line of sight";
                return false;
            }
            headDirection.Normalize();

            IRSource winner = null;
            float bestScore = float.NegativeInfinity;
            float bestAircraftScore = float.NegativeInfinity;
            float closestHeadAngle = float.PositiveInfinity;
            bool foundInGimbal = false;
            for (int i = 0; i < sources.Count; i++)
            {
                IRSource candidate = sources[i];
                if (candidate == null || candidate.transform == null || candidate.intensity <= 0f)
                {
                    continue;
                }
                if (candidate.flare && FlareDecoyGain <= 0f)
                {
                    continue;
                }
                Vector3 toSource = candidate.transform.GlobalPosition().AsVector3() - missileGlobalPosition;
                if (toSource.sqrMagnitude <= 1e-6f ||
                    Vector3.Angle(missile.transform.forward, toSource) > KrisCloner.MaxAlignment)
                {
                    continue;
                }
                foundInGimbal = true;
                float headAngle = Vector3.Angle(headDirection, toSource);
                closestHeadAngle = Mathf.Min(closestHeadAngle, headAngle);
                if (headAngle > OpticalTrackFov)
                {
                    continue;
                }
                if (Physics.Linecast(missilePosition, candidate.transform.position, PhysicsLayers.StaticsMask))
                {
                    continue;
                }
                float score = EvaluateSourceScore(seeker, candidate, toSource.normalized, toSource.magnitude);
                if (!candidate.flare && score > bestAircraftScore)
                {
                    bestAircraftScore = score;
                }
                if (score > bestScore)
                {
                    bestScore = score;
                    winner = candidate;
                    trackAngle = headAngle;
                    range = toSource.magnitude;
                }
            }
            if (winner == null)
            {
                failure = !foundInGimbal
                    ? $"no source within {KrisCloner.MaxAlignment:F1}-degree gimbal"
                    : $"track error {closestHeadAngle:F1} exceeds {OpticalTrackFov:F1} degrees";
                return false;
            }

            IRTargetField?.SetValue(seeker, winner);
            TargetUnitField?.SetValue(seeker, target);
            KnownPositionField?.SetValue(seeker, winner.transform.GlobalPosition());
            if (winner.flare)
            {
                decoyedToFlare = true;
                KnownVelocityField?.SetValue(seeker, Vector3.zero);
                KnownPreviousVelocityField?.SetValue(seeker, Vector3.zero);
                KnownAccelerationField?.SetValue(seeker, Vector3.zero);
                DriftErrorField?.SetValue(seeker, Vector3.zero);
                DazzleAmountField?.SetValue(seeker, 0f);
                missile.SetTarget(null);
                FlareTracks[missile.GetInstanceID()] = new FlareTrackState
                {
                    LastPosition = winner.transform.GlobalPosition(),
                    HasLastPosition = true,
                    Velocity = Vector3.zero
                };
                KrisCloner.Logger?.LogDebug(
                    $"[Phase 2C] Kris IRCCM decoyed onto flare after " +
                    $"{Mathf.Max(0f, Time.timeSinceLevelLoad - state.StartedAt):F2} s at {trackAngle:F2} degrees/" +
                    $"{range:F0} m (flare score {bestScore:F2} vs aircraft {bestAircraftScore:F2}).");
            }
            else
            {
                Vector3 reacquiredVelocity = target.rb != null ? target.rb.velocity : Vector3.zero;
                KnownVelocityField?.SetValue(seeker, reacquiredVelocity);
                KnownPreviousVelocityField?.SetValue(seeker, reacquiredVelocity);
                KnownAccelerationField?.SetValue(seeker, Vector3.zero);
                DriftErrorField?.SetValue(seeker, Vector3.zero);
                DazzleAmountField?.SetValue(seeker, 0f);
                missile.SetTarget(target);
            }
            return true;
        }

        private static float EvaluateSourceScore(
            IRSeeker seeker,
            IRSource candidate,
            Vector3 losDirection,
            float distance)
        {
            float rangeCoef = 1f;
            if (RangeCoefMethod != null)
            {
                try
                {
                    rangeCoef = Mathf.Max(
                        (float)RangeCoefMethod.Invoke(seeker, new object[] { distance }), 1e-3f);
                }
                catch
                {
                    rangeCoef = 1f;
                }
            }
            float background = 0f;
            if (BackgroundBrightnessMethod != null)
            {
                try
                {
                    background = Mathf.Clamp01(
                        (float)BackgroundBrightnessMethod.Invoke(seeker, new object[] { losDirection }));
                }
                catch
                {
                    background = 0f;
                }
            }
            float aspect = 0f;
            if (!candidate.flare && AspectCoefMethod != null)
            {
                try
                {
                    aspect = Mathf.Max((float)AspectCoefMethod.Invoke(seeker, new object[] { losDirection }), 0f);
                }
                catch
                {
                    aspect = 1f;
                }
            }
            float intensity = candidate.intensity * (candidate.flare ? Mathf.Max(FlareDecoyGain, 0f) : 1f);
            return intensity * (1f + aspect) /
                Mathf.Max(rangeCoef + background * 2f, 1e-3f);
        }

        internal static void UpdateTrackRate(IRSeeker seeker, Missile missile)
        {
            if (missile == null || IsSuspended(missile))
            {
                return;
            }
            int id = missile.GetInstanceID();
            IRSource tracked = IRTargetField?.GetValue(seeker) as IRSource;
            if (tracked == null || tracked.flare || tracked.transform == null)
            {
                TrackRates.Remove(id);
                return;
            }
            Vector3 direction =
                tracked.transform.GlobalPosition().AsVector3() - missile.GlobalPosition().AsVector3();
            if (direction.sqrMagnitude < 1e-6f)
            {
                return;
            }
            direction.Normalize();
            float now = Time.timeSinceLevelLoad;
            if (!TrackRates.TryGetValue(id, out TrackRateState track))
            {
                TrackRates[id] = new TrackRateState { LastDirection = direction, LastTime = now };
                return;
            }
            float deltaTime = now - track.LastTime;
            if (deltaTime > 1e-3f)
            {
                float rate = Vector3.Angle(track.LastDirection, direction) / deltaTime;
                track.SmoothedRate = Mathf.Lerp(track.SmoothedRate, rate, TrackRateBlend);
                track.LastDirection = direction;
                track.LastTime = now;
            }
        }

        private static bool IsFastSeparatingFlare(
            Missile missile,
            Vector3 trackedDirection,
            Vector3 flareDirection,
            float separation,
            out float sweepRate,
            out float exitTime)
        {
            sweepRate = 0f;
            exitTime = float.PositiveInfinity;
            if (BeamRejectHorizon <= 0f ||
                !TrackRates.TryGetValue(missile.GetInstanceID(), out TrackRateState track) ||
                track.SmoothedRate <= MinimumSweepRate)
            {
                return false;
            }
            sweepRate = track.SmoothedRate;
            exitTime = (OpticalTrackFov - separation) / sweepRate;
            return exitTime <= BeamRejectHorizon;
        }

        internal static void UpdateFlareLock(IRSeeker seeker, Missile missile)
        {
            if (missile == null || IsSuspended(missile))
            {
                return;
            }
            int id = missile.GetInstanceID();
            IRSource locked = IRTargetField?.GetValue(seeker) as IRSource;
            if (locked == null || !locked.flare)
            {
                FlareTracks.Remove(id);
                return;
            }
            if (locked.transform == null || locked.intensity <= 0f)
            {
                FlareTracks.Remove(id);
                Unit target = TargetUnitField?.GetValue(seeker) as Unit;
                if (LoseLockMethod != null)
                {
                    LoseLockMethod.Invoke(seeker, null);
                }
                else
                {
                    IRTargetField?.SetValue(seeker, null);
                    missile.SetTarget(null);
                }
                if (target != null)
                {
                    KrisGuidance.BeginSearch(missile, target);
                }
                KrisCloner.Logger?.LogDebug(
                    "[Phase 2C] Kris IRCCM flare lock ended after burnout; widened to gimbal search.");
                return;
            }
            if (!FlareTracks.TryGetValue(id, out FlareTrackState track))
            {
                track = new FlareTrackState();
                FlareTracks.Add(id, track);
            }
            GlobalPosition position = locked.transform.GlobalPosition();
            if (track.HasLastPosition)
            {
                float deltaTime = Mathf.Max(Time.fixedDeltaTime, 1e-4f);
                track.Velocity = (position.AsVector3() - track.LastPosition.AsVector3()) / deltaTime;
            }
            track.LastPosition = position;
            track.HasLastPosition = true;
        }

        internal static bool TryGetFlareVelocity(Missile missile, out Vector3 velocity)
        {
            if (missile != null && FlareTracks.TryGetValue(missile.GetInstanceID(), out FlareTrackState track))
            {
                velocity = track.Velocity;
                return true;
            }
            velocity = default;
            return false;
        }

        private static Vector3 SafeDirection(Missile missile, IRSource source)
        {
            if (source != null && source.transform != null)
            {
                Vector3 direction =
                    source.transform.GlobalPosition().AsVector3() - missile.GlobalPosition().AsVector3();
                if (direction.sqrMagnitude > 1e-6f)
                {
                    return direction.normalized;
                }
            }
            return missile.transform.forward;
        }

        private static void RecordSuspensionEnd(int missileId, float now)
        {
            if (!Fatigues.TryGetValue(missileId, out FatigueState fatigue))
            {
                fatigue = new FatigueState();
                Fatigues.Add(missileId, fatigue);
            }
            fatigue.LastEndedAt = now;
        }

        private static bool IsWithinGimbalAndVisible(Missile missile, Transform source)
        {
            Vector3 toSource = source.position - missile.transform.position;
            return toSource.sqrMagnitude > 1e-6f &&
                Vector3.Angle(missile.transform.forward, toSource) <= KrisCloner.MaxAlignment &&
                !Physics.Linecast(missile.transform.position, source.position, PhysicsLayers.StaticsMask);
        }

        private static bool IsFinite(Vector3 value)
        {
            return !float.IsNaN(value.x) && !float.IsInfinity(value.x) &&
                !float.IsNaN(value.y) && !float.IsInfinity(value.y) &&
                !float.IsNaN(value.z) && !float.IsInfinity(value.z);
        }

        private static Missile GetMissile(IRSeeker seeker)
        {
            return MissileField?.GetValue(seeker) as Missile;
        }
    }

    [HarmonyPatch(typeof(IRSeeker), "IRSeeker_OnTargetFlare")]
    internal static class KrisFlareTrackingSuspensionPatch
    {
        private static bool Prefix(IRSeeker __instance, IRSource source)
        {
            return !KrisIrccm.BeginOrExtend(__instance, source);
        }
    }
}
