using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Erenaldi.Phantom
{
    public static class PhantomPreviewBuilder
    {
        private const int Width = 1024;
        private const int Height = 768;
        private const string RuntimeGeometryRoot = @"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\config\Erenaldi.MunitionsPackage";
        // Preview-only reference materials live under TexturePreviews so they
        // can never become a bundle dependency of the candidate root.
        private const string PreviewRoot = PhantomMeshBuilder.OutputRoot + "/TexturePreviews";
        // Extracted vanilla atlases live in a gitignored Assets location so no
        // vanilla texture data is committed under the tracked PhantomMod root.
        private const string ReferenceTextureRoot = "Assets/Reference/vanilla_textures";

        [MenuItem("Blueprinter/Phantom/Render Unity Previews")]
        public static void RenderPreviews()
        {
            var prefabPath = PhantomMeshBuilder.OutputRoot + "/" + PhantomMeshBuilder.MissilePrefabName + ".prefab";
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                throw new System.InvalidOperationException("Phantom missile prefab has not been built");
            }
            var rackPath = PhantomMeshBuilder.OutputRoot + "/" + PhantomMeshBuilder.RackPrefabName + ".prefab";
            var rackPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(rackPath);
            if (rackPrefab == null)
            {
                throw new System.InvalidOperationException("Phantom rack prefab has not been built");
            }

            var instance = Object.Instantiate(prefab);
            instance.name = "PhantomUnityPreview";
            var cameraObject = new GameObject("PhantomPreviewCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.075f);
            camera.fieldOfView = 32f;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 30f;

            var key = CreateLight("PhantomPreviewKey", new Vector3(35f, -35f, 0f), 1.4f);
            var fill = CreateLight("PhantomPreviewFill", new Vector3(-25f, 145f, 15f), 0.65f);
            var rim = CreateLight("PhantomPreviewRim", new Vector3(15f, 30f, 180f), 0.9f);
            try
            {
                string outputRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad"));
                Render(camera, new Vector3(2.5f, 1.4f, 3.4f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Phantom_Unity_Full.png"));
                // Opposed view: 180-degree roll about the length axis (the
                // u -> u+0.5 hemisphere under the cylindrical unwrap).
                instance.transform.rotation = Quaternion.Euler(0f, 0f, 180f);
                Render(camera, new Vector3(2.5f, 1.4f, 3.4f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Phantom_Unity_Opposed.png"));
                instance.transform.rotation = Quaternion.identity;
                // Representative combat distance: the 2.8 m missile subtends
                // roughly a third of the frame at ~11 m standoff.
                Render(camera, new Vector3(6f, 3.5f, 8.5f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Phantom_Unity_CombatDistance.png"));
                // Aft-biased view exposing the recessed exhaust and the flush
                // nozzle-lip/body coplanar faces flagged by the issue-004 review.
                Render(camera, new Vector3(1.1f, 0.7f, -2.6f), new Vector3(0f, 0f, -1.0f),
                    Path.Combine(outputRoot, "Phantom_Unity_Aft.png"));
            }
            finally
            {
                Object.DestroyImmediate(instance);
                Object.DestroyImmediate(cameraObject);
                Object.DestroyImmediate(key);
                Object.DestroyImmediate(fill);
                Object.DestroyImmediate(rim);
            }

            RenderRetractedViews(rackPrefab);
            RenderVanillaComparison(prefab, rackPrefab);
        }

        private static void RenderRetractedViews(GameObject rackPrefab)
        {
            var cameraObject = new GameObject("PhantomRackCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.075f);
            camera.fieldOfView = 32f;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 30f;

            var key = CreateLight("PhantomRackKey", new Vector3(35f, -35f, 0f), 1.4f);
            var fill = CreateLight("PhantomRackFill", new Vector3(-25f, 145f, 15f), 0.65f);
            var rim = CreateLight("PhantomRackRim", new Vector3(15f, 30f, 180f), 0.9f);
            try
            {
                string outputRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad"));
                // Retracted full view: the missile alone (pylon removed) so the
                // dorsal slot/stack/fairing are inspectable without the gray
                // pylon obscuring them. The rack-context view keeps the pylon.
                var missileOnly = Object.Instantiate(rackPrefab);
                missileOnly.name = "PhantomRetractedMissilePreview";
                var pylon = missileOnly.transform.Find("pylon");
                var missile = pylon != null ? pylon.Find("rdm9") : null;
                if (missile == null)
                {
                    throw new System.InvalidOperationException("Phantom rack prefab has no pylon/rdm9 missile");
                }
                missile.SetParent(missileOnly.transform, false);
                Object.DestroyImmediate(pylon.gameObject);
                Render(camera, new Vector3(2.5f, 1.4f, 3.4f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Phantom_Unity_Retracted.png"));
                Object.DestroyImmediate(missileOnly);

                // Rack-context view: closer, framed on the pylon and the
                // stowed missile as it would read on the loadout screen.
                var rackInstance = Object.Instantiate(rackPrefab);
                rackInstance.name = "PhantomRackPreview";
                Render(camera, new Vector3(1.6f, 0.9f, 2.2f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Phantom_Unity_RackContext.png"));
                Object.DestroyImmediate(rackInstance);
            }
            finally
            {
                Object.DestroyImmediate(cameraObject);
                Object.DestroyImmediate(key);
                Object.DestroyImmediate(fill);
                Object.DestroyImmediate(rim);
            }
        }

        /// <summary>
        /// Same-scale real vanilla comparison: the Phantom deployed and
        /// retracted candidates beside the actual AGM1 (Missiles1), AAM1
        /// (Missiles1) and AAM3 (Missiles3) runtime meshes with their extracted
        /// atlases, under matched orthographic scale and lighting.
        /// </summary>
        private static void RenderVanillaComparison(GameObject deployedPrefab, GameObject rackPrefab)
        {
            var agm1 = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AGM1.geometry.obj"), "MeshPhantomAGM1Reference");
            var aam1 = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM1.geometry.obj"), "MeshPhantomAAM1Reference");
            var aam3 = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM3.geometry.obj"), "MeshPhantomAAM3Reference");
            var agm1Material = CreateReferenceMaterial("PhantomAGM1Reference", "missiles1");
            var aam1Material = CreateReferenceMaterial("PhantomAAM1Reference", "missiles1");
            var aam3Material = CreateReferenceMaterial("PhantomAAM3Reference", "missiles3");

            CreateLighting();
            var camera = CreateCamera();
            CreatePrefabInstance("RDM-9 PHANTOM  (CUSTOM, DEPLOYED)", 2.6f, deployedPrefab);
            CreatePrefabInstance("RDM-9 PHANTOM  (CUSTOM, RETRACTED)", 1.3f, rackPrefab);
            CreateMissile("AAM-1  (VANILLA / missiles1)", 0f, aam1, aam1Material);
            CreateMissile("AAM-3  (VANILLA / missiles3)", -1.3f, aam3, aam3Material);
            CreateMissile("AGM-1  (VANILLA / missiles1)", -2.6f, agm1, agm1Material);
            CreateLabel("RDM-9 PHANTOM  /  CUSTOM", 3.2f);
            CreateLabel("RDM-9 PHANTOM  /  CUSTOM", 1.9f);
            CreateLabel("AAM-1  /  missiles1 albedo+MS", 0.6f);
            CreateLabel("AAM-3  /  missiles3 albedo+MS", -0.7f);
            CreateLabel("AGM-1  /  missiles1 albedo+MS", -2.0f);

            string outputRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad"));
            RenderPreview(camera, Path.Combine(outputRoot, "Phantom_Unity_VanillaComparison.png"));
        }

        private static GameObject CreateLight(string name, Vector3 eulerAngles, float intensity)
        {
            var lightObject = new GameObject(name);
            lightObject.transform.eulerAngles = eulerAngles;
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = Color.white;
            light.intensity = intensity;
            light.shadows = LightShadows.Soft;
            return lightObject;
        }

        private static void Render(Camera camera, Vector3 position, Vector3 target, string outputPath)
        {
            camera.transform.position = position;
            camera.transform.rotation = Quaternion.LookRotation(target - position, Vector3.up);
            var renderTexture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32);
            var image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = renderTexture;
                camera.Render();
                RenderTexture.active = renderTexture;
                image.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
                image.Apply();
                ValidateNonBlank(image, outputPath);
                File.WriteAllBytes(outputPath, image.EncodeToPNG());
                Debug.Log("[Phantom] Unity preview rendered: " + outputPath);
            }
            finally
            {
                camera.targetTexture = null;
                RenderTexture.active = previous;
                Object.DestroyImmediate(image);
                renderTexture.Release();
                Object.DestroyImmediate(renderTexture);
            }
        }

        /// <summary>
        /// A blank frame (uniform background) means no graphics device was
        /// available; the preview must run without -nographics.
        /// </summary>
        private static void ValidateNonBlank(Texture2D image, string outputPath)
        {
            var pixels = image.GetPixels();
            float minValue = float.MaxValue;
            float maxValue = float.MinValue;
            for (int i = 0; i < pixels.Length; i++)
            {
                minValue = Mathf.Min(minValue, pixels[i].r);
                maxValue = Mathf.Max(maxValue, pixels[i].r);
            }
            if (maxValue - minValue < 0.02f)
            {
                throw new System.InvalidOperationException(
                    "Phantom preview rendered blank (no graphics device?): " + outputPath);
            }
        }

        private static Mesh LoadRuntimeObj(string path, string name)
        {
            if (!File.Exists(path))
            {
                throw new FileNotFoundException("Runtime missile geometry is missing", path);
            }
            var vertices = new List<Vector3>();
            var uvs = new List<Vector2>();
            var triangles = new List<int>();
            foreach (var line in File.ReadLines(path))
            {
                if (line.StartsWith("v "))
                {
                    var values = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                    vertices.Add(new Vector3(ParseFloat(values[1]), ParseFloat(values[2]), ParseFloat(values[3])));
                }
                else if (line.StartsWith("vt "))
                {
                    var values = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                    uvs.Add(new Vector2(ParseFloat(values[1]), ParseFloat(values[2])));
                }
                else if (line.StartsWith("f "))
                {
                    var values = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                    for (int i = 1; i <= 3; i++)
                    {
                        var token = values[i];
                        var parts = token.Split('/');
                        int vertexIndex = int.Parse(parts[0], CultureInfo.InvariantCulture) - 1;
                        if (parts.Length > 1 && parts[1].Length > 0)
                        {
                            int uvIndex = int.Parse(parts[1], CultureInfo.InvariantCulture) - 1;
                            if (uvIndex != vertexIndex)
                            {
                                throw new System.InvalidOperationException(
                                    "Runtime OBJ UV index " + uvIndex + " does not match vertex index " + vertexIndex + ": " + path);
                            }
                        }
                        triangles.Add(vertexIndex);
                    }
                }
            }
            if (vertices.Count == 0 || triangles.Count == 0)
            {
                throw new System.InvalidOperationException("Runtime OBJ has no geometry: " + path);
            }
            if (uvs.Count != vertices.Count)
            {
                throw new System.InvalidOperationException(
                    "Runtime OBJ UV count " + uvs.Count + " does not match vertex count " + vertices.Count + ": " + path);
            }

            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(vertices);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            mesh.RecalculateTangents();
            return mesh;
        }

        private static float ParseFloat(string value)
        {
            return float.Parse(value, NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        private static Material CreateReferenceMaterial(string name, string atlasBase)
        {
            EnsureReferenceTextures();
            if (!AssetDatabase.IsValidFolder(PreviewRoot))
            {
                AssetDatabase.CreateFolder(PhantomMeshBuilder.OutputRoot, "TexturePreviews");
            }
            var albedo = LoadReferenceTexture(atlasBase + "_b");
            var packed = LoadReferenceTexture(atlasBase + "_m");
            var ao = LoadReferenceTexture(atlasBase + "_ao");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }
            var material = new Material(shader) { name = "Mat" + name };
            material.color = Color.white;
            material.SetTexture("_BaseMap", albedo);
            material.SetTexture("_MainTex", albedo);
            material.SetTexture("_MetallicGlossMap", packed);
            material.SetTexture("_OcclusionMap", ao);
            // Normal map deliberately omitted: the extracted normal PNGs carry
            // a swizzle that does not reproduce the game's runtime normal
            // import, so binding them would render wrong normals. This preview
            // is an albedo/MS comparison, not an exact runtime match.
            material.SetFloat("_SmoothnessTextureChannel", 0f);
            material.SetFloat("_Metallic", 1f);
            material.SetFloat("_Smoothness", 1f);
            material.EnableKeyword("_METALLICSPECGLOSSMAP");
            SaveAsset(material, PreviewRoot, material.name + ".mat");
            return material;
        }

        /// <summary>
        /// Copies the extracted vanilla atlases from the gitignored repo-root
        /// reference/ folder into a gitignored Assets location and imports
        /// them with the correct color space: albedo sRGB, packed MS and AO
        /// linear (data, not color).
        /// </summary>
        private static void EnsureReferenceTextures()
        {
            var sourceRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "reference", "vanilla_textures"));
            if (!AssetDatabase.IsValidFolder("Assets/Reference"))
            {
                AssetDatabase.CreateFolder("Assets", "Reference");
            }
            if (!AssetDatabase.IsValidFolder(ReferenceTextureRoot))
            {
                AssetDatabase.CreateFolder("Assets/Reference", "vanilla_textures");
            }
            foreach (var fileName in new[] { "missiles1_b", "missiles1_m", "missiles1_ao", "missiles3_b", "missiles3_m", "missiles3_ao" })
            {
                var source = Path.Combine(sourceRoot, fileName + ".png");
                if (!File.Exists(source))
                {
                    throw new FileNotFoundException("Extracted reference texture is missing", source);
                }
                var target = ReferenceTextureRoot + "/" + fileName + ".png";
                var targetFull = Path.Combine(Application.dataPath, "Reference", "vanilla_textures", fileName + ".png");
                if (!File.Exists(targetFull))
                {
                    File.Copy(source, targetFull);
                    AssetDatabase.ImportAsset(target);
                }
                var importer = AssetImporter.GetAtPath(target) as TextureImporter;
                if (importer != null)
                {
                    bool isAlbedo = fileName.EndsWith("_b");
                    if (importer.sRGBTexture != isAlbedo)
                    {
                        importer.sRGBTexture = isAlbedo;
                        importer.SaveAndReimport();
                    }
                }
            }
        }

        private static Texture2D LoadReferenceTexture(string fileName)
        {
            var path = ReferenceTextureRoot + "/" + fileName + ".png";
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (texture == null)
            {
                throw new FileNotFoundException("Extracted reference texture is missing", path);
            }
            return texture;
        }

        private static void CreateMissile(string name, float z, Mesh bodyMesh, Material bodyMaterial)
        {
            var root = new GameObject(name);
            root.transform.position = new Vector3(0f, 0f, z);
            root.transform.rotation = Quaternion.Euler(0f, 90f, 0f);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
        }

        private static void CreatePrefabInstance(string name, float z, GameObject prefab)
        {
            var instance = Object.Instantiate(prefab);
            instance.name = name;
            instance.transform.position = new Vector3(0f, 0f, z);
            instance.transform.rotation = Quaternion.Euler(0f, 90f, 0f);
        }

        private static void CreateLabel(string text, float z)
        {
            var label = new GameObject(text + " Label");
            label.transform.position = new Vector3(0f, 0.04f, z);
            label.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            var textMesh = label.AddComponent<TextMesh>();
            textMesh.text = text;
            textMesh.fontSize = 48;
            textMesh.characterSize = 0.035f;
            textMesh.anchor = TextAnchor.MiddleCenter;
            textMesh.alignment = TextAlignment.Center;
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
            camera.orthographicSize = 3.5f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.08f);
            return camera;
        }

        private static void RenderPreview(Camera camera, string outputPath)
        {
            var renderTexture = new RenderTexture(2000, 1600, 24, RenderTextureFormat.ARGB32);
            var image = new Texture2D(2000, 1600, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = renderTexture;
                RenderTexture.active = renderTexture;
                camera.Render();
                image.ReadPixels(new Rect(0f, 0f, 2000, 1600), 0, 0);
                image.Apply();
                ValidateNonBlank(image, outputPath);
                File.WriteAllBytes(outputPath, image.EncodeToPNG());
                Debug.Log("[Phantom] Unity preview rendered: " + outputPath);
            }
            finally
            {
                camera.targetTexture = null;
                RenderTexture.active = previous;
                Object.DestroyImmediate(renderTexture);
                Object.DestroyImmediate(image);
            }
        }

        private static void SaveAsset(Object asset, string assetRoot, string fileName)
        {
            var path = assetRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(asset, path);
        }
    }
}