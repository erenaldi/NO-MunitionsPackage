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
            foreach (var dependency in UnityEditor.AssetDatabase.GetDependencies(builds[0].assetNames, true))
            {
                if (dependency.ToLowerInvariant().Contains("/reference/") ||
                    dependency.ToLowerInvariant().Contains("/texturepreviews/"))
                {
                    throw new System.InvalidOperationException("Shipping prefab depends on a reference/preview asset: " + dependency);
                }
            }
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
                ValidateTexturedMaterial(bundle, HalberdMeshBuilder.MissilePrefabName, null);
                ValidateTexturedMaterial(bundle, HalberdMeshBuilder.MissilePrefabName, "Booster");
                ValidateTexturedMaterial(bundle, HalberdMeshBuilder.RackPrefabName, "pylon/aam4");
                ValidateTexturedMaterial(bundle, HalberdMeshBuilder.RackPrefabName, "pylon/aam4/Booster");
                ValidateTexturedMaterial(bundle, HalberdMeshBuilder.MissilePrefabName, "Intakes", false);
                ValidateHalberdPlainShared(bundle, HalberdMeshBuilder.MissilePrefabName);
                ValidateMissile(bundle, KrisMeshBuilder.MissilePrefabName, new[] { "Hardware", "Dark", "Seeker", "GridFins" });
                ValidateRack(bundle, KrisMeshBuilder.RackPrefabName, new[] { "pylon/aam1/Hardware", "pylon/aam1/Dark", "pylon/aam1/Seeker", "pylon/aam1/GridFins" });
                if (validateRebuiltKris)
                {
                    ValidateKrisGeometry(bundle, KrisMeshBuilder.MissilePrefabName, KrisMeshBuilder.RackPrefabName);
                }
                ValidateBallista(bundle, BallistaMeshBuilder.MissilePrefabName, BallistaMeshBuilder.RackPrefabName);
                ValidateTexturedMaterial(bundle, KrisMeshBuilder.MissilePrefabName, null);
                ValidateTexturedMaterial(bundle, KrisMeshBuilder.RackPrefabName, "pylon/aam1");
                ValidateTexturedMaterial(bundle, BallistaMeshBuilder.MissilePrefabName, null);
                ValidateTexturedMaterial(bundle, BallistaMeshBuilder.MissilePrefabName, "FixedHardware_Panel");
                ValidateTexturedMaterial(bundle, BallistaMeshBuilder.MissilePrefabName, "WingLeft");
                ValidateBallistaWingUvs(bundle, BallistaMeshBuilder.MissilePrefabName);
                ValidateCylindricalUvs(bundle, HalberdMeshBuilder.MissilePrefabName, null, "Halberd body");
                ValidateCylindricalUvs(bundle, HalberdMeshBuilder.MissilePrefabName, "Booster", "Halberd booster");
                ValidateCylindricalUvs(bundle, KrisMeshBuilder.MissilePrefabName, null, "Kris body");
                ValidateCylindricalUvs(bundle, BallistaMeshBuilder.MissilePrefabName, null, "Ballista body");
                ValidateTextureMirrorSymmetry(bundle, HalberdMeshBuilder.MissilePrefabName, null, "Halberd body");
                ValidateTextureMirrorSymmetry(bundle, HalberdMeshBuilder.MissilePrefabName, "Booster", "Halberd booster");
                ValidateTextureMirrorSymmetry(bundle, KrisMeshBuilder.MissilePrefabName, null, "Kris body");
                ValidateTextureMirrorSymmetry(bundle, BallistaMeshBuilder.MissilePrefabName, null, "Ballista body");
                ValidateTextureMirrorSymmetry(bundle, BallistaMeshBuilder.MissilePrefabName, "WingLeft", "Ballista wing");
                ValidateNoReferenceAssets(bundle);
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

        private static void ValidateTexturedMaterial(AssetBundle bundle, string prefabName, string childPath, bool expectWhiteTint = true)
        {
            var prefab = bundle.LoadAsset<GameObject>(prefabName);
            var target = prefab == null ? null : childPath == null ? prefab.transform : prefab.transform.Find(childPath);
            var material = target != null ? target.GetComponent<MeshRenderer>()?.sharedMaterial : null;
            var albedo = material != null ? material.GetTexture("_BaseMap") ?? material.GetTexture("_MainTex") : null;
            var packed = material != null ? material.GetTexture("_MetallicGlossMap") : null;
            var label = prefabName + "/" + (childPath ?? "<root>");
            if (material == null || albedo == null || packed == null)
            {
                throw new System.InvalidOperationException(
                    "Built bundle textured material at " + label +
                    ": material=" + (material != null) +
                    ", albedo=" + (albedo != null) +
                    ", packed=" + (packed != null));
            }
            if (expectWhiteTint &&
                (Mathf.Abs(material.color.r - 1f) > 0.001f ||
                 Mathf.Abs(material.color.g - 1f) > 0.001f ||
                 Mathf.Abs(material.color.b - 1f) > 0.001f))
            {
                throw new System.InvalidOperationException("Built bundle textured material at " + label + " is not white-tinted");
            }
            if (Mathf.Abs(material.GetFloat("_Metallic") - 1f) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - 1f) > 0.001f ||
                !material.IsKeywordEnabled("_METALLICSPECGLOSSMAP"))
            {
                throw new System.InvalidOperationException("Built bundle textured material at " + label + " is not texture-driven");
            }
            var albedo2d = albedo as Texture2D;
            var packed2d = packed as Texture2D;
            if (albedo2d == null || packed2d == null)
            {
                throw new System.InvalidOperationException("Built bundle material at " + label + " requires Texture2D maps");
            }
            if (albedo2d != null && !UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(albedo2d.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Built bundle albedo at " + label + " is not sRGB (format=" + albedo2d.graphicsFormat + "); expected sRGB");
            }
            if (packed2d != null && UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(packed2d.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Built bundle packed MS at " + label + " is sRGB (format=" + packed2d.graphicsFormat + "); expected linear");
            }
        }

        private static void ValidateHalberdPlainShared(AssetBundle bundle, string prefabName)
        {
            var prefab = bundle.LoadAsset<GameObject>(prefabName);
            Texture2D sharedAlbedo = null;
            Texture2D sharedPacked = null;
            foreach (var childPath in new[] { "Intakes", "SustainerFins", "Hardware", "SustainerNozzle", "Booster/Fins" })
            {
                var child = prefab.transform.Find(childPath);
                var material = child?.GetComponent<MeshRenderer>()?.sharedMaterial;
                var albedo = material?.GetTexture("_BaseMap") as Texture2D;
                var packed = material?.GetTexture("_MetallicGlossMap") as Texture2D;
                if (albedo == null || packed == null)
                {
                    throw new System.InvalidOperationException("Built bundle Halberd plain material at " + childPath + " is missing textures");
                }
                if (sharedAlbedo == null)
                {
                    sharedAlbedo = albedo;
                    sharedPacked = packed;
                }
                else if (albedo != sharedAlbedo || packed != sharedPacked)
                {
                    throw new System.InvalidOperationException("Built bundle Halberd plain materials do not share one albedo/MS texture pair");
                }
            }
        }

        private static void ValidateBallistaWingUvs(AssetBundle bundle, string prefabName)
        {
            var missile = bundle.LoadAsset<GameObject>(prefabName);
            foreach (var wingPath in new[] { "WingLeft", "WingRight", "TailControl1", "TailControl2", "TailControl3", "TailControl4" })
            {
                var wing = missile.transform.Find(wingPath);
                var mesh = wing != null ? wing.GetComponent<MeshFilter>()?.sharedMesh : null;
                if (mesh == null || !mesh.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Built bundle Ballista wing " + wingPath + " has no UVs");
                }
                var vertices = mesh.vertices;
                var uvs = mesh.uv;
                float sumU = 0f, sumX = 0f, sumV = 0f, sumZ = 0f;
                float sumU2 = 0f, sumX2 = 0f, sumV2 = 0f, sumZ2 = 0f;
                float sumUx = 0f, sumVz = 0f;
                for (int i = 0; i < vertices.Length; i++)
                {
                    float u = uvs[i].x, v = uvs[i].y, x = vertices[i].x, z = vertices[i].z;
                    sumU += u; sumX += x; sumV += v; sumZ += z;
                    sumU2 += u * u; sumX2 += x * x; sumV2 += v * v; sumZ2 += z * z;
                    sumUx += u * x; sumVz += v * z;
                }
                float corrUx = Correlation(vertices.Length, sumU, sumX, sumU2, sumX2, sumUx);
                float corrVz = Correlation(vertices.Length, sumV, sumZ, sumV2, sumZ2, sumVz);
                if (float.IsNaN(corrUx) || float.IsNaN(corrVz) || float.IsInfinity(corrUx) || float.IsInfinity(corrVz) || corrUx < 0.9f || corrVz < 0.9f)
                {
                    throw new System.InvalidOperationException(
                        "Built bundle Ballista wing " + wingPath + " UVs are not planar: corr(u,x)=" +
                        corrUx.ToString("F3") + ", corr(v,z)=" + corrVz.ToString("F3"));
                }
            }
        }

        private static float Correlation(int n, float sumA, float sumB, float sumA2, float sumB2, float sumAB)
        {
            if (n < 2)
            {
                return 0f;
            }
            float numerator = n * sumAB - sumA * sumB;
            float denominator = Mathf.Sqrt((n * sumA2 - sumA * sumA) * (n * sumB2 - sumB * sumB));
            if (denominator < 1e-9f)
            {
                return 0f;
            }
            return numerator / denominator;
        }

        /// <summary>
        /// The cylindrical unwrap (u = (atan2(y,x)+pi)/2pi, v = z-normalized)
        /// maps the geometric mirror across the x-z plane (y -> -y) onto the
        /// texture mirror u -> 1-u. Verify the actual mesh UVs follow that
        /// formula so a texture symmetric under u -> 1-u is a real geometric
        /// mirror on the body, not just a texture-internal coincidence. The u
        /// coordinate is checked exactly (scale-independent); v is checked for
        /// z-monotonicity only, because the Kris body unwrap normalizes v
        /// against the pre-scale bounds (RecalculateBounds runs after the
        /// unwrap there), which shifts v by a constant without breaking the
        /// mirror mapping.
        /// </summary>
        private static void ValidateCylindricalUvs(AssetBundle bundle, string prefabName, string childPath, string label)
        {
            var prefab = bundle.LoadAsset<GameObject>(prefabName);
            var target = prefab == null ? null : childPath == null ? prefab.transform : prefab.transform.Find(childPath);
            var mesh = target != null ? target.GetComponent<MeshFilter>()?.sharedMesh : null;
            if (mesh == null || !mesh.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
            {
                throw new System.InvalidOperationException("Built bundle has no cylindrical UVs at " + label);
            }
            var vertices = mesh.vertices;
            var uvs = mesh.uv;
            float maxUError = 0f;
            float sumV = 0f, sumZ = 0f, sumV2 = 0f, sumZ2 = 0f, sumVz = 0f;
            for (int i = 0; i < vertices.Length; i++)
            {
                float expectedU = (Mathf.Atan2(vertices[i].y, vertices[i].x) + Mathf.PI) / (Mathf.PI * 2f);
                float du = Mathf.Abs(uvs[i].x - expectedU);
                du = Mathf.Min(du, 1f - du);
                maxUError = Mathf.Max(maxUError, du);
                float v = uvs[i].y;
                float z = vertices[i].z;
                sumV += v; sumZ += z; sumV2 += v * v; sumZ2 += z * z; sumVz += v * z;
            }
            float corrVz = Correlation(vertices.Length, sumV, sumZ, sumV2, sumZ2, sumVz);
            if (maxUError > 0.01f)
            {
                throw new System.InvalidOperationException(
                    "Built bundle cylindrical UVs at " + label + " deviate from the mirror-safe unwrap: max u error " +
                    maxUError.ToString("F4") + " (expected <= 0.01)");
            }
            if (float.IsNaN(corrVz) || corrVz < 0.99f)
            {
                throw new System.InvalidOperationException(
                    "Built bundle cylindrical UVs at " + label + " are not z-monotonic: corr(v,z)=" +
                    corrVz.ToString("F3") + " (expected >= 0.99)");
            }
        }

        /// <summary>
        /// Pixel-based symmetry check on the shipped albedo texture for all
        /// three cylindrical-unwrap transformations:
        ///   y-mirror (x-z plane, y -> -y):  u -> 1-u
        ///   x-mirror (y-z plane, x -> -x):  u -> (1.5-u) mod 1
        ///   180 roll (z-axis):              u -> u+0.5 mod 1 (rotation, not
        ///   a reflection)
        /// A deterministic marking must match its transformed pixel under each
        /// transformation. The tolerance is 0.12 max-channel difference,
        /// justified by measurement: the stochastic grunge mirror diff peaks
        /// at 0.098 on the lightest base (0.77, 400k-sample measurement), and
        /// the faintest one-sided marking in these textures is 0.18 (Ballista
        /// SeamLight on the dark base) — so 0.12 neither false-positives on
        /// grunge nor hides the actual marks. A +/-1 pixel tolerance absorbs
        /// the u = x/(W-1) rounding at each transformed position.
        /// </summary>
        private static void ValidateTextureMirrorSymmetry(AssetBundle bundle, string prefabName, string childPath, string label)
        {
            const float diffThreshold = 0.12f;
            const float maxMismatchFraction = 0.0005f;
            var prefab = bundle.LoadAsset<GameObject>(prefabName);
            var target = prefab == null ? null : childPath == null ? prefab.transform : prefab.transform.Find(childPath);
            var material = target != null ? target.GetComponent<MeshRenderer>()?.sharedMaterial : null;
            var albedo = material != null ? material.GetTexture("_BaseMap") as Texture2D ?? material.GetTexture("_MainTex") as Texture2D : null;
            if (albedo == null)
            {
                throw new System.InvalidOperationException("Built bundle has no albedo texture at " + label);
            }
            if (!albedo.isReadable)
            {
                throw new System.InvalidOperationException("Built bundle albedo at " + label + " is not readable for symmetry validation");
            }
            var pixels = albedo.GetPixels();
            int width = albedo.width;
            int height = albedo.height;
            int mismatchedY = 0;
            int mismatchedX = 0;
            int mismatchedRoll = 0;
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    float u = x / (float)(width - 1);
                    if (BestMirrorDiff(pixels, width, y, x, (1f - u) * (width - 1)) > diffThreshold)
                    {
                        mismatchedY++;
                    }
                    if (BestMirrorDiff(pixels, width, y, x, Mathf.Repeat(1.5f - u, 1f) * (width - 1)) > diffThreshold)
                    {
                        mismatchedX++;
                    }
                    if (BestMirrorDiff(pixels, width, y, x, Mathf.Repeat(u + 0.5f, 1f) * (width - 1)) > diffThreshold)
                    {
                        mismatchedRoll++;
                    }
                }
            }
            int total = width * height;
            float fractionY = (float)mismatchedY / total;
            float fractionX = (float)mismatchedX / total;
            float fractionRoll = (float)mismatchedRoll / total;
            if (fractionY > maxMismatchFraction || fractionX > maxMismatchFraction || fractionRoll > maxMismatchFraction)
            {
                throw new System.InvalidOperationException(
                    "Built bundle texture at " + label + " is not symmetric under the cylindrical transforms: " +
                    "y-mirror " + fractionY.ToString("P3") + ", x-mirror " + fractionX.ToString("P3") +
                    ", 180 roll " + fractionRoll.ToString("P3") +
                    " of pixels differ from their transformed mirror by more than " + diffThreshold +
                    "; expected <= " + maxMismatchFraction.ToString("P3") + " each");
            }
        }

        private static float BestMirrorDiff(Color[] pixels, int width, int y, int x, float mirrorXf)
        {
            int baseX = Mathf.FloorToInt(mirrorXf);
            var color = pixels[y * width + x];
            float best = float.MaxValue;
            for (int d = -1; d <= 1; d++)
            {
                int mx = baseX + d;
                if (mx < 0 || mx >= width)
                {
                    continue;
                }
                var mirror = pixels[y * width + mx];
                float diff = Mathf.Max(
                    Mathf.Abs(color.r - mirror.r),
                    Mathf.Abs(color.g - mirror.g),
                    Mathf.Abs(color.b - mirror.b));
                best = Mathf.Min(best, diff);
            }
            return best;
        }

        /// <summary>
        /// The shipped bundle must never contain vanilla reference assets
        /// (extracted atlases or preview-only reference materials/meshes).
        /// </summary>
        private static void ValidateNoReferenceAssets(AssetBundle bundle)
        {
            foreach (var assetName in bundle.GetAllAssetNames())
            {
                var lower = assetName.ToLowerInvariant();
                if (lower.Contains("weapons4") || lower.Contains("missiles3") ||
                    lower.Contains("vanilla_textures") || lower.Contains("scythereference") ||
                    lower.Contains("scimitarreference") || lower.Contains("texturepreviews"))
                {
                    throw new System.InvalidOperationException("Built bundle contains a vanilla reference asset: " + assetName);
                }
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
