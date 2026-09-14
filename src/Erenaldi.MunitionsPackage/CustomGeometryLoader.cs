using System;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal static class CustomGeometryLoader
    {
        private const string MissilePrefabName = "Erenaldi.AAM44";
        private const string RackPrefabName = "Erenaldi.AAM44_single";

        internal static bool TryApply(
            ManualLogSource logger,
            string resourceName,
            GameObject missileClone,
            GameObject rackClone,
            string missilePrefabName = MissilePrefabName,
            string rackPrefabName = RackPrefabName)
        {
            AssetBundle bundle = null;
            try
            {
                if (!TryLoadBundle(logger, resourceName, out bundle))
                {
                    return false;
                }
                var missileGeometry = bundle.LoadAsset<GameObject>(missilePrefabName);
                var rackGeometry = bundle.LoadAsset<GameObject>(rackPrefabName);
                int applied = 0;
                if (missileGeometry != null)
                {
                    Transplant(missileGeometry, missileClone);
                    applied++;
                }
                else
                {
                    logger.LogWarning($"[Phase 3] Geometry bundle has no prefab named '{missilePrefabName}'.");
                }
                if (rackGeometry != null)
                {
                    Transplant(rackGeometry, rackClone);
                    applied++;
                }
                else
                {
                    logger.LogWarning($"[Phase 3] Geometry bundle has no prefab named '{rackPrefabName}'.");
                }
                logger.LogInfo(
                    $"[Phase 3] Custom geometry applied to '{missilePrefabName}'/'{rackPrefabName}': " +
                    $"{applied} of 2 prefabs transplanted from '{resourceName}'.");
                return applied > 0;
            }
            catch (Exception exception)
            {
                logger.LogWarning($"[Phase 3] Custom geometry load failed; keeping vanilla geometry. {exception.GetType().Name}: {exception.Message}");
                return false;
            }
            finally
            {
                bundle?.Unload(false);
            }
        }

        private static bool TryLoadBundle(ManualLogSource logger, string resourceName, out AssetBundle bundle)
        {
            bundle = null;
            var assembly = typeof(CustomGeometryLoader).Assembly;
            string found = null;
            foreach (var candidate in assembly.GetManifestResourceNames())
            {
                if (string.Equals(candidate, resourceName, StringComparison.OrdinalIgnoreCase) ||
                    candidate.EndsWith("." + resourceName, StringComparison.OrdinalIgnoreCase))
                {
                    found = candidate;
                    break;
                }
                if (found == null && candidate.EndsWith(".bundle", StringComparison.OrdinalIgnoreCase))
                {
                    found = candidate;
                }
            }
            if (found == null)
            {
                logger.LogInfo("[Phase 3] No embedded geometry bundle found; using vanilla geometry.");
                return false;
            }
            using (var stream = assembly.GetManifestResourceStream(found))
            {
                if (stream == null)
                {
                    logger.LogWarning($"[Phase 3] Embedded geometry resource '{found}' could not be opened.");
                    return false;
                }
                using (var memory = new MemoryStream())
                {
                    stream.CopyTo(memory);
                    bundle = AssetBundle.LoadFromMemory(memory.ToArray());
                }
            }
            if (bundle == null)
            {
                logger.LogWarning($"[Phase 3] Geometry bundle '{found}' failed to load; using vanilla geometry.");
                return false;
            }
            logger.LogInfo($"[Phase 3] Loaded geometry bundle '{found}'.");
            return true;
        }

        private static void Transplant(GameObject customRoot, GameObject targetRoot)
        {
            foreach (var renderer in targetRoot.GetComponentsInChildren<MeshRenderer>(true))
            {
                renderer.enabled = false;
            }
            foreach (var renderer in customRoot.GetComponentsInChildren<MeshRenderer>(true))
            {
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null)
                {
                    continue;
                }
                var targetTransform = FindOrCreate(targetRoot.transform, RelativePath(renderer.transform, customRoot.transform));
                CopyLocalTransform(renderer.transform, targetTransform, customRoot.transform);
                var targetFilter = targetTransform.GetComponent<MeshFilter>();
                if (targetFilter == null)
                {
                    targetFilter = targetTransform.gameObject.AddComponent<MeshFilter>();
                }
                targetFilter.sharedMesh = filter.sharedMesh;
                var targetRenderer = targetTransform.GetComponent<MeshRenderer>();
                if (targetRenderer == null)
                {
                    targetRenderer = targetTransform.gameObject.AddComponent<MeshRenderer>();
                }
                targetRenderer.sharedMaterials = renderer.sharedMaterials;
                targetRenderer.enabled = true;
            }
            ReplaceColliders(customRoot, targetRoot);
        }

        private static void ReplaceColliders(GameObject customRoot, GameObject targetRoot)
        {
            foreach (var collider in targetRoot.GetComponentsInChildren<Collider>(true))
            {
                if (collider.GetComponent<ParticleSystem>() != null)
                {
                    continue;
                }
                UnityEngine.Object.DestroyImmediate(collider);
            }
            foreach (var collider in customRoot.GetComponentsInChildren<Collider>(true))
            {
                var target = FindOrCreate(targetRoot.transform, RelativePath(collider.transform, customRoot.transform));
                CopyLocalTransform(collider.transform, target, customRoot.transform);
                if (collider is CapsuleCollider capsule)
                {
                    var cloned = target.gameObject.AddComponent<CapsuleCollider>();
                    cloned.center = capsule.center;
                    cloned.radius = capsule.radius;
                    cloned.height = capsule.height;
                    cloned.direction = capsule.direction;
                }
                else if (collider is BoxCollider box)
                {
                    var cloned = target.gameObject.AddComponent<BoxCollider>();
                    cloned.center = box.center;
                    cloned.size = box.size;
                }
                else if (collider is SphereCollider sphere)
                {
                    var cloned = target.gameObject.AddComponent<SphereCollider>();
                    cloned.center = sphere.center;
                    cloned.radius = sphere.radius;
                }
                else if (collider is MeshCollider mesh)
                {
                    var cloned = target.gameObject.AddComponent<MeshCollider>();
                    cloned.sharedMesh = mesh.sharedMesh;
                    cloned.convex = mesh.convex;
                }
            }
        }

        private static void CopyLocalTransform(Transform source, Transform target, Transform sourceRoot)
        {
            if (source == sourceRoot)
            {
                return;
            }
            target.localPosition = source.localPosition;
            target.localRotation = source.localRotation;
            target.localScale = source.localScale;
        }

        private static string RelativePath(Transform transform, Transform root)
        {
            if (transform == root)
            {
                return string.Empty;
            }
            var segments = new Stack<string>();
            var current = transform;
            while (current != null && current != root)
            {
                segments.Push(current.name);
                current = current.parent;
            }
            return string.Join("/", segments);
        }

        private static Transform FindOrCreate(Transform root, string relativePath)
        {
            if (string.IsNullOrEmpty(relativePath))
            {
                return root;
            }
            var current = root;
            foreach (var segment in relativePath.Split('/'))
            {
                var child = current.Find(segment);
                if (child == null)
                {
                    child = new GameObject(segment).transform;
                    child.SetParent(current, false);
                }
                current = child;
            }
            return current;
        }
    }
}
