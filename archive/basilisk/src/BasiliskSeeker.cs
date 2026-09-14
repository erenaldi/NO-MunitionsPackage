using System;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class BasiliskSeeker : MissileSeeker
    {
        private const float BothLostSelfDestructDelay = 6f;

        private enum GuidanceChannel
        {
            None,
            Infrared,
            Radar
        }

        [SerializeField] private IRSeeker infrared;
        [SerializeField] private ARHSeeker radar;

        private Unit desiredTarget;
        private GuidanceChannel activeChannel = GuidanceChannel.Radar;
        private float bothLostSince = -1f;
        private bool infraredOperational = true;
        private bool radarOperational = true;
        private GlobalPosition initialAimpoint;
        private float nextSafetyCheck;

        internal bool RetainTargetOnNull => activeChannel == GuidanceChannel.Radar;

        internal void Configure(Missile owner, IRSeeker infraredSeeker, ARHSeeker radarSeeker)
        {
            missile = owner;
            infrared = infraredSeeker;
            radar = radarSeeker;
            triggerMissileWarning = true;
            proximityFuse = true;
        }

        private void Awake()
        {
            if (missile == null)
            {
                missile = GetComponent<Missile>();
            }
            if (infrared == null)
            {
                infrared = GetComponentInChildren<IRSeeker>(true);
            }
            if (radar == null)
            {
                radar = GetComponentInChildren<ARHSeeker>(true);
            }
        }

        public override void Initialize(Unit target, GlobalPosition aimpoint)
        {
            desiredTarget = target;
            initialAimpoint = aimpoint;
            activeChannel = GuidanceChannel.Radar;
            bothLostSince = -1f;
            nextSafetyCheck = 0f;

            TryInitialize(radar, target, aimpoint, "ARH", ref radarOperational);
            if (target != null)
            {
                missile.SetTarget(target);
            }
            if (!radarOperational)
            {
                SwitchToInfrared("ARH initialization failed");
            }
            else
            {
                BasiliskCloner.Logger?.LogInfo(
                    $"[Phase 2B] Basilisk ARH stage initialized for '{target?.unitName ?? "no target"}'.");
            }
        }

        public override void Seek()
        {
            if (missile == null || missile.disabled)
            {
                return;
            }

            GuidanceChannel selected = GuidanceChannel.None;
            if (activeChannel == GuidanceChannel.Radar && radarOperational)
            {
                TrySeek(radar, "ARH", ref radarOperational);
                if (radarOperational && IsRadarHealthy())
                {
                    selected = GuidanceChannel.Radar;
                }
                else
                {
                    SwitchToInfrared("ARH stage defeated");
                }
            }

            if (activeChannel == GuidanceChannel.Infrared && infraredOperational)
            {
                TrySeek(infrared, "IR", ref infraredOperational);
                if (infraredOperational && IsInfraredHealthy())
                {
                    selected = GuidanceChannel.Infrared;
                }
            }

            if (selected != GuidanceChannel.None && desiredTarget != null && missile.targetID.NotValid)
            {
                missile.SetTarget(desiredTarget);
            }
            UpdateSelfDestruct(selected);
        }

        public override string GetSeekerType()
        {
            return activeChannel == GuidanceChannel.Infrared ? "IR" : "ARH";
        }

        public override float GetMinSpeed()
        {
            return radar != null ? radar.GetMinSpeed() : base.GetMinSpeed();
        }

        public override float GetSeekerThreat()
        {
            return Mathf.Max(
                infrared != null ? infrared.GetSeekerThreat() : 0f,
                radar != null ? radar.GetSeekerThreat() : 0f);
        }

        public override GlobalPosition GetEvasionPoint()
        {
            if (activeChannel == GuidanceChannel.Infrared && infrared != null)
            {
                return infrared.GetEvasionPoint();
            }
            return radar != null ? radar.GetEvasionPoint() : base.GetEvasionPoint();
        }

        private void TryInitialize(MissileSeeker seeker, Unit target, GlobalPosition aimpoint,
            string channel, ref bool operational)
        {
            if (seeker == null)
            {
                operational = false;
                BasiliskCloner.Logger?.LogError($"[Phase 2B] Basilisk {channel} channel is missing.");
                return;
            }
            try
            {
                seeker.Initialize(target, aimpoint);
            }
            catch (Exception exception)
            {
                operational = false;
                BasiliskCloner.Logger?.LogError(
                    $"[Phase 2B] Basilisk {channel} initialization failed; channel disabled. {exception}");
            }
        }

        private void TrySeek(MissileSeeker seeker, string channel, ref bool operational)
        {
            try
            {
                seeker.Seek();
            }
            catch (Exception exception)
            {
                operational = false;
                BasiliskCloner.Logger?.LogError(
                    $"[Phase 2B] Basilisk {channel} guidance failed; channel disabled. {exception}");
            }
        }

        private bool IsInfraredHealthy()
        {
            var source = (IRSource)HalberdCloner.GetField(infrared, "IRTarget");
            var target = (Unit)HalberdCloner.GetField(infrared, "targetUnit");
            return source != null && source.transform != null && !source.flare &&
                target != null && !target.disabled;
        }

        private bool IsRadarHealthy()
        {
            var target = (Unit)HalberdCloner.GetField(radar, "targetUnit");
            if (target == null || target.disabled)
            {
                return false;
            }
            bool lockEstablished = (bool)HalberdCloner.GetField(radar, "radarLockEstablished");
            if (!lockEstablished)
            {
                return !(bool)HalberdCloner.GetField(radar, "isJammed");
            }
            float timeWithoutReturn = (float)HalberdCloner.GetField(radar, "timeWithoutReturn");
            float lockPerseverance = (float)HalberdCloner.GetField(radar, "lockPerseverance");
            return timeWithoutReturn <= lockPerseverance;
        }

        private void SwitchToInfrared(string reason)
        {
            if (activeChannel == GuidanceChannel.Infrared)
            {
                return;
            }
            activeChannel = GuidanceChannel.Infrared;
            TryInitialize(infrared, desiredTarget, initialAimpoint, "IR", ref infraredOperational);
            BasiliskCloner.Logger?.LogInfo(
                $"[Phase 2B] Basilisk guidance handoff: ARH -> IR ({reason}).");
        }

        private void UpdateSelfDestruct(GuidanceChannel selected)
        {
            if (Time.timeSinceLevelLoad < nextSafetyCheck)
            {
                return;
            }
            nextSafetyCheck = Time.timeSinceLevelLoad + 0.5f;

            if (selected != GuidanceChannel.None)
            {
                bothLostSince = -1f;
                return;
            }
            if (bothLostSince < 0f)
            {
                bothLostSince = Time.timeSinceLevelLoad;
            }
            else if (Time.timeSinceLevelLoad - bothLostSince > BothLostSelfDestructDelay)
            {
                BasiliskCloner.Logger?.LogInfo("[Phase 2B] Basilisk self-destructing after both seeker channels were lost.");
                missile.Detonate(missile.rb.velocity, false, false);
            }
        }
    }
}
