using System.IO;
using Erenaldi.Ballista;
using Erenaldi.Halberd;
using Erenaldi.Kris;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Munitions
{
    public static class MunitionsGeometryBundleBuilder
    {
        private const string BundleName = "erenaldi_munitions.geometry";
        private const string BundleFolder = "BlueprinterCache/MunitionsGeometry";

        [MenuItem("Blueprinter/Munitions/Build Geometry Bundle")]
        public static void BuildBundle()
        {
            BuildBundle(true);
        }

        [MenuItem("Blueprinter/Munitions/Rebuild Halberd Geometry Bundle")]
        public static void BuildHalberdBundle()
        {
            BuildBundle(false);
        }

        private static void BuildBundle(bool rebuildKris)
        {
            HalberdMeshBuilder.Build();
            if (rebuildKris)
            {
                KrisMeshBuilder.Build();
            }
            BallistaMeshBuilder.Build();

            var bundleFolder = Path.GetFullPath(BundleFolder);
            Directory.CreateDirectory(bundleFolder);
            var builds = new[]
            {
                new AssetBundleBuild
                {
                    assetBundleName = BundleName,
                    assetNames = new[]
                    {
                        HalberdMeshBuilder.OutputRoot + "/" + HalberdMeshBuilder.MissilePrefabName + ".prefab",
                        HalberdMeshBuilder.OutputRoot + "/" + HalberdMeshBuilder.RackPrefabName + ".prefab",
                        KrisMeshBuilder.OutputRoot + "/" + KrisMeshBuilder.MissilePrefabName + ".prefab",
                        KrisMeshBuilder.OutputRoot + "/" + KrisMeshBuilder.RackPrefabName + ".prefab",
                        BallistaMeshBuilder.OutputRoot + "/" + BallistaMeshBuilder.MissilePrefabName + ".prefab",
                        BallistaMeshBuilder.OutputRoot + "/" + BallistaMeshBuilder.RackPrefabName + ".prefab"
                    }
                }
            };
            if (BuildPipeline.BuildAssetBundles(bundleFolder, builds, BuildAssetBundleOptions.ForceRebuildAssetBundle, BuildTarget.StandaloneWindows64) == null)
            {
                throw new System.InvalidOperationException("Failed to build munitions geometry bundle");
            }

            var sourcePath = Path.Combine(bundleFolder, BundleName);
            var outputPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "src", "Erenaldi.MunitionsPackage", "erenaldi_munitions.geometry.bundle"));
            File.Copy(sourcePath, outputPath, true);

            ValidateBundle(outputPath, rebuildKris);
            Debug.Log("[Munitions] Geometry bundle built: " + outputPath);
        }

        private static void ValidateBundle(string outputPath, bool validateRebuiltKris)
        {
            var bundle = AssetBundle.LoadFromFile(outputPath);
            if (bundle == null)
            {
                throw new System.InvalidOperationException("Built munitions geometry bundle could not be reopened");
            }
            try
            {
                ValidateMissile(bundle, HalberdMeshBuilder.MissilePrefabName, new[] { "Intakes", "SustainerFins", "Hardware", "SustainerNozzle", "Booster", "Booster/Fins", "Booster/Nozzle", "Booster/NozzleRecess" });
                ValidateRack(bundle, HalberdMeshBuilder.RackPrefabName, new[] { "pylon/aam4/Intakes", "pylon/aam4/SustainerFins", "pylon/aam4/Hardware", "pylon/aam4/SustainerNozzle", "pylon/aam4/Booster", "pylon/aam4/Booster/Fins", "pylon/aam4/Booster/Nozzle", "pylon/aam4/Booster/NozzleRecess" });
                ValidateTexturedMesh(bundle, HalberdMeshBuilder.MissilePrefabName, null);
                ValidateTexturedMesh(bundle, HalberdMeshBuilder.MissilePrefabName, "Booster");
                ValidateTexturedMesh(bundle, HalberdMeshBuilder.RackPrefabName, "pylon/aam4");
                ValidateTexturedMesh(bundle, HalberdMeshBuilder.RackPrefabName, "pylon/aam4/Booster");
                ValidateMissile(bundle, KrisMeshBuilder.MissilePrefabName, new[] { "Hardware", "Dark", "Seeker", "GridFins" });
                ValidateRack(bundle, KrisMeshBuilder.RackPrefabName, new[] { "pylon/aam1/Hardware", "pylon/aam1/Dark", "pylon/aam1/Seeker", "pylon/aam1/GridFins" });
                if (validateRebuiltKris)
                {
                    ValidateKrisGeometry(bundle, KrisMeshBuilder.MissilePrefabName, KrisMeshBuilder.RackPrefabName);
                }
                ValidateBallista(bundle, BallistaMeshBuilder.MissilePrefabName, BallistaMeshBuilder.RackPrefabName);
            }
            finally
            {
                bundle.Unload(true);
            }
        }

        private static void ValidateBallista(AssetBundle bundle, string missilePrefabName, string rackPrefabName)
        {
            var missile = bundle.LoadAsset<GameObject>(missilePrefabName);
            if (missile == null || missile.GetComponent<MeshFilter>()?.sharedMesh == null ||
                missile.GetComponent<MeshRenderer>()?.sharedMaterial == null ||
                missile.GetComponent<CapsuleCollider>() == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + missilePrefabName + " missile prefab");
            }
            if (Mathf.Abs(missile.GetComponent<CapsuleCollider>().height - BallistaMeshBuilder.TotalLength) > 0.001f ||
                Mathf.Abs(missile.GetComponent<CapsuleCollider>().radius - BallistaMeshBuilder.BodyHalfWidth) > 0.001f)
            {
                throw new System.InvalidOperationException("Built bundle Ballista missile capsule is incorrect");
            }
            var wingLeft = missile.transform.Find("WingLeft");
            var wingRight = missile.transform.Find("WingRight");
            if (wingLeft == null || wingRight == null)
            {
                throw new System.InvalidOperationException("Built bundle Ballista missile is missing wing groups");
            }
            if (Mathf.Abs(wingLeft.localPosition.x - (-BallistaMeshBuilder.WingPivotXRight)) > 0.0005f ||
                Mathf.Abs(wingLeft.localPosition.y - BallistaMeshBuilder.WingPivotY) > 0.0005f ||
                Mathf.Abs(wingLeft.localPosition.z - BallistaMeshBuilder.WingPivotZ) > 0.0005f ||
                Mathf.Abs(wingRight.localPosition.x - BallistaMeshBuilder.WingPivotXRight) > 0.0005f)
            {
                throw new System.InvalidOperationException("Built bundle Ballista wing pivots are incorrect");
            }
            // Deployed missile wings sweep out-and-aft at 45 degrees via Y rotation.
            if (Quaternion.Angle(wingLeft.localRotation, Quaternion.Euler(0f, 45f, 0f)) > 0.1f ||
                Quaternion.Angle(wingRight.localRotation, Quaternion.Euler(0f, -45f, 0f)) > 0.1f)
            {
                throw new System.InvalidOperationException("Built bundle Ballista wing deployment rotations are incorrect");
            }
            ValidateBallistaChildren(missile.transform, missilePrefabName);
            var mesh = missile.GetComponent<MeshFilter>().sharedMesh;
            if (Mathf.Abs(mesh.bounds.max.z - BallistaMeshBuilder.TotalLength * 0.5f) > 0.001f)
            {
                throw new System.InvalidOperationException("Built bundle Ballista missile body nose is off datum");
            }

            var rack = bundle.LoadAsset<GameObject>(rackPrefabName);
            var pylon = rack == null ? null : rack.transform.Find("pylon");
            var mountedMissile = rack == null ? null : rack.transform.Find("pylon/agm1");
            if (rack == null || pylon == null || mountedMissile == null ||
                pylon.GetComponent<MeshFilter>()?.sharedMesh == null ||
                mountedMissile.GetComponent<CapsuleCollider>() == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + rackPrefabName + " rack prefab");
            }
            if (Mathf.Abs(mountedMissile.localPosition.y - BallistaMeshBuilder.RackMissileOffsetY) > 0.0005f)
            {
                throw new System.InvalidOperationException("Built bundle Ballista rack display offset is incorrect");
            }
            ValidateBallistaChildren(mountedMissile.transform, rackPrefabName);
        }

        private static void ValidateBallistaChildren(Transform root, string prefabName)
        {
            int renderers = root.GetComponentsInChildren<MeshRenderer>(true).Length;
            if (renderers != 25)
            {
                throw new System.InvalidOperationException(
                    "Built bundle Ballista geometry at " + prefabName + " has " + renderers +
                    " renderers; expected 25 (root + 24 group children)");
            }
        }

        private static void ValidateMissile(AssetBundle bundle, string prefabName, string[] childPaths)
        {
            var missile = bundle.LoadAsset<GameObject>(prefabName);
            if (missile == null || missile.GetComponent<MeshFilter>() == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + prefabName + " missile prefab");
            }
            foreach (var childPath in childPaths)
            {
                if (missile.transform.Find(childPath) == null)
                {
                    throw new System.InvalidOperationException("Built bundle missile " + prefabName + " is missing child " + childPath);
                }
            }
        }

        private static void ValidateRack(AssetBundle bundle, string prefabName, string[] childPaths)
        {
            var rack = bundle.LoadAsset<GameObject>(prefabName);
            if (rack == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + prefabName + " rack prefab");
            }
            foreach (var childPath in childPaths)
            {
                if (rack.transform.Find(childPath) == null)
                {
                    throw new System.InvalidOperationException("Built bundle rack " + prefabName + " is missing child " + childPath);
                }
            }
        }

        private static void ValidateTexturedMesh(AssetBundle bundle, string prefabName, string childPath)
        {
            var prefab = bundle.LoadAsset<GameObject>(prefabName);
            var target = prefab == null ? null : childPath == null ? prefab.transform : prefab.transform.Find(childPath);
            var mesh = target != null ? target.GetComponent<MeshFilter>()?.sharedMesh : null;
            var material = target != null ? target.GetComponent<MeshRenderer>()?.sharedMaterial : null;
            var texture = material != null
                ? material.GetTexture("_BaseMap") ?? material.GetTexture("_MainTex")
                : null;
            bool hasUvs = mesh != null && mesh.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0);
            if (!hasUvs || texture == null)
            {
                throw new System.InvalidOperationException(
                    "Built bundle has invalid textured geometry at " + prefabName + "/" + (childPath ?? "<root>") +
                    ": mesh=" + (mesh != null) +
                    ", vertices=" + (mesh != null ? mesh.vertexCount : 0) +
                    ", hasUvs=" + hasUvs +
                    ", material=" + (material != null) +
                    ", texture=" + (texture != null));
            }
        }

        private static void ValidateKrisGeometry(AssetBundle bundle, string missilePrefabName, string rackPrefabName)
        {
            ValidateKrisMissile(bundle, missilePrefabName);
            ValidateKrisRack(bundle, rackPrefabName);
        }

        private static void ValidateKrisMissile(AssetBundle bundle, string prefabName)
        {
            var missile = bundle.LoadAsset<GameObject>(prefabName);
            if (missile == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + prefabName + " missile prefab");
            }
            if (missile.GetComponentsInChildren<MeshRenderer>(true).Length != 5)
            {
                throw new System.InvalidOperationException("Built bundle Kris missile does not contain exactly five renderers");
            }
            ValidateKrisRenderer(missile.transform, prefabName + "/<root>");
            ValidateKrisCapsule(missile.transform, prefabName + "/<root>");
            foreach (var childPath in new[] { "Hardware", "Dark", "Seeker", "GridFins" })
            {
                var child = missile.transform.Find(childPath);
                if (child == null)
                {
                    throw new System.InvalidOperationException("Built bundle missile " + prefabName + " is missing child " + childPath);
                }
                ValidateKrisRenderer(child, prefabName + "/" + childPath);
            }
        }

        private static void ValidateKrisRack(AssetBundle bundle, string prefabName)
        {
            var rack = bundle.LoadAsset<GameObject>(prefabName);
            if (rack == null)
            {
                throw new System.InvalidOperationException("Built bundle has an invalid " + prefabName + " rack prefab");
            }
            var pylon = rack.transform.Find("pylon");
            var mountedMissile = rack.transform.Find("pylon/aam1");
            if (pylon == null || mountedMissile == null)
            {
                throw new System.InvalidOperationException("Built bundle rack " + prefabName + " is missing pylon/aam1");
            }
            if (pylon.GetComponent<MeshFilter>()?.sharedMesh == null ||
                pylon.GetComponent<MeshRenderer>()?.sharedMaterial == null ||
                pylon.GetComponent<BoxCollider>() == null ||
                mountedMissile.GetComponentsInChildren<MeshRenderer>(true).Length != 5 ||
                Mathf.Abs(mountedMissile.localPosition.y - KrisMeshBuilder.RackMissileOffsetY) > 0.001f ||
                Quaternion.Angle(mountedMissile.localRotation, Quaternion.Euler(0f, 0f, KrisMeshBuilder.RackRollDegrees)) > 0.1f)
            {
                throw new System.InvalidOperationException("Built bundle Kris rack display has invalid pylon alignment or strake clearance");
            }
            ValidateKrisRenderer(mountedMissile, prefabName + "/pylon/aam1");
            ValidateKrisCapsule(mountedMissile, prefabName + "/pylon/aam1");
            foreach (var childPath in new[] { "Hardware", "Dark", "Seeker", "GridFins" })
            {
                var child = mountedMissile.Find(childPath);
                if (child == null)
                {
                    throw new System.InvalidOperationException("Built bundle rack " + prefabName + " is missing child pylon/aam1/" + childPath);
                }
                ValidateKrisRenderer(child, prefabName + "/pylon/aam1/" + childPath);
            }
        }

        private static bool IsKrisBodyLabel(string label)
        {
            return label.EndsWith("/<root>") || label.EndsWith("pylon/aam1") || label.EndsWith("/aam1");
        }

        private static void ValidateKrisRenderer(Transform transform, string label)
        {
            var mesh = transform.GetComponent<MeshFilter>()?.sharedMesh;
            var material = transform.GetComponent<MeshRenderer>()?.sharedMaterial;
            if (mesh == null || material == null)
            {
                throw new System.InvalidOperationException(
                    "Built bundle has invalid Kris geometry at " + label +
                    ": mesh=" + (mesh != null) + ", material=" + (material != null));
            }
            if (IsKrisBodyLabel(label))
            {
                // Body material is texture-driven; validate structure instead of flat color.
                if (material.name != "MatKrisBody" ||
                    Mathf.Abs(material.color.r - 1f) > 0.001f ||
                    Mathf.Abs(material.color.g - 1f) > 0.001f ||
                    Mathf.Abs(material.color.b - 1f) > 0.001f ||
                    Mathf.Abs(material.GetFloat("_Metallic") - 1f) > 0.001f ||
                    material.GetTexture("_MetallicGlossMap") == null ||
                    material.GetTexture("_BaseMap") == null)
                {
                    throw new System.InvalidOperationException("Built bundle has incorrect Kris body textured material at " + label);
                }
                return;
            }

            string expectedMaterial;
            Color expectedColor;
            float expectedMetallic;
            float expectedSmoothness;
            if (label.EndsWith("/Dark"))
            {
                expectedMaterial = "MatKrisDark";
                expectedColor = new Color(0.033105f, 0.039546f, 0.042311f);
                expectedMetallic = 0.1f;
                expectedSmoothness = 0.35f;
            }
            else if (label.EndsWith("/GridFins"))
            {
                expectedMaterial = "MatKrisGridFins";
                expectedColor = new Color(0.0185f, 0.023153f, 0.026241f);
                expectedMetallic = 0.35f;
                expectedSmoothness = 0.45f;
            }
            else if (label.EndsWith("/Seeker"))
            {
                expectedMaterial = "MatKrisSeeker";
                expectedColor = new Color(0.008568f, 0.019382f, 0.026241f);
                expectedMetallic = 0.05f;
                expectedSmoothness = 0.94f;
            }
            else
            {
                expectedMaterial = "MatKrisHardware";
                expectedColor = new Color(0.270498f, 0.309469f, 0.309469f);
                expectedMetallic = 0.35f;
                expectedSmoothness = 0.45f;
            }
            var color = material.color;
            if (material.name != expectedMaterial ||
                Mathf.Abs(color.r - expectedColor.r) > 0.001f ||
                Mathf.Abs(color.g - expectedColor.g) > 0.001f ||
                Mathf.Abs(color.b - expectedColor.b) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Metallic") - expectedMetallic) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - expectedSmoothness) > 0.001f)
            {
                throw new System.InvalidOperationException("Built bundle has incorrect Kris material at " + label);
            }
            if (label.EndsWith("/Seeker") &&
                (Mathf.Abs(material.GetFloat("_ClearCoat") - 1f) > 0.001f ||
                 Mathf.Abs(material.GetFloat("_ClearCoatMask") - 1f) > 0.001f ||
                 Mathf.Abs(material.GetFloat("_ClearCoatSmoothness") - 0.975f) > 0.001f ||
                 !material.IsKeywordEnabled("_CLEARCOAT")))
            {
                throw new System.InvalidOperationException("Built bundle has incorrect Kris seeker clearcoat at " + label);
            }
        }

        private static void ValidateKrisCapsule(Transform transform, string label)
        {
            var capsule = transform.GetComponent<CapsuleCollider>();
            if (capsule == null ||
                Mathf.Abs(capsule.height - KrisMeshBuilder.TotalLength) > 0.001f ||
                Mathf.Abs(capsule.radius - KrisMeshBuilder.BodyRadius) > 0.001f ||
                capsule.direction != 2)
            {
                throw new System.InvalidOperationException(
                    "Built bundle has invalid Kris capsule at " + label +
                    ": height=" + (capsule != null ? capsule.height : 0f) +
                    ", radius=" + (capsule != null ? capsule.radius : 0f) +
                    ", direction=" + (capsule != null ? capsule.direction : 0));
            }
        }
    }
}
