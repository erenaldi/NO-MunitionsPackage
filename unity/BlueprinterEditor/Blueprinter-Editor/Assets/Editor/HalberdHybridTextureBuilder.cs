using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;
using Object = UnityEngine.Object;

namespace Erenaldi.Halberd
{
    /// <summary>Hybrid authoring preview. Uses the approved original vanilla-style texture painter.</summary>
    public static class HalberdHybridTextureBuilder
    {
        private const string Root = "Assets/Blueprinter/Mods/HalberdHybrid";
        private const float Seam = -0.3367f;
        private const float Half = 1.6835f;

        [Serializable] private sealed class MeshPacket
        {
            public string sourceSha256;
            public int triangleCount;
            public PartData[] parts;
        }
        [Serializable] private sealed class PartData
        {
            public string label;
            public float[] vertices;
            public float[] normals;
            public int[] exterior;
            public int[] interior;
        }

        [MenuItem("Blueprinter/Halberd Hybrid/Build Textured Candidate")]
        public static void BuildAndPreview()
        {
            AssetDatabase.Refresh();
            var packet = JsonUtility.FromJson<MeshPacket>(File.ReadAllText(Root + "/Models/HalberdHybridMeshData.json"));
            if (packet.parts == null || packet.parts.Length != 19 || packet.triangleCount > 75000)
                throw new InvalidOperationException("Invalid hybrid mesh packet");
            var bodyMaterial = HalberdTexturedMaterialBuilder.CreateBodyMaterial(Root, "MatHybridBody");
            var boosterMaterial = HalberdTexturedMaterialBuilder.CreateBoosterMaterial(Root, "MatHybridBooster");
            var finMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(Root, "MatHybridFins", new Color(.80f, .815f, .81f));
            var hardwareMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(Root, "MatHybridHardware", new Color(.61f, .62f, .63f));
            var intakeMaterial = HalberdTexturedMaterialBuilder.CreatePlainMaterial(Root, "MatHybridIntakeInterior", new Color(.30f, .31f, .32f));
            var nozzleMaterial = Flat("MatHybridNozzles", new Color(.24f, .25f, .26f));
            var backingMaterial = Flat("MatHybridRecess", new Color(.025f, .03f, .035f));

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var missile = new GameObject("Erenaldi.AAM44.HybridCandidate");
            var booster = new GameObject("Booster");
            booster.transform.SetParent(missile.transform, false);
            var labels = new HashSet<string>();
            int triangles = 0;
            foreach (var part in packet.parts)
            {
                if (!labels.Add(part.label)) throw new InvalidOperationException("Duplicate hybrid label: " + part.label);
                var mesh = MakeMesh(part);
                bool boosterPart = part.label.StartsWith("booster_", StringComparison.Ordinal);
                bool hull = part.label == "sustainer_body" || part.label == "radome" || part.label == "booster_body";
                bool fin = part.label.Contains("_fin_");
                bool backing = part.label.StartsWith("intake_floor_", StringComparison.Ordinal);
                if (hull)
                {
                    var mapped = HalberdMeshBuilder.GenerateCylindricalUvs(mesh);
                    Object.DestroyImmediate(mesh);
                    mesh = mapped;
                    var uv = mesh.uv;
                    var vertices = mesh.vertices;
                    float low = boosterPart ? -Half : Seam;
                    float high = boosterPart ? Seam : Half;
                    for (int i = 0; i < uv.Length; i++) uv[i].y = (vertices[i].z - low) / (high - low);
                    mesh.uv = uv;
                }
                else if (fin) SetFinUvs(mesh);
                else
                {
                    var mapped = HalberdMeshBuilder.GenerateCylindricalUvs(mesh);
                    Object.DestroyImmediate(mesh);
                    mesh = mapped;
                }
                mesh.RecalculateTangents();
                mesh.name = "Mesh_" + part.label;
                mesh = Save(mesh, Root + "/" + mesh.name + ".asset");
                var node = part.label == "sustainer_body" ? missile : part.label == "booster_body" ? booster : new GameObject(part.label);
                if (node != missile && node != booster) node.transform.SetParent(boosterPart ? booster.transform : missile.transform, false);
                node.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = node.AddComponent<MeshRenderer>();
                Material outer = hull ? (boosterPart ? boosterMaterial : bodyMaterial) : fin ? finMaterial : backing ? backingMaterial : part.label.StartsWith("mount_", StringComparison.Ordinal) ? hardwareMaterial : nozzleMaterial;
                renderer.sharedMaterials = part.interior.Length > 0 ? new[] { outer, intakeMaterial } : new[] { outer };
                triangles += mesh.triangles.Length / 3;
                Debug.Log($"[Halberd Hybrid] {part.label}: {mesh.vertexCount} vertices, {mesh.triangles.Length / 3} triangles, {mesh.subMeshCount} slots; bounds={mesh.bounds}");
            }
            Validate(missile, packet, triangles);
            PrefabUtility.SaveAsPrefabAsset(missile, Root + "/Erenaldi.AAM44.HybridCandidate.prefab");
            AssetDatabase.SaveAssets();

            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.34f, .37f, .42f);
            var light = new GameObject("Key Light").AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.35f;
            light.color = new Color(1f, .96f, .90f);
            light.transform.rotation = Quaternion.Euler(48, -32, 0);
            var fill = new GameObject("Fill Light").AddComponent<Light>();
            fill.type = LightType.Directional;
            fill.intensity = .40f;
            fill.transform.rotation = Quaternion.Euler(25, 145, 0);
            var camera = new GameObject("Hybrid Preview Camera").AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.055f, .065f, .08f);
            Render(camera, new Vector3(3, 2, 4), Vector3.zero, 1.30f, "Halberd_Hybrid_Unity_Textured.png");
            Render(camera, new Vector3(5, 0, 0), Vector3.zero, 1.10f, "Halberd_Hybrid_Unity_Side.png");
            Render(camera, new Vector3(-5, 0, 0), Vector3.zero, 1.10f, "Halberd_Hybrid_Unity_Opposed.png");
            Render(camera, new Vector3(1.8f, 1.3f, 2.1f), new Vector3(0, 0, .75f), .64f, "Halberd_Hybrid_Unity_Intakes.png");
            booster.transform.localPosition = new Vector3(0, 0, -.45f);
            Render(camera, new Vector3(3, 2, 4), new Vector3(0, 0, -.2f), 1.45f, "Halberd_Hybrid_Unity_Separated.png");
            booster.transform.localPosition = Vector3.zero;
            camera.transform.position = new Vector3(3, 2, 4);
            camera.transform.LookAt(Vector3.zero);
            camera.orthographicSize = 1.3f;
            EditorSceneManager.SaveScene(scene, Root + "/HalberdHybridTexturePreview.unity");
            Debug.Log($"[Halberd Hybrid] PASS: textured candidate, {triangles} triangles, source {packet.sourceSha256}; preview scene saved. No bundle or install performed.");
        }

        private static Mesh MakeMesh(PartData part)
        {
            if (part.vertices.Length % 3 != 0 || part.normals.Length != part.vertices.Length)
                throw new InvalidOperationException("Malformed buffers: " + part.label);
            var vertices = new Vector3[part.vertices.Length / 3];
            var normals = new Vector3[vertices.Length];
            for (int i = 0; i < vertices.Length; i++)
            {
                vertices[i] = new Vector3(part.vertices[3 * i], part.vertices[3 * i + 1], part.vertices[3 * i + 2]);
                normals[i] = new Vector3(part.normals[3 * i], part.normals[3 * i + 1], part.normals[3 * i + 2]);
            }
            var mesh = new Mesh { name = part.label, indexFormat = IndexFormat.UInt32, vertices = vertices, normals = normals };
            mesh.subMeshCount = part.interior.Length > 0 ? 2 : 1;
            mesh.SetTriangles(part.exterior, 0);
            if (part.interior.Length > 0) mesh.SetTriangles(part.interior, 1);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void SetFinUvs(Mesh mesh)
        {
            var vertices = mesh.vertices;
            float min = float.MaxValue, max = float.MinValue;
            foreach (var v in vertices) { float r = new Vector2(v.x, v.y).magnitude; min = Mathf.Min(min, r); max = Mathf.Max(max, r); }
            var uv = new Vector2[vertices.Length];
            for (int i = 0; i < uv.Length; i++) uv[i] = new Vector2((vertices[i].z - mesh.bounds.min.z) / mesh.bounds.size.z,
                (new Vector2(vertices[i].x, vertices[i].y).magnitude - min) / Mathf.Max(max - min, .001f));
            mesh.uv = uv;
        }

        private static Material Flat(string name, Color color)
        {
            var material = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = name, color = color };
            material.SetFloat("_Metallic", .08f);
            material.SetFloat("_Smoothness", .30f);
            return Save(material, Root + "/" + name + ".mat");
        }

        private static T Save<T>(T value, string path) where T : Object
        {
            var old = AssetDatabase.LoadAssetAtPath<T>(path);
            if (old == null) { AssetDatabase.CreateAsset(value, path); return value; }
            EditorUtility.CopySerialized(value, old);
            Object.DestroyImmediate(value);
            return old;
        }

        private static void Validate(GameObject root, MeshPacket packet, int triangles)
        {
            if (triangles != packet.triangleCount || root.GetComponentsInChildren<MeshRenderer>().Length != 19)
                throw new InvalidOperationException("Hybrid mesh/renderer totals changed on import");
            if (root.transform.localPosition != Vector3.zero || root.transform.localScale != Vector3.one || root.transform.localRotation != Quaternion.identity)
                throw new InvalidOperationException("Hybrid root transform changed");
            var bounds = root.GetComponent<MeshFilter>().sharedMesh.bounds;
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>())
            {
                bounds.Encapsulate(filter.sharedMesh.bounds);
                if (filter.sharedMesh.uv.Length != filter.sharedMesh.vertexCount) throw new InvalidOperationException("Missing UVs");
                foreach (var uv in filter.sharedMesh.uv) if (float.IsNaN(uv.x) || float.IsNaN(uv.y) || float.IsInfinity(uv.x) || float.IsInfinity(uv.y)) throw new InvalidOperationException("Nonfinite UVs");
                if (filter.name.StartsWith("booster_", StringComparison.Ordinal) && !filter.transform.IsChildOf(root.transform.Find("Booster"))) throw new InvalidOperationException("Detached booster hierarchy broken");
            }
            if (Mathf.Abs(bounds.min.z + Half) > .0001f || Mathf.Abs(bounds.max.z - Half) > .0001f) throw new InvalidOperationException("Hybrid scale/axis/pivot bounds changed");
            foreach (var renderer in root.GetComponentsInChildren<MeshRenderer>())
            foreach (var material in renderer.sharedMaterials)
            {
                var albedo = material.GetTexture("_BaseMap");
                var packed = material.GetTexture("_MetallicGlossMap");
                if (albedo != null && !GraphicsFormatUtility.IsSRGBFormat(albedo.graphicsFormat)) throw new InvalidOperationException("Albedo is not sRGB");
                if (packed != null && GraphicsFormatUtility.IsSRGBFormat(packed.graphicsFormat)) throw new InvalidOperationException("Packed MS must be linear");
            }
            if (root.GetComponentsInChildren<MonoBehaviour>().Length > 0) throw new InvalidOperationException("Gameplay script in geometry preview prefab");
        }

        private static void Render(Camera camera, Vector3 position, Vector3 target, float size, string name)
        {
            camera.transform.position = position;
            camera.transform.LookAt(target, Vector3.up);
            camera.orthographicSize = size;
            var rt = new RenderTexture(2000, 1200, 24, RenderTextureFormat.ARGB32);
            var image = new Texture2D(2000, 1200, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = rt;
                RenderTexture.active = rt;
                camera.Render();
                image.ReadPixels(new Rect(0, 0, 2000, 1200), 0, 0);
                image.Apply();
                File.WriteAllBytes(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad", name)), image.EncodeToPNG());
                Debug.Log("[Halberd Hybrid] Rendered " + name);
            }
            finally { camera.targetTexture = null; RenderTexture.active = previous; rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(image); }
        }
    }
}
