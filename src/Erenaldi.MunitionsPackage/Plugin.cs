using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using System.Collections;
using System.IO;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public sealed class Plugin : BaseUnityPlugin
    {
        public const string PluginGuid = "Erenaldi.MunitionsPackage";
        public const string PluginName = "Nuclear Option Munitions Package";
        public const string PluginVersion = "0.1.0";

        internal static Plugin Instance { get; private set; }
        internal ManualLogSource Log => Logger;

        private ConfigEntry<bool> dumpSchemaOnStartup;
        private ConfigEntry<bool> enableHalberd;
        private ConfigEntry<bool> enableKris;
        private ConfigEntry<bool> enableBallista;
        private ConfigEntry<bool> enableArad80;
        private ConfigEntry<bool> enableKrisJHook;
        private ConfigEntry<float> krisJHookLoftAltitude;
        private ConfigEntry<float> krisJHookDiveRange;
        private ConfigEntry<float> krisJHookBlendRange;
        private ConfigEntry<float> krisJHookTerminalFade;
        private ConfigEntry<float> krisJHookTerminalShare;
        private ConfigEntry<bool> enableKrisLeadGuidance;
        private ConfigEntry<float> krisLeadGain;
        private ConfigEntry<float> krisMaxCommandedAngle;
        private ConfigEntry<float> krisIrccmProcessingPause;
        private ConfigEntry<float> krisIrccmOpticalFov;
        private ConfigEntry<float> krisIrccmReacquireWindow;
        private ConfigEntry<float> krisCoastMachFloor;
        private ConfigEntry<KrisDualPulseController.PulseTwoTriggerMode> krisPulseTwoTrigger;
        private ConfigEntry<float> krisIrccmFlareDecoyGain;
        private ConfigEntry<float> krisIrccmGimbalSlewRate;
        private ConfigEntry<float> krisIrccmFatigueStep;
        private ConfigEntry<float> krisIrccmSuspensionDrift;
        private ConfigEntry<float> krisIrccmBeamRejectHorizon;
        private ConfigEntry<bool> enableCustomGeometry;
        internal ConfigEntry<bool> showMapDiagnostics;
        private ConfigEntry<float> stableWaitSeconds;
        private ConfigEntry<float> maximumWaitSeconds;
        private ConfigEntry<int> maxValueDepth;
        private ConfigEntry<int> maxCollectionItems;

        private void Awake()
        {
            Instance = this;
            dumpSchemaOnStartup = Config.Bind("Phase 1", "DumpSchemaOnStartup", true,
                "Write weapon schema and analog validation reports after the encyclopedia finishes loading.");
            stableWaitSeconds = Config.Bind("Phase 1", "StableWaitSeconds", 3f,
                "Seconds for which encyclopedia counts must remain stable before dumping.");
            maximumWaitSeconds = Config.Bind("Phase 1", "MaximumWaitSeconds", 120f,
                "Maximum time to wait for the encyclopedia before reporting a failure.");
            maxValueDepth = Config.Bind("Phase 1", "MaxValueDepth", 5,
                "Maximum reflection depth for serialized non-Unity values.");
            maxCollectionItems = Config.Bind("Phase 1", "MaxCollectionItems", 256,
                "Maximum number of values emitted from one reflected collection.");
            enableHalberd = Config.Bind("Phase 2", "EnableHalberd", true,
                "Runtime-clone the AAM-44 Halberd from the AAM-36 Scimitar after the encyclopedia loads.");
            enableKris = Config.Bind("Phase 2", "EnableKris", true,
                "Runtime-clone the IRM-S4 Kris from the MMR-S3 after the encyclopedia loads.");
            enableBallista = Config.Bind("Phase 2", "EnableBallista", true,
                "Runtime-clone the AGM-110 Ballista from the AGM-99 (AShM2) with AGM-68 carriage after the encyclopedia loads.");
            enableArad80 = Config.Bind("Phase 2", "EnableArad80", true,
                "Runtime-clone the ARAD-80 single-burn sprinter from the ARAD-116 (ARM1) after the encyclopedia loads.");
            enableKrisJHook = Config.Bind("Phase 2", "EnableKrisJHook", true,
                "Loft Kris missiles into an energy-preserving J-hook arc with a terminal dive onto the target.");
            krisJHookLoftAltitude = Config.Bind("Phase 2", "KrisJHookLoftAltitude", 2762f,
                "Maximum vertical aim offset (meters) of the Kris J-hook loft at full range.");
            krisJHookDiveRange = Config.Bind("Phase 2", "KrisJHookDiveRange", 2550f,
                "Horizontal distance to the aimpoint (meters) below which the Kris J-hook bias reaches zero and the missile dives.");
            krisJHookBlendRange = Config.Bind("Phase 2", "KrisJHookBlendRange", 3825f,
                "Horizontal distance (meters) over which the Kris J-hook loft tapers from full to zero.");
            krisJHookTerminalFade = Config.Bind("Phase 2", "KrisJHookTerminalFade", 2f,
                "Seconds over which the Kris J-hook loft tapers down after pulse two ignites; 0 drops the loft to its terminal share instantly.");
            krisJHookTerminalShare = Config.Bind("Phase 2", "KrisJHookTerminalShare", 0.4f,
                "Fraction of the Kris J-hook loft that survives into the terminal phase, hybridizing with the intercept guidance until the dive-range taper zeroes it; 0 restores the previous fade-to-direct-intercept behavior.");
            enableKrisLeadGuidance = Config.Bind("Phase 2", "EnableKrisLeadGuidance", true,
                "Compute Kris lead-pursuit aimpoints from the missile's real closing speed, fixing early-turn lag.");
            krisLeadGain = Config.Bind("Phase 2", "KrisLeadGain", 1f,
                "Multiplier on the Kris lead-pursuit aim offset; below 1 trims lead for maneuvering targets.");
            krisMaxCommandedAngle = Config.Bind("Phase 2", "KrisMaxCommandedAngle", 35f,
                "Maximum angle (degrees) between the Kris velocity vector and the commanded aim direction; prevents over-lead the TVC cannot recover after burnout. 0 disables.");
            krisIrccmProcessingPause = Config.Bind("Phase 2", "KrisIrccmProcessingPause", 0.4f,
                "Seconds the Kris dead-reckons after detecting a flare before attempting optical reacquisition.");
            krisIrccmOpticalFov = Config.Bind("Phase 2", "KrisIrccmOpticalFov", 3f,
                "Kris instantaneous optical tracking half-angle in degrees around its predicted line of sight; separate from the 72.1-degree gimbal limit.");
            krisIrccmReacquireWindow = Config.Bind("Phase 2", "KrisIrccmReacquireWindow", 2f,
                "Maximum seconds from flare detection for narrow-field Kris reacquisition before it widens to a full gimbal search.");
            krisCoastMachFloor = Config.Bind("Phase 2", "KrisCoastMachFloor", 1.5f,
                "Mach number below which the Kris second pulse ignites automatically during coast; 0 disables.");
            krisPulseTwoTrigger = Config.Bind("Phase 2", "KrisPulseTwoTrigger",
                KrisDualPulseController.PulseTwoTriggerMode.Auto,
                "Pulse two ignition policy: Auto = first of halfway to the launch range or the Mach floor; Halfway = range trigger only; MachFloor = speed floor only; Immediate = light pulse two as pulse one ends (continuous burn).");
            krisIrccmFlareDecoyGain = Config.Bind("Phase 2", "KrisIrccmFlareDecoyGain", 1f,
                "Intensity multiplier applied to flares during Kris narrow-field reacquisition scoring; above 1 makes decoys easier, 0 disables flare candidacy.");
            krisIrccmGimbalSlewRate = Config.Bind("Phase 2", "KrisIrccmGimbalSlewRate", 120f,
                "Maximum Kris seeker head slew rate (degrees per second) while reacquiring during an IRCCM suspension; 0 disables the limit.");
            krisIrccmFatigueStep = Config.Bind("Phase 2", "KrisIrccmFatigueStep", 0.15f,
                "Extra seconds added to each consecutive Kris IRCCM processing pause triggered within 4 seconds of the previous one; 0 disables.");
            krisIrccmSuspensionDrift = Config.Bind("Phase 2", "KrisIrccmSuspensionDrift", 20f,
                "Kris suspension inertial drift magnitude in meters per sqrt(second): the blind prediction wanders by roughly this many meters after one second of suspension; 0 disables.");
            krisIrccmBeamRejectHorizon = Config.Bind("Phase 2", "KrisIrccmBeamRejectHorizon", 0.25f,
                "Seconds within which a Kris flare is predicted to leave the optical window on a fast-sweeping line of sight (beam aspect); such flares are ignored instead of blinding the seeker. 0 disables.");
            enableCustomGeometry = Config.Bind("Phase 3", "EnableCustomGeometry", true,
                "Transplant custom geometry from the embedded bundle onto cloned weapons when available.");
            showMapDiagnostics = Config.Bind("Testing", "MapDiagnostics", true,
                "Log every proving-ground map maximize/minimize transition with the calling code, to trace fullscreen-map overlays.");

            Logger.LogInfo($"{PluginName} {PluginVersion} loaded (Phase 2A clone mode).");
            new Harmony(PluginGuid).PatchAll();
            if (dumpSchemaOnStartup.Value || enableHalberd.Value || enableKris.Value || enableBallista.Value ||
                enableArad80.Value)
            {
                StartCoroutine(WaitForStableEncyclopedia());
            }
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        private IEnumerator WaitForStableEncyclopedia()
        {
            var previousWeaponCount = -1;
            var previousUnitCount = -1;
            var stableFor = 0f;
            var waitedFor = 0f;

            while (waitedFor < maximumWaitSeconds.Value)
            {
                var weaponCount = Encyclopedia.WeaponLookup?.Count ?? 0;
                var unitCount = Encyclopedia.Lookup?.Count ?? 0;
                if (weaponCount > 0 && unitCount > 0 &&
                    weaponCount == previousWeaponCount && unitCount == previousUnitCount)
                {
                    stableFor += 0.5f;
                    if (stableFor >= stableWaitSeconds.Value)
                    {
                        break;
                    }
                }
                else
                {
                    previousWeaponCount = weaponCount;
                    previousUnitCount = unitCount;
                    stableFor = 0f;
                }

                yield return new WaitForSecondsRealtime(0.5f);
                waitedFor += 0.5f;
            }

            if (stableFor < stableWaitSeconds.Value)
            {
                Logger.LogError($"Encyclopedia initialization timed out after {waitedFor:F1} seconds.");
                yield break;
            }

            if (enableHalberd.Value)
            {
                try
                {
                    HalberdCloner.EnableCustomGeometry = enableCustomGeometry.Value;
                    HalberdCloner.Clone(Logger);
                }
                catch (System.Exception exception)
                {
                    Logger.LogError($"Phase 2A Halberd clone failed: {exception}");
                }
            }
            if (enableKris.Value)
            {
                try
                {
                    KrisCloner.EnableCustomGeometry = enableCustomGeometry.Value;
                    KrisGuidance.JHookEnabled = enableKrisJHook.Value;
                    KrisGuidance.JHookLoftAltitude = krisJHookLoftAltitude.Value;
                    KrisGuidance.JHookDiveRange = krisJHookDiveRange.Value;
                    KrisGuidance.JHookBlendRange = krisJHookBlendRange.Value;
                    KrisGuidance.JHookTerminalFade = Mathf.Clamp(krisJHookTerminalFade.Value, 0f, 8f);
                    KrisGuidance.JHookTerminalShare = Mathf.Clamp(krisJHookTerminalShare.Value, 0f, 1f);
                    KrisGuidance.LeadGuidanceEnabled = enableKrisLeadGuidance.Value;
                    KrisGuidance.LeadGain = krisLeadGain.Value;
                    KrisGuidance.MaxCommandedAngle = krisMaxCommandedAngle.Value;
                    KrisIrccm.ProcessingPause = Mathf.Clamp(krisIrccmProcessingPause.Value, 0.05f, 2f);
                    KrisIrccm.OpticalTrackFov = Mathf.Clamp(krisIrccmOpticalFov.Value, 0.5f, 10f);
                    KrisIrccm.ReacquireWindow = Mathf.Max(
                        KrisIrccm.ProcessingPause,
                        Mathf.Clamp(krisIrccmReacquireWindow.Value, 0.1f, 5f));
                    KrisDualPulseController.CoastMachFloor = Mathf.Clamp(krisCoastMachFloor.Value, 0f, 3f);
                    KrisDualPulseController.PulseTwoTrigger = krisPulseTwoTrigger.Value;
                    KrisIrccm.FlareDecoyGain = Mathf.Clamp(krisIrccmFlareDecoyGain.Value, 0f, 3f);
                    KrisIrccm.GimbalSlewRate = Mathf.Clamp(krisIrccmGimbalSlewRate.Value, 0f, 360f);
                    KrisIrccm.FatigueStep = Mathf.Clamp(krisIrccmFatigueStep.Value, 0f, 0.5f);
                    KrisIrccm.SuspensionDrift = Mathf.Clamp(krisIrccmSuspensionDrift.Value, 0f, 100f);
                    KrisIrccm.BeamRejectHorizon = Mathf.Clamp(krisIrccmBeamRejectHorizon.Value, 0f, 2f);
                    Logger.LogInfo(
                        $"[Phase 2C] Kris IRCCM configured: {KrisIrccm.ProcessingPause:F2} s processing pause, " +
                        $"{KrisIrccm.OpticalTrackFov:F1}-degree optical half-angle, " +
                        $"{KrisIrccm.ReacquireWindow:F2} s narrow-field window, {KrisCloner.MaxAlignment:F1}-degree gimbal, " +
                        $"flare decoy gain {KrisIrccm.FlareDecoyGain:F2}, gimbal slew {KrisIrccm.GimbalSlewRate:F0} deg/s, " +
                        $"fatigue step +{KrisIrccm.FatigueStep:F2} s, suspension drift {KrisIrccm.SuspensionDrift:F0} m/sqrt(s), " +
                        $"beam reject horizon {KrisIrccm.BeamRejectHorizon:F2} s.");
                    KrisCloner.Clone(Logger);
                }
                catch (System.Exception exception)
                {
                    Logger.LogError($"Phase 2C Kris clone failed: {exception}");
                }
            }
            if (enableBallista.Value)
            {
                try
                {
                    BallistaCloner.EnableCustomGeometry = enableCustomGeometry.Value;
                    BallistaCloner.Clone(Logger);
                }
                catch (System.Exception exception)
                {
                    Logger.LogError($"Phase 2D Ballista clone failed: {exception}");
                }
            }
            if (enableArad80.Value)
            {
                try
                {
                    AradCloner.Clone(Logger);
                }
                catch (System.Exception exception)
                {
                    Logger.LogError($"Phase 2E ARAD-80 clone failed: {exception}");
                }
            }
            if (!dumpSchemaOnStartup.Value)
            {
                yield break;
            }

            var outputDirectory = Path.Combine(Paths.ConfigPath, PluginGuid);
            try
            {
                Directory.CreateDirectory(outputDirectory);
            }
            catch (System.Exception exception)
            {
                Logger.LogError($"Phase 1 output directory creation failed: {exception}");
                yield break;
            }

            try
            {
                var geometryDumper = new MissileGeometryDumper(Logger);
                geometryDumper.Dump(outputDirectory);
            }
            catch (System.Exception exception)
            {
                Logger.LogError($"Phase 3 geometry dump failed: {exception}");
            }

            try
            {
                var dumper = new WeaponSchemaDumper(
                    Logger,
                    Mathf.Clamp(maxValueDepth.Value, 1, 10),
                    Mathf.Clamp(maxCollectionItems.Value, 1, 4096));
                dumper.Dump(outputDirectory);
            }
            catch (System.Exception exception)
            {
                Logger.LogError($"Phase 1 schema dump failed: {exception}");
            }
        }
    }
}
