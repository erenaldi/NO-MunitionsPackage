using System.IO;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Halberd
{
    /// <summary>Dumps built Halberd textures to PNG for offline style review.</summary>
    public static class HalberdTextureDumpUtility
    {
        [MenuItem("Blueprinter/Halberd/Dump Textures To PNG")]
        public static void Dump()
        {
            var outputDirectory = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../..", "cad", "texture_dump"));
            Directory.CreateDirectory(outputDirectory);
            DumpTexture(HalberdMeshBuilder.OutputRoot + "/TexHalberdBodyAlbedo.asset", outputDirectory);
            DumpTexture(HalberdMeshBuilder.OutputRoot + "/TexHalberdBodyMS.asset", outputDirectory);
            DumpTexture(HalberdMeshBuilder.OutputRoot + "/TexHalberdBoosterAlbedo.asset", outputDirectory);
            DumpTexture(HalberdMeshBuilder.OutputRoot + "/TexHalberdBoosterMS.asset", outputDirectory);
            DumpTexture(HalberdMeshBuilder.OutputRoot + "/TexHalberdPlainAlbedo.asset", outputDirectory);
            Debug.Log("[Halberd] Texture dump written to " + outputDirectory);
        }

        private static void DumpTexture(string path, string outputDirectory)
        {
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (texture == null)
            {
                Debug.LogWarning("[Halberd] No texture at " + path);
                return;
            }
            var pixels = texture.GetPixels32();
            var flat = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, false);
            flat.SetPixels32(pixels);
            File.WriteAllBytes(Path.Combine(outputDirectory, texture.name + ".png"), flat.EncodeToPNG());
            Object.DestroyImmediate(flat);
        }
    }
}
