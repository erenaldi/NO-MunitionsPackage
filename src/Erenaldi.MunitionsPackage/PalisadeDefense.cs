using System.Collections.Generic;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class PalisadeDefense : MonoBehaviour
    {
        private const float DecisionInterval = 0.1f;
        private const float MinimumClosingSpeed = 25f;
        private Aircraft aircraft;
        private float lastDecisionTime;
        private readonly Dictionary<int, string> lastDecisionByThreat = new Dictionary<int, string>();

        internal void AttachToAircraft(Aircraft attachedAircraft)
        {
            aircraft = attachedAircraft;
        }

        private void Update()
        {
            if (aircraft == null || !ShouldCoordinate() || aircraft.disabled || aircraft.radarAlt < 10f ||
                Time.timeSinceLevelLoad - lastDecisionTime < DecisionInterval || !IsCoordinator())
            {
                return;
            }
            lastDecisionTime = Time.timeSinceLevelLoad;
            RefreshCountermeasureAmmo(aircraft);

            var countermeasures = aircraft.GetComponentsInChildren<PalisadeCountermeasure>(true);
            if (countermeasures.Length == 0 || countermeasures[0].Mode == PalisadeCountermeasure.PalisadeMode.Safe)
            {
                return;
            }
            var station = FindStation(aircraft);
            var warning = aircraft.GetMissileWarningSystem();
            if (station == null || station.Ammo <= 0 || warning == null || warning.knownMissiles == null)
            {
                return;
            }

            Missile bestThreat = null;
            float bestTti = float.MaxValue;
            string bestReason = null;
            foreach (var threat in warning.knownMissiles)
            {
                if (!TryAssessThreat(threat, station, countermeasures[0].Mode, out float tti, out string reason))
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
            station.LaunchMount(aircraft, bestThreat, bestThreat.GlobalPosition());
            RefreshCountermeasureAmmo(aircraft);
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
            if (threat == null || threat.disabled || threat.targetID != aircraft.persistentID)
            {
                return false;
            }
            Vector3 offset = threat.transform.position - aircraft.transform.position;
            float distance = offset.magnitude;
            var requirements = station.WeaponInfo.targetRequirements;
            if (distance < requirements.minRange || distance > requirements.maxRange)
            {
                return false;
            }
            Vector3 relativeVelocity = threat.rb.velocity - aircraft.rb.velocity;
            float closingSpeed = -Vector3.Dot(relativeVelocity, offset / Mathf.Max(distance, 0.01f));
            if (closingSpeed < MinimumClosingSpeed)
            {
                return false;
            }
            tti = distance / closingSpeed;
            float interceptorSpeed = Mathf.Max(station.WeaponInfo.GetMaxSpeed(), 1f);
            if (tti <= distance / interceptorSpeed + 0.15f)
            {
                LogDecisionOnce(threat, "unreachable", $"cannot reach threat at {distance:F0} m before impact");
                return false;
            }
            float clearanceTime = PalisadeCloner.ReengageClearance / interceptorSpeed;
            if (Time.timeSinceLevelLoad - station.LastFiredTime < Mathf.Max(PalisadeCloner.RefireCooldown, clearanceTime) ||
                station.SalvoInProgress)
            {
                return false;
            }
            var tracking = aircraft.NetworkHQ?.GetTrackingData(threat.persistentID);
            if (tracking != null && tracking.missileAttacks > 0)
            {
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
            var defenses = aircraft.GetComponentsInChildren<PalisadeDefense>(true);
            PalisadeDefense coordinator = this;
            foreach (var defense in defenses)
            {
                if (defense != null && defense.GetInstanceID() < coordinator.GetInstanceID())
                {
                    coordinator = defense;
                }
            }
            return coordinator == this;
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

        internal static void RefreshCountermeasureAmmo(Aircraft aircraft)
        {
            if (aircraft == null)
            {
                return;
            }
            var station = FindStation(aircraft);
            var countermeasures = aircraft.GetComponentsInChildren<PalisadeCountermeasure>(true);
            for (int i = 0; i < countermeasures.Length; i++)
            {
                countermeasures[i].ammo = i == 0 && station != null ? station.Ammo : 0;
            }
            if (countermeasures.Length > 0 && GameManager.IsLocalAircraft(aircraft))
            {
                countermeasures[0].UpdateHUD();
            }
        }

        private static WeaponStation FindStation(Aircraft aircraft)
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
