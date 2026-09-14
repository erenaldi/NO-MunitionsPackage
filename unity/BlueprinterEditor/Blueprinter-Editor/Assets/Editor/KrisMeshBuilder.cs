using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Kris
{
    public static class KrisMeshBuilder
    {
        internal const float SizeScale = 1.1f;
        internal const float TotalLength = 2.8715922f * SizeScale;
        internal const float BodyRadius = 0.07183347f * SizeScale;
        internal const float RackRollDegrees = 45f;
        private const float PylonTargetClearance = 0.009f;
        private const float DeployedRadius = 0.22356208f * SizeScale;
        private const float MaximumSpan = 0.44446433f * SizeScale;
        // Total across the five parts after the body's seam-deduplicated
        // cylindrical UV unwrap (64388 source vertices + 251 seam duplicates).
        private const int ExpectedVertexCount = 64639;
        private const int ExpectedTriangleCount = 100328;

        internal static float RackMissileOffsetY { get; private set; } = -0.22746752f;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/KrisMod";
        private const string BodyModelPath = OutputRoot + "/Models/Kris_Body.obj";
        private const string HardwareModelPath = OutputRoot + "/Models/Kris_Hardware.obj";
        private const string DarkModelPath = OutputRoot + "/Models/Kris_Dark.obj";
        private const string GridFinsModelPath = OutputRoot + "/Models/Kris_GridFins.obj";
        private const string SeekerModelPath = OutputRoot + "/Models/Kris_Seeker.obj";
        internal const string MissilePrefabName = "Erenaldi.IRMS4";
        internal const string RackPrefabName = "Erenaldi.IRMS4_single";

        [MenuItem("Blueprinter/Kris/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "KrisMod");
            DeleteStaleLegacyAssets();

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var clearcoatShader = Shader.Find("Universal Render Pipeline/Complex Lit");
            if (shader == null || clearcoatShader == null)
            {
                throw new System.InvalidOperationException("Required URP Lit shaders are unavailable");
            }
            var bodyMaterial = KrisTexturedMaterialBuilder.CreateBodyMaterial(OutputRoot, "MatKrisBody");
            var hardwareMaterial = CreateFlatMaterial(shader, "MatKrisHardware", new Color(0.270498f, 0.309469f, 0.309469f), 0.35f, 0.45f, 0f, 0f);
            var darkMaterial = CreateFlatMaterial(shader, "MatKrisDark", new Color(0.033105f, 0.039546f, 0.042311f), 0.1f, 0.35f, 0f, 0f);
            var gridFinsMaterial = CreateFlatMaterial(shader, "MatKrisGridFins", new Color(0.0185f, 0.023153f, 0.026241f), 0.35f, 0.45f, 0f, 0f);
            var seekerMaterial = CreateFlatMaterial(clearcoatShader, "MatKrisSeeker", new Color(0.008568f, 0.019382f, 0.026241f), 0.05f, 0.94f, 1f, 0.975f);
            var pylonMaterial = new Material(shader) { name = "MatKrisPylon" };
            pylonMaterial.color = new Color(0.45f, 0.47f, 0.5f);
            ValidateMaterial(hardwareMaterial, "hardware", 0.270498f, 0.309469f, 0.309469f, 0.35f, 0.45f);
            ValidateMaterial(darkMaterial, "dark", 0.033105f, 0.039546f, 0.042311f, 0.1f, 0.35f);
            ValidateMaterial(gridFinsMaterial, "grid fins", 0.0185f, 0.023153f, 0.026241f, 0.35f, 0.45f);
            ValidateMaterial(seekerMaterial, "seeker", 0.008568f, 0.019382f, 0.026241f, 0.05f, 0.94f);
            if (Mathf.Abs(bodyMaterial.color.r - 1f) > 0.001f ||
                Mathf.Abs(bodyMaterial.color.g - 1f) > 0.001f ||
                Mathf.Abs(bodyMaterial.color.b - 1f) > 0.001f ||
                Mathf.Abs(bodyMaterial.GetFloat("_Metallic") - 1f) > 0.001f ||
                !bodyMaterial.IsKeywordEnabled("_METALLICSPECGLOSSMAP") ||
                bodyMaterial.GetTexture("_MetallicGlossMap") == null)
            {
                throw new System.InvalidOperationException("Kris body textured material was not configured");
            }
            if (Mathf.Abs(seekerMaterial.GetFloat("_ClearCoat") - 1f) > 0.001f ||
                Mathf.Abs(seekerMaterial.GetFloat("_ClearCoatMask") - 1f) > 0.001f ||
                Mathf.Abs(seekerMaterial.GetFloat("_ClearCoatSmoothness") - 0.975f) > 0.001f ||
                !seekerMaterial.IsKeywordEnabled("_CLEARCOAT"))
            {
                throw new System.InvalidOperationException("Kris seeker clearcoat material was not configured");
            }

            var bodyMesh = LoadCadMesh(BodyModelPath, "MeshKrisBody", true);
            var hardwareMesh = LoadCadMesh(HardwareModelPath, "MeshKrisHardware", false);
            var darkMesh = LoadCadMesh(DarkModelPath, "MeshKrisDark", false);
            var seekerMesh = LoadCadMesh(SeekerModelPath, "MeshKrisSeeker", false);
            var gridFinsMesh = LoadCadMesh(GridFinsModelPath, "MeshKrisGridFins", false);
            ValidateAssembly(bodyMesh, hardwareMesh, darkMesh, seekerMesh, gridFinsMesh);
            var pylonMesh = BuildPylonMesh();

            SaveAsset(bodyMesh, "MeshKrisBody.asset");
            SaveAsset(hardwareMesh, "MeshKrisHardware.asset");
            SaveAsset(darkMesh, "MeshKrisDark.asset");
            SaveAsset(seekerMesh, "MeshKrisSeeker.asset");
            SaveAsset(gridFinsMesh, "MeshKrisGridFins.asset");
            SaveAsset(pylonMesh, "MeshKrisPylon.asset");
            // MatKrisBody is created and saved by KrisTexturedMaterialBuilder;
            // re-saving it would destroy the in-memory asset.
            SaveAsset(hardwareMaterial, "MatKrisHardware.mat");
            SaveAsset(darkMaterial, "MatKrisDark.mat");
            SaveAsset(seekerMaterial, "MatKrisSeeker.mat");
            SaveAsset(gridFinsMaterial, "MatKrisGridFins.mat");
            SaveAsset(pylonMaterial, "MatKrisPylon.mat");

            var missile = BuildMissilePrefab(bodyMesh, hardwareMesh, darkMesh, seekerMesh, gridFinsMesh, bodyMaterial, hardwareMaterial, darkMaterial, seekerMaterial, gridFinsMaterial);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            var rack = BuildRackPrefab(pylonMesh, pylonMaterial, bodyMesh, hardwareMesh, darkMesh, seekerMesh, gridFinsMesh, bodyMaterial, hardwareMaterial, darkMaterial, seekerMaterial, gridFinsMaterial);
            SaveAsPrefab(rack, RackPrefabName + ".prefab");
            Object.DestroyImmediate(rack);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Kris] CAD geometry built: " + OutputRoot);
        }

        [MenuItem("Blueprinter/Kris/Build Geometry Bundle")]
        public static void BuildBundle()
        {
            MunitionsGeometryBundleBuilder.BuildBundle();
        }

        private static void DeleteStaleLegacyAssets()
        {
            AssetDatabase.DeleteAsset(OutputRoot + "/MeshKrisNozzle.asset");
            AssetDatabase.DeleteAsset(OutputRoot + "/MeshKrisControlVanes.asset");
            AssetDatabase.DeleteAsset(OutputRoot + "/MatKrisNozzle.mat");
            AssetDatabase.DeleteAsset(OutputRoot + "/MatKrisControlVanes.mat");
            AssetDatabase.DeleteAsset(OutputRoot + "/Models/Kris_Nozzle.obj");
            AssetDatabase.DeleteAsset(OutputRoot + "/Models/Kris_ControlVanes.obj");
            AssetDatabase.DeleteAsset(OutputRoot + "/Models/KrisHybrid_ControlVanes.obj");
        }

        private static Mesh LoadCadMesh(string path, string meshName, bool textured)
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
            if (Mathf.Abs(SizeScale - 1f) > 1e-6f)
            {
                var scaledVertices = mesh.vertices;
                for (int i = 0; i < scaledVertices.Length; i++)
                {
                    scaledVertices[i] *= SizeScale;
                }
                mesh.vertices = scaledVertices;
            }
            mesh.RecalculateNormals();
            if (textured)
            {
                var texturedMesh = GenerateCylindricalUVs(mesh);
                Object.DestroyImmediate(mesh);
                mesh = texturedMesh;
            }
            mesh.RecalculateBounds();
            Debug.Log($"[Kris] Imported {path}: {mesh.vertices.Length} vertices, bounds {mesh.bounds}");
            return mesh;
        }

        /// <summary>
        /// Full 2-pi cylindrical unwrap along the Kris z-axis (v 0 tail .. 1
        /// nose), with seam-wrapping triangles duplicated so no triangle
        /// spans the u seam. Matches the Halberd body unwrap convention.
        /// </summary>
        internal static Mesh GenerateCylindricalUVs(Mesh source)
        {
            var sourceVertices = source.vertices;
            var sourceNormals = source.normals;
            var bounds = source.bounds;
            var length = Mathf.Max(bounds.size.z, 0.001f);
            var vertices = new List<Vector3>(sourceVertices);
            var normals = new List<Vector3>(sourceNormals);
            var uvs = new List<Vector2>(sourceVertices.Length);
            for (int i = 0; i < sourceVertices.Length; i++)
            {
                float u = (Mathf.Atan2(sourceVertices[i].y, sourceVertices[i].x) + Mathf.PI) / (Mathf.PI * 2f);
                float v = (sourceVertices[i].z - bounds.min.z) / length;
                uvs.Add(new Vector2(u, v));
            }

            int subMeshCount = source.subMeshCount;
            var subMeshTriangles = new List<int[]>(subMeshCount);
            var seamDuplicates = new Dictionary<int, int>();
            for (int subMesh = 0; subMesh < subMeshCount; subMesh++)
            {
                var triangles = source.GetTriangles(subMesh);
                for (int triangle = 0; triangle < triangles.Length; triangle += 3)
                {
                    float minU = Mathf.Min(uvs[triangles[triangle]].x, uvs[triangles[triangle + 1]].x, uvs[triangles[triangle + 2]].x);
                    float maxU = Mathf.Max(uvs[triangles[triangle]].x, uvs[triangles[triangle + 1]].x, uvs[triangles[triangle + 2]].x);
                    if (maxU - minU <= 0.5f)
                    {
                        continue;
                    }
                    for (int corner = 0; corner < 3; corner++)
                    {
                        int triangleIndex = triangle + corner;
                        int vertexIndex = triangles[triangleIndex];
                        if (uvs[vertexIndex].x >= 0.5f)
                        {
                            continue;
                        }
                        if (!seamDuplicates.TryGetValue(vertexIndex, out int duplicateIndex))
                        {
                            duplicateIndex = vertices.Count;
                            seamDuplicates.Add(vertexIndex, duplicateIndex);
                            vertices.Add(vertices[vertexIndex]);
                            normals.Add(normals[vertexIndex]);
                            uvs.Add(new Vector2(uvs[vertexIndex].x + 1f, uvs[vertexIndex].y));
                        }
                        triangles[triangleIndex] = duplicateIndex;
                    }
                }
                subMeshTriangles.Add(triangles);
            }

            var mesh = new Mesh { name = source.name, indexFormat = source.indexFormat };
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetUVs(0, uvs);
            mesh.subMeshCount = subMeshCount;
            for (int subMesh = 0; subMesh < subMeshCount; subMesh++)
            {
                mesh.SetTriangles(subMeshTriangles[subMesh], subMesh);
            }
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void ValidateAssembly(Mesh bodyMesh, Mesh hardwareMesh, Mesh darkMesh, Mesh seekerMesh, Mesh gridFinsMesh)
        {
            float aft = -TotalLength * 0.5f;
            float nose = TotalLength * 0.5f;
            if (Mathf.Abs(hardwareMesh.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException($"Kris aft extent is at z={hardwareMesh.bounds.min.z:F3}; expected {aft:F3}");
            }
            if (Mathf.Abs(seekerMesh.bounds.max.z - nose) > 0.001f)
            {
                throw new System.InvalidOperationException($"Kris nose is at z={seekerMesh.bounds.max.z:F3}; expected {nose:F3}");
            }
            float measuredLength = seekerMesh.bounds.max.z - hardwareMesh.bounds.min.z;
            if (Mathf.Abs(measuredLength - TotalLength) > 0.001f)
            {
                throw new System.InvalidOperationException($"Kris total length is {measuredLength:F3} m; expected {TotalLength:F3} m");
            }
            float deployedRadius = GetMaximumRadialDistance(gridFinsMesh);
            if (Mathf.Abs(deployedRadius - DeployedRadius) > 0.002f)
            {
                throw new System.InvalidOperationException($"Kris deployed radial extent is {deployedRadius:F3} m; expected {DeployedRadius:F3} m");
            }
            var meshes = new Mesh[] { bodyMesh, hardwareMesh, darkMesh, seekerMesh, gridFinsMesh };
            float maximumSpan = 0f;
            for (int i = 0; i < meshes.Length; i++)
            {
                maximumSpan = Mathf.Max(maximumSpan, Mathf.Max(meshes[i].bounds.size.x, meshes[i].bounds.size.y));
            }
            if (Mathf.Abs(maximumSpan - MaximumSpan) > 0.002f)
            {
                throw new System.InvalidOperationException($"Kris maximum X/Y span is {maximumSpan:F3} m; expected {MaximumSpan:F3} m");
            }
            ValidateCenteredOnAxis(bodyMesh, "body");
            ValidateCenteredOnAxis(hardwareMesh, "hardware");
            ValidateCenteredOnAxis(seekerMesh, "seeker");
            ValidateCenteredOnAxis(gridFinsMesh, "grid fins");
            int vertexCount = 0;
            int triangleCount = 0;
            for (int i = 0; i < meshes.Length; i++)
            {
                vertexCount += meshes[i].vertices.Length;
                triangleCount += GetTriangleCount(meshes[i]);
            }
            if (triangleCount != ExpectedTriangleCount || vertexCount != ExpectedVertexCount)
            {
                throw new System.InvalidOperationException(
                    $"Kris mesh totals are {vertexCount} vertices / {triangleCount} triangles; expected {ExpectedVertexCount} / {ExpectedTriangleCount}");
            }
            ValidateRackClearance(meshes);
            Debug.Log($"[Kris] Assembly verified: length={TotalLength:F3} m, deployed radius={deployedRadius:F3} m, span={maximumSpan:F3} m, {vertexCount} vertices / {triangleCount} triangles.");
        }

        private static void ValidateRackClearance(Mesh[] meshes)
        {
            const float pylonHalfWidth = 0.08f;
            const float pylonHalfLength = 0.25f;
            const float pylonBottom = -0.14f;
            var rotation = Quaternion.Euler(0f, 0f, RackRollDegrees);
            float highestMissilePoint = float.NegativeInfinity;
            foreach (var mesh in meshes)
            {
                foreach (var vertex in mesh.vertices)
                {
                    var point = rotation * vertex;
                    if (Mathf.Abs(point.x) <= pylonHalfWidth + 0.0001f &&
                        Mathf.Abs(point.z) <= pylonHalfLength + 0.0001f)
                    {
                        highestMissilePoint = Mathf.Max(highestMissilePoint, point.y);
                    }
                }
            }
            if (float.IsNegativeInfinity(highestMissilePoint))
            {
                throw new System.InvalidOperationException("No Kris strake vertices fall inside the pylon footprint");
            }
            // The footprint test is y-independent, so solve the mount offset that
            // restores the authored strake-to-rail clearance for the scaled body.
            RackMissileOffsetY = pylonBottom - PylonTargetClearance - highestMissilePoint;
            float clearance = pylonBottom - (RackMissileOffsetY + highestMissilePoint);
            if (clearance < 0.008f || clearance > 0.010f)
            {
                throw new System.InvalidOperationException(
                    $"Kris pylon clearance is {clearance:F4} m; expected {PylonTargetClearance:F4} m between strakes");
            }
            Debug.Log($"[Kris] Rack alignment verified: {clearance:F4} m pylon clearance at {RackRollDegrees:F0}-degree roll, " +
                $"missile offset y={RackMissileOffsetY:F5} m.");
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

        private static void ValidateMaterial(Material material, string partName, float r, float g, float b, float metallic, float smoothness)
        {
            var color = material.color;
            if (Mathf.Abs(color.r - r) > 0.001f || Mathf.Abs(color.g - g) > 0.001f || Mathf.Abs(color.b - b) > 0.001f)
            {
                throw new System.InvalidOperationException(
                    $"Kris {partName} material color is ({color.r:F3},{color.g:F3},{color.b:F3}); expected ({r:F3},{g:F3},{b:F3})");
            }
            float measuredMetallic = material.GetFloat("_Metallic");
            float measuredSmoothness = material.GetFloat("_Smoothness");
            if (Mathf.Abs(measuredMetallic - metallic) > 0.001f || Mathf.Abs(measuredSmoothness - smoothness) > 0.001f)
            {
                throw new System.InvalidOperationException(
                    $"Kris {partName} material metallic/smoothness is {measuredMetallic:F3}/{measuredSmoothness:F3}; expected {metallic:F3}/{smoothness:F3}");
            }
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
                throw new System.InvalidOperationException($"Kris {partName} is not centered on the z-axis");
            }
        }

        private static Material CreateFlatMaterial(Shader shader, string name, Color color, float metallic, float smoothness, float clearcoat, float clearcoatSmoothness)
        {
            var material = new Material(shader) { name = name };
            material.color = color;
            material.SetFloat("_Metallic", metallic);
            material.SetFloat("_Smoothness", smoothness);
            material.SetFloat("_ClearCoat", clearcoat);
            material.SetFloat("_ClearCoatMask", clearcoat);
            material.SetFloat("_ClearCoatSmoothness", clearcoatSmoothness);
            if (clearcoat > 0f)
            {
                material.EnableKeyword("_CLEARCOAT");
            }
            return material;
        }

        private class SurfaceData
        {
            public readonly List<Vector3> vertices = new List<Vector3>();
            public readonly List<Vector3> normals = new List<Vector3>();
            public readonly List<Vector2> uvs = new List<Vector2>();
            public readonly List<int> triangles = new List<int>();

            public Mesh ToMesh(string name)
            {
                var mesh = new Mesh { name = name };
                mesh.SetVertices(vertices);
                mesh.SetTriangles(triangles, 0);
                if (normals.Count == vertices.Count)
                {
                    mesh.SetNormals(normals);
                }
                if (uvs.Count == vertices.Count)
                {
                    mesh.SetUVs(0, uvs);
                }
                mesh.RecalculateBounds();
                return mesh;
            }
        }

        private static Mesh BuildPylonMesh()
        {
            var surface = new SurfaceData();
            float width = 0.16f;
            float height = 0.14f;
            float depth = 0.5f;
            Vector3 c = new Vector3(0f, -height * 0.5f, 0f);
            Vector3 hx = new Vector3(width * 0.5f, 0f, 0f);
            Vector3 hy = new Vector3(0f, height * 0.5f, 0f);
            Vector3 hz = new Vector3(0f, 0f, depth * 0.5f);
            AddDoubleSidedQuad(surface, c + hx + hy + hz, c + hx + hy - hz, c + hx - hy - hz, c + hx - hy + hz, new Vector3(1f, 0f, 0f));
            AddDoubleSidedQuad(surface, c - hx + hy - hz, c - hx + hy + hz, c - hx - hy + hz, c - hx - hy - hz, new Vector3(-1f, 0f, 0f));
            AddDoubleSidedQuad(surface, c - hx + hy + hz, c + hx + hy + hz, c + hx - hy + hz, c - hx - hy + hz, new Vector3(0f, 0f, 1f));
            AddDoubleSidedQuad(surface, c + hx + hy - hz, c - hx + hy - hz, c - hx - hy - hz, c + hx - hy - hz, new Vector3(0f, 0f, -1f));
            AddDoubleSidedQuad(surface, c - hx + hy + hz, c - hx + hy - hz, c + hx + hy - hz, c + hx + hy + hz, new Vector3(0f, 1f, 0f));
            AddDoubleSidedQuad(surface, c + hx - hy + hz, c + hx - hy - hz, c - hx - hy - hz, c - hx - hy + hz, new Vector3(0f, -1f, 0f));
            return surface.ToMesh("MeshKrisPylon");
        }

        private static void AddDoubleSidedQuad(SurfaceData surface, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
        {
            AddSingleQuad(surface, a, b, c, d, normal);
            AddSingleQuad(surface, d, c, b, a, normal);
        }

        private static void AddSingleQuad(SurfaceData surface, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
        {
            int s = surface.vertices.Count;
            surface.vertices.Add(a);
            surface.vertices.Add(b);
            surface.vertices.Add(c);
            surface.vertices.Add(d);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.uvs.Add(new Vector2(0f, 1f));
            surface.uvs.Add(new Vector2(1f, 1f));
            surface.uvs.Add(new Vector2(1f, 0f));
            surface.uvs.Add(new Vector2(0f, 0f));
            surface.triangles.Add(s);
            surface.triangles.Add(s + 1);
            surface.triangles.Add(s + 2);
            surface.triangles.Add(s);
            surface.triangles.Add(s + 2);
            surface.triangles.Add(s + 3);
        }

        private static GameObject BuildMissilePrefab(Mesh bodyMesh, Mesh hardwareMesh, Mesh darkMesh, Mesh seekerMesh, Mesh gridFinsMesh, Material bodyMaterial, Material hardwareMaterial, Material darkMaterial, Material seekerMaterial, Material gridFinsMaterial)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;

            var bodyCapsule = root.AddComponent<CapsuleCollider>();
            bodyCapsule.center = Vector3.zero;
            bodyCapsule.height = TotalLength;
            bodyCapsule.radius = BodyRadius;
            bodyCapsule.direction = 2;

            AddChildRenderer(root, "Hardware", hardwareMesh, hardwareMaterial);
            AddChildRenderer(root, "Dark", darkMesh, darkMaterial);
            AddChildRenderer(root, "Seeker", seekerMesh, seekerMaterial);
            AddChildRenderer(root, "GridFins", gridFinsMesh, gridFinsMaterial);

            return root;
        }

        private static GameObject BuildRackPrefab(Mesh pylonMesh, Material pylonMaterial, Mesh bodyMesh, Mesh hardwareMesh, Mesh darkMesh, Mesh seekerMesh, Mesh gridFinsMesh, Material bodyMaterial, Material hardwareMaterial, Material darkMaterial, Material seekerMaterial, Material gridFinsMaterial)
        {
            var root = new GameObject(RackPrefabName);
            var pylon = new GameObject("pylon");
            pylon.transform.SetParent(root.transform, false);
            pylon.AddComponent<MeshFilter>().sharedMesh = pylonMesh;
            pylon.AddComponent<MeshRenderer>().sharedMaterial = pylonMaterial;

            var box = pylon.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, -0.07f, 0f);
            box.size = new Vector3(0.16f, 0.14f, 0.5f);

            var mountedMissile = new GameObject("aam1");
            mountedMissile.transform.SetParent(pylon.transform, false);
            mountedMissile.transform.localPosition = new Vector3(0f, RackMissileOffsetY, 0f);
            mountedMissile.transform.localRotation = Quaternion.Euler(0f, 0f, RackRollDegrees);
            mountedMissile.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            mountedMissile.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            var missileCapsule = mountedMissile.AddComponent<CapsuleCollider>();
            missileCapsule.center = Vector3.zero;
            missileCapsule.height = TotalLength;
            missileCapsule.radius = BodyRadius;
            missileCapsule.direction = 2;

            AddChildRenderer(mountedMissile, "Hardware", hardwareMesh, hardwareMaterial);
            AddChildRenderer(mountedMissile, "Dark", darkMesh, darkMaterial);
            AddChildRenderer(mountedMissile, "Seeker", seekerMesh, seekerMaterial);
            AddChildRenderer(mountedMissile, "GridFins", gridFinsMesh, gridFinsMaterial);

            return root;
        }

        private static void AddChildRenderer(GameObject parent, string name, Mesh mesh, Material material)
        {
            var child = new GameObject(name);
            child.transform.SetParent(parent.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = mesh;
            child.AddComponent<MeshRenderer>().sharedMaterial = material;
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
