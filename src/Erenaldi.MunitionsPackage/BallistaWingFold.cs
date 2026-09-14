using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch(typeof(OpticalSeekerCruiseMissile), "TerminalMode")]
    internal static class BallistaWingFoldPatch
    {
        private static void Postfix(OpticalSeekerCruiseMissile __instance)
        {
            BallistaWingFoldController.OnTerminalMode(__instance);
        }
    }

    internal static class BallistaWingFoldController
    {
        private const float StateLimit = 64;

        private static readonly FieldInfo SeekerMissileField = AccessTools.Field(
            typeof(MissileSeeker), "missile");
        private static readonly FieldInfo MissileTargetField = AccessTools.Field(
            typeof(Missile), "target");
        private static readonly FieldInfo CurrentFinAreaField = AccessTools.Field(
            typeof(Missile), "currentFinArea");
        private static readonly FieldInfo SeekerAimPosField = AccessTools.Field(
            typeof(OpticalSeekerCruiseMissile), "aimPos");
        private static readonly FieldInfo SeekerKnownVelField = AccessTools.Field(
            typeof(OpticalSeekerCruiseMissile), "knownVel");

        private sealed class SprintState
        {
            internal Missile Missile;
            internal bool LoftStarted;
            internal float FoldAtTime;
            internal bool FoldTriggered;
        }

        private static readonly Dictionary<int, SprintState> States =
            new Dictionary<int, SprintState>();

        internal static void OnTerminalMode(OpticalSeekerCruiseMissile seeker)
        {
            Missile missile = SeekerMissileField?.GetValue(seeker) as Missile;
            if (!BallistaCloner_IsBallista(missile))
            {
                return;
            }

            SprintState state = GetState(missile);
            if (!state.LoftStarted)
            {
                // Phase 1: the seeker enters terminal mode at 10 km. The
                // vanilla top attack is zeroed at launch for every target that
                // starts within its TooCloseRange (10 km) or is small, so the
                // loft is commanded here instead: the seeker's aim is raised
                // every tick and the missile pitches up with wings deployed.
                state.LoftStarted = true;
                state.FoldAtTime = Time.timeSinceLevelLoad + BallistaCloner.FoldDelaySeconds;
                BallistaCloner.Logger?.LogInfo(
                    $"[Phase 2D] Ballista terminal loft started at {missile.speed:F0} m/s with wings deployed.");
            }

            if (!state.FoldTriggered)
            {
                RaiseAim(seeker, missile);

                float range = float.MaxValue;
                var target = MissileTargetField?.GetValue(missile) as Unit;
                if (target != null && target.rb != null && missile.rb != null)
                {
                    range = FastMath.Distance(missile.GlobalPosition(), target.GlobalPosition());
                }
                if (Time.timeSinceLevelLoad < state.FoldAtTime && range > BallistaCloner.FoldRange)
                {
                    return;
                }

                // Phase 2: fold the wings and light the sprint rocket once the
                // loft climb is established (time-based, or earlier by range).
                state.FoldTriggered = true;
                FoldWings(missile.transform);
                CutAeroReferenceArea(missile);
                IgniteSprint(missile);
                BallistaCloner.Logger?.LogInfo(
                    $"[Phase 2D] Ballista wings folded, fin area cut to {BallistaCloner.TerminalFinArea:F2} m2, " +
                    $"sprint ignited at {missile.speed:F0} m/s, {range:F0} m to target.");
            }
        }

        private static void RaiseAim(OpticalSeekerCruiseMissile seeker, Missile missile)
        {
            // Runs as a postfix, after the seeker has computed and published
            // its aim for this tick; raise the published aimpoint so the
            // missile climbs through the loft phase. GlobalPosition supports
            // Vector3 addition (the seeker's own code relies on it).
            var aimPosValue = SeekerAimPosField?.GetValue(seeker);
            if (aimPosValue == null)
            {
                return;
            }
            var raised = (GlobalPosition)aimPosValue + BallistaCloner.LoftAimRise * Vector3.up;
            var knownVel = SeekerKnownVelField?.GetValue(seeker) as Vector3? ?? Vector3.zero;
            missile.SetAimpoint(raised, knownVel);
        }

        internal static void Remove(Missile missile)
        {
            if (missile != null)
            {
                States.Remove(missile.GetInstanceID());
            }
        }

        private static bool BallistaCloner_IsBallista(Missile missile)
        {
            return missile != null && missile.definition != null &&
                string.Equals(missile.definition.jsonKey, BallistaCloner.MissileJsonKey, StringComparison.Ordinal);
        }

        private static SprintState GetState(Missile missile)
        {
            int id = missile.GetInstanceID();
            if (!States.TryGetValue(id, out SprintState state))
            {
                PruneDestroyedStates();
                state = new SprintState { Missile = missile };
                States[id] = state;
            }
            return state;
        }

        private static void PruneDestroyedStates()
        {
            if (States.Count < StateLimit)
            {
                return;
            }
            var dead = new List<int>();
            foreach (var pair in States)
            {
                // Destroyed Unity objects compare equal to null.
                if (pair.Value.Missile == null)
                {
                    dead.Add(pair.Key);
                }
            }
            foreach (int id in dead)
            {
                States.Remove(id);
            }
        }

        private static void CutAeroReferenceArea(Missile missile)
        {
            // The donor sea-skimmer deploys currentFinArea to its full 2.5 m2
            // at 0.5 s and nothing ever re-folds it; Missile.ApplyAero scales
            // BOTH drag and lift by that area, so the folded missile was still
            // paying 2.5 m2 of drag through the whole sprint. Nothing re-lerps
            // the field after the deploy coroutine finished, so a direct set
            // here persists to impact. Lift authority in the sprint comes from
            // the loft already being established, not from wing area.
            if (CurrentFinAreaField == null)
            {
                BallistaCloner.Logger?.LogWarning("[Phase 2D] Missile.currentFinArea not found; drag cut skipped.");
                return;
            }
            CurrentFinAreaField.SetValue(missile, BallistaCloner.TerminalFinArea);
        }

        private static void FoldWings(Transform missileTransform)
        {
            int folded = 0;
            foreach (Transform wing in missileTransform)
            {
                if (wing.name.StartsWith("WingLeft") || wing.name.StartsWith("WingRight"))
                {
                    wing.localRotation = Quaternion.identity;
                    folded++;
                }
            }
            if (folded == 0)
            {
                BallistaCloner.Logger?.LogWarning("[Phase 2D] Ballista wing fold found no wing transforms.");
            }
        }

        private static void IgniteSprint(Missile missile)
        {
            var motors = HalberdCloner.GetField(missile, "motors") as Array;
            if (motors == null || motors.Length < 2)
            {
                BallistaCloner.Logger?.LogWarning("[Phase 2D] Ballista sprint trigger found no second motor stage.");
                return;
            }
            // Cutting the cruise motor's fuel advances the game's motor stage on
            // the next FixedUpdate; the sprint stage's reserve delay clears so
            // it lights immediately. Burnout(false) only stops looping FX, so
            // the jet plume is stopped explicitly here — otherwise it plays
            // straight through the sprint and masks the dedicated plume.
            var cruise = motors.GetValue(0);
            var cruiseFx = HalberdCloner.GetField(cruise, "particleSystems") as Array;
            if (cruiseFx != null)
            {
                foreach (var value in cruiseFx)
                {
                    if (value is ParticleSystem plume)
                    {
                        plume.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                    }
                }
            }
            var cruiseTrails = HalberdCloner.GetField(cruise, "trailEmitters") as Array;
            if (cruiseTrails != null)
            {
                foreach (var value in cruiseTrails)
                {
                    if (value is TrailEmitter trail)
                    {
                        trail.StopTrail();
                    }
                }
            }
            HalberdCloner.SetField(cruise, "fuelMass", 0f);
            HalberdCloner.SetField(motors.GetValue(1), "delayTimer", 0f);
        }
    }
}
