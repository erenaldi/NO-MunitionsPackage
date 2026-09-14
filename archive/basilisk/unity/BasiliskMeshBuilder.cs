using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Basilisk
{
    public static class BasiliskMeshBuilder
    {
        private const float TotalLength = 2.9f;
        private const float BodyRadius = 0.105f;
        private const float TailFinSpan = 0.543f;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/BasiliskMod";
        private const string BodyModelPath = OutputRoot + "/Models/Basilisk_Body.obj";
        private const string SeekerModelPath = OutputRoot + "/Models/Basilisk_Seeker.obj";
        private const string StrakesModelPath = OutputRoot + "/Models/Basilisk_Strakes.obj";
        private const string TailFinsModelPath = OutputRoot + "/Models/Basilisk_TailFins.obj";
        internal const string MissilePrefabName = "Erenaldi.AAM41";
        internal const string RackPrefabName = "Erenaldi.AAM41_single";

        [MenuItem("Blueprinter/Basilisk/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "BasiliskMod");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var bodyMaterial = new Material(shader) { name = "MatBasiliskBody" };
            bodyMaterial.color = new Color(0.62f, 0.64f, 0.66f);
            var seekerMaterial = new Material(shader) { name = "MatBasiliskSeeker" };
            seekerMaterial.color = new Color(0.35f, 0.36f, 0.38f);
            var strakesMaterial = new Material(shader) { name = "MatBasiliskStrakes" };
            strakesMaterial.color = new Color(0.45f, 0.47f, 0.5f);
            var tailFinsMaterial = new Material(shader) { name = "MatBasiliskTailFins" };
            tailFinsMaterial.color = new Color(0.45f, 0.47f, 0.5f);
            var pylonMaterial = new Material(shader) { name = "MatBasiliskPylon" };
            pylonMaterial.color = new Color(0.45f, 0.47f, 0.5f);

            var bodyMesh = LoadCadMesh(BodyModelPath, "MeshBasiliskBody");
            var seekerMesh = LoadCadMesh(SeekerModelPath, "MeshBasiliskSeeker");
            var strakesMesh = LoadCadMesh(StrakesModelPath, "MeshBasiliskStrakes");
            var tailFinsMesh = LoadCadMesh(TailFinsModelPath, "MeshBasiliskTailFins");
            ValidateAssembly(bodyMesh, seekerMesh, strakesMesh, tailFinsMesh);
            var pylonMesh = BuildPylonMesh();

            SaveAsset(bodyMesh, "MeshBasiliskBody.asset");
            SaveAsset(seekerMesh, "MeshBasiliskSeeker.asset");
            SaveAsset(strakesMesh, "MeshBasiliskStrakes.asset");
            SaveAsset(tailFinsMesh, "MeshBasiliskTailFins.asset");
            SaveAsset(pylonMesh, "MeshBasiliskPylon.asset");
            SaveAsset(bodyMaterial, "MatBasiliskBody.mat");
            SaveAsset(seekerMaterial, "MatBasiliskSeeker.mat");
            SaveAsset(strakesMaterial, "MatBasiliskStrakes.mat");
            SaveAsset(tailFinsMaterial, "MatBasiliskTailFins.mat");
            SaveAsset(pylonMaterial, "MatBasiliskPylon.mat");

            var missile = BuildMissilePrefab(bodyMesh, seekerMesh, strakesMesh, tailFinsMesh, bodyMaterial, seekerMaterial, strakesMaterial, tailFinsMaterial);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            var rack = BuildRackPrefab(pylonMesh, pylonMaterial, bodyMesh, seekerMesh, strakesMesh, tailFinsMesh, bodyMaterial, seekerMaterial, strakesMaterial, tailFinsMaterial);
            SaveAsPrefab(rack, RackPrefabName + ".prefab");
            Object.DestroyImmediate(rack);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Basilisk] CAD geometry built: " + OutputRoot);
        }

        [MenuItem("Blueprinter/Basilisk/Build Geometry Bundle")]
        public static void BuildBundle()
        {
            MunitionsGeometryBundleBuilder.BuildBundle();
        }

        private static Mesh LoadCadMesh(string path, string meshName)
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
            mesh.RecalculateBounds();
            Debug.Log($"[Basilisk] Imported {path}: {mesh.vertices.Length} vertices, bounds {mesh.bounds}");
            return mesh;
        }

        private static void ValidateAssembly(Mesh bodyMesh, Mesh seekerMesh, Mesh strakesMesh, Mesh tailFinsMesh)
        {
            float tail = -TotalLength * 0.5f;
            float nose = TotalLength * 0.5f;
            if (Mathf.Abs(bodyMesh.bounds.min.z - tail) > 0.001f)
            {
                throw new System.InvalidOperationException($"Basilisk body tail is at z={bodyMesh.bounds.min.z:F3}; expected {tail:F3}");
            }
            if (Mathf.Abs(seekerMesh.bounds.min.z - bodyMesh.bounds.max.z) > 0.001f)
            {
                throw new System.InvalidOperationException("Basilisk seeker and body do not meet at the nose seam");
            }
            if (Mathf.Abs(seekerMesh.bounds.max.z - nose) > 0.001f)
            {
                throw new System.InvalidOperationException($"Basilisk nose is at z={seekerMesh.bounds.max.z:F3}; expected {nose:F3}");
            }
            float bodyRadius = Mathf.Max(bodyMesh.bounds.size.x, bodyMesh.bounds.size.y) * 0.5f;
            if (Mathf.Abs(bodyRadius - BodyRadius) > 0.005f)
            {
                throw new System.InvalidOperationException($"Basilisk body radius is {bodyRadius:F3} m; expected {BodyRadius:F3} m");
            }
            float tailSpan = Mathf.Max(tailFinsMesh.bounds.size.x, tailFinsMesh.bounds.size.y);
            if (Mathf.Abs(tailSpan - TailFinSpan) > 0.005f)
            {
                throw new System.InvalidOperationException($"Basilisk tail-fin span is {tailSpan:F3} m; expected {TailFinSpan:F3} m");
            }
            ValidateCenteredOnAxis(bodyMesh, "body");
            ValidateCenteredOnAxis(seekerMesh, "seeker");
            ValidateCenteredOnAxis(strakesMesh, "strakes");
            ValidateCenteredOnAxis(tailFinsMesh, "tail fins");
            if (strakesMesh.bounds.min.z < tail - 0.001f || strakesMesh.bounds.max.z > bodyMesh.bounds.max.z + 0.001f)
            {
                throw new System.InvalidOperationException("Basilisk strakes extend outside the body length");
            }
            if (tailFinsMesh.bounds.min.z < tail - 0.001f || tailFinsMesh.bounds.max.z > bodyMesh.bounds.max.z + 0.001f)
            {
                throw new System.InvalidOperationException("Basilisk tail fins extend outside the body length");
            }
            Debug.Log($"[Basilisk] Assembly verified: length={TotalLength:F3} m, body radius={bodyRadius:F3} m, tail-fin span={tailSpan:F3} m.");
        }

        private static void ValidateCenteredOnAxis(Mesh mesh, string partName)
        {
            if (Mathf.Abs(mesh.bounds.min.x + mesh.bounds.max.x) > 0.001f ||
                Mathf.Abs(mesh.bounds.min.y + mesh.bounds.max.y) > 0.001f)
            {
                throw new System.InvalidOperationException($"Basilisk {partName} is not centered on the z-axis; axis mapping may have changed");
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
            return surface.ToMesh("MeshBasiliskPylon");
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

        private static GameObject BuildMissilePrefab(Mesh bodyMesh, Mesh seekerMesh, Mesh strakesMesh, Mesh tailFinsMesh, Material bodyMaterial, Material seekerMaterial, Material strakesMaterial, Material tailFinsMaterial)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            var bodyCapsule = root.AddComponent<CapsuleCollider>();
            bodyCapsule.center = Vector3.zero;
            bodyCapsule.height = TotalLength;
            bodyCapsule.radius = BodyRadius;
            bodyCapsule.direction = 2;

            AddChildRenderer(root, "Seeker", seekerMesh, seekerMaterial);
            AddChildRenderer(root, "Strakes", strakesMesh, strakesMaterial);
            AddChildRenderer(root, "TailFins", tailFinsMesh, tailFinsMaterial);
            return root;
        }

        private static GameObject BuildRackPrefab(Mesh pylonMesh, Material pylonMaterial, Mesh bodyMesh, Mesh seekerMesh, Mesh strakesMesh, Mesh tailFinsMesh, Material bodyMaterial, Material seekerMaterial, Material strakesMaterial, Material tailFinsMaterial)
        {
            var root = new GameObject(RackPrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = pylonMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = pylonMaterial;
            var box = root.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, -0.07f, 0f);
            box.size = new Vector3(0.16f, 0.14f, 0.5f);

            var bomb = new GameObject("bomb");
            bomb.transform.SetParent(root.transform, false);
            bomb.transform.localPosition = new Vector3(0f, -0.29f, 0f);
            bomb.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            bomb.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            AddChildRenderer(bomb, "Seeker", seekerMesh, seekerMaterial);
            AddChildRenderer(bomb, "Strakes", strakesMesh, strakesMaterial);
            AddChildRenderer(bomb, "TailFins", tailFinsMesh, tailFinsMaterial);
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
