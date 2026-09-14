using System.Collections.Generic;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class HalberdBoosterJettison
    {
        private const string BoosterNodeName = "Booster";
        private const float LifetimeSeconds = 10f;
        private static readonly HashSet<Missile> Completed = new HashSet<Missile>();

        internal static void TryJettison(Missile missile, int stage)
        {
            if (stage < 1 || !Completed.Add(missile))
            {
                return;
            }

            try
            {
                Jettison(missile);
            }
            catch (System.Exception exception)
            {
                HalberdCloner.Logger?.LogError(
                    $"[Phase 2A] Halberd booster jettison failed without affecting missile control: {exception}");
            }
        }

        private static void Jettison(Missile missile)
        {
            var booster = missile.transform.Find(BoosterNodeName);
            if (booster == null)
            {
                HalberdCloner.Logger?.LogWarning(
                    "[Phase 2A] Halberd booster jettison skipped because the Booster visual was not found.");
                return;
            }

            booster.name = BoosterNodeName + " (Jettisoned)";
            booster.SetParent(null, true);
            foreach (var collider in booster.GetComponentsInChildren<Collider>(true))
            {
                collider.enabled = false;
            }

            var debrisBody = booster.GetComponent<Rigidbody>() ?? booster.gameObject.AddComponent<Rigidbody>();
            debrisBody.mass = 25f;
            debrisBody.drag = 0.1f;
            debrisBody.angularDrag = 0.05f;
            debrisBody.interpolation = RigidbodyInterpolation.Interpolate;
            var missileVelocity = missile.rb != null ? missile.rb.velocity : missile.transform.forward * missile.speed;
            booster.position -= missile.transform.forward * 0.08f;
            debrisBody.velocity = missileVelocity - missile.transform.forward * 30f + Vector3.down * 4f;
            debrisBody.angularVelocity = missile.transform.TransformDirection(
                new Vector3(2.5f, 1.25f, -0.75f));

            Object.Destroy(booster.gameObject, LifetimeSeconds);
            HalberdCloner.Logger?.LogInfo(
                "[Phase 2A] Halberd booster jettisoned at sustainer transition; local debris lifetime 10 s.");
        }

        internal static void Remove(Missile missile)
        {
            if (missile != null)
            {
                Completed.Remove(missile);
            }
        }
    }
}
