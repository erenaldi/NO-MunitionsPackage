using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Phantom
{
    public static class PhantomMeshBuilder
    {
        internal const float TotalLength = 2.8f;
        internal const float BodyRadius = 0.1002f;
        internal const float DeployedSpan = 1.3987f;
        // Total across the four exported groups (Phantom_Export_Report.json);
        // the cylindrical unwrap adds seam-duplicate vertices, so only the
        // triangle count is fixed here.
        private const int ExpectedTriangleCount = 18846;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/PhantomMod";
        private const string ModelsRoot = OutputRoot + "/Models";
        internal const string MissilePrefabName = "Erenaldi.RDM9";

        [MenuItem("Blueprinter/Phantom/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "PhantomMod");
            EnsureFolder(OutputRoot, "Models");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                throw new System.InvalidOperationException("Required URP Lit shader is unavailable");
            }

            var bodyMaterial = PhantomTexturedMaterialBuilder.CreateBodyMaterial(OutputRoot, "MatPhantomBody");
            var wingMaterial = PhantomTexturedMaterialBuilder.CreateWingMaterial(OutputRoot, "MatPhantomWing");
            var finsMaterial = CreateFlatMaterial(shader, "MatPhantomFins", new Color(0.44f, 0.48f, 0.49f), 0.06f, 0.42f);
            var nozzleMaterial = CreateFlatMaterial(shader, "MatPhantomNozzle", new Color(0.25f, 0.28f, 0.29f), 0.12f, 0.50f);

            var bodyMesh = LoadCadMesh(ModelsRoot + "/Phantom_Body.obj", "MeshPhantomBody", true);
            var wingsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Wings.obj", "MeshPhantomWings", false);
            var finsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Fins.obj", "MeshPhantomFins", false);
            var nozzleMesh = LoadCadMesh(ModelsRoot + "/Phantom_Nozzle.obj", "MeshPhantomNozzle", true);
            ValidateAssembly(bodyMesh, wingsMesh, finsMesh, nozzleMesh);
            ValidateTexturedMaterials(bodyMaterial, wingMaterial);

            SaveAsset(bodyMesh, "MeshPhantomBody.asset");
            SaveAsset(wingsMesh, "MeshPhantomWings.asset");
            SaveAsset(finsMesh, "MeshPhantomFins.asset");
            SaveAsset(nozzleMesh, "MeshPhantomNozzle.asset");
            SaveAsset(finsMaterial, "MatPhantomFins.mat");
            SaveAsset(nozzleMaterial, "MatPhantomNozzle.mat");

            var missile = BuildMissilePrefab(bodyMesh, wingsMesh, finsMesh, nozzleMesh, bodyMaterial, wingMaterial, finsMaterial, nozzleMaterial);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            ValidateNoReferenceAssets(OutputRoot + "/" + MissilePrefabName + ".prefab");

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Phantom] CAD geometry built: " + OutputRoot);
        }

        private static Mesh LoadCadMesh(string path, string meshName, bool cylindrical)
        {
            Mesh source = null;
            foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                source = asset as Mesh;
                if (source != null)
                {
                    break;
                }
            }
            if (source == null)
            {
                throw new System.InvalidOperationException("No mesh found in CAD model: " + path);
            }

            var mesh = Object.Instantiate(source);
            mesh.name = meshName;
            mesh.RecalculateNormals();
            // Recalculate bounds BEFORE the unwrap so v is normalized against
            // the imported bounds (the Kris body unwrap convention).
            mesh.RecalculateBounds();
            // Body/nozzle groups get the seam-deduplicated full-2pi cylindrical
            // unwrap (z-axis, v 0 tail .. 1 nose); the flat wing/fin panels get
            // a planar unwrap instead (cylindrical mapping degenerates on a
            // flat panel).
            var unwrapped = cylindrical
                ? Erenaldi.Kris.KrisMeshBuilder.GenerateCylindricalUVs(mesh)
                : GeneratePlanarUvs(mesh);
            Object.DestroyImmediate(mesh);
            unwrapped.RecalculateBounds();
            Debug.Log($"[Phantom] Imported {path}: {unwrapped.vertices.Length} vertices, bounds {unwrapped.bounds}");
            return unwrapped;
        }

        /// <summary>
        /// Planar unwrap onto the mesh's XZ plane (u along local x, v along
        /// local z), matching the flat wing/fin panels. No seam duplication is
        /// needed: u spans 0..1 continuously.
        /// </summary>
        private static Mesh GeneratePlanarUvs(Mesh source)
        {
            var sourceVertices = source.vertices;
            var sourceNormals = source.normals;
            var bounds = source.bounds;
            var sizeX = Mathf.Max(bounds.size.x, 0.001f);
            var sizeZ = Mathf.Max(bounds.size.z, 0.001f);
            var uvs = new List<Vector2>(sourceVertices.Length);
            for (int i = 0; i < sourceVertices.Length; i++)
            {
                uvs.Add(new Vector2((sourceVertices[i].x - bounds.min.x) / sizeX, (sourceVertices[i].z - bounds.min.z) / sizeZ));
            }
            var mesh = new Mesh { name = source.name, indexFormat = source.indexFormat };
            mesh.SetVertices(sourceVertices);
            mesh.SetNormals(sourceNormals);
            mesh.SetUVs(0, uvs);
            mesh.subMeshCount = source.subMeshCount;
            for (int subMesh = 0; subMesh < source.subMeshCount; subMesh++)
            {
                mesh.SetTriangles(source.GetTriangles(subMesh), subMesh);
            }
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void ValidateAssembly(Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh)
        {
            float nose = TotalLength * 0.5f;
            float aft = -nose;
            if (Mathf.Abs(bodyMesh.bounds.max.z - nose) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom nose is at z={bodyMesh.bounds.max.z:F3}; expected {nose:F3}");
            }
            if (Mathf.Abs(bodyMesh.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom aft is at z={bodyMesh.bounds.min.z:F3}; expected {aft:F3}");
            }
            float measuredLength = bodyMesh.bounds.max.z - bodyMesh.bounds.min.z;
            if (Mathf.Abs(measuredLength - TotalLength) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom total length is {measuredLength:F3} m; expected {TotalLength:F3} m");
            }
            float bodyRadius = GetMaximumRadialDistance(bodyMesh);
            if (Mathf.Abs(bodyRadius - BodyRadius) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom body radius is {bodyRadius:F3} m; expected {BodyRadius:F3} m");
            }
            var meshes = new Mesh[] { bodyMesh, wingsMesh, finsMesh, nozzleMesh };
            float maximumSpan = 0f;
            for (int i = 0; i < meshes.Length; i++)
            {
                maximumSpan = Mathf.Max(maximumSpan, Mathf.Max(meshes[i].bounds.size.x, meshes[i].bounds.size.y));
            }
            if (Mathf.Abs(maximumSpan - DeployedSpan) > 0.002f)
            {
                throw new System.InvalidOperationException($"Phantom maximum X/Y span is {maximumSpan:F3} m; expected {DeployedSpan:F3} m");
            }
            ValidateCenteredOnAxis(bodyMesh, "body");
            ValidateCenteredOnAxis(nozzleMesh, "nozzle");
            int triangleCount = 0;
            for (int i = 0; i < meshes.Length; i++)
            {
                if (!meshes[i].HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Phantom mesh has no UVs: " + meshes[i].name);
                }
                triangleCount += GetTriangleCount(meshes[i]);
            }
            if (triangleCount != ExpectedTriangleCount)
            {
                throw new System.InvalidOperationException(
                    $"Phantom mesh totals are {triangleCount} triangles; expected {ExpectedTriangleCount}");
            }
            Debug.Log($"[Phantom] Assembly verified: length={TotalLength:F3} m, body radius={bodyRadius:F3} m, span={maximumSpan:F3} m, {triangleCount} triangles.");
        }

        private static void ValidateTexturedMaterials(Material bodyMaterial, Material wingMaterial)
        {
            ValidateTexturedMaterial(bodyMaterial, "body");
            ValidateTexturedMaterial(wingMaterial, "wing");
            ValidateMicrosurfaceRange(bodyMaterial, "body");
            ValidateMicrosurfaceRange(wingMaterial, "wing");
            ValidateTextureMirrorSymmetry(bodyMaterial, "Phantom body");
            ValidateTextureMirrorSymmetry(wingMaterial, "Phantom wing");
        }

        private static void ValidateTexturedMaterial(Material material, string label)
        {
            var albedo = material.GetTexture("_BaseMap") as Texture2D;
            var packed = material.GetTexture("_MetallicGlossMap") as Texture2D;
            if (albedo == null || packed == null)
            {
                throw new System.InvalidOperationException("Phantom textured material at " + label + " is missing albedo or packed MS");
            }
            if (Mathf.Abs(material.color.r - 1f) > 0.001f ||
                Mathf.Abs(material.color.g - 1f) > 0.001f ||
                Mathf.Abs(material.color.b - 1f) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Metallic") - 1f) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - 1f) > 0.001f ||
                !material.IsKeywordEnabled("_METALLICSPECGLOSSMAP"))
            {
                throw new System.InvalidOperationException("Phantom textured material at " + label + " is not texture-driven");
            }
            if (!UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(albedo.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Phantom albedo at " + label + " is not sRGB (format=" + albedo.graphicsFormat + "); expected sRGB");
            }
            if (UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(packed.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Phantom packed MS at " + label + " is sRGB (format=" + packed.graphicsFormat + "); expected linear");
            }
        }

        /// <summary>
        /// Painted-composite microsurface: metallic 0.05-0.10 and smoothness
        /// 0.40-0.50 per the PRD, with higher values limited to charcoal
        /// hardware. Reject anything outside the measured vanilla family range.
        /// </summary>
        private static void ValidateMicrosurfaceRange(Material material, string label)
        {
            var packed = material.GetTexture("_MetallicGlossMap") as Texture2D;
            if (packed == null || !packed.isReadable)
            {
                throw new System.InvalidOperationException("Phantom packed MS at " + label + " is not readable");
            }
            var pixels = packed.GetPixels();
            for (int i = 0; i < pixels.Length; i++)
            {
                float metal = pixels[i].r;
                float smooth = pixels[i].a;
                if (metal < 0.03f || metal > 0.12f || smooth < 0.35f || smooth > 0.55f)
                {
                    throw new System.InvalidOperationException(
                        "Phantom packed MS at " + label + " has out-of-range microsurface values: metal=" +
                        metal.ToString("F3") + ", smooth=" + smooth.ToString("F3"));
                }
            }
        }

        /// <summary>
        /// Pixel-based symmetry check on the albedo texture for all three
        /// cylindrical-unwrap transformations (y-mirror u -> 1-u, x-mirror
        /// u -> (1.5-u) mod 1, 180 roll u -> u+0.5 mod 1). Tolerance matches
        /// the bundle validator: 0.12 max-channel difference with a +/-1 pixel
        /// tolerance, at most 0.05% mismatched pixels per transform.
        /// </summary>
        private static void ValidateTextureMirrorSymmetry(Material material, string label)
        {
            const float diffThreshold = 0.12f;
            const float maxMismatchFraction = 0.0005f;
            var albedo = material.GetTexture("_BaseMap") as Texture2D;
            if (albedo == null || !albedo.isReadable)
            {
                throw new System.InvalidOperationException("Phantom albedo at " + label + " is not readable for symmetry validation");
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
                    "Phantom texture at " + label + " is not symmetric under the cylindrical transforms: " +
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
        /// The candidate prefab must never depend on vanilla reference assets
        /// (extracted atlases or preview-only reference materials/meshes).
        /// </summary>
        private static void ValidateNoReferenceAssets(string prefabPath)
        {
            foreach (var dependency in AssetDatabase.GetDependencies(prefabPath, true))
            {
                var lower = dependency.ToLowerInvariant();
                if (lower.Contains("/reference/") || lower.Contains("/texturepreviews/"))
                {
                    throw new System.InvalidOperationException("Phantom prefab depends on a reference/preview asset: " + dependency);
                }
            }
        }

        private static GameObject BuildMissilePrefab(Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh, Material bodyMaterial, Material wingMaterial, Material finsMaterial, Material nozzleMaterial)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;

            var bodyCapsule = root.AddComponent<CapsuleCollider>();
            bodyCapsule.center = Vector3.zero;
            bodyCapsule.height = TotalLength;
            bodyCapsule.radius = BodyRadius;
            bodyCapsule.direction = 2;

            AddChildRenderer(root, "Wings", wingsMesh, wingMaterial);
            AddChildRenderer(root, "Fins", finsMesh, finsMaterial);
            AddChildRenderer(root, "Nozzle", nozzleMesh, nozzleMaterial);

            return root;
        }

        private static void AddChildRenderer(GameObject parent, string name, Mesh mesh, Material material)
        {
            var child = new GameObject(name);
            child.transform.SetParent(parent.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = mesh;
            child.AddComponent<MeshRenderer>().sharedMaterial = material;
        }

        private static Material CreateFlatMaterial(Shader shader, string name, Color color, float metallic, float smoothness)
        {
            var material = new Material(shader) { name = name };
            material.color = color;
            material.SetFloat("_Metallic", metallic);
            material.SetFloat("_Smoothness", smoothness);
            var measured = material.color;
            if (Mathf.Abs(measured.r - color.r) > 0.001f ||
                Mathf.Abs(measured.g - color.g) > 0.001f ||
                Mathf.Abs(measured.b - color.b) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Metallic") - metallic) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - smoothness) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom material {name} was not configured");
            }
            return material;
        }

        private static int GetTriangleCount(Mesh mesh)
        {
            int count = 0;
            for (int subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
            {
                count += mesh.GetTriangles(subMesh).Length / 3;
            }
            return count;
        }

        private static float GetMaximumRadialDistance(Mesh mesh)
        {
            float maximum = 0f;
            var vertices = mesh.vertices;
            for (int i = 0; i < vertices.Length; i++)
            {
                float radial = Mathf.Sqrt(vertices[i].x * vertices[i].x + vertices[i].y * vertices[i].y);
                maximum = Mathf.Max(maximum, radial);
            }
            return maximum;
        }

        private static void ValidateCenteredOnAxis(Mesh mesh, string partName)
        {
            if (Mathf.Abs(mesh.bounds.min.x + mesh.bounds.max.x) > 0.001f ||
                Mathf.Abs(mesh.bounds.min.y + mesh.bounds.max.y) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom {partName} is not centered on the z-axis");
            }
        }

        private static void SaveAsset(Object asset, string fileName)
        {
            string path = OutputRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(asset, path);
        }

        private static void SaveAsPrefab(GameObject gameObject, string fileName)
        {
            string path = OutputRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            PrefabUtility.SaveAsPrefabAsset(gameObject, path);
        }

        private static void EnsureFolder(string parent, string folder)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + folder))
            {
                AssetDatabase.CreateFolder(parent, folder);
            }
        }
    }
}