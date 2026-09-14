using System;
using System.Collections.Generic;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class KrisThrustVectorVisual : MonoBehaviour
    {
        private const float Response = 8f;

        private sealed class SmoothedTransform
        {
            internal Transform Transform;
            internal Quaternion Rotation;
            internal bool Initialized;
        }

        private readonly List<SmoothedTransform> transforms = new List<SmoothedTransform>();

        private void Awake()
        {
            var missile = GetComponent<Missile>();
            var motors = (Array)HalberdCloner.GetField(missile, "motors");
            foreach (var motor in motors)
            {
                var particles = (ParticleSystem[])HalberdCloner.GetField(motor, "particleSystems");
                foreach (var particle in particles)
                {
                    if (particle != null)
                    {
                        transforms.Add(new SmoothedTransform { Transform = particle.transform });
                    }
                }
            }
        }

        private void LateUpdate()
        {
            float blend = 1f - Mathf.Exp(-Response * Time.deltaTime);
            foreach (var smoothed in transforms)
            {
                if (smoothed.Transform == null)
                {
                    continue;
                }

                Quaternion target = smoothed.Transform.localRotation;
                if (!smoothed.Initialized)
                {
                    smoothed.Rotation = target;
                    smoothed.Initialized = true;
                }
                else
                {
                    smoothed.Rotation = Quaternion.Slerp(smoothed.Rotation, target, blend);
                    smoothed.Transform.localRotation = smoothed.Rotation;
                }
            }
        }
    }
}
