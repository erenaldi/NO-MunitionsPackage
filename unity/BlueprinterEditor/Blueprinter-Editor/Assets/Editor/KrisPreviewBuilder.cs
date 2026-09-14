using System.IO;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Kris
{
    public static class KrisPreviewBuilder
    {
        private const int Width = 1024;
        private const int Height = 768;

        [MenuItem("Blueprinter/Kris/Render Unity Previews")]
        public static void RenderPreviews()
        {
            var prefabPath = KrisMeshBuilder.OutputRoot + "/" + KrisMeshBuilder.MissilePrefabName + ".prefab";
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            var rackPath = KrisMeshBuilder.OutputRoot + "/" + KrisMeshBuilder.RackPrefabName + ".prefab";
            var rackPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(rackPath);
            if (prefab == null || rackPrefab == null)
            {
                throw new System.InvalidOperationException("Kris missile or rack prefab has not been built");
            }

            var instance = Object.Instantiate(prefab);
            instance.name = "KrisUnityPreview";
            var rackInstance = Object.Instantiate(rackPrefab);
            rackInstance.name = "KrisRackUnityPreview";
            rackInstance.SetActive(false);
            var cameraObject = new GameObject("KrisPreviewCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.075f);
            camera.fieldOfView = 32f;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 20f;

            var key = CreateLight("KrisPreviewKey", new Vector3(35f, -35f, 0f), 1.4f);
            var fill = CreateLight("KrisPreviewFill", new Vector3(-25f, 145f, 15f), 0.65f);
            var rim = CreateLight("KrisPreviewRim", new Vector3(15f, 30f, 180f), 0.9f);
            try
            {
                string outputRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad"));
                Render(camera, new Vector3(2.5f, 1.4f, 3.4f), new Vector3(0f, 0f, 0f),
                    Path.Combine(outputRoot, "Kris_Unity_Full.png"));
                Render(camera, new Vector3(0.35f, 0.24f, 1.82f), new Vector3(0f, 0f, 1.39f),
                    Path.Combine(outputRoot, "Kris_Unity_Seeker.png"));
                instance.SetActive(false);
                rackInstance.SetActive(true);
                Render(camera, new Vector3(0.72f, 0.52f, 0.25f), new Vector3(0f, -0.18f, -0.05f),
                    Path.Combine(outputRoot, "Kris_Unity_RackAlignment.png"));
            }
            finally
            {
                Object.DestroyImmediate(instance);
                Object.DestroyImmediate(rackInstance);
                Object.DestroyImmediate(cameraObject);
                Object.DestroyImmediate(key);
                Object.DestroyImmediate(fill);
                Object.DestroyImmediate(rim);
            }
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
                File.WriteAllBytes(outputPath, image.EncodeToPNG());
                Debug.Log("[Kris] Unity preview rendered: " + outputPath);
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
    }
}
