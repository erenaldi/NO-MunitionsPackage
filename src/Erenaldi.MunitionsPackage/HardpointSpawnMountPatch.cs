using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch(typeof(Hardpoint), nameof(Hardpoint.SpawnMount))]
    internal static class HardpointSpawnMountPatch
    {
        private static void Postfix(
            Hardpoint __instance,
            GameObject __result,
            Aircraft aircraft,
            WeaponMount weaponMount)
        {
            if (__result == null || aircraft == null || weaponMount == null)
            {
                return;
            }
            ManualLogSource logger;
            string label;
            if (weaponMount.jsonKey == HalberdCloner.MountJsonKey)
            {
                logger = HalberdCloner.Logger;
                label = "[Phase 2A] Halberd";
            }
            else if (weaponMount.jsonKey == KrisCloner.MountJsonKey)
            {
                logger = KrisCloner.Logger;
                label = "[Phase 2C] Kris";
            }
            else if (weaponMount.jsonKey == BallistaCloner.MountJsonKey)
            {
                logger = BallistaCloner.Logger;
                label = "[Phase 2D] Ballista";
            }
            else if (weaponMount.jsonKey == AradCloner.MountJsonKey)
            {
                logger = AradCloner.Logger;
                label = "[Phase 2E] ARAD-80";
            }
            else if (weaponMount.jsonKey == PhantomCloner.MountJsonKey)
            {
                logger = PhantomCloner.Logger;
                label = "[Phase 2F] Phantom";
            }
            else if (weaponMount.jsonKey == PalisadeCloner.MountJsonKey)
            {
                logger = PalisadeCloner.Logger;
                label = "[Phase 4] Palisade";
            }
            else
            {
                return;
            }

            __result.SetActive(true);
            int registered = 0;
            int alreadyRegistered = 0;
            // SpawnMount skips Weapon components while the dormant clone is
            // inactive, so registration must happen after this activation.
            foreach (var weapon in __result.GetComponentsInChildren<Weapon>(true))
            {
                if (IsRegistered(aircraft, weapon))
                {
                    alreadyRegistered++;
                }
                else
                {
                    aircraft.weaponManager.RegisterWeapon(weapon, weaponMount, __instance);
                    registered++;
                }
            }
            logger?.LogInfo(
                $"{label} rack activated on {aircraft.definition?.unitName ?? "unknown aircraft"}; " +
                $"registered {registered} weapon component(s), {alreadyRegistered} already registered.");
        }

        private static bool IsRegistered(Aircraft aircraft, Weapon weapon)
        {
            foreach (var station in aircraft.weaponStations)
            {
                if (station != null && station.Weapons != null && station.Weapons.Contains(weapon))
                {
                    return true;
                }
            }
            return false;
        }
    }
}
