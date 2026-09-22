using System.IO;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Phantom
{
    public static class PhantomPreviewBuilder
    {
        private const int Width = 1024;
        private const int Height = 768;

        [MenuItem("Blueprinter/Phantom/Render Unity Previews")]
        public static void RenderPreviews()
        {
            var prefabPath = PhantomMeshBuilder.OutputRoot + "/" + PhantomMeshBuilder.MissilePrefabName + ".prefab";
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                throw new System.InvalidOperationException("Phantom missile prefab has not been built");
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
            }
            finally
            {
                Object.DestroyImmediate(instance);
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
    }
}