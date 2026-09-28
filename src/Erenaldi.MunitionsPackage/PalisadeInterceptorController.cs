using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class PalisadeInterceptorController : MonoBehaviour
    {
        private enum FlightPhase
        {
            Ejecting,
            SnapTurning,
            Powered,
            Coast
        }

        private const float EjectionDuration = 0.2f;
        private const float EjectionThrust = 2500f;
        private const float MinimumSnapDuration = 0.1f;
        private const float SnapTurnTimeout = 0.55f;
        private const float AlignmentThreshold = 5f;
        private const float SettledTurnRate = 60f;
        private const float MaximumAngularAcceleration = 60f;
        private const float MaximumTurnRate = 720f;
        private const float TvcDeflection = 35f;
        private const float TvcLimitG = 35f;
        private const float TvcRampDuration = 0.2f;
        private const float DebrisLifetime = 10f;
        private const float StandardGravity = 9.81f;
        private const string TurningCapName = "TurningCap";

        private static readonly System.Reflection.FieldInfo EngineCurrentThrustField =
            AccessTools.Field(typeof(Missile), "engineCurrentThrust");
        private static readonly System.Reflection.FieldInfo AimPointField =
            AccessTools.Field(typeof(Missile), "aimPoint");

        private Missile missile;
        private FlightPhase phase;
        private Vector3 commandDirection;
        private float poweredAt;
        private bool sawPoweredThrust;
        private bool burnoutLogged;

        internal bool SuppressVanillaFlightControl =>
            phase == FlightPhase.Ejecting || phase == FlightPhase.SnapTurning;

        private void Awake()
        {
            missile = GetComponent<Missile>();
            phase = FlightPhase.Ejecting;
            commandDirection = transform.forward;
            if (missile != null)
            {
                missile.boosterIsAttached = true;
            }
        }

        private void FixedUpdate()
        {
            if (missile == null || missile.disabled || missile.rb == null)
            {
                return;
            }

            UpdateCommandDirection();
            switch (phase)
            {
                case FlightPhase.Ejecting:
                    Eject();
                    break;
                case FlightPhase.SnapTurning:
                    SnapTurn();
                    break;
                case FlightPhase.Powered:
                    TrackPoweredFlight();
                    break;
            }
        }

        private void Eject()
        {
            if (missile.LocalSim)
            {
                missile.rb.AddForce(transform.forward * EjectionThrust);
            }
            if (missile.timeSinceSpawn < EjectionDuration)
            {
                return;
            }

            phase = FlightPhase.SnapTurning;
            Log($"ejection complete; snap-turn started at {Vector3.Angle(transform.forward, commandDirection):F1} deg error");
        }

        private void SnapTurn()
        {
            if (missile.LocalSim)
            {
                ApplySnapTurnTorque();
            }

            float elapsed = missile.timeSinceSpawn - EjectionDuration;
            float error = Vector3.Angle(transform.forward, commandDirection);
            float turnRate = missile.rb.angularVelocity.magnitude * Mathf.Rad2Deg;
            bool aligned = elapsed >= MinimumSnapDuration &&
                error <= AlignmentThreshold && turnRate <= SettledTurnRate;
            if (!aligned && elapsed < SnapTurnTimeout)
            {
                return;
            }

            ReleaseCap(aligned ? "aligned" : "timeout", error, turnRate);
        }

        private void ApplySnapTurnTorque()
        {
            Vector3 forward = transform.forward;
            float error = Vector3.Angle(forward, commandDirection) * Mathf.Deg2Rad;
            Vector3 axis = Vector3.Cross(forward, commandDirection);
            Vector3 desiredAngularVelocity = Vector3.zero;
            if (axis.sqrMagnitude > 1e-8f && error > 1e-4f)
            {
                axis.Normalize();
                float stoppingRate = Mathf.Sqrt(2f * MaximumAngularAcceleration * error);
                float requestedRate = Mathf.Min(MaximumTurnRate * Mathf.Deg2Rad, stoppingRate);
                desiredAngularVelocity = axis * requestedRate;
            }

            Vector3 angularAcceleration =
                (desiredAngularVelocity - missile.rb.angularVelocity) / Mathf.Max(Time.fixedDeltaTime, 0.001f);
            missile.rb.AddTorque(
                Vector3.ClampMagnitude(angularAcceleration, MaximumAngularAcceleration),
                ForceMode.Acceleration);
        }

        private void ReleaseCap(string reason, float error, float turnRate)
        {
            phase = FlightPhase.Powered;
            poweredAt = missile.timeSinceSpawn;
            missile.boosterIsAttached = false;
            JettisonCap();
            Log($"turning cap released ({reason}); t={missile.timeSinceSpawn:F2}s, " +
                $"error={error:F1} deg, rate={turnRate:F0} deg/s; main motor enabled");
        }

        private void TrackPoweredFlight()
        {
            float thrust = EngineCurrentThrustField != null
                ? (float)EngineCurrentThrustField.GetValue(missile)
                : 0f;
            if (thrust > 0f)
            {
                sawPoweredThrust = true;
                return;
            }
            if (!sawPoweredThrust)
            {
                return;
            }

            phase = FlightPhase.Coast;
            if (!burnoutLogged)
            {
                burnoutLogged = true;
                Log($"main motor burnout; t={missile.timeSinceSpawn:F2}s, speed={missile.speed:F0} m/s");
            }
        }

        internal void ApplyPoweredTvc()
        {
            if (phase != FlightPhase.Powered || !missile.LocalSim || missile.rb == null ||
                missile.speed >= PalisadeCloner.InterceptorTopSpeed)
            {
                return;
            }

            float thrust = EngineCurrentThrustField != null
                ? (float)EngineCurrentThrustField.GetValue(missile)
                : 0f;
            if (thrust <= 0f || commandDirection.sqrMagnitude < 0.5f)
            {
                return;
            }

            float lateralLimit = TvcLimitG * StandardGravity * missile.rb.mass;
            float forceLimitedAngle = Mathf.Asin(Mathf.Clamp01(lateralLimit / thrust)) * Mathf.Rad2Deg;
            float maxAngle = Mathf.Min(TvcDeflection, forceLimitedAngle);
            float ramp = Mathf.SmoothStep(
                0f,
                1f,
                Mathf.Clamp01((missile.timeSinceSpawn - poweredAt) / TvcRampDuration));
            float angle = Mathf.Min(Vector3.Angle(transform.forward, commandDirection), maxAngle) * ramp;
            Vector3 thrustDirection = Vector3.RotateTowards(
                transform.forward,
                commandDirection,
                angle * Mathf.Deg2Rad,
                0f).normalized;
            missile.rb.AddForce((thrustDirection - transform.forward) * thrust);
        }

        private void UpdateCommandDirection()
        {
            if (AimPointField == null)
            {
                return;
            }

            var aimPoint = (GlobalPosition)AimPointField.GetValue(missile);
            Vector3 direction = aimPoint - missile.GlobalPosition();
            if (direction.sqrMagnitude > 1e-6f)
            {
                commandDirection = direction.normalized;
            }
        }

        private void JettisonCap()
        {
            var cap = transform.Find(TurningCapName);
            if (cap == null)
            {
                return;
            }

            cap.name = TurningCapName + " (Jettisoned)";
            cap.SetParent(null, true);
            foreach (var collider in cap.GetComponentsInChildren<Collider>(true))
            {
                collider.enabled = false;
            }

            var debrisBody = cap.GetComponent<Rigidbody>() ?? cap.gameObject.AddComponent<Rigidbody>();
            debrisBody.mass = 4f;
            debrisBody.drag = 0.1f;
            debrisBody.angularDrag = 0.05f;
            debrisBody.interpolation = RigidbodyInterpolation.Interpolate;
            debrisBody.velocity = missile.rb.velocity - transform.forward * 12f;
            debrisBody.angularVelocity = missile.rb.angularVelocity +
                transform.TransformDirection(new Vector3(1.5f, -2f, 0.75f));
            Destroy(cap.gameObject, DebrisLifetime);
        }

        private void Log(string message)
        {
            if (missile.LocalSim)
            {
                PalisadeCloner.Logger?.LogInfo($"[Phase 4] Palisade interceptor: {message}.");
            }
        }
    }

    [HarmonyPatch(typeof(Missile), "Steering")]
    internal static class PalisadeInterceptorSteeringPatch
    {
        private static bool Prefix(Missile __instance)
        {
            var controller = __instance.GetComponent<PalisadeInterceptorController>();
            return controller == null || !controller.SuppressVanillaFlightControl;
        }
    }

    [HarmonyPatch(typeof(Missile), "ApplyAero")]
    internal static class PalisadeInterceptorAeroPatch
    {
        private static bool Prefix(Missile __instance)
        {
            var controller = __instance.GetComponent<PalisadeInterceptorController>();
            return controller == null || !controller.SuppressVanillaFlightControl;
        }

        private static void Postfix(Missile __instance)
        {
            __instance.GetComponent<PalisadeInterceptorController>()?.ApplyPoweredTvc();
        }
    }
}
