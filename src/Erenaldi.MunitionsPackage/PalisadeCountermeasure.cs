using System.Collections.Generic;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class PalisadeCountermeasure : Countermeasure
    {
        internal enum PalisadeMode
        {
            Safe,
            SmartEngage,
            MaxCoverage
        }

        internal PalisadeMode Mode { get; private set; }
        private bool cycleArmed = true;

        protected override void Awake()
        {
            // Hardpoint.SpawnMount attaches countermeasures before the dormant clone is activated.
            enabled = true;
        }

        internal void Configure(PalisadeMode initialMode, Sprite icon)
        {
            displayName = "Palisade";
            displayImage = icon;
            chargeable = true;
            Mode = initialMode;
            ammo = PalisadeCloner.RoundsPerPod;
        }

        public override List<string> GetThreatTypes()
        {
            if (threatTypes == null)
            {
                threatTypes = new List<string> { "MISSILE" };
            }
            return threatTypes;
        }

        public override void AttachToUnit(Aircraft attachedAircraft)
        {
            base.AttachToUnit(attachedAircraft);
            var defense = GetComponent<PalisadeDefense>();
            if (defense != null)
            {
                defense.AttachToAircraft(attachedAircraft);
            }
        }

        public override void Fire()
        {
            if (!cycleArmed || aircraft == null || !GameManager.IsLocalAircraft(aircraft))
            {
                return;
            }
            cycleArmed = false;
            Mode = (PalisadeMode)(((int)Mode + 1) % 3);
            UpdateHUD();
            if (SceneSingleton<AircraftActionsReport>.i != null)
            {
                SceneSingleton<AircraftActionsReport>.i.ReportText($"Palisade: {ModeLabel}", 2f);
            }
            PalisadeCloner.Logger?.LogInfo($"[Phase 4] Palisade mode on {aircraft?.unitName ?? "unknown aircraft"}: {ModeLabel}.");
        }

        public override void Rearm(Aircraft attachedAircraft, Unit rearmer)
        {
            PalisadeDefense.RefreshCountermeasureAmmo(attachedAircraft);
            if (GameManager.IsLocalAircraft(attachedAircraft))
            {
                UpdateHUD();
            }
        }

        public override void UpdateHUD()
        {
            if (aircraft != null && GameManager.IsLocalAircraft(aircraft) && SceneSingleton<CombatHUD>.i != null)
            {
                SceneSingleton<CombatHUD>.i.DisplayCountermeasures($"Palisade: {ModeLabel}", displayImage, ammo);
            }
        }

        private void Update()
        {
            if (aircraft != null && !aircraft.countermeasureTrigger)
            {
                cycleArmed = true;
            }
        }

        private string ModeLabel
        {
            get
            {
                switch (Mode)
                {
                    case PalisadeMode.SmartEngage:
                        return "Smart Engage";
                    case PalisadeMode.MaxCoverage:
                        return "Max Coverage";
                    default:
                        return "Safe";
                }
            }
        }
    }
}
