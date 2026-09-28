using HarmonyLib;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch]
    internal static class PalisadeWeaponSelectionPatch
    {
        [HarmonyPatch(typeof(WeaponManager), nameof(WeaponManager.NextWeaponStation))]
        [HarmonyPrefix]
        private static bool NextWeaponStationPrefix(WeaponManager __instance, Aircraft ___aircraft)
        {
            return SelectVisibleStation(__instance, ___aircraft, 1);
        }

        [HarmonyPatch(typeof(WeaponManager), nameof(WeaponManager.PreviousWeaponStation))]
        [HarmonyPrefix]
        private static bool PreviousWeaponStationPrefix(WeaponManager __instance, Aircraft ___aircraft)
        {
            return SelectVisibleStation(__instance, ___aircraft, -1);
        }

        [HarmonyPatch(typeof(WeaponManager), nameof(WeaponManager.Fire))]
        [HarmonyPrefix]
        private static bool FirePrefix(WeaponManager __instance)
        {
            return !IsHidden(__instance.currentWeaponStation);
        }

        [HarmonyPatch(typeof(WeaponManager), "OrganizeWeaponStations")]
        [HarmonyPostfix]
        private static void OrganizeWeaponStationsPostfix(WeaponManager __instance, Aircraft ___aircraft)
        {
            if (!IsHidden(__instance.currentWeaponStation))
            {
                return;
            }
            foreach (var station in ___aircraft.weaponStations)
            {
                if (!IsHidden(station))
                {
                    __instance.SetActiveStation(station.Number);
                    ShowStation(__instance, ___aircraft);
                    return;
                }
            }
        }

        private static bool SelectVisibleStation(WeaponManager manager, Aircraft aircraft, int direction)
        {
            var stations = aircraft?.weaponStations;
            if (stations == null || manager.currentWeaponStation == null || stations.Count < 2)
            {
                return true;
            }
            bool hasHiddenStation = false;
            foreach (var station in stations)
            {
                if (IsHidden(station))
                {
                    hasHiddenStation = true;
                    break;
                }
            }
            if (!hasHiddenStation)
            {
                return true;
            }

            int index = manager.currentWeaponStation.Number;
            for (int offset = 1; offset <= stations.Count; offset++)
            {
                int candidateIndex = (index + direction * offset + stations.Count) % stations.Count;
                var candidate = stations[candidateIndex];
                if (!IsHidden(candidate))
                {
                    SetStation(manager, aircraft, candidate);
                    break;
                }
            }
            return false;
        }

        private static void SetStation(WeaponManager manager, Aircraft aircraft, WeaponStation station)
        {
            aircraft.SetActiveStation(station.Number);
            ShowStation(manager, aircraft);
        }

        private static void ShowStation(WeaponManager manager, Aircraft aircraft)
        {
            if (SceneSingleton<CombatHUD>.i != null && SceneSingleton<CombatHUD>.i.aircraft == aircraft)
            {
                SceneSingleton<CombatHUD>.i.ShowWeaponStation(manager.currentWeaponStation);
            }
        }

        private static bool IsHidden(WeaponStation station)
        {
            return station?.WeaponInfo != null && station.WeaponInfo.hideInDisplay;
        }
    }
}
