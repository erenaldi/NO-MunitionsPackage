using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Halberd
{
    public static class HalberdMeshBuilder
    {
        private const float DesignLength = 3.367f;
        private const float BodyRadius = 0.1005f;
        private const float StageSeamZ = -0.3367f;
        private const float MaxRadius = 0.2181f;
        private const float SustainerFinRadius = 0.1721f;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/HalberdMod";
        private const string BodyModelPath = OutputRoot + "/Models/Halberd_Body.obj";
        private const string IntakesModelPath = OutputRoot + "/Models/Halberd_Intakes.obj";
        private const string SustainerFinsModelPath = OutputRoot + "/Models/Halberd_SustainerFins.obj";
        private const string HardwareModelPath = OutputRoot + "/Models/Halberd_Hardware.obj";
        private const string SustainerNozzleModelPath = OutputRoot + "/Models/Halberd_SustainerNozzle.obj";
        private const string BoosterBodyModelPath = OutputRoot + "/Models/Halberd_BoosterBody.obj";
        private const string BoosterFinsModelPath = OutputRoot + "/Models/Halberd_BoosterFins.obj";
        private const string BoosterNozzleModelPath = OutputRoot + "/Models/Halberd_BoosterNozzle.obj";
        private const string BoosterNozzleRecessModelPath = OutputRoot + "/Models/Halberd_BoosterNozzleRecess.obj";
        internal const string MissilePrefabName = "Erenaldi.AAM44";
        internal const string RackPrefabName = "Erenaldi.AAM44_single";

        [MenuItem("Blueprinter/Halberd/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "HalberdMod");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var bodyMaterial = HalberdTexturePreviewBuilder.CreateApprovedBodyMaterial(OutputRoot, "HalberdBody");
            var boosterMaterial = HalberdTexturePreviewBuilder.CreateApprovedBoosterMaterial(OutputRoot, "HalberdBooster");
            var pylonMaterial = new Material(shader) { name = "MatHalberdPylon" };
            pylonMaterial.color = new Color(0.45f, 0.47f, 0.5f);
            var intakesMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(OutputRoot, "MatHalberdIntakes", new Color(0.30f, 0.31f, 0.32f));
            var sustainerFinsMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(OutputRoot, "MatHalberdSustainerFins", new Color(0.56f, 0.58f, 0.57f));
            var hardwareMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(OutputRoot, "MatHalberdHardware", new Color(0.42f, 0.43f, 0.45f));
            var sustainerNozzleMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(OutputRoot, "MatHalberdSustainerNozzle", new Color(0.30f, 0.30f, 0.32f));
            var finsMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(OutputRoot, "MatHalberdFins", new Color(0.56f, 0.58f, 0.57f));
            var boosterNozzleMaterial = CreateFlatMaterial(shader, "MatHalberdBoosterNozzle", new Color(0.24f, 0.07f, 0.045f));
            var boosterNozzleRecessMaterial = CreateFlatMaterial(shader, "MatHalberdBoosterNozzleRecess", new Color(0.025f, 0.03f, 0.035f));

            var bodyMesh = LoadCadMesh(BodyModelPath, "MeshHalberdBody", true);
            var intakesMesh = LoadCadMesh(IntakesModelPath, "MeshHalberdIntakes", true);
            var sustainerFinsMesh = LoadCadMesh(SustainerFinsModelPath, "MeshHalberdSustainerFins", true);
            var hardwareMesh = LoadCadMesh(HardwareModelPath, "MeshHalberdHardware", true);
            var sustainerNozzleMesh = LoadCadMesh(SustainerNozzleModelPath, "MeshHalberdSustainerNozzle", true);
            var boosterBodyMesh = LoadCadMesh(BoosterBodyModelPath, "MeshHalberdBooster", true);
            var boosterFinsMesh = LoadCadMesh(BoosterFinsModelPath, "MeshHalberdBoosterFins", true);
            var boosterNozzleMesh = LoadCadMesh(BoosterNozzleModelPath, "MeshHalberdBoosterNozzle", false);
            var boosterNozzleRecessMesh = LoadCadMesh(BoosterNozzleRecessModelPath, "MeshHalberdBoosterNozzleRecess", false);
            ValidateAssembly(bodyMesh, intakesMesh, sustainerFinsMesh, hardwareMesh, sustainerNozzleMesh, boosterBodyMesh, boosterFinsMesh, boosterNozzleMesh, boosterNozzleRecessMesh);
            var pylonMesh = BuildPylonMesh();

            SaveAsset(bodyMesh, "MeshHalberdBody.asset");
            SaveAsset(intakesMesh, "MeshHalberdIntakes.asset");
            SaveAsset(sustainerFinsMesh, "MeshHalberdSustainerFins.asset");
            SaveAsset(hardwareMesh, "MeshHalberdHardware.asset");
            SaveAsset(sustainerNozzleMesh, "MeshHalberdSustainerNozzle.asset");
            SaveAsset(boosterBodyMesh, "MeshHalberdBooster.asset");
            SaveAsset(boosterFinsMesh, "MeshHalberdBoosterFins.asset");
            SaveAsset(boosterNozzleMesh, "MeshHalberdBoosterNozzle.asset");
            SaveAsset(boosterNozzleRecessMesh, "MeshHalberdBoosterNozzleRecess.asset");
            SaveAsset(pylonMesh, "MeshHalberdPylon.asset");
            SaveAsset(pylonMaterial, "MatHalberdPylon.mat");
            // Intakes/fins/hardware/sustainer-nozzle/fins materials are created and
            // saved by HalberdTexturedMaterialBuilder; re-saving them would destroy
            // the in-memory assets (DeleteAsset + CreateAsset on the same object).
            SaveAsset(boosterNozzleMaterial, "MatHalberdBoosterNozzle.mat");
            SaveAsset(boosterNozzleRecessMaterial, "MatHalberdBoosterNozzleRecess.mat");

            var missile = BuildMissilePrefab(bodyMesh, intakesMesh, sustainerFinsMesh, hardwareMesh, sustainerNozzleMesh, boosterBodyMesh, boosterFinsMesh, boosterNozzleMesh, boosterNozzleRecessMesh, bodyMaterial, intakesMaterial, sustainerFinsMaterial, hardwareMaterial, sustainerNozzleMaterial, boosterMaterial, finsMaterial, boosterNozzleMaterial, boosterNozzleRecessMaterial);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            var rack = BuildRackPrefab(pylonMesh, pylonMaterial, bodyMesh, intakesMesh, sustainerFinsMesh, hardwareMesh, sustainerNozzleMesh, boosterBodyMesh, boosterFinsMesh, boosterNozzleMesh, boosterNozzleRecessMesh, bodyMaterial, intakesMaterial, sustainerFinsMaterial, hardwareMaterial, sustainerNozzleMaterial, boosterMaterial, finsMaterial, boosterNozzleMaterial, boosterNozzleRecessMaterial);
            SaveAsPrefab(rack, RackPrefabName + ".prefab");
            Object.DestroyImmediate(rack);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Halberd] CAD geometry built: " + OutputRoot);
        }

        [MenuItem("Blueprinter/Halberd/Build Geometry Bundle")]
        public static void BuildBundle()
        {
            MunitionsGeometryBundleBuilder.BuildBundle();
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
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            if (textured)
            {
                var texturedMesh = GenerateCylindricalUvs(mesh);
                Object.DestroyImmediate(mesh);
                mesh = texturedMesh;
                mesh.RecalculateTangents();
            }
            Debug.Log($"[Halberd] Imported {path}: {mesh.vertices.Length} vertices, bounds {mesh.bounds}");
            return mesh;
        }

        internal static Mesh GenerateCylindricalUvs(Mesh source)
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

        private static void ValidateAssembly(Mesh bodyMesh, Mesh intakesMesh, Mesh sustainerFinsMesh, Mesh hardwareMesh, Mesh sustainerNozzleMesh, Mesh boosterBodyMesh, Mesh boosterFinsMesh, Mesh boosterNozzleMesh, Mesh boosterNozzleRecessMesh)
        {
            var meshes = new Mesh[] { bodyMesh, intakesMesh, sustainerFinsMesh, hardwareMesh, sustainerNozzleMesh, boosterBodyMesh, boosterFinsMesh, boosterNozzleMesh, boosterNozzleRecessMesh };
            var names = new[] { "body", "intakes", "sustainer fins", "hardware", "sustainer nozzle", "booster body", "booster fins", "booster nozzle", "booster nozzle recess" };
            for (int i = 0; i < meshes.Length; i++)
            {
                if (meshes[i].vertices.Length == 0 || meshes[i].bounds.size.z <= 0f)
                {
                    throw new System.InvalidOperationException("Halberd " + names[i] + " has no usable geometry");
                }
            }

            float nose = bodyMesh.bounds.max.z;
            float exhaust = boosterNozzleMesh.bounds.min.z;
            float measuredLength = nose - exhaust;
            if (Mathf.Abs(measuredLength - DesignLength) > 0.001f)
            {
                throw new System.InvalidOperationException($"Halberd total length is {measuredLength:F3} m; expected {DesignLength:F3} m");
            }
            if (Mathf.Abs(bodyMesh.bounds.min.z - StageSeamZ) > 0.001f ||
                Mathf.Abs(boosterBodyMesh.bounds.max.z - StageSeamZ) > 0.001f)
            {
                throw new System.InvalidOperationException($"Halberd stage seam is at z={bodyMesh.bounds.min.z:F3}/{boosterBodyMesh.bounds.max.z:F3}; expected {StageSeamZ:F3}");
            }
            float bodyRadius = Mathf.Max(bodyMesh.bounds.size.x, bodyMesh.bounds.size.y) * 0.5f;
            if (Mathf.Abs(bodyRadius - BodyRadius) > 0.003f)
            {
                throw new System.InvalidOperationException($"Halberd body radius is {bodyRadius:F3} m; expected {BodyRadius:F3} m");
            }
            ValidateCenteredOnAxis(bodyMesh, "body");
            ValidateCenteredOnAxis(boosterBodyMesh, "booster body");
            float sustainerFinRadius = GetMaximumRadialDistance(sustainerFinsMesh);
            if (Mathf.Abs(sustainerFinRadius - SustainerFinRadius) > 0.005f)
            {
                throw new System.InvalidOperationException($"Halberd sustainer-fin radius is {sustainerFinRadius:F3} m; expected {SustainerFinRadius:F3} m");
            }
            float maximumRadius = 0f;
            for (int i = 0; i < meshes.Length; i++)
            {
                maximumRadius = Mathf.Max(maximumRadius, GetMaximumRadialDistance(meshes[i]));
            }
            if (Mathf.Abs(maximumRadius - MaxRadius) > 0.005f)
            {
                throw new System.InvalidOperationException($"Halberd maximum radius is {maximumRadius:F3} m; expected {MaxRadius:F3} m");
            }
            Debug.Log(
                $"[Halberd] Assembly verified: length={measuredLength:F3} m, seam z={StageSeamZ:F3}, " +
                $"body radius={bodyRadius:F3} m, max radius={maximumRadius:F3} m.");
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
                throw new System.InvalidOperationException($"Halberd {partName} is not centered on the z-axis");
            }
        }

        private static void ValidateColliderPlacement(CapsuleCollider collider, Mesh mesh, string partName)
        {
            var bounds = mesh.bounds;
            float expectedCenterZ = (bounds.min.z + bounds.max.z) * 0.5f;
            float expectedHeight = bounds.size.z;
            float expectedRadius = GetMaximumRadialDistance(mesh);
            if (Mathf.Abs(collider.center.z - expectedCenterZ) > 0.001f ||
                Mathf.Abs(collider.height - expectedHeight) > 0.001f ||
                Mathf.Abs(collider.radius - expectedRadius) > 0.001f)
            {
                throw new System.InvalidOperationException(
                    $"Halberd {partName} collider does not match geometry: center z={collider.center.z:F3} (expected {expectedCenterZ:F3}), " +
                    $"height={collider.height:F3} (expected {expectedHeight:F3}), radius={collider.radius:F3} (expected {expectedRadius:F3})");
            }
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
            float width = 0.18f;
            float height = 0.16f;
            float depth = 0.6f;
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
            return surface.ToMesh("MeshHalberdPylon");
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

        private static Material CreateFlatMaterial(Shader shader, string name, Color color)
        {
            var material = new Material(shader) { name = name };
            material.color = color;
            return material;
        }

        private static CapsuleCollider AddBodyCollider(GameObject target, Mesh mesh)
        {
            var bounds = mesh.bounds;
            var collider = target.AddComponent<CapsuleCollider>();
            collider.center = new Vector3(0f, 0f, (bounds.min.z + bounds.max.z) * 0.5f);
            collider.height = bounds.size.z;
            collider.radius = GetMaximumRadialDistance(mesh);
            collider.direction = 2;
            return collider;
        }

        private static void AddChildRenderer(GameObject parent, string name, Mesh mesh, Material material)
        {
            var child = new GameObject(name);
            child.transform.SetParent(parent.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = mesh;
            child.AddComponent<MeshRenderer>().sharedMaterial = material;
        }

        private static GameObject BuildMissilePrefab(Mesh bodyMesh, Mesh intakesMesh, Mesh sustainerFinsMesh, Mesh hardwareMesh, Mesh sustainerNozzleMesh, Mesh boosterBodyMesh, Mesh boosterFinsMesh, Mesh boosterNozzleMesh, Mesh boosterNozzleRecessMesh, Material bodyMaterial, Material intakesMaterial, Material sustainerFinsMaterial, Material hardwareMaterial, Material sustainerNozzleMaterial, Material boosterMaterial, Material finsMaterial, Material boosterNozzleMaterial, Material boosterNozzleRecessMaterial)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            var bodyCollider = AddBodyCollider(root, bodyMesh);
            ValidateColliderPlacement(bodyCollider, bodyMesh, "body");

            AddChildRenderer(root, "Intakes", intakesMesh, intakesMaterial);
            AddChildRenderer(root, "SustainerFins", sustainerFinsMesh, sustainerFinsMaterial);
            AddChildRenderer(root, "Hardware", hardwareMesh, hardwareMaterial);
            AddChildRenderer(root, "SustainerNozzle", sustainerNozzleMesh, sustainerNozzleMaterial);

            var booster = new GameObject("Booster");
            booster.transform.SetParent(root.transform, false);
            booster.AddComponent<MeshFilter>().sharedMesh = boosterBodyMesh;
            booster.AddComponent<MeshRenderer>().sharedMaterial = boosterMaterial;
            var boosterCollider = AddBodyCollider(booster, boosterBodyMesh);
            ValidateColliderPlacement(boosterCollider, boosterBodyMesh, "booster");
            AddChildRenderer(booster, "Fins", boosterFinsMesh, finsMaterial);
            AddChildRenderer(booster, "Nozzle", boosterNozzleMesh, boosterNozzleMaterial);
            AddChildRenderer(booster, "NozzleRecess", boosterNozzleRecessMesh, boosterNozzleRecessMaterial);
            return root;
        }

        private static GameObject BuildRackPrefab(Mesh pylonMesh, Material pylonMaterial, Mesh bodyMesh, Mesh intakesMesh, Mesh sustainerFinsMesh, Mesh hardwareMesh, Mesh sustainerNozzleMesh, Mesh boosterBodyMesh, Mesh boosterFinsMesh, Mesh boosterNozzleMesh, Mesh boosterNozzleRecessMesh, Material bodyMaterial, Material intakesMaterial, Material sustainerFinsMaterial, Material hardwareMaterial, Material sustainerNozzleMaterial, Material boosterMaterial, Material finsMaterial, Material boosterNozzleMaterial, Material boosterNozzleRecessMaterial)
        {
            var root = new GameObject(RackPrefabName);
            var pylon = new GameObject("pylon");
            pylon.transform.SetParent(root.transform, false);
            pylon.AddComponent<MeshFilter>().sharedMesh = pylonMesh;
            pylon.AddComponent<MeshRenderer>().sharedMaterial = pylonMaterial;
            var box = pylon.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, -0.08f, 0f);
            box.size = new Vector3(0.18f, 0.16f, 0.6f);

            var bomb = new GameObject("aam4");
            bomb.transform.SetParent(pylon.transform, false);
            bomb.transform.localPosition = new Vector3(0f, -0.31f, 0f);
            bomb.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            bomb.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            var bombCollider = AddBodyCollider(bomb, bodyMesh);
            ValidateColliderPlacement(bombCollider, bodyMesh, "rack aam4 body");

            AddChildRenderer(bomb, "Intakes", intakesMesh, intakesMaterial);
            AddChildRenderer(bomb, "SustainerFins", sustainerFinsMesh, sustainerFinsMaterial);
            AddChildRenderer(bomb, "Hardware", hardwareMesh, hardwareMaterial);
            AddChildRenderer(bomb, "SustainerNozzle", sustainerNozzleMesh, sustainerNozzleMaterial);

            var bombBooster = new GameObject("Booster");
            bombBooster.transform.SetParent(bomb.transform, false);
            bombBooster.AddComponent<MeshFilter>().sharedMesh = boosterBodyMesh;
            bombBooster.AddComponent<MeshRenderer>().sharedMaterial = boosterMaterial;
            var bombBoosterCollider = AddBodyCollider(bombBooster, boosterBodyMesh);
            ValidateColliderPlacement(bombBoosterCollider, boosterBodyMesh, "rack aam4 booster");
            AddChildRenderer(bombBooster, "Fins", boosterFinsMesh, finsMaterial);
            AddChildRenderer(bombBooster, "Nozzle", boosterNozzleMesh, boosterNozzleMaterial);
            AddChildRenderer(bombBooster, "NozzleRecess", boosterNozzleRecessMesh, boosterNozzleRecessMaterial);
            return root;
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
