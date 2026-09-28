using System.Collections.Generic;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class PalisadeDefense : MonoBehaviour
    {
        private const float DecisionInterval = 0.1f;
        private const float MinimumClosingSpeed = 25f;
        private const float InterceptSafetyMargin = 0.15f;
        private static readonly Dictionary<int, List<PalisadeDefense>> DefensesByAircraft =
            new Dictionary<int, List<PalisadeDefense>>();
        private Aircraft aircraft;
        private PalisadeCountermeasure countermeasure;
        private int registeredAircraftId;
        private float lastDecisionTime;
        private string lastState;
        private readonly Dictionary<int, string> lastDecisionByThreat = new Dictionary<int, string>();

        internal void AttachToAircraft(Aircraft attachedAircraft)
        {
            Unregister();
            aircraft = attachedAircraft;
            countermeasure = GetComponent<PalisadeCountermeasure>();
            if (aircraft == null)
            {
                return;
            }
            registeredAircraftId = aircraft.GetInstanceID();
            if (!DefensesByAircraft.TryGetValue(registeredAircraftId, out var defenses))
            {
                defenses = new List<PalisadeDefense>();
                DefensesByAircraft.Add(registeredAircraftId, defenses);
            }
            if (!defenses.Contains(this))
            {
                defenses.Add(this);
            }
        }

        private void OnDestroy()
        {
            Unregister();
        }

        private void Update()
        {
            if (aircraft == null)
            {
                return;
            }
            if (!ShouldCoordinate())
            {
                LogStateOnce("not-authority", "is idle on this peer because it does not coordinate this aircraft");
                return;
            }
            if (aircraft.disabled)
            {
                LogStateOnce("disabled", "is idle because the aircraft is disabled");
                return;
            }
            if (aircraft.radarAlt < 10f)
            {
                LogStateOnce("low-altitude", $"is inhibited below 10 m radar altitude ({aircraft.radarAlt:F1} m)");
                return;
            }
            if (!IsCoordinator() || Time.timeSinceLevelLoad - lastDecisionTime < DecisionInterval)
            {
                return;
            }
            lastDecisionTime = Time.timeSinceLevelLoad;
            RefreshCountermeasureAmmo(aircraft);

            if (countermeasure == null)
            {
                LogStateOnce("no-countermeasure", "cannot find its countermeasure component");
                return;
            }
            if (countermeasure.Mode == PalisadeCountermeasure.PalisadeMode.Safe)
            {
                LogStateOnce("safe", "is inhibited in Safe mode");
                return;
            }
            var station = FindStation(aircraft);
            var warning = aircraft.GetMissileWarningSystem();
            if (station == null)
            {
                LogStateOnce("no-station", "cannot find its interceptor weapon station");
                return;
            }
            if (station.Ammo <= 0)
            {
                LogStateOnce("empty", "has no interceptor rounds remaining");
                return;
            }
            if (warning == null || warning.knownMissiles == null)
            {
                LogStateOnce("no-warning-system", "cannot access the aircraft missile-warning system");
                return;
            }
            if (warning.knownMissiles.Count == 0)
            {
                LogStateOnce("no-threats", $"is armed in {countermeasure.Mode} mode with {station.Ammo} rounds; no known incoming missiles");
                return;
            }
            LogStateOnce("assessing", $"is assessing {warning.knownMissiles.Count} known incoming missile(s) in {countermeasure.Mode} mode");

            Missile bestThreat = null;
            float bestTti = float.MaxValue;
            string bestReason = null;
            foreach (var threat in warning.knownMissiles)
            {
                if (!TryAssessThreat(threat, station, countermeasure.Mode, out float tti, out string reason))
                {
                    continue;
                }
                if (tti < bestTti)
                {
                    bestThreat = threat;
                    bestTti = tti;
                    bestReason = reason;
                }
            }
            if (bestThreat == null)
            {
                return;
            }

            if (!(aircraft.radar is Radar))
            {
                LogDecisionOnce(bestThreat, "no-radar", "cannot launch SARH runtime-spike interceptor because the carrier has no compatible radar");
                return;
            }
            int ammoBefore = station.Ammo;
            station.LaunchMount(aircraft, bestThreat, bestThreat.GlobalPosition());
            RefreshCountermeasureAmmo(aircraft);
            if (station.Ammo >= ammoBefore)
            {
                LogDecisionOnce(bestThreat, "launch-failed", "issued a launch command but station ammo did not decrease");
                return;
            }
            PalisadeCloner.Logger?.LogInfo(
                $"[Phase 4] Palisade launched at {bestThreat.unitName} ({bestThreat.GetSeekerType()}, TTI {bestTti:F1} s): {bestReason}; {station.Ammo} rounds remain.");
        }

        private bool TryAssessThreat(
            Missile threat,
            WeaponStation station,
            PalisadeCountermeasure.PalisadeMode mode,
            out float tti,
            out string reason)
        {
            tti = float.MaxValue;
            reason = null;
            if (threat == null || threat.disabled || threat.rb == null || aircraft.rb == null ||
                threat.targetID != aircraft.persistentID)
            {
                return false;
            }
            Vector3 offset = threat.transform.position - aircraft.transform.position;
            float distance = offset.magnitude;
            var requirements = station.WeaponInfo.targetRequirements;
            if (distance < requirements.minRange || distance > requirements.maxRange)
            {
                LogDecisionOnce(threat, "range", $"cannot engage threat at {distance:F0} m outside the {requirements.minRange:F0}-{requirements.maxRange:F0} m envelope");
                return false;
            }
            Vector3 relativeVelocity = threat.rb.velocity - aircraft.rb.velocity;
            float closingSpeed = -Vector3.Dot(relativeVelocity, offset / Mathf.Max(distance, 0.01f));
            if (closingSpeed < MinimumClosingSpeed)
            {
                LogDecisionOnce(threat, "closure", $"cannot engage threat closing at only {closingSpeed:F0} m/s");
                return false;
            }
            tti = distance / closingSpeed;
            float interceptorSpeed = Mathf.Max(station.WeaponInfo.GetMaxSpeed(), 1f);
            if (!TryGetInterceptTime(offset, relativeVelocity, interceptorSpeed, out float interceptTime) ||
                interceptTime + InterceptSafetyMargin >= tti)
            {
                LogDecisionOnce(
                    threat,
                    "unreachable",
                    $"cannot reach threat at {distance:F0} m before impact (TTI {tti:F2} s, " +
                    $"intercept {(float.IsPositiveInfinity(interceptTime) ? "none" : $"{interceptTime:F2} s")}, " +
                    $"closure {closingSpeed:F0} m/s, interceptor {interceptorSpeed:F0} m/s)");
                return false;
            }
            float clearanceTime = PalisadeCloner.ReengageClearance / interceptorSpeed;
            if (Time.timeSinceLevelLoad - station.LastFiredTime < Mathf.Max(PalisadeCloner.RefireCooldown, clearanceTime) ||
                station.SalvoInProgress)
            {
                LogDecisionOnce(threat, "cooldown", "is waiting for interceptor refire clearance");
                return false;
            }
            if (!station.Ready())
            {
                LogDecisionOnce(threat, "not-ready", "interceptor station is not ready to fire");
                return false;
            }
            var tracking = aircraft.NetworkHQ?.GetTrackingData(threat.persistentID);
            if (tracking != null && tracking.missileAttacks > 0)
            {
                LogDecisionOnce(threat, "assigned", "is withholding because an interceptor is already assigned");
                return false;
            }
            if (mode == PalisadeCountermeasure.PalisadeMode.SmartEngage && SoftKillIsSufficient(threat, tti, out string softKillReason))
            {
                LogDecisionOnce(threat, "withhold", $"withholding hard kill: {softKillReason}");
                return false;
            }
            reason = mode == PalisadeCountermeasure.PalisadeMode.MaxCoverage
                ? "Max Coverage"
                : "soft-kill resources or response time insufficient";
            return true;
        }

        private static bool TryGetInterceptTime(
            Vector3 relativePosition,
            Vector3 relativeVelocity,
            float interceptorSpeed,
            out float interceptTime)
        {
            float a = relativeVelocity.sqrMagnitude - interceptorSpeed * interceptorSpeed;
            float b = 2f * Vector3.Dot(relativePosition, relativeVelocity);
            float c = relativePosition.sqrMagnitude;
            interceptTime = float.PositiveInfinity;

            if (Mathf.Abs(a) < 0.001f)
            {
                if (b >= -0.001f)
                {
                    return false;
                }
                interceptTime = -c / b;
                return interceptTime > 0f;
            }

            float discriminant = b * b - 4f * a * c;
            if (discriminant < 0f)
            {
                return false;
            }
            float root = Mathf.Sqrt(discriminant);
            float q = -0.5f * (b + (b >= 0f ? root : -root));
            float first = q / a;
            float second = Mathf.Abs(q) > 0.001f ? c / q : float.PositiveInfinity;
            if (first > 0f)
            {
                interceptTime = first;
            }
            if (second > 0f && second < interceptTime)
            {
                interceptTime = second;
            }
            return !float.IsPositiveInfinity(interceptTime);
        }

        private bool SoftKillIsSufficient(Missile threat, float tti, out string reason)
        {
            reason = null;
            if (tti <= PalisadeCloner.SoftKillLeadTime)
            {
                return false;
            }
            string seekerType = threat.GetSeekerType();
            if (seekerType == "IR")
            {
                int flareAmmo = 0;
                foreach (var ejector in aircraft.GetComponentsInChildren<FlareEjector>(true))
                {
                    flareAmmo += ejector.GetAmmo();
                }
                if (flareAmmo >= PalisadeCloner.MinimumFlareReserve)
                {
                    reason = $"{flareAmmo} flares available and {tti:F1} s TTI";
                    return true;
                }
                return false;
            }
            if (seekerType == "ARH" || seekerType == "SARH")
            {
                bool hasRadarCountermeasure = aircraft.GetComponentsInChildren<RadarJammer>(true).Length > 0 ||
                    aircraft.GetComponentsInChildren<ChaffEjector>(true).Length > 0;
                var power = aircraft.GetPowerSupply();
                float charge = power != null ? power.GetCharge() : 0f;
                if (hasRadarCountermeasure && charge >= PalisadeCloner.MinimumCapacitorReserve)
                {
                    reason = $"radar countermeasure available, capacitor {charge:P0}, and {tti:F1} s TTI";
                    return true;
                }
            }
            return false;
        }

        private bool IsCoordinator()
        {
            return FindCoordinator(aircraft) == this;
        }

        private bool ShouldCoordinate()
        {
            if (aircraft.Player != null)
            {
                return aircraft.Player.IsLocalPlayer;
            }
            return aircraft.IsServer;
        }

        private void LogDecisionOnce(Missile threat, string decision, string message)
        {
            int id = threat.GetInstanceID();
            if (lastDecisionByThreat.TryGetValue(id, out string previous) && previous == decision)
            {
                return;
            }
            lastDecisionByThreat[id] = decision;
            PalisadeCloner.Logger?.LogInfo($"[Phase 4] Palisade {message} ({threat.unitName}, {threat.GetSeekerType()}).");
        }

        private void LogStateOnce(string state, string message)
        {
            if (lastState == state)
            {
                return;
            }
            lastState = state;
            PalisadeCloner.Logger?.LogInfo($"[Phase 4] Palisade on {aircraft?.unitName ?? "unknown aircraft"} {message}.");
        }

        internal static void RefreshCountermeasureAmmo(Aircraft aircraft)
        {
            if (aircraft == null)
            {
                return;
            }
            var station = FindStation(aircraft);
            var defenses = GetDefenses(aircraft);
            var coordinator = FindCoordinator(aircraft);
            if (defenses == null || coordinator == null)
            {
                return;
            }
            foreach (var defense in defenses)
            {
                if (defense.countermeasure != null)
                {
                    defense.countermeasure.ammo = defense == coordinator && station != null ? station.Ammo : 0;
                }
            }
        }

        private static PalisadeDefense FindCoordinator(Aircraft aircraft)
        {
            var defenses = GetDefenses(aircraft);
            if (defenses == null || defenses.Count == 0)
            {
                return null;
            }
            PalisadeDefense coordinator = defenses[0];
            for (int i = 1; i < defenses.Count; i++)
            {
                if (defenses[i].GetInstanceID() < coordinator.GetInstanceID())
                {
                    coordinator = defenses[i];
                }
            }
            return coordinator;
        }

        private static List<PalisadeDefense> GetDefenses(Aircraft aircraft)
        {
            if (aircraft == null || !DefensesByAircraft.TryGetValue(aircraft.GetInstanceID(), out var defenses))
            {
                return null;
            }
            for (int i = defenses.Count - 1; i >= 0; i--)
            {
                if (defenses[i] == null || defenses[i].aircraft != aircraft)
                {
                    defenses.RemoveAt(i);
                }
            }
            if (defenses.Count == 0)
            {
                DefensesByAircraft.Remove(aircraft.GetInstanceID());
                return null;
            }
            return defenses;
        }

        private void Unregister()
        {
            if (registeredAircraftId == 0 || !DefensesByAircraft.TryGetValue(registeredAircraftId, out var defenses))
            {
                registeredAircraftId = 0;
                return;
            }
            defenses.Remove(this);
            if (defenses.Count == 0)
            {
                DefensesByAircraft.Remove(registeredAircraftId);
            }
            registeredAircraftId = 0;
        }

        internal static WeaponStation FindStation(Aircraft aircraft)
        {
            if (aircraft == null)
            {
                return null;
            }
            foreach (var station in aircraft.weaponStations)
            {
                if (station != null && station.WeaponInfo == PalisadeCloner.InterceptorInfo)
                {
                    return station;
                }
            }
            return null;
        }
    }
}
