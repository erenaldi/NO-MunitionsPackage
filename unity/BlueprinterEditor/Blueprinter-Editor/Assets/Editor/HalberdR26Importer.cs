using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace Erenaldi.Halberd
{
    /// <summary>
    /// Candidate import of the accepted R26 Halberd export (cad/candidates/halberd_r26). Reads the OBJ groups directly
    /// (Unity's OBJ importer mirrors X), builds a script-free prefab and GPU preview renders. No bundle, collider,
    /// plugin or install work is done here.
    /// </summary>
    public static class HalberdR26Importer
    {
        private const string Root = "Assets/Blueprinter/Mods/HalberdR26";
        private const float Half = 1.685f;
        private const float Seam = -1.1233f;
        private static readonly string[] UpperGroups = { "Body", "IntakeRecess", "SustainerFins", "HardwareMain", "SustainerNozzle" };
        private static readonly string[] BoosterGroups = { "BoosterBody", "BoosterFins", "HardwareBooster", "BoosterNozzle" };

        [MenuItem("Blueprinter/Halberd R26/Build Candidate")]
        public static void BuildAndPreview()
        {
            AssetDatabase.Refresh();
            if (!AssetDatabase.IsValidFolder(Root)) AssetDatabase.CreateFolder("Assets/Blueprinter/Mods", "HalberdR26");
            string repo = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../.."));
            string source = Path.Combine(repo, "cad", "candidates", "halberd_r26");
            string reviews = Path.Combine(repo, "cad", "halberd_rounded_square", "reviews");
            string report = File.ReadAllText(Path.Combine(source, "HalberdR26_Export_Report.json"));
            int expectedTriangles = int.Parse(Regex.Match(report, "\"triangles\": (\\d+),\\s*\"triangleCeiling\"").Groups[1].Value);

            var files = Directory.GetFiles(source, "HalberdR26_*.obj");
            Array.Sort(files, StringComparer.Ordinal);
            if (files.Length != 18) throw new InvalidOperationException("Expected 18 R26 OBJ meshes, found " + files.Length);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var missile = new GameObject("Erenaldi.AAM44.R26Candidate");
            var booster = new GameObject("Booster");
            booster.transform.SetParent(missile.transform, false);
            var fins = new GameObject("SustainerFins");
            fins.transform.SetParent(missile.transform, false);
            var materials = new Dictionary<string, Material>();
            int triangles = 0, renderers = 0;
            foreach (var file in files)
            {
                var match = Regex.Match(Path.GetFileNameWithoutExtension(file), "^HalberdR26_([A-Za-z]+)_([0-9A-F]{6})$");
                if (!match.Success) throw new InvalidOperationException("Unexpected OBJ name: " + file);
                string group = match.Groups[1].Value, hex = match.Groups[2].Value;
                bool isBooster = Array.IndexOf(BoosterGroups, group) >= 0;
                if (!isBooster && Array.IndexOf(UpperGroups, group) < 0) throw new InvalidOperationException("Unknown group " + group);
                var mesh = LoadObj(file, group + "_" + hex);
                mesh = Save(mesh, Root + "/Mesh_" + group + "_" + hex + ".asset");
                triangles += mesh.triangles.Length / 3;
                GameObject node;
                if (group == "Body" && hex == "76828B") node = missile;                                        // largest upper-stage colour on the root
                else if (group == "BoosterBody") node = booster;                                               // booster hull on the Booster node
                else if (group == "SustainerFins") { node = new GameObject("SustainerFins_" + hex); node.transform.SetParent(fins.transform, false); }
                else { node = new GameObject(group + "_" + hex); node.transform.SetParent(isBooster ? booster.transform : missile.transform, false); }
                node.AddComponent<MeshFilter>().sharedMesh = mesh;
                node.AddComponent<MeshRenderer>().sharedMaterial = MaterialFor(hex, materials);
                renderers++;
                Debug.Log($"[Halberd R26] {group}_{hex}: {mesh.vertexCount} vertices, {mesh.triangles.Length / 3} triangles; bounds={mesh.bounds}");
            }
            Validate(missile, booster, expectedTriangles, triangles, renderers);
            PrefabUtility.SaveAsPrefabAsset(missile, Root + "/Erenaldi.AAM44.R26Candidate.prefab");
            AssetDatabase.SaveAssets();

            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.34f, .37f, .42f);
            var light = new GameObject("Key Light").AddComponent<Light>();
            light.type = LightType.Directional; light.intensity = 1.35f; light.color = new Color(1f, .96f, .90f);
            light.transform.rotation = Quaternion.Euler(48, -32, 0);
            var fill = new GameObject("Fill Light").AddComponent<Light>();
            fill.type = LightType.Directional; fill.intensity = .40f; fill.transform.rotation = Quaternion.Euler(25, 145, 0);
            var camera = new GameObject("R26 Preview Camera").AddComponent<Camera>();
            camera.tag = "MainCamera"; camera.orthographic = true; camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.055f, .065f, .08f); camera.nearClipPlane = .01f; camera.farClipPlane = 50f;
            Render(camera, reviews, new Vector3(3, 2, 4), Vector3.zero, 1.30f, "R26_unity_whole.png");
            Render(camera, reviews, new Vector3(5, 0, 0), Vector3.zero, 1.10f, "R26_unity_side.png");
            Render(camera, reviews, new Vector3(-1.4f, 1.0f, -3.4f), new Vector3(0, 0, -1.45f), .42f, "R26_unity_tail.png");
            Render(camera, reviews, new Vector3(1.4f, 1.0f, 3.4f), new Vector3(0, 0, 1.35f), .42f, "R26_unity_nose.png");
            Render(camera, reviews, new Vector3(1.8f, 1.3f, 0.2f), new Vector3(0, 0, -.45f), .55f, "R26_unity_intakes.png");
            booster.transform.localPosition = new Vector3(0, 0, -.45f);
            Render(camera, reviews, new Vector3(3, 2, 4), new Vector3(0, 0, -.2f), 1.45f, "R26_unity_separated.png");
            booster.transform.localPosition = Vector3.zero;
            EditorSceneManager.SaveScene(scene, Root + "/HalberdR26Preview.unity");
            Debug.Log($"[Halberd R26] PASS: candidate prefab, {triangles} triangles, {renderers} renderers, {materials.Count} material colours. No collider, bundle or install performed.");
        }

        private static Mesh LoadObj(string path, string name)
        {
            var v = new List<Vector3>(); var n = new List<Vector3>();
            var outV = new List<Vector3>(); var outN = new List<Vector3>(); var tri = new List<int>();
            var cache = new Dictionary<long, int>();
            var inv = CultureInfo.InvariantCulture;
            foreach (var raw in File.ReadLines(path))
            {
                if (raw.StartsWith("v ", StringComparison.Ordinal))
                {
                    var p = raw.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    v.Add(new Vector3(float.Parse(p[1], inv), float.Parse(p[2], inv), float.Parse(p[3], inv)));
                }
                else if (raw.StartsWith("vn ", StringComparison.Ordinal))
                {
                    var p = raw.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    n.Add(new Vector3(float.Parse(p[1], inv), float.Parse(p[2], inv), float.Parse(p[3], inv)));
                }
                else if (raw.StartsWith("f ", StringComparison.Ordinal))
                {
                    var p = raw.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length != 4) throw new InvalidOperationException("Non-triangle face in " + name);
                    for (int k = 1; k <= 3; k++)
                    {
                        var idx = p[k].Split('/');
                        int vi = int.Parse(idx[0]) - 1;
                        int ni = idx.Length >= 3 && idx[2].Length > 0 ? int.Parse(idx[2]) - 1 : -1;
                        long key = ((long)vi << 32) | (uint)(ni + 1);
                        if (!cache.TryGetValue(key, out int o))
                        {
                            o = outV.Count; cache[key] = o;
                            outV.Add(v[vi]); outN.Add(ni >= 0 ? n[ni] : Vector3.up);
                        }
                        tri.Add(o);
                    }
                }
            }
            if (outV.Count == 0 || tri.Count == 0) throw new InvalidOperationException("Empty OBJ " + name);
            var mesh = new Mesh { name = "Mesh_" + name, indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(outV); mesh.SetNormals(outN); mesh.SetTriangles(tri, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        // The export writes colours as linear 8-bit hex; Unity materials take the sRGB value.
        private static Material MaterialFor(string linearHex, Dictionary<string, Material> cache)
        {
            if (cache.TryGetValue(linearHex, out var existing)) return existing;
            float Lin(int i) => Convert.ToInt32(linearHex.Substring(i, 2), 16) / 255f;
            float Srgb(float c) => c <= 0.0031308f ? 12.92f * c : 1.055f * Mathf.Pow(c, 1f / 2.4f) - 0.055f;
            var color = new Color(Srgb(Lin(0)), Srgb(Lin(2)), Srgb(Lin(4)), 1f);
            var material = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "MatR26_" + linearHex, color = color };
            material.SetFloat("_Metallic", .10f);
            material.SetFloat("_Smoothness", .30f);
            material = Save(material, Root + "/MatR26_" + linearHex + ".mat");
            cache[linearHex] = material;
            return material;
        }

        private static T Save<T>(T value, string path) where T : Object
        {
            var old = AssetDatabase.LoadAssetAtPath<T>(path);
            if (old == null) { AssetDatabase.CreateAsset(value, path); return value; }
            EditorUtility.CopySerialized(value, old);
            Object.DestroyImmediate(value);
            return old;
        }

        private static void Validate(GameObject root, GameObject booster, int expected, int triangles, int renderers)
        {
            if (triangles != expected) throw new InvalidOperationException($"Triangle total {triangles} != export report {expected}");
            if (root.GetComponentsInChildren<MeshRenderer>().Length != 18 || renderers != 18) throw new InvalidOperationException("Renderer count changed");
            if (root.transform.localPosition != Vector3.zero || root.transform.localScale != Vector3.one || root.transform.localRotation != Quaternion.identity)
                throw new InvalidOperationException("Root transform changed");
            if (root.GetComponent<MeshRenderer>() == null) throw new InvalidOperationException("Body renderer must be on the root");
            bool first = true; Bounds all = default;
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>())
            {
                if (first) { all = filter.sharedMesh.bounds; first = false; } else all.Encapsulate(filter.sharedMesh.bounds);
                bool underBooster = filter.transform == booster.transform || filter.transform.IsChildOf(booster.transform);
                string meshName = filter.sharedMesh.name;
                bool boosterMesh = meshName.StartsWith("Mesh_Booster", StringComparison.Ordinal) || meshName.StartsWith("Mesh_HardwareBooster", StringComparison.Ordinal);
                if (underBooster != boosterMesh) throw new InvalidOperationException("Stage ownership wrong for " + meshName);
                var b = filter.sharedMesh.bounds;
                if (underBooster && b.max.z > Seam + .0001f) throw new InvalidOperationException("Booster mesh forward of the seam: " + meshName);
                if (!underBooster && b.min.z < Seam - .0001f) throw new InvalidOperationException("Upper mesh aft of the seam: " + meshName);
            }
            if (Mathf.Abs(all.min.z + Half) > .0005f || Mathf.Abs(all.max.z - Half) > .0005f) throw new InvalidOperationException("Axis/scale/pivot bounds changed: " + all);
            if (root.GetComponentsInChildren<MonoBehaviour>().Length > 0 || root.GetComponentsInChildren<Collider>().Length > 0)
                throw new InvalidOperationException("Scripts or colliders present in the geometry candidate");
        }

        private static void Render(Camera camera, string folder, Vector3 position, Vector3 target, float size, string name)
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
                File.WriteAllBytes(Path.Combine(folder, name), image.EncodeToPNG());
                Debug.Log("[Halberd R26] Rendered " + name);
            }
            finally { camera.targetTexture = null; RenderTexture.active = previous; rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(image); }
        }
    }
}
