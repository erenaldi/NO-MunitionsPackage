using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch(typeof(Missile), "MotorThrust")]
    internal static class KrisMotorThrustPatch
    {
        private static void Prefix(Missile __instance)
        {
            KrisDualPulseController.PrepareSecondPulse(__instance);
        }
    }

    internal static class KrisDualPulseController
    {
        private const float ReserveDelay = 3600f;

        internal enum PulseTwoTriggerMode
        {
            Auto,
            Halfway,
            MachFloor,
            Immediate
        }

        internal static PulseTwoTriggerMode PulseTwoTrigger { get; set; } =
            PulseTwoTriggerMode.Auto;
        internal static float CoastMachFloor { get; set; } = 1.5f;

        private const float TerminalAngleRampTime = 0.5f;

        private static readonly FieldInfo MotorsField = AccessTools.Field(typeof(Missile), "motors");
        private static readonly FieldInfo MotorStageField = AccessTools.Field(typeof(Missile), "motorStage");
        private static readonly FieldInfo MissileTargetField = AccessTools.Field(typeof(Missile), "target");
        private static readonly FieldInfo SeekerTargetField = AccessTools.Field(typeof(MissileSeeker), "targetUnit");
        private static readonly FieldInfo SeekerMissileField = AccessTools.Field(typeof(MissileSeeker), "missile");
        private sealed class PulseState
        {
            internal float InitialRange;
            internal bool Initialized;
            internal bool SecondPulsePrepared;
            internal bool TerminalPhase;
            internal float TerminalStartedAt = -1f;
        }

        private static readonly Dictionary<int, PulseState> States = new Dictionary<int, PulseState>();

        internal static void PrepareSecondPulse(Missile missile)
        {
            if (!KrisGuidance.IsKris(missile))
            {
                return;
            }

            PulseState state = GetState(missile);
            TrackFlight(missile, state);
            if (GetMotorStage(missile) != 1 || state.TerminalPhase)
            {
                return;
            }

            if (!state.SecondPulsePrepared)
            {
                object secondPulse = GetSecondPulse(missile);
                if (secondPulse == null)
                {
                    return;
                }
                HalberdCloner.SetField(secondPulse, "delayTimer", ReserveDelay);
                state.SecondPulsePrepared = true;
            }

            if (PulseTwoTrigger == PulseTwoTriggerMode.Immediate)
            {
                TriggerSecondPulse(missile, state, "immediate, continuous burn");
                return;
            }

            Unit target = GetTarget(missile);
            if (target == null || target.disabled || target.rb == null || missile.rb == null)
            {
                return;
            }

            float range = FastMath.Distance(missile.GlobalPosition(), target.GlobalPosition());

            // Halfway trigger: light pulse two once the missile has covered half
            // of its launch range toward the target.
            if ((PulseTwoTrigger == PulseTwoTriggerMode.Auto ||
                 PulseTwoTrigger == PulseTwoTriggerMode.Halfway) &&
                state.InitialRange > 0f && range <= state.InitialRange * 0.5f)
            {
                TriggerSecondPulse(missile, state, $"halfway to target at {range:F0} m");
                return;
            }

            // Speed floor: re-boost before coast drag bleeds away too much energy.
            if ((PulseTwoTrigger == PulseTwoTriggerMode.Auto ||
                 PulseTwoTrigger == PulseTwoTriggerMode.MachFloor) && CoastMachFloor > 0f)
            {
                float mach = missile.speed /
                    Mathf.Max(LevelInfo.GetSpeedOfSound(missile.transform.GlobalPosition().y), 1f);
                if (mach < CoastMachFloor)
                {
                    TriggerSecondPulse(
                        missile,
                        state,
                        $"Mach floor, Mach {mach:F2} < {CoastMachFloor:F2}");
                }
            }
        }

        internal static bool IsTerminalPhase(Missile missile)
        {
            return missile != null && States.TryGetValue(missile.GetInstanceID(), out PulseState state) &&
                state.TerminalPhase;
        }

        internal static bool TryGetPulseTwoElapsed(Missile missile, out float elapsed)
        {
            if (missile != null &&
                States.TryGetValue(missile.GetInstanceID(), out PulseState state) &&
                state.TerminalPhase && state.TerminalStartedAt >= 0f)
            {
                elapsed = Mathf.Max(0f, Time.timeSinceLevelLoad - state.TerminalStartedAt);
                return true;
            }
            elapsed = 0f;
            return false;
        }

        internal static float GetCommandedAngleLimit(Missile missile)
        {
            if (TryGetPulseTwoElapsed(missile, out float elapsed))
            {
                // Ramp the commanded-angle envelope open across the pulse-two
                // ignition so the guidance command does not step with the motor.
                float blend = Mathf.Clamp01(elapsed / TerminalAngleRampTime);
                return Mathf.Lerp(
                    KrisGuidance.MaxCommandedAngle,
                    KrisCloner.MaxAlignment,
                    Mathf.SmoothStep(0f, 1f, blend));
            }
            return KrisGuidance.MaxCommandedAngle;
        }

        internal static float GetTvcAdditionG(Missile missile)
        {
            int stage = GetMotorStage(missile);
            if (stage == 0)
            {
                return KrisCloner.FirstPulseTvcG;
            }
            if (stage == 1 && missile.rb != null)
            {
                return KrisCloner.FirstPulseTvcG *
                    (KrisCloner.SecondPulseThrust / KrisCloner.FirstPulseThrust) *
                    (KrisCloner.MissileMassKg / Mathf.Max(missile.rb.mass, 1f));
            }
            return 0f;
        }

        internal static bool PreventCoastSelfDestruct(Missile missile)
        {
            if (!KrisGuidance.IsKris(missile) || GetMotorStage(missile) != 1)
            {
                return false;
            }

            object secondPulse = GetSecondPulse(missile);
            Unit target = GetTarget(missile);
            if (secondPulse == null || target == null || target.disabled)
            {
                return false;
            }

            float delay = (float)HalberdCloner.GetField(secondPulse, "delayTimer");
            if (delay <= 0f)
            {
                return false;
            }
            if (missile.speed >= 200f && !missile.LosingGround() && !missile.MissedTarget())
            {
                return false;
            }

            TriggerSecondPulse(missile, GetState(missile), "coast self-destruct recovery");
            return true;
        }

        internal static void Remove(int instanceId)
        {
            States.Remove(instanceId);
        }

        private static PulseState GetState(Missile missile)
        {
            int id = missile.GetInstanceID();
            if (!States.TryGetValue(id, out PulseState state))
            {
                state = new PulseState();
                States.Add(id, state);
            }
            return state;
        }

        private static void InitializeState(Missile missile, PulseState state, Unit target)
        {
            state.InitialRange = target != null
                ? FastMath.Distance(missile.GlobalPosition(), target.GlobalPosition())
                : 0f;
            state.Initialized = true;
        }

        private static void TrackFlight(Missile missile, PulseState state)
        {
            if (!state.Initialized)
            {
                InitializeState(missile, state, GetTarget(missile));
            }
        }

        private static void TriggerSecondPulse(Missile missile, PulseState state, string reason)
        {
            object secondPulse = GetSecondPulse(missile);
            if (secondPulse == null || state.TerminalPhase)
            {
                return;
            }

            HalberdCloner.SetField(secondPulse, "delayTimer", 0f);
            state.TerminalPhase = true;
            state.TerminalStartedAt = Time.timeSinceLevelLoad;
            KrisCloner.Logger?.LogDebug(
                $"[Phase 2C] Kris second pulse triggered at {missile.GlobalPosition().y:F0} m, " +
                $"{missile.speed:F0} m/s ({reason}).");
        }

        private static int GetMotorStage(Missile missile)
        {
            return MotorStageField != null ? (int)MotorStageField.GetValue(missile) : -1;
        }

        private static object GetSecondPulse(Missile missile)
        {
            var motors = MotorsField?.GetValue(missile) as Array;
            return motors != null && motors.Length > 1 ? motors.GetValue(1) : null;
        }

        private static Unit GetTarget(Missile missile)
        {
            Unit target = MissileTargetField?.GetValue(missile) as Unit;
            if (target != null)
            {
                return target;
            }
            var seeker = missile.GetComponent<MissileSeeker>();
            return seeker != null ? SeekerTargetField?.GetValue(seeker) as Unit : null;
        }

        internal static Missile GetMissile(IRSeeker seeker)
        {
            return SeekerMissileField?.GetValue(seeker) as Missile;
        }
    }

    [HarmonyPatch(typeof(IRSeeker), "SlowChecks")]
    internal static class KrisReservePulseSelfDestructPatch
    {
        private static bool Prefix(IRSeeker __instance)
        {
            Missile missile = KrisDualPulseController.GetMissile(__instance);
            return missile == null || !KrisDualPulseController.PreventCoastSelfDestruct(missile);
        }
    }

    internal static class KrisFlightController
    {
        private const float StandardGravity = 9.81f;
        private const float FullAccelerationError = 6f;
        private const float AccelerationDeadband = 0.2f;
        private const float AccelerationSlewTime = 0.12f;
        private const float AttitudeResponseTime = 0.12f;
        private const float AngularVelocityDampingTime = 0.08f;
        private const float ThrustAuthorityRampTime = 0.3f;

        private static readonly FieldInfo EngineCurrentThrustField = AccessTools.Field(typeof(Missile), "engineCurrentThrust");
        private static readonly FieldInfo ThrottleField = AccessTools.Field(typeof(Missile), "throttle");
        private static readonly FieldInfo LiftCurveField = AccessTools.Field(typeof(Missile), "liftCurve");
        private static readonly FieldInfo DragCurveField = AccessTools.Field(typeof(Missile), "dragCurve");
        private static readonly FieldInfo AirDensityField = AccessTools.Field(typeof(Missile), "airDensity");
        private static readonly FieldInfo CurrentFinAreaField = AccessTools.Field(typeof(Missile), "currentFinArea");
        private static readonly FieldInfo SupersonicDragField = AccessTools.Field(typeof(Missile), "supersonicDrag");
        private static readonly FieldInfo MotorsField = AccessTools.Field(typeof(Missile), "motors");
        private static readonly FieldInfo ParticleSystemsField =
            AccessTools.Field(AccessTools.Inner(typeof(Missile), "Motor"), "particleSystems");

        private sealed class ControllerState
        {
            internal Vector3 CommandDirection;
            internal Vector3 AccelerationCommand;
            internal float ThrustOnAt;
            internal bool WasPowered;
            internal float LastCoastLogAt;
            internal Quaternion[] OriginalPlumeRotations;
            internal Vector3 AuthoredExhaustDirection;
        }

        private static readonly Dictionary<int, ControllerState> States = new Dictionary<int, ControllerState>();

        internal static void SetCommandDirection(Missile missile, Vector3 direction)
        {
            if (missile == null || direction.sqrMagnitude < 1e-6f)
            {
                return;
            }

            GetState(missile).CommandDirection = direction.normalized;
        }

        internal static float EstimateAvailableTurnRate(Missile missile)
        {
            if (missile == null || missile.rb == null)
            {
                return 0f;
            }

            Vector3 airVelocity = missile.rb.velocity -
                NetworkSceneSingleton<LevelInfo>.i.GetWind(missile.transform.GlobalPosition());
            float aeroCapacityG = CalculateAerodynamicCapacityG(missile, airVelocity);
            float currentThrust = (float)EngineCurrentThrustField.GetValue(missile);
            bool powered = currentThrust > 0f && missile.speed < KrisCloner.TopSpeed;
            float tvcAdditionG = powered ? KrisDualPulseController.GetTvcAdditionG(missile) : 0f;
            float availableG = Mathf.Min(KrisCloner.CombinedMaxG, aeroCapacityG + tvcAdditionG);
            return Mathf.Min(
                KrisCloner.SteeringMaxTurnRate * Mathf.Deg2Rad,
                availableG * StandardGravity / Mathf.Max(missile.speed, 1f));
        }

        internal static float GetCurrentThrust(Missile missile)
        {
            return missile != null && EngineCurrentThrustField != null
                ? (float)EngineCurrentThrustField.GetValue(missile)
                : 0f;
        }

        internal static void Remove(int instanceId)
        {
            States.Remove(instanceId);
        }

        internal static void Apply(Missile missile)
        {
            Rigidbody rb = missile.rb;
            if (rb == null)
            {
                return;
            }

            ControllerState state = GetState(missile);
            Vector3 commandDirection = state.CommandDirection.sqrMagnitude > 0.5f
                ? state.CommandDirection
                : missile.transform.forward;
            float currentThrust = (float)EngineCurrentThrustField.GetValue(missile);
            bool powered = currentThrust > 0f && missile.speed < KrisCloner.TopSpeed;
            if (powered && !state.WasPowered)
            {
                state.ThrustOnAt = Time.timeSinceLevelLoad;
            }
            state.WasPowered = powered;
            // Ramp TVC authority in across ignition so the endgame does not step
            // from zero to full thrust-vector force in one physics frame.
            float authorityScale = 1f;
            if (powered)
            {
                authorityScale = Mathf.SmoothStep(
                    0f,
                    1f,
                    Mathf.Clamp01((Time.timeSinceLevelLoad - state.ThrustOnAt) / ThrustAuthorityRampTime));
            }

            Vector3 airVelocity = rb.velocity - NetworkSceneSingleton<LevelInfo>.i.GetWind(missile.transform.GlobalPosition());
            Vector3 dragForce = Vector3.zero;
            Vector3 liftForce = Vector3.zero;
            if (airVelocity.sqrMagnitude > 1e-4f)
            {
                CalculateAerodynamicForces(missile, airVelocity, out liftForce, out dragForce);
            }

            float aeroCapacityG = CalculateAerodynamicCapacityG(missile, airVelocity);
            float tvcAdditionG = powered
                ? KrisDualPulseController.GetTvcAdditionG(missile) * authorityScale
                : 0f;
            float combinedCapacityG = Mathf.Min(
                KrisCloner.CombinedMaxG,
                aeroCapacityG + tvcAdditionG);
            float predictedBodyTurnRate = ApplyAttitudeControl(missile, commandDirection, combinedCapacityG);

            float aeroForceLimit = aeroCapacityG * rb.mass * StandardGravity;
            liftForce = Vector3.ClampMagnitude(liftForce, aeroForceLimit);

            Vector3 tvcCorrection = Vector3.zero;
            Vector3 augmentedTvcForce = Vector3.zero;
            Vector3 thrustDirection = missile.transform.forward;
            if (powered && rb.velocity.sqrMagnitude > 1f)
            {
                Vector3 velocityDirection = rb.velocity.normalized;
                float errorAngle = Vector3.Angle(velocityDirection, commandDirection);
                float bodyError = Vector3.Angle(missile.transform.forward, commandDirection) * Mathf.Deg2Rad;
                float velocityError = errorAngle * Mathf.Deg2Rad;
                float noseLead = Mathf.Max(0f, velocityError - bodyError);
                float coherentTurnRate = predictedBodyTurnRate + noseLead / AttitudeResponseTime;
                float attitudeLimitedG = missile.speed * coherentTurnRate / StandardGravity;
                float maneuverCapacityG = Mathf.Min(combinedCapacityG, attitudeLimitedG);
                Vector3 turnDirection = Vector3.ProjectOnPlane(commandDirection, velocityDirection);
                if (turnDirection.sqrMagnitude > 1e-6f && errorAngle > AccelerationDeadband)
                {
                    turnDirection.Normalize();
                    float commandFraction = Mathf.SmoothStep(
                        0f,
                        1f,
                        Mathf.InverseLerp(AccelerationDeadband, FullAccelerationError, errorAngle));
                    Vector3 rawAcceleration = turnDirection * (maneuverCapacityG * StandardGravity * commandFraction);
                    float slewRate = combinedCapacityG * StandardGravity / AccelerationSlewTime;
                    state.AccelerationCommand = Vector3.MoveTowards(
                        state.AccelerationCommand,
                        rawAcceleration,
                        slewRate * Time.fixedDeltaTime);
                }
                else
                {
                    float slewRate = combinedCapacityG * StandardGravity / AccelerationSlewTime;
                    state.AccelerationCommand = Vector3.MoveTowards(
                        state.AccelerationCommand,
                        Vector3.zero,
                        slewRate * Time.fixedDeltaTime);
                }

                // Keep the state purely centripetal as velocity rotates. Without
                // this projection, a retained world-space command can acquire an
                // axial component and spend TVC authority changing speed.
                state.AccelerationCommand = Vector3.ClampMagnitude(
                    Vector3.ProjectOnPlane(state.AccelerationCommand, velocityDirection),
                    maneuverCapacityG * StandardGravity);
                float commandFractionForNozzle = Mathf.Clamp01(
                    state.AccelerationCommand.magnitude / Mathf.Max(combinedCapacityG * StandardGravity, 0.001f));
                Vector3 desiredTvcForce = state.AccelerationCommand.sqrMagnitude > 1e-6f
                    ? state.AccelerationCommand.normalized * (tvcAdditionG * StandardGravity * rb.mass * commandFractionForNozzle)
                    : Vector3.zero;
                float deflection = KrisCloner.ThrustVectoring * commandFractionForNozzle;
                Vector3 nozzleTurnDirection = Vector3.ProjectOnPlane(state.AccelerationCommand, missile.transform.forward);
                if (nozzleTurnDirection.sqrMagnitude > 1e-6f && deflection > 0f)
                {
                    nozzleTurnDirection.Normalize();
                    float radians = deflection * Mathf.Deg2Rad;
                    thrustDirection =
                        missile.transform.forward * Mathf.Cos(radians) + nozzleTurnDirection * Mathf.Sin(radians);
                    thrustDirection.Normalize();
                    float effectiveThrust = currentThrust * (float)ThrottleField.GetValue(missile);
                    tvcCorrection = (thrustDirection - missile.transform.forward) * effectiveThrust;
                }

                Vector3 redirectedLateral = Vector3.ProjectOnPlane(tvcCorrection, velocityDirection);
                augmentedTvcForce = desiredTvcForce - redirectedLateral;
            }
            else
            {
                state.AccelerationCommand = Vector3.zero;
            }

            rb.AddForce(liftForce + dragForce + tvcCorrection + augmentedTvcForce);
            if (!powered && rb.mass > 0f && Time.timeSinceLevelLoad - state.LastCoastLogAt >= 2f)
            {
                state.LastCoastLogAt = Time.timeSinceLevelLoad;
                KrisCloner.Logger?.LogDebug(
                    $"[Phase 2C] Kris coast: speed {missile.speed:F0} m/s at {missile.GlobalPosition().y:F0} m, " +
                    $"drag decel {(dragForce.magnitude / rb.mass):F1} m/s².");
            }
            UpdatePlume(missile, thrustDirection);
        }

        private static ControllerState GetState(Missile missile)
        {
            int id = missile.GetInstanceID();
            if (!States.TryGetValue(id, out ControllerState state))
            {
                state = new ControllerState();
                States.Add(id, state);
            }
            return state;
        }

        private static float ApplyAttitudeControl(Missile missile, Vector3 commandDirection, float availableG)
        {
            Rigidbody rb = missile.rb;
            Vector3 forward = missile.transform.forward;
            float errorRadians = Vector3.Angle(forward, commandDirection) * Mathf.Deg2Rad;
            Vector3 rotationAxis = Vector3.Cross(forward, commandDirection);
            Vector3 desiredAngularVelocity = Vector3.zero;
            Vector3 turnAxis = Vector3.zero;
            if (rotationAxis.sqrMagnitude > 1e-8f && errorRadians > 1e-4f)
            {
                rotationAxis.Normalize();
                turnAxis = rotationAxis;
                float rateLimit = Mathf.Min(
                    KrisCloner.SteeringMaxTurnRate * Mathf.Deg2Rad,
                    availableG * StandardGravity / Mathf.Max(missile.speed, 1f));
                desiredAngularVelocity = rotationAxis * Mathf.Min(errorRadians / AttitudeResponseTime, rateLimit);
            }

            Vector3 angularAcceleration =
                (desiredAngularVelocity - rb.angularVelocity) / AngularVelocityDampingTime;
            angularAcceleration = Vector3.ClampMagnitude(angularAcceleration, KrisCloner.SteeringTorque);
            rb.AddTorque(angularAcceleration, ForceMode.Acceleration);
            if (turnAxis.sqrMagnitude < 0.5f)
            {
                return 0f;
            }

            Vector3 predictedAngularVelocity = rb.angularVelocity + angularAcceleration * Time.fixedDeltaTime;
            return Mathf.Max(0f, Vector3.Dot(predictedAngularVelocity, turnAxis));
        }

        private static float CalculateAerodynamicCapacityG(Missile missile, Vector3 airVelocity)
        {
            if (missile.rb == null || airVelocity.sqrMagnitude < 1e-4f)
            {
                return 0f;
            }

            float airDensity = (float)AirDensityField.GetValue(missile);
            float finArea = (float)CurrentFinAreaField.GetValue(missile);
            float maximumLift = KrisCloner.PeakLiftCoefficient *
                airDensity * airVelocity.sqrMagnitude * 0.5f * finArea;
            return Mathf.Min(
                KrisCloner.AerodynamicMaxG,
                maximumLift / (missile.rb.mass * StandardGravity));
        }

        private static void CalculateAerodynamicForces(
            Missile missile,
            Vector3 airVelocity,
            out Vector3 liftForce,
            out Vector3 dragForce)
        {
            float speedSquared = airVelocity.sqrMagnitude;
            float airDensity = (float)AirDensityField.GetValue(missile);
            float finArea = (float)CurrentFinAreaField.GetValue(missile);
            var liftCurve = LiftCurveField.GetValue(missile) as AnimationCurve;
            var dragCurve = DragCurveField.GetValue(missile) as AnimationCurve;
            if (liftCurve == null || dragCurve == null)
            {
                liftForce = Vector3.zero;
                dragForce = Vector3.zero;
                return;
            }

            Vector3 liftDirection = Vector3.Cross(
                Vector3.Cross(missile.transform.forward, airVelocity),
                airVelocity).normalized;
            float angleOfAttack = Vector3.Angle(missile.transform.forward, airVelocity) * Mathf.Deg2Rad;
            float dynamicPressureArea = airDensity * speedSquared * 0.5f * finArea;
            liftForce = liftDirection * (-liftCurve.Evaluate(angleOfAttack) * dynamicPressureArea);
            dragForce = -airVelocity.normalized * (dragCurve.Evaluate(angleOfAttack) * dynamicPressureArea);

            float supersonicDrag = (float)SupersonicDragField.GetValue(missile);
            if (supersonicDrag <= 0f)
            {
                return;
            }

            float speedOfSound = LevelInfo.GetSpeedOfSound(missile.transform.GlobalPosition().y);
            const float transonicWidth = 0.1f;
            if (missile.speed > (1f + transonicWidth) * speedOfSound)
            {
                dragForce *= 1f + supersonicDrag;
            }
            else if (missile.speed > (1f - transonicWidth) * speedOfSound)
            {
                float transonicDrag = supersonicDrag + 0.15f;
                float distance = Mathf.Min(Mathf.Abs((speedOfSound - missile.speed) / speedOfSound), transonicWidth);
                float blend = (transonicWidth - distance) / transonicWidth;
                dragForce *= 1f + blend * blend * blend * transonicDrag;
            }
        }

        private static void UpdatePlume(Missile missile, Vector3 thrustDirection)
        {
            var motors = MotorsField?.GetValue(missile) as Array;
            if (motors == null || motors.Length == 0)
            {
                return;
            }

            object motor = motors.GetValue(0);
            var particles = ParticleSystemsField?.GetValue(motor) as ParticleSystem[];
            if (particles == null || particles.Length == 0)
            {
                return;
            }

            ControllerState state = GetState(missile);
            if (state.OriginalPlumeRotations == null || state.OriginalPlumeRotations.Length != particles.Length)
            {
                state.OriginalPlumeRotations = new Quaternion[particles.Length];
                for (int i = 0; i < particles.Length; i++)
                {
                    state.OriginalPlumeRotations[i] = particles[i] != null
                        ? particles[i].transform.rotation
                        : Quaternion.identity;
                }
                // Anchor the plume to the missile-aft body axis instead of the
                // emitter transform's own forward: the FX's local rotation
                // convention is unknown, and deriving the emission axis from its
                // +z flipped the plume 180 degrees. Zero deflection now restores
                // the authored aft-streaming orientation exactly.
                state.AuthoredExhaustDirection = -missile.transform.forward;
            }

            // Aim the plume along the exhaust, opposite the thrust vector.
            Vector3 plumeDirection = -thrustDirection;
            Quaternion delta = Quaternion.FromToRotation(
                state.AuthoredExhaustDirection,
                plumeDirection);
            for (int i = 0; i < particles.Length; i++)
            {
                if (particles[i] == null)
                {
                    continue;
                }
                particles[i].transform.rotation = delta * state.OriginalPlumeRotations[i];
            }
        }
    }

    [HarmonyPatch(typeof(Missile), "ApplyAero")]
    internal static class KrisApplyAeroPatch
    {
        private static bool Prefix(Missile __instance)
        {
            if (!KrisGuidance.IsKris(__instance) || !__instance.LocalSim)
            {
                return true;
            }

            KrisFlightController.Apply(__instance);
            return false;
        }
    }
}
