using System;
using HarmonyLib;

namespace Erenaldi.MunitionsPackage
{
    internal static class BasiliskGuidance
    {
        internal static bool IsBasilisk(Missile missile)
        {
            return missile != null && missile.definition != null &&
                string.Equals(missile.definition.jsonKey, BasiliskCloner.MissileJsonKey, StringComparison.Ordinal);
        }
    }

    [HarmonyPatch(typeof(Missile), nameof(Missile.SetTarget), new[] { typeof(Unit) })]
    internal static class BasiliskTargetRetentionPatch
    {
        private static bool Prefix(Missile __instance, Unit target)
        {
            if (target != null || !BasiliskGuidance.IsBasilisk(__instance) || __instance.disabled)
            {
                return true;
            }
            var composite = __instance.GetComponent<BasiliskSeeker>();
            return composite == null || !composite.RetainTargetOnNull;
        }
    }

    [HarmonyPatch(typeof(Aircraft), nameof(Aircraft.LockedByMissile))]
    internal static class BasiliskWarningTracePatch
    {
        private static void Postfix(Aircraft __instance, Missile missile)
        {
            if (BasiliskGuidance.IsBasilisk(missile))
            {
                BasiliskCloner.Logger?.LogInfo(
                    $"[Phase 2B] Basilisk warning registered for '{__instance.unitName}'.");
            }
        }
    }

    [HarmonyPatch(typeof(IRSeeker), "SlowChecks")]
    internal static class BasiliskIrSlowChecksPatch
    {
        private static bool Prefix(IRSeeker __instance)
        {
            var missile = (Missile)HalberdCloner.GetField(__instance, "missile");
            return missile != null && !BasiliskGuidance.IsBasilisk(missile);
        }
    }

    [HarmonyPatch(typeof(ARHSeeker), "SlowChecks")]
    internal static class BasiliskArhSlowChecksPatch
    {
        private static bool Prefix(ARHSeeker __instance)
        {
            var missile = (Missile)HalberdCloner.GetField(__instance, "missile");
            return missile != null && !BasiliskGuidance.IsBasilisk(missile);
        }
    }

    [HarmonyPatch(typeof(Missile), nameof(Missile.UnitDisabled))]
    internal static class BasiliskTargetCleanupPatch
    {
        private static void Postfix(Missile __instance)
        {
            if (BasiliskGuidance.IsBasilisk(__instance) && __instance.LocalSim)
            {
                __instance.Network_targetID = PersistentID.None;
            }
        }
    }
}
