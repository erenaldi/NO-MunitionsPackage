using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class HalberdMotorControl
    {
        private sealed class TelemetryState
        {
            internal int LastStage = -1;
            internal bool SustainerStarted;
            internal bool LoggedMach25;
            internal bool LoggedMach35;
        }

        private static readonly Dictionary<int, TelemetryState> Telemetry = new Dictionary<int, TelemetryState>();
        private static readonly FieldInfo MotorStageField = AccessTools.Field(typeof(Missile), "motorStage");
        private static readonly FieldInfo CurrentMotorField = AccessTools.Field(typeof(Missile), "motor");
        private static readonly FieldInfo EngineCurrentThrustField = AccessTools.Field(typeof(Missile), "engineCurrentThrust");
        private static readonly FieldInfo SupersonicDragField = AccessTools.Field(typeof(Missile), "supersonicDrag");
        private static readonly FieldInfo MotorFuelMassField = AccessTools.Field(AccessTools.Inner(typeof(Missile), "Motor"), "fuelMass");
        private static readonly FieldInfo MotorTopSpeedField = AccessTools.Field(AccessTools.Inner(typeof(Missile), "Motor"), "topSpeed");
        private static bool controlDisabled;

        internal static bool IsHalberd(Missile missile)
        {
            return missile != null && missile.definition != null &&
                string.Equals(missile.definition.jsonKey, HalberdCloner.MissileJsonKey, StringComparison.Ordinal);
        }

        internal static void Prepare(Missile missile)
        {
            int stage = (int)MotorStageField.GetValue(missile);
            var motor = CurrentMotorField.GetValue(missile);
            if (stage != 1 || motor == null)
            {
                return;
            }

            float fuelMass = motor != null ? (float)MotorFuelMassField.GetValue(motor) : 0f;
            float burnRate = HalberdCloner.SustainerFuelMass / HalberdCloner.SustainerBurnTime;
            float elapsed = (HalberdCloner.SustainerFuelMass - Mathf.Max(fuelMass, 0f)) / burnRate;
            float acceleration = Mathf.Clamp01(elapsed / HalberdCloner.SustainerAccelerationTime);
            MotorTopSpeedField.SetValue(
                motor, Mathf.Lerp(HalberdCloner.BoosterTopSpeed, HalberdCloner.SustainerTopSpeed, acceleration));
        }

        internal static void Update(Missile missile)
        {
            int stage = (int)MotorStageField.GetValue(missile);
            var motor = CurrentMotorField.GetValue(missile);
            float currentThrust = (float)EngineCurrentThrustField.GetValue(missile);
            bool sustainerBurning = stage == 1 && motor != null && currentThrust > 0f;
            float supersonicDrag = stage >= 2
                ? HalberdCloner.CoastSupersonicDrag
                : sustainerBurning ? HalberdCloner.SustainerSupersonicDrag : HalberdCloner.BoosterSupersonicDrag;
            SupersonicDragField.SetValue(missile, supersonicDrag);
            HalberdBoosterJettison.TryJettison(missile, stage);

            if (!missile.LocalSim)
            {
                return;
            }

            int id = missile.GetInstanceID();
            if (!Telemetry.TryGetValue(id, out var state))
            {
                state = new TelemetryState();
                Telemetry.Add(id, state);
            }
            float speed = missile.rb != null ? missile.rb.velocity.magnitude : missile.speed;

            if (state.LastStage < 0)
            {
                Log(missile, "booster ignition", stage);
            }
            if (state.LastStage == 0 && stage == 1)
            {
                Log(missile, "booster burnout", stage);
            }
            if (sustainerBurning && !state.SustainerStarted)
            {
                state.SustainerStarted = true;
                Log(missile, "sustainer ignition; supersonic drag reduced to 0.25", stage);
            }
            if (state.LastStage == 1 && stage >= 2)
            {
                Log(missile, "sustainer burnout; supersonic drag set to 0.25", stage);
            }

            if (!state.LoggedMach25 && speed >= HalberdCloner.BoosterTopSpeed)
            {
                state.LoggedMach25 = true;
                Log(missile, "Mach 2.5 benchmark speed reached", stage);
            }
            if (!state.LoggedMach35 && speed >= HalberdCloner.SustainerTopSpeed)
            {
                state.LoggedMach35 = true;
                Log(missile, "Mach 3.5 benchmark speed reached", stage);
            }
            state.LastStage = stage;
        }

        internal static void Remove(Missile missile)
        {
            if (missile != null)
            {
                Telemetry.Remove(missile.GetInstanceID());
                HalberdBoosterJettison.Remove(missile);
            }
        }

        internal static void TryPrepare(Missile missile)
        {
            if (controlDisabled)
            {
                return;
            }

            try
            {
                Prepare(missile);
            }
            catch (Exception exception)
            {
                DisableControl(exception);
            }
        }

        internal static void TryUpdate(Missile missile)
        {
            if (controlDisabled)
            {
                return;
            }

            try
            {
                Update(missile);
            }
            catch (Exception exception)
            {
                DisableControl(exception);
            }
        }

        private static void DisableControl(Exception exception)
        {
            controlDisabled = true;
            HalberdCloner.Logger?.LogError(
                $"[Phase 2A] Halberd motor control disabled after an unexpected error: {exception}");
        }

        private static void Log(Missile missile, string message, int stage)
        {
            float altitude = missile.GlobalPosition().y;
            float soundSpeed = LevelInfo.GetSpeedOfSound(altitude);
            float speed = missile.rb != null ? missile.rb.velocity.magnitude : missile.speed;
            float mach = soundSpeed > 0f ? speed / soundSpeed : 0f;
            float mass = missile.rb != null ? missile.rb.mass : 0f;
            HalberdCloner.Logger?.LogInfo(
                $"[Phase 2A] Halberd motor telemetry: {message}; t={missile.timeSinceSpawn:F2}s, " +
                $"stage={stage}, speed={speed:F1}m/s (Mach {mach:F2}), altitude={altitude:F0}m, mass={mass:F1}kg.");
        }
    }

    [HarmonyPatch(typeof(Missile), "MotorThrust")]
    internal static class HalberdMotorThrustPatch
    {
        private static void Prefix(Missile __instance)
        {
            if (HalberdMotorControl.IsHalberd(__instance))
            {
                HalberdMotorControl.TryPrepare(__instance);
            }
        }

        private static void Postfix(Missile __instance)
        {
            if (HalberdMotorControl.IsHalberd(__instance))
            {
                HalberdMotorControl.TryUpdate(__instance);
            }
        }
    }

    [HarmonyPatch(typeof(Missile), nameof(Missile.UnitDisabled))]
    internal static class HalberdMotorCleanupPatch
    {
        private static void Postfix(Missile __instance)
        {
            HalberdMotorControl.Remove(__instance);
        }
    }

    [HarmonyPatch(typeof(Unit), "OnDestroy")]
    internal static class HalberdMotorDestroyCleanupPatch
    {
        private static void Postfix(Unit __instance)
        {
            if (__instance is Missile missile)
            {
                HalberdMotorControl.Remove(missile);
            }
        }
    }
}
