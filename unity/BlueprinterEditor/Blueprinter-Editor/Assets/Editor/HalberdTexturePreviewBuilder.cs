using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Erenaldi.Ballista;
using Erenaldi.Kris;
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
        // Extracted vanilla atlases live in a gitignored Assets location so no
        // vanilla texture data is committed under the tracked PreviewRoot.
        private const string ReferenceTextureRoot = "Assets/Reference/vanilla_textures";

        [MenuItem("Blueprinter/Halberd/Build Vanilla Texture Comparison")]
        public static void BuildAndOpen()
        {
            HalberdMeshBuilder.Build();
            KrisMeshBuilder.Build();
            BallistaMeshBuilder.Build();
            EnsureFolder(HalberdMeshBuilder.OutputRoot, "TexturePreviews");

            // Vanilla references use the game's actual extracted atlases bound
            // like the runtime materials (missile-geometry.json), and the
            // runtime OBJ UVs are kept — no procedural stand-ins. The normal
            // map is deliberately omitted (see CreateReferenceMaterial).
            var scythe = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM2.geometry.obj"), "MeshScytheRuntime");
            var scimitar = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM4.geometry.obj"), "MeshScimitarRuntime");
            // IRM-S2 is the vanilla AAM3 (Missiles3 atlas) and MMR-S3 is the
            // vanilla AAM1 (Missiles1 atlas) — confirmed from the runtime
            // weapon-schema dump; IRMS1 is a SAM (SAM_IR1), not IRM-S2.
            var irmS2 = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM3.geometry.obj"), "MeshIRMS2Runtime");
            var mmrS3 = LoadRuntimeObj(Path.Combine(RuntimeGeometryRoot, "AAM1.geometry.obj"), "MeshMMRS3Runtime");
            SaveAsset(scythe, scythe.name + ".asset");
            SaveAsset(scimitar, scimitar.name + ".asset");
            SaveAsset(irmS2, irmS2.name + ".asset");
            SaveAsset(mmrS3, mmrS3.name + ".asset");

            var scytheMaterial = CreateReferenceMaterial("ScytheReference", "weapons4");
            var scimitarMaterial = CreateReferenceMaterial("ScimitarReference", "missiles3");
            var irmS2Material = CreateReferenceMaterial("IRMS2Reference", "missiles3");
            var mmrS3Material = CreateReferenceMaterial("MMRS3Reference", "missiles1");

            var halberdPrefab = LoadPrefab(HalberdMeshBuilder.OutputRoot, HalberdMeshBuilder.MissilePrefabName);
            var krisPrefab = LoadPrefab(KrisMeshBuilder.OutputRoot, KrisMeshBuilder.MissilePrefabName);
            var ballistaPrefab = LoadPrefab(BallistaMeshBuilder.OutputRoot, BallistaMeshBuilder.MissilePrefabName);

            RenderComparison5Weapon(scythe, scimitar, halberdPrefab, krisPrefab, ballistaPrefab, scytheMaterial, scimitarMaterial);
            RenderKrisReferenceMapping(krisPrefab, irmS2, mmrS3, irmS2Material, mmrS3Material);
            RenderOpposedViews(halberdPrefab, krisPrefab, ballistaPrefab);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Halberd] Vanilla texture comparison scene built: " + ScenePath);
        }

        private static void RenderComparison5Weapon(Mesh scythe, Mesh scimitar, GameObject halberdPrefab, GameObject krisPrefab, GameObject ballistaPrefab, Material scytheMaterial, Material scimitarMaterial)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateLighting();
            var camera = CreateCamera();
            // Rows are spaced so the deployed Ballista wings (which sweep
            // ±0.75 m in the image-y direction) clear the adjacent row, and
            // every label sits above its weapon's bounding silhouette.
            CreateMissile("AAM-29 SCYTHE  (VANILLA)", 2.6f, scythe, scytheMaterial);
            CreatePrefabInstance("AAM-44 HALBERD", 1.6f, halberdPrefab);
            CreatePrefabInstance("IRM-S4 KRIS", 0.6f, krisPrefab);
            CreatePrefabInstance("AGM-110 BALLISTA", -2.4f, ballistaPrefab);
            CreateMissile("AAM-36 SCIMITAR  (VANILLA)", -0.4f, scimitar, scimitarMaterial);
            CreateLabel("AAM-29 SCYTHE  /  weapons4 albedo+MS", 3.2f);
            CreateLabel("AAM-44 HALBERD  /  CUSTOM", 2.2f);
            CreateLabel("IRM-S4 KRIS  /  CUSTOM", 1.2f);
            CreateLabel("AGM-110 BALLISTA  /  CUSTOM", -1.4f);
            CreateLabel("AAM-36 SCIMITAR  /  missiles3 albedo+MS", 0.2f);

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorSceneManager.SaveScene(scene, LegacyScenePath, true);
            RenderPreview(camera, "Halberd_Vanilla_Texture_Comparison.png");
        }

        /// <summary>
        /// Kris next to its two actual redesign references: IRM-S2 (AAM3,
        /// Missiles3 atlas) and MMR-S3 (AAM1, Missiles1 atlas), both rendered
        /// with their runtime meshes and extracted atlases.
        /// </summary>
        private static void RenderKrisReferenceMapping(GameObject krisPrefab, Mesh irmS2, Mesh mmrS3, Material irmS2Material, Material mmrS3Material)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateLighting();
            var camera = CreateCamera();
            CreateMissile("IRM-S2  (AAM3 / missiles3)", 1.6f, irmS2, irmS2Material);
            CreatePrefabInstance("IRM-S4 KRIS  (CUSTOM)", 0f, krisPrefab);
            CreateMissile("MMR-S3  (AAM1 / missiles1)", -1.6f, mmrS3, mmrS3Material);
            CreateLabel("IRM-S2  /  missiles3 albedo+MS", 2.2f);
            CreateLabel("IRM-S4 KRIS  /  CUSTOM", 0.6f);
            CreateLabel("MMR-S3  /  missiles1 albedo+MS", -1.0f);
            RenderPreview(camera, "Kris_Reference_Mapping.png");
        }

        /// <summary>
        /// Each custom weapon rendered twice from opposed roll angles (0 and
        /// 180 degrees around the length axis). Under the cylindrical unwrap
        /// the two views show the u and u+0.5 hemispheres; a texture symmetric
        /// under the 180 roll (u -> u+0.5, a rotation, not a reflection) reads
        /// identically between the two views, and the y/x mirror symmetries
        /// (u -> 1-u / u -> (1.5-u) mod 1) make each flank carry the same
        /// markings.
        /// </summary>
        private static void RenderOpposedViews(GameObject halberdPrefab, GameObject krisPrefab, GameObject ballistaPrefab)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateLighting();
            var camera = CreateSideCamera();
            CreateOpposedPair("AAM-44 HALBERD", 1.7f, halberdPrefab);
            CreateOpposedPair("IRM-S4 KRIS", 0f, krisPrefab);
            CreateOpposedPair("AGM-110 BALLISTA", -1.7f, ballistaPrefab);
            RenderPreview(camera, "Weapon_Opposed_Views.png", 3200, 1400);
        }

        private static void CreateOpposedPair(string name, float y, GameObject prefab)
        {
            CreatePrefabInstance(name + "  SIDE A (ROLL 0)", new Vector3(0f, y, -2.5f), Quaternion.Euler(0f, 0f, 0f), prefab);
            CreatePrefabInstance(name + "  SIDE B (ROLL 180, OPPOSED)", new Vector3(0f, y, 2.5f), Quaternion.Euler(0f, 0f, 180f), prefab);
            CreateSideLabel(name + "  SIDE A (ROLL 0)", y, -2.5f);
            CreateSideLabel(name + "  SIDE B (ROLL 180, OPPOSED)", y, 2.5f);
        }

        private static GameObject LoadPrefab(string outputRoot, string prefabName)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(outputRoot + "/" + prefabName + ".prefab");
            if (prefab == null)
            {
                throw new System.InvalidOperationException("Missile prefab has not been built: " + prefabName);
            }
            return prefab;
        }

        internal static Material CreateApprovedBodyMaterial(string assetRoot, string name)
        {
            return HalberdTexturedMaterialBuilder.CreateBodyMaterial(assetRoot, name);
        }

        internal static Material CreateApprovedBoosterMaterial(string assetRoot, string name)
        {
            return HalberdTexturedMaterialBuilder.CreateBoosterMaterial(assetRoot, name);
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
            // The runtime dumper writes one vt per vertex (f v/vt with
            // matching indices, verified above), so the extracted UVs map 1:1
            // onto the vertices and are kept as-is.
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
            // import (2026-09-13 extraction note: _donotship copies differ in
            // normal swizzle), so binding them without the correct swizzle
            // would render wrong normals. This preview is an albedo/MS
            // comparison, not an exact runtime match.
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
            foreach (var fileName in new[] { "weapons4_b", "weapons4_m", "weapons4_ao", "missiles3_b", "missiles3_m", "missiles3_ao", "missiles1_b", "missiles1_m", "missiles1_ao" })
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
            CreatePrefabInstance(name, new Vector3(0f, 0f, z), Quaternion.Euler(0f, 90f, 0f), prefab);
        }

        private static void CreatePrefabInstance(string name, Vector3 position, Quaternion rotation, GameObject prefab)
        {
            var instance = Object.Instantiate(prefab);
            instance.name = name;
            instance.transform.position = position;
            instance.transform.rotation = rotation;
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

        private static void CreateSideLabel(string text, float y, float z)
        {
            var label = new GameObject(text + " Label");
            var position = new Vector3(0f, y + 0.55f, z);
            label.transform.position = position;
            // TextMesh uses the camera's forward basis, not a normal pointing
            // toward the camera (which exposes the mirrored back of the text).
            label.transform.rotation = Quaternion.LookRotation(Vector3.left, Vector3.up);
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

        private static Camera CreateSideCamera()
        {
            var cameraObject = new GameObject("Opposed Views Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(7f, 0f, 0f);
            cameraObject.transform.rotation = Quaternion.LookRotation(new Vector3(-1f, 0f, 0f), Vector3.up);
            var camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 2.4f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.08f);
            return camera;
        }

        private static void RenderPreview(Camera camera, string fileName, int width = 2000, int height = 1600)
        {
            var renderTexture = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            var image = new Texture2D(width, height, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = renderTexture;
                RenderTexture.active = renderTexture;
                camera.Render();
                image.ReadPixels(new Rect(0f, 0f, width, height), 0, 0);
                image.Apply();
                var outputPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad", fileName));
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
