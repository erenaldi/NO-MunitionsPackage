using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace Erenaldi.Halberd
{
    public static class HalberdTexturePreviewBuilder
    {
        private const string PreviewRoot = HalberdMeshBuilder.OutputRoot + "/TexturePreviews";
        private const string ScenePath = PreviewRoot + "/HalberdTextureComparison.unity";
        private const string LegacyScenePath = PreviewRoot + "/HalberdTextureSchemes.unity";
        private const string RuntimeGeometryRoot = @"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\config\Erenaldi.MunitionsPackage";
        private const int TextureWidth = 512;
        private const int TextureHeight = 128;

        private struct ColorBand
        {
            public float Min;
            public float Max;
            public Color Color;

            public ColorBand(float min, float max, Color color)
            {
                Min = min;
                Max = max;
                Color = color;
            }
        }

        private struct TextureFeature
        {
            public float UMin;
            public float UMax;
            public float VMin;
            public float VMax;
            public Color Fill;
            public Color Border;
            public float BorderWidth;

            public TextureFeature(float uMin, float uMax, float vMin, float vMax, Color fill, Color border, float borderWidth)
            {
                UMin = uMin;
                UMax = uMax;
                VMin = vMin;
                VMax = vMax;
                Fill = fill;
                Border = border;
                BorderWidth = borderWidth;
            }
        }

        [MenuItem("Blueprinter/Halberd/Build Vanilla Texture Comparison")]
        public static void BuildAndOpen()
        {
            HalberdMeshBuilder.Build();
            EnsureFolder(HalberdMeshBuilder.OutputRoot, "TexturePreviews");

            var sourceBody = LoadMesh(HalberdMeshBuilder.OutputRoot + "/MeshHalberdBody.asset");
            var sourceBooster = LoadMesh(HalberdMeshBuilder.OutputRoot + "/MeshHalberdBooster.asset");
            var halberdBody = CreatePreviewMesh(sourceBody, "MeshHalberdBodyPreview");
            var halberdBooster = CreatePreviewMesh(sourceBooster, "MeshHalberdBoosterPreview");
            var scythe = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM2.geometry.obj"), "MeshScytheRuntime");
            var scimitar = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM4.geometry.obj"), "MeshScimitarRuntime");
            SaveAsset(halberdBody, halberdBody.name + ".asset");
            SaveAsset(halberdBooster, halberdBooster.name + ".asset");
            SaveAsset(scythe, scythe.name + ".asset");
            SaveAsset(scimitar, scimitar.name + ".asset");

            var charcoal = new Color(0.075f, 0.085f, 0.095f);
            var seam = new Color(0.20f, 0.22f, 0.23f);
            var scytheMaterial = CreateMaterial(
                "ScytheReference",
                new Color(0.76f, 0.78f, 0.77f),
                seam,
                new[] { 0.18f, 0.57f, 0.75f, 0.88f },
                new[]
                {
                    new ColorBand(0f, 0.055f, charcoal),
                    new ColorBand(0.865f, 1f, charcoal)
                },
                0.08f,
                0.34f);
            var scimitarMaterial = CreateMaterial(
                "ScimitarReference",
                new Color(0.70f, 0.72f, 0.71f),
                seam,
                new[] { 0.17f, 0.43f, 0.70f, 0.82f },
                new[]
                {
                    new ColorBand(0f, 0.055f, new Color(0.28f, 0.29f, 0.28f)),
                    new ColorBand(0.70f, 0.82f, new Color(0.43f, 0.45f, 0.44f)),
                    new ColorBand(0.94f, 1f, new Color(0.46f, 0.40f, 0.30f))
                },
                0.20f,
                0.40f);
            var halberdBodyMaterial = CreateApprovedBodyMaterial(PreviewRoot, "HalberdVanillaBody");
            var halberdBoosterMaterial = CreateApprovedBoosterMaterial(PreviewRoot, "HalberdVanillaBooster");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateLighting();
            var camera = CreateCamera();
            CreateMissile("AAM-29 SCYTHE  (VANILLA)", 0.9f, scythe, scytheMaterial, null, null);
            CreateMissile("AAM-44 HALBERD", 0f, halberdBody, halberdBodyMaterial, halberdBooster, halberdBoosterMaterial);
            CreateMissile("AAM-36 SCIMITAR  (VANILLA)", -0.9f, scimitar, scimitarMaterial, null, null);
            CreateLabel("AAM-29 SCYTHE  /  REFERENCE", 1.12f);
            CreateLabel("AAM-44 HALBERD  /  VANILLA STYLE", 0.22f);
            CreateLabel("AAM-36 SCIMITAR  /  REFERENCE", -0.68f);

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorSceneManager.SaveScene(scene, LegacyScenePath, true);
            RenderPreview(camera);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Halberd] Vanilla texture comparison scene built: " + ScenePath);
        }

        internal static Material CreateApprovedBodyMaterial(string assetRoot, string name)
        {
            return HalberdTexturedMaterialBuilder.CreateBodyMaterial(assetRoot, name);
        }

        internal static Material CreateApprovedBoosterMaterial(string assetRoot, string name)
        {
            return HalberdTexturedMaterialBuilder.CreateBoosterMaterial(assetRoot, name);
        }

        private static Mesh LoadMesh(string path)
        {
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (mesh == null)
            {
                throw new System.InvalidOperationException("Preview source mesh was not built: " + path);
            }
            return mesh;
        }

        private static Mesh LoadRuntimeObj(string path, string name)
        {
            if (!File.Exists(path))
            {
                throw new FileNotFoundException("Runtime missile geometry is missing", path);
            }
            var vertices = new List<Vector3>();
            var triangles = new List<int>();
            foreach (var line in File.ReadLines(path))
            {
                if (line.StartsWith("v "))
                {
                    var values = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                    vertices.Add(new Vector3(ParseFloat(values[1]), ParseFloat(values[2]), ParseFloat(values[3])));
                }
                else if (line.StartsWith("f "))
                {
                    var values = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                    for (int i = 1; i <= 3; i++)
                    {
                        var token = values[i];
                        var slash = token.IndexOf('/');
                        if (slash >= 0)
                        {
                            token = token.Substring(0, slash);
                        }
                        triangles.Add(int.Parse(token, CultureInfo.InvariantCulture) - 1);
                    }
                }
            }
            if (vertices.Count == 0 || triangles.Count == 0)
            {
                throw new System.InvalidOperationException("Runtime OBJ has no geometry: " + path);
            }

            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(vertices);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            var texturedMesh = HalberdMeshBuilder.GenerateCylindricalUvs(mesh);
            Object.DestroyImmediate(mesh);
            mesh = texturedMesh;
            mesh.RecalculateTangents();
            return mesh;
        }

        private static float ParseFloat(string value)
        {
            return float.Parse(value, NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        private static Mesh CreatePreviewMesh(Mesh source, string name)
        {
            var mesh = Object.Instantiate(source);
            mesh.name = name;
            var texturedMesh = HalberdMeshBuilder.GenerateCylindricalUvs(mesh);
            Object.DestroyImmediate(mesh);
            mesh = texturedMesh;
            mesh.RecalculateTangents();
            return mesh;
        }

        private static Material CreateMaterial(
            string name,
            Color baseColor,
            Color seamColor,
            float[] panelSeams,
            ColorBand[] bands,
            float metallic,
            float smoothness,
            TextureFeature[] features = null)
        {
            return CreateMaterial(PreviewRoot, name, baseColor, seamColor, panelSeams, bands, metallic, smoothness, features);
        }

        private static Material CreateMaterial(
            string assetRoot,
            string name,
            Color baseColor,
            Color seamColor,
            float[] panelSeams,
            ColorBand[] bands,
            float metallic,
            float smoothness,
            TextureFeature[] features = null)
        {
            var texture = CreateTexture(name, baseColor, seamColor, panelSeams, bands, features);
            SaveAsset(texture, assetRoot, "Tex" + name + ".asset");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }
            var material = new Material(shader) { name = "Mat" + name };
            material.color = Color.white;
            material.SetTexture("_BaseMap", texture);
            material.SetTexture("_MainTex", texture);
            material.SetFloat("_Metallic", metallic);
            material.SetFloat("_Smoothness", smoothness);
            SaveAsset(material, assetRoot, material.name + ".mat");
            return material;
        }

        private static Texture2D CreateTexture(
            string name,
            Color baseColor,
            Color seamColor,
            float[] panelSeams,
            ColorBand[] bands,
            TextureFeature[] features)
        {
            var texture = new Texture2D(TextureWidth, TextureHeight, TextureFormat.RGBA32, true, false)
            {
                name = "Tex" + name,
                wrapMode = TextureWrapMode.Repeat,
                filterMode = FilterMode.Bilinear,
                anisoLevel = 4
            };
            var pixels = new Color[TextureWidth * TextureHeight];
            for (int y = 0; y < TextureHeight; y++)
            {
                var v = y / (TextureHeight - 1f);
                for (int x = 0; x < TextureWidth; x++)
                {
                    var u = x / (TextureWidth - 1f);
                    var hash = Mathf.Repeat(Mathf.Sin(x * 12.9898f + y * 78.233f) * 43758.5453f, 1f);
                    var color = baseColor * Mathf.Lerp(0.975f, 1.025f, hash);
                    for (int i = 0; i < panelSeams.Length; i++)
                    {
                        if (Mathf.Abs(v - panelSeams[i]) < 0.0045f)
                        {
                            color = Color.Lerp(color, seamColor, 0.62f);
                        }
                    }
                    for (int i = 0; i < bands.Length; i++)
                    {
                        if (v >= bands[i].Min && v <= bands[i].Max)
                        {
                            color = bands[i].Color * Mathf.Lerp(0.985f, 1.015f, hash);
                        }
                    }
                    if (features != null)
                    {
                        for (int i = 0; i < features.Length; i++)
                        {
                            var feature = features[i];
                            var wrapsU = feature.UMin > feature.UMax;
                            var insideU = wrapsU
                                ? u >= feature.UMin || u <= feature.UMax
                                : u >= feature.UMin && u <= feature.UMax;
                            if (!insideU || v < feature.VMin || v > feature.VMax)
                            {
                                continue;
                            }
                            var uOffset = wrapsU ? Mathf.Repeat(u - feature.UMin, 1f) : u - feature.UMin;
                            var uWidth = wrapsU ? 1f - feature.UMin + feature.UMax : feature.UMax - feature.UMin;
                            var border = feature.BorderWidth > 0f &&
                                (uOffset < feature.BorderWidth || uWidth - uOffset < feature.BorderWidth ||
                                 v - feature.VMin < feature.BorderWidth || feature.VMax - v < feature.BorderWidth);
                            color = border ? feature.Border : feature.Fill * Mathf.Lerp(0.985f, 1.015f, hash);
                        }
                    }
                    pixels[y * TextureWidth + x] = new Color(color.r, color.g, color.b, 1f);
                }
            }
            texture.SetPixels(pixels);
            texture.Apply(true, false);
            return texture;
        }

        private static void CreateMissile(
            string name,
            float z,
            Mesh bodyMesh,
            Material bodyMaterial,
            Mesh childMesh,
            Material childMaterial)
        {
            var root = new GameObject(name);
            root.transform.position = new Vector3(0f, 0f, z);
            root.transform.rotation = Quaternion.Euler(0f, 90f, 0f);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            if (childMesh != null)
            {
                var child = new GameObject("Booster");
                child.transform.SetParent(root.transform, false);
                child.AddComponent<MeshFilter>().sharedMesh = childMesh;
                child.AddComponent<MeshRenderer>().sharedMaterial = childMaterial;
            }
        }

        private static void CreateLabel(string text, float z)
        {
            var label = new GameObject(text + " Label");
            label.transform.position = new Vector3(-1.75f, 0.04f, z);
            label.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            var textMesh = label.AddComponent<TextMesh>();
            textMesh.text = text;
            textMesh.fontSize = 48;
            textMesh.characterSize = 0.037f;
            textMesh.anchor = TextAnchor.LowerLeft;
            textMesh.alignment = TextAlignment.Left;
            textMesh.color = new Color(0.82f, 0.85f, 0.88f);
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            textMesh.font = font;
            label.GetComponent<MeshRenderer>().sharedMaterial = font.material;
        }

        private static void CreateLighting()
        {
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.34f, 0.37f, 0.42f);
            var lightObject = new GameObject("Key Light");
            lightObject.transform.rotation = Quaternion.Euler(48f, -32f, 0f);
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = new Color(1f, 0.96f, 0.90f);
            light.intensity = 1.35f;
        }

        private static Camera CreateCamera()
        {
            var cameraObject = new GameObject("Preview Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(0f, 7f, 0f);
            cameraObject.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            var camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 1.5f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.08f);
            return camera;
        }

        private static void RenderPreview(Camera camera)
        {
            var renderTexture = new RenderTexture(1600, 1000, 24, RenderTextureFormat.ARGB32);
            var image = new Texture2D(1600, 1000, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = renderTexture;
                RenderTexture.active = renderTexture;
                camera.Render();
                image.ReadPixels(new Rect(0f, 0f, 1600f, 1000f), 0, 0);
                image.Apply();
                var outputPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad", "Halberd_Vanilla_Texture_Comparison.png"));
                File.WriteAllBytes(outputPath, image.EncodeToPNG());
                Debug.Log("[Halberd] Vanilla texture comparison rendered: " + outputPath);
            }
            finally
            {
                camera.targetTexture = null;
                RenderTexture.active = previous;
                Object.DestroyImmediate(renderTexture);
                Object.DestroyImmediate(image);
            }
        }

        private static void SaveAsset(Object asset, string fileName)
        {
            SaveAsset(asset, PreviewRoot, fileName);
        }

        private static void SaveAsset(Object asset, string assetRoot, string fileName)
        {
            var path = assetRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(asset, path);
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
