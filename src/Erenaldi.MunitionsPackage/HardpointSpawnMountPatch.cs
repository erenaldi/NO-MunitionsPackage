using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch(typeof(Hardpoint), nameof(Hardpoint.SpawnMount))]
    internal static class HardpointSpawnMountPatch
    {
        private static void Postfix(GameObject __result, Aircraft aircraft, WeaponMount weaponMount)
        {
            if (__result == null || weaponMount == null)
            {
                return;
            }
            if (weaponMount.jsonKey == HalberdCloner.MountJsonKey)
            {
                __result.SetActive(true);
                HalberdCloner.Logger?.LogInfo(
                    $"[Phase 2A] Halberd rack activated on {aircraft?.definition?.unitName ?? "unknown aircraft"}.");
            }
            else if (weaponMount.jsonKey == KrisCloner.MountJsonKey)
            {
                __result.SetActive(true);
                KrisCloner.Logger?.LogInfo(
                    $"[Phase 2C] Kris rack activated on {aircraft?.definition?.unitName ?? "unknown aircraft"}.");
            }
            else if (weaponMount.jsonKey == BallistaCloner.MountJsonKey)
            {
                __result.SetActive(true);
                BallistaCloner.Logger?.LogInfo(
                    $"[Phase 2D] Ballista rack activated on {aircraft?.definition?.unitName ?? "unknown aircraft"}.");
            }
        }
    }
}
