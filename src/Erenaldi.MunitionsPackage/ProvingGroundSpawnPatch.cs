using BepInEx.Logging;
using Cysharp.Threading.Tasks;
using HarmonyLib;
using NuclearOption.Networking;
using NuclearOption.SavedMission;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch]
    internal static class ProvingGroundSpawnPatch
    {
        private const string MissionName = "Erenaldi.ProvingGround";
        private const string PreferredAirbase = "North Boscali Airbase";
        private const string CloseTargetName = "AIR-CLOSE-IR-TARGET";
        private const string CloseTargetGun = "gun_20mm_internal";
        private const float AirSpawnAltitude = 5000f;
        private static bool awaitingSpawn;
        private static Airbase pendingAirSpawnBase;

        [HarmonyPostfix]
        [HarmonyPatch(typeof(MissionManager), nameof(MissionManager.StartMission))]
        private static void PauseAndOpenSelection()
        {
            if (!IsProvingGround() || Plugin.Instance == null)
            {
                return;
            }

            NormalizeMapAnchor();
            if (Plugin.Instance.showMapDiagnostics.Value)
            {
                LogMapActionBindings();
                LogMapState("state at mission start");
            }
            if (NetworkManagerNuclearOption.i != null && NetworkManagerNuclearOption.i.Server.Active)
            {
                Plugin.Instance.StartCoroutine(KeepTargetsDatalinked(MissionManager.CurrentMission));
            }
            if (!IsSinglePlayerProvingGround())
            {
                return;
            }

            awaitingSpawn = true;
            Plugin.Instance.StartCoroutine(OpenSelection());
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Spawner), nameof(Spawner.RequestSpawnAtAirbase))]
        private static void ResumeForSpawn(Airbase airbase, out bool __state)
        {
            __state = awaitingSpawn;
            if (!IsSinglePlayerProvingGround() || Plugin.Instance == null)
            {
                return;
            }

            pendingAirSpawnBase = airbase;
            if (__state)
            {
                awaitingSpawn = false;
                TimeScaleManager.Scale = 1f;
                Plugin.Instance.Log.LogInfo("[Testing] Proving ground resumed for the selected aircraft spawn.");
            }
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Spawner), nameof(Spawner.RequestSpawnAtAirbase))]
        private static void MonitorSpawnResult(ref UniTask<bool> __result, bool __state)
        {
            if (IsSinglePlayerProvingGround())
            {
                __result = RePauseIfRejected(__result, __state);
            }
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(MissionManager), "UnloadMission")]
        private static void ResetState()
        {
            awaitingSpawn = false;
            pendingAirSpawnBase = null;
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(GameplayUI), nameof(GameplayUI.ShowJoinMenu))]
        private static bool SuppressJoinMenuDuringSelection()
        {
            if (!awaitingSpawn || !IsSinglePlayerProvingGround() || Plugin.Instance == null)
            {
                return true;
            }

            Plugin.Instance.Log.LogInfo("[Testing] Suppressed the join menu while the proving-ground loadout selector is open.");
            return false;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(DynamicMap), nameof(DynamicMap.Maximize))]
        private static void LogMapMaximize()
        {
            LogMapState("maximized");
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(DynamicMap), nameof(DynamicMap.Minimize))]
        private static void LogMapMinimize()
        {
            LogMapState("minimized");
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Spawner), nameof(Spawner.SpawnAircraft))]
        private static void ApplyPlayerAirSpawn(
            Player player,
            GameObject prefab,
            ref GlobalPosition globalPosition,
            ref Quaternion rotation,
            ref Vector3 startingVel,
            ref Hangar spawningHangar)
        {
            if (player == null || !GameManager.IsLocalPlayer(player) || pendingAirSpawnBase == null ||
                Plugin.Instance == null || !IsSinglePlayerProvingGround())
            {
                return;
            }

            var definition = prefab.GetComponent<Aircraft>().definition;
            var parameters = definition.aircraftParameters;
            var minimumSpeed = parameters.verticalLanding ? 50f : 180f;
            var spawnSpeed = Mathf.Max(parameters.takeoffSpeed * 1.3f, minimumSpeed);
            globalPosition = pendingAirSpawnBase.center.GlobalPosition() + Vector3.up * AirSpawnAltitude;
            var closeTarget = MissionManager.CurrentMission.aircraft.FirstOrDefault(target => target.UniqueName == CloseTargetName);
            if (closeTarget != null)
            {
                var direction = closeTarget.globalPosition - globalPosition;
                direction.y = 0f;
                if (direction.sqrMagnitude > 1f)
                {
                    var heading = Quaternion.LookRotation(direction.normalized, Vector3.up);
                    rotation = heading * Quaternion.Euler(definition.restRotation);
                }
            }
            startingVel = rotation * Vector3.forward * spawnSpeed;
            spawningHangar = null;
            pendingAirSpawnBase = null;
            Plugin.Instance.Log.LogInfo($"[Testing] Player aircraft air-spawned at {AirSpawnAltitude / 1000f:F0} km altitude and {spawnSpeed:F0} m/s.");
        }

        [HarmonyPostfix]
        [HarmonyPriority(Priority.Last)]
        [HarmonyPatch(typeof(Aircraft), "OnStartClient")]
        private static void EnforceCloseTargetLoadout(Aircraft __instance)
        {
            if (!IsProvingGround() || Plugin.Instance == null || __instance.weaponManager == null ||
                string.IsNullOrEmpty(__instance.UniqueName) || !__instance.UniqueName.StartsWith(CloseTargetName))
            {
                return;
            }

            var loadout = new Loadout();
            foreach (var hardpointSet in __instance.weaponManager.hardpointSets)
            {
                var mount = hardpointSet.weaponOptions.FirstOrDefault(option =>
                    option != null && option.jsonKey == CloseTargetGun);
                loadout.weapons.Add(mount);
            }

            if (loadout.weapons.Count(mount => mount != null && mount.jsonKey == CloseTargetGun) != 1)
            {
                Plugin.Instance.Log.LogError("[Testing] Could not resolve the AIR-CLOSE-IR-TARGET internal gun; loadout was not changed.");
                return;
            }

            __instance.Networkloadout = loadout;
            if (!__instance.IsHost)
            {
                __instance.weaponManager.WeaponManager_OnLoadoutChanged();
            }
            Plugin.Instance.Log.LogInfo($"[Testing] {__instance.UniqueName} configured gun-only with no missiles.");
        }

        private static IEnumerator OpenSelection()
        {
            const float timeoutSeconds = 30f;
            var waited = 0f;
            while (waited < timeoutSeconds && awaitingSpawn && IsSinglePlayerProvingGround())
            {
                if (TryOpenSelection(Plugin.Instance.Log))
                {
                    yield break;
                }

                yield return new WaitForSecondsRealtime(0.25f);
                waited += 0.25f;
            }

            if (!awaitingSpawn || !IsSinglePlayerProvingGround())
            {
                yield break;
            }

            TimeScaleManager.Scale = 0f;
            Plugin.Instance.Log.LogError(
                "[Testing] Could not open the proving-ground loadout selector within 30 seconds; the mission is paused.");
        }

        private static IEnumerator KeepTargetsDatalinked(Mission mission)
        {
            var logged = false;
            var hq = FactionRegistry.HqFromName("Boscali");
            var targets = mission.aircraft.Cast<SavedUnit>()
                .Concat(mission.vehicles)
                .Concat(mission.ships)
                .Concat(mission.buildings)
                .ToList();
            while (MissionManager.CurrentMission == mission)
            {
                var networkManager = NetworkManagerNuclearOption.i;
                if (networkManager != null && networkManager.Server.Active && hq != null)
                {
                    var updated = 0;
                    foreach (var target in targets)
                    {
                        if (target.HasSpawned && target.Unit != null && target.Unit.NetworkHQ != hq)
                        {
                            hq.RpcUpdateTrackingInfo(target.Unit.persistentID);
                            updated++;
                        }
                    }

                    if (!logged && updated > 0)
                    {
                        logged = true;
                        Plugin.Instance?.Log.LogInfo($"[Testing] {updated} proving-ground targets revealed and linked to Boscali.");
                    }
                }

                yield return new WaitForSecondsRealtime(1f);
            }
        }

        private static bool TryOpenSelection(ManualLogSource logger)
        {
            if (!GameManager.GetLocalPlayer<Player>(out var player) ||
                SceneSingleton<GameplayUI>.i == null ||
                SceneSingleton<DynamicMap>.i == null)
            {
                return false;
            }

            var hq = FactionRegistry.HqFromName("Boscali");
            if (hq == null)
            {
                return false;
            }

            var airbases = hq.GetAirbases().ToList();
            var airbase = airbases.FirstOrDefault(candidate => candidate.SavedAirbase.DisplayName == PreferredAirbase)
                ?? airbases.FirstOrDefault();
            if (airbase == null)
            {
                return false;
            }

            if (player.HQ == null)
            {
                player.SetFaction(hq);
            }
            if (player.HQ != hq)
            {
                TimeScaleManager.Scale = 0f;
                logger.LogError($"[Testing] Cannot open proving-ground selection because the local player joined '{player.HQ?.faction?.factionName}'.");
                return true;
            }

            TimeScaleManager.Scale = 0f;
            SceneSingleton<DynamicMap>.i.SetFaction(hq);
            SceneSingleton<GameplayUI>.i.SelectAirbase(airbase);
            SceneSingleton<GameplayUI>.i.SelectAircraft();
            logger.LogInfo($"[Testing] Proving ground paused at the '{airbase.SavedAirbase.DisplayName}' loadout selector.");
            return true;
        }

        private static async UniTask<bool> RePauseIfRejected(UniTask<bool> spawnResult, bool rePauseOnFailure)
        {
            try
            {
                var spawned = await spawnResult;
                if (!spawned)
                {
                    pendingAirSpawnBase = null;
                    if (rePauseOnFailure && IsSinglePlayerProvingGround())
                    {
                        awaitingSpawn = true;
                        TimeScaleManager.Scale = 0f;
                        Plugin.Instance?.Log.LogWarning("[Testing] Aircraft spawn was rejected; the proving ground is paused for another selection.");
                    }
                }
                return spawned;
            }
            catch
            {
                pendingAirSpawnBase = null;
                if (rePauseOnFailure && IsSinglePlayerProvingGround())
                {
                    awaitingSpawn = true;
                    TimeScaleManager.Scale = 0f;
                }
                throw;
            }
        }

        private static void LogMapActionBindings()
        {
            var player = Rewired.ReInput.players.GetPlayer(0);
            if (player == null)
            {
                return;
            }

            var mapActionId = Rewired.ReInput.mapping.GetActionId("Map");
            var bindings = new List<string>();
            foreach (var controllerMap in player.controllers.maps.GetAllMaps())
            {
                foreach (var elementMap in controllerMap.ElementMaps)
                {
                    if (elementMap.actionId != mapActionId)
                    {
                        continue;
                    }

                    bindings.Add($"{controllerMap.controllerType} category {controllerMap.categoryId} -> {DescribeElement(controllerMap.controllerType, elementMap)}");
                }
            }

            Plugin.Instance.Log.LogInfo(
                bindings.Count > 0
                    ? $"[Testing] Map action bindings: {string.Join("; ", bindings)}"
                    : "[Testing] Map action bindings: none found (action id may differ).");
        }

        private static readonly string[] MouseButtons = { "Left", "Right", "Middle", "Button3", "Button4", "Button5", "WheelUp", "WheelDown" };
        private static readonly string[] MouseAxes = { "X", "Y", "Wheel" };

        private static string DescribeElement(Rewired.ControllerType controllerType, Rewired.ActionElementMap elementMap)
        {
            if (controllerType == Rewired.ControllerType.Keyboard && elementMap.elementType == Rewired.ControllerElementType.Button)
            {
                return $"key {elementMap.elementIndex} ({(Rewired.KeyboardKeyCode)elementMap.elementIndex})";
            }

            if (controllerType == Rewired.ControllerType.Mouse)
            {
                if (elementMap.elementType == Rewired.ControllerElementType.Button && elementMap.elementIndex < MouseButtons.Length)
                {
                    return $"mouse {MouseButtons[elementMap.elementIndex]}";
                }

                if (elementMap.elementType == Rewired.ControllerElementType.Axis && elementMap.elementIndex < MouseAxes.Length)
                {
                    return $"mouse {MouseAxes[elementMap.elementIndex]} axis, range {elementMap.axisRange}, invert {elementMap.invert}";
                }
            }

            return $"{elementMap.elementType} {elementMap.elementIndex}, range {elementMap.axisRange}, invert {elementMap.invert}";
        }

        private static void NormalizeMapAnchor()
        {
            var map = SceneSingleton<DynamicMap>.i;
            if (map == null || map.hudMapAnchor == null || map.transform.parent == map.hudMapAnchor)
            {
                return;
            }

            map.transform.SetParent(map.hudMapAnchor);
            map.transform.localScale = Vector3.one;
            map.transform.localPosition = Vector3.zero;
            map.maximizedMapCanvas.gameObject.SetActive(false);
            Plugin.Instance?.Log.LogWarning(
                $"[Testing] Map root was stranded under '{map.maximizedMapAnchor.name}' while minimized; returned it to the HUD anchor.");
        }

        private static void LogMapState(string action)
        {
            if (!IsProvingGround() || Plugin.Instance == null || !Plugin.Instance.showMapDiagnostics.Value)
            {
                return;
            }

            var map = SceneSingleton<DynamicMap>.i;
            if (map == null)
            {
                Plugin.Instance.Log.LogInfo($"[Testing] Map {action}: no DynamicMap instance.");
                return;
            }

            var imageRect = map.mapImage.transform as RectTransform;
            var backgroundRect = map.mapBackground.GetComponent<RectTransform>();
            Plugin.Instance.Log.LogInfo(
                $"[Testing] Map {action} (mapMaximized={DynamicMap.mapMaximized}) from {DescribeCallers()} | " +
                $"imageScale={map.mapImage.transform.localScale.x:F2} imageSize={imageRect?.sizeDelta.x:F0} " +
                $"centerScale={map.mapScaleCenter.localScale.x:F2} proxyScale={map.mapScaleProxy.localScale.x:F2} " +
                $"bgScale={map.mapBackground.transform.localScale.x:F2} bgSize={backgroundRect.sizeDelta.x:F0} " +
                $"rootParent={map.transform.parent?.name} rootScale={map.transform.localScale.x:F2} " +
                $"imageParent={map.mapImage.transform.parent?.name} | " +
                $"displayFactor={map.mapDisplayFactor:E3} scaleCurrent={map.mapScaleCurrent:F0} " +
                $"scaleMin={map.mapScaleMinimized:F0} scaleMax={map.mapScaleMaximized:F0} dimension={map.mapDimension:F0}");
        }

        private static string DescribeCallers()
        {
            var frames = new System.Diagnostics.StackTrace(2, false).GetFrames();
            if (frames == null)
            {
                return "unknown caller";
            }

            var names = new List<string>();
            foreach (var frame in frames)
            {
                var method = frame.GetMethod();
                var declaring = method?.DeclaringType;
                if (declaring == null || declaring == typeof(ProvingGroundSpawnPatch) ||
                    declaring.Name.StartsWith("<") || declaring.Namespace?.StartsWith("HarmonyLib") == true)
                {
                    continue;
                }

                names.Add($"{declaring.Name}.{method.Name}");
                if (names.Count == 3)
                {
                    break;
                }
            }

            return names.Count > 0 ? string.Join(" <- ", names) : "unknown caller";
        }

        private static bool IsSinglePlayerProvingGround()
        {
            return GameManager.gameState == GameState.SinglePlayer && IsProvingGround();
        }

        private static bool IsProvingGround()
        {
            return MissionManager.CurrentMission != null && MissionManager.CurrentMission.Name == MissionName;
        }
    }
}
