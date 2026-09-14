using UnityEditor;
using UnityEngine;

namespace Erenaldi.Ballista
{
    /// <summary>
    /// Original vanilla-style textures for the AGM-110 Ballista, matched to the
    /// measured language of the game's Bombs1 atlas (the bomb/standoff-munition
    /// family): warm light-gray body, olive panel zones, one orange accent
    /// band, thin dark seams with rivet rows, faint streak grunge, low
    /// metallic, semi-matte paint via packed metallic(R)/smoothness(A) on URP
    /// Lit. Markings are purely geometric — no stencil text, per user
    /// preference. No vanilla texture data is used — everything is painted
    /// procedurally.
    /// </summary>
    internal static class BallistaTexturedMaterialBuilder
    {
        private const int Width = 2048;
        private const int Height = 1024;

        // Body axial zones: v 0 tail .. 1 nose.
        private const float NoseDarkStart = 0.93f;
        private const float OrangeStart = 0.80f;
        private const float OrangeEnd = 0.815f;
        private const float OliveStart = 0.30f;
        private const float OliveEnd = 0.62f;

        private static readonly float[] SeamRings = { 0.08f, 0.30f, 0.62f, 0.80f, 0.93f };
        private static readonly float[] AxialSeamsU = { 0.13f, 0.37f, 0.63f, 0.87f };
        private const float AxialSeamStartV = 0.09f;
        private const float AxialSeamEndV = 0.92f;

        private static readonly Color Charcoal = new Color(56f / 255f, 55f / 255f, 53f / 255f);
        private static readonly Color OliveGray = new Color(122f / 255f, 121f / 255f, 108f / 255f);
        private static readonly Color BaseGray = new Color(182f / 255f, 180f / 255f, 174f / 255f);
        private static readonly Color Orange = new Color(225f / 255f, 140f / 255f, 40f / 255f);
        private static readonly Color SeamDark = new Color(30f / 255f, 29f / 255f, 28f / 255f);
        private static readonly Color InkBlack = new Color(22f / 255f, 22f / 255f, 22f / 255f);

        internal static Material CreateBodyMaterial(string assetRoot, string name)
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float u = x / (float)(Width - 1);
                    pixels[y * Width + x] = PaintBody(u, v, Hash(x, y));
                }
            }
            StampRectBorder(pixels, 0.40f, 0.56f, 0.36f, 0.44f, 2, InkBlack);
            StampXInBox(pixels, 0.44f, 0.52f, 0.375f, 0.425f, 2, InkBlack);
            BakeRingShading(pixels, SeamRings);
            var albedo = FinishTexture("TexBallistaBodyAlbedo", pixels);
            var packed = CreateBodyPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        internal static Material CreatePanelMaterial(string assetRoot, string name)
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float u = x / (float)(Width - 1);
                    Color color = new Color(0.38f, 0.385f, 0.375f);
                    color = ApplyGrunge(color, u, v, Hash(x, y));
                    if (Mathf.Abs(v - 0.33f) < 0.0030f || Mathf.Abs(v - 0.67f) < 0.0030f)
                    {
                        color = Color.Lerp(color, SeamDark, 0.55f);
                    }
                    pixels[y * Width + x] = color;
                }
            }
            var albedo = FinishTexture("TexBallistaPanelAlbedo", pixels);
            var packed = CreatePacked("TexBallistaPanelMS", 0.10f, 0.42f);
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        internal static Material CreateWingMaterial(string assetRoot, string name)
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float u = x / (float)(Width - 1);
                    Color color = OliveGray;
                    color = ApplyGrunge(color, u, v, Hash(x, y));
                    if (Mathf.Abs(v - 0.5f) < 0.0026f)
                    {
                        color = Color.Lerp(color, SeamDark, 0.5f);
                    }
                    pixels[y * Width + x] = color;
                }
            }
            var albedo = FinishTexture("TexBallistaWingAlbedo", pixels);
            var packed = CreatePacked("TexBallistaWingMS", 0.08f, 0.44f);
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        private static Color PaintBody(float u, float v, float hash)
        {
            Color color;
            if (v >= NoseDarkStart)
            {
                color = Charcoal;
            }
            else if (v >= OrangeStart && v <= OrangeEnd)
            {
                color = Orange;
            }
            else if (v >= OliveStart && v <= OliveEnd)
            {
                color = OliveGray;
            }
            else
            {
                color = BaseGray;
            }
            color = ApplyGrunge(color, u, v, hash);
            color = ApplyPanelLines(color, u, v);
            return color;
        }

        private static void BakeRingShading(Color[] pixels, float[] rings)
        {
            foreach (float ring in rings)
            {
                int center = Mathf.RoundToInt(ring * (Height - 1));
                for (int x = 0; x < Width; x++)
                {
                    for (int d = 1; d <= 6; d++)
                    {
                        float shade = Mathf.Lerp(0.9f, 1f, d / 6f);
                        MultiplyPixel(pixels, x, center + d, shade);
                        MultiplyPixel(pixels, x, center - d, shade);
                    }
                }
            }
        }

        private static Texture2D CreateBodyPacked()
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float hash = Hash(x, y);
                    float metal;
                    float smooth;
                    if (v >= NoseDarkStart)
                    {
                        metal = 0.12f;
                        smooth = 0.55f;
                    }
                    else if (v >= OrangeStart && v <= OrangeEnd)
                    {
                        metal = 0.05f;
                        smooth = 0.50f;
                    }
                    else
                    {
                        metal = 0.06f;
                        smooth = 0.45f;
                    }
                    smooth += (hash - 0.5f) * 0.05f;
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth));
                }
            }
            return FinishTexture("TexBallistaBodyMS", pixels);
        }

        private static Texture2D CreatePacked(string name, float metal, float smooth)
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    float hash = Hash(x, y);
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth + (hash - 0.5f) * 0.05f));
                }
            }
            return FinishTexture(name, pixels);
        }

        private static Material CreateTexturedMaterial(string assetRoot, string name, Texture2D albedo, Texture2D packed)
        {
            albedo.name = name + "Albedo";
            packed.name = name + "MS";
            SaveAsset(albedo, assetRoot, albedo.name + ".asset");
            SaveAsset(packed, assetRoot, packed.name + ".asset");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }
            var material = new Material(shader) { name = name };
            material.color = Color.white;
            material.SetTexture("_BaseMap", albedo);
            material.SetTexture("_MainTex", albedo);
            material.SetTexture("_MetallicGlossMap", packed);
            material.SetFloat("_SmoothnessTextureChannel", 0f);
            material.SetFloat("_Metallic", 1f);
            material.SetFloat("_Smoothness", 1f);
            material.EnableKeyword("_METALLICSPECGLOSSMAP");
            SaveAsset(material, assetRoot, material.name + ".mat");
            return material;
        }

        private static Color ApplyGrunge(Color color, float u, float v, float hash)
        {
            color *= Mathf.Lerp(0.965f, 1.035f, hash);
            float column = Hash(Mathf.FloorToInt(u * Width / 3f), 7);
            color *= Mathf.Lerp(0.965f, 1.01f, column);
            float blotch = ValueNoise(u * 9f, v * 5f, 13);
            color *= Mathf.Lerp(0.975f, 1.02f, blotch);
            return color;
        }

        private static Color ApplyPanelLines(Color color, float u, float v)
        {
            foreach (float ring in SeamRings)
            {
                if (Mathf.Abs(v - ring) < 0.0030f)
                {
                    color = Color.Lerp(color, SeamDark, 0.60f);
                }
            }
            if (v > AxialSeamStartV && v < AxialSeamEndV)
            {
                foreach (float seamU in AxialSeamsU)
                {
                    if (Mathf.Abs(u - seamU) < 0.0016f)
                    {
                        color = Color.Lerp(color, SeamDark, 0.55f);
                    }
                }
            }
            foreach (float ring in SeamRings)
            {
                foreach (float seamU in AxialSeamsU)
                {
                    if (NearDot(u, v, Mathf.Repeat(seamU - 0.014f, 1f), ring, 0.0011f) ||
                        NearDot(u, v, Mathf.Repeat(seamU + 0.014f, 1f), ring, 0.0011f))
                    {
                        color = SeamDark;
                    }
                }
            }
            return color;
        }

        private static bool NearDot(float u, float v, float dotU, float dotV, float radius)
        {
            float du = u - dotU;
            float dv = v - dotV;
            return du * du + dv * dv <= radius * radius;
        }

        private static float Hash(int x, int y)
        {
            return Mathf.Repeat(Mathf.Sin(x * 12.9898f + y * 78.233f) * 43758.5453f, 1f);
        }

        private static float ValueNoise(float x, float y, int seed)
        {
            int xi = Mathf.FloorToInt(x);
            int yi = Mathf.FloorToInt(y);
            float xf = x - xi;
            float yf = y - yi;
            float a = Hash(xi, yi + seed);
            float b = Hash(xi + 1, yi + seed);
            float c = Hash(xi, yi + 1 + seed);
            float d = Hash(xi + 1, yi + 1 + seed);
            float sx = xf * xf * (3f - 2f * xf);
            float sy = yf * yf * (3f - 2f * yf);
            return Mathf.Lerp(Mathf.Lerp(a, b, sx), Mathf.Lerp(c, d, sx), sy);
        }

        private static void StampRectBorder(Color[] pixels, float uMin, float uMax, float vMin, float vMax, int widthPx, Color ink)
        {
            int xMin = Mathf.RoundToInt(uMin * (Width - 1));
            int xMax = Mathf.RoundToInt(uMax * (Width - 1));
            int yMin = Mathf.RoundToInt(vMin * (Height - 1));
            int yMax = Mathf.RoundToInt(vMax * (Height - 1));
            for (int x = xMin; x <= xMax; x++)
            {
                for (int t = 0; t < widthPx; t++)
                {
                    SetPixel(pixels, x, yMin + t, ink);
                    SetPixel(pixels, x, yMax - t, ink);
                }
            }
            for (int y = yMin; y <= yMax; y++)
            {
                for (int t = 0; t < widthPx; t++)
                {
                    SetPixel(pixels, xMin + t, y, ink);
                    SetPixel(pixels, xMax - t, y, ink);
                }
            }
        }

        private static void StampXInBox(Color[] pixels, float uMin, float uMax, float vMin, float vMax, int widthPx, Color ink)
        {
            StampRectBorder(pixels, uMin, uMax, vMin, vMax, widthPx, ink);
            int xMin = Mathf.RoundToInt(uMin * (Width - 1)) + widthPx;
            int xMax = Mathf.RoundToInt(uMax * (Width - 1)) - widthPx;
            int yMin = Mathf.RoundToInt(vMin * (Height - 1)) + widthPx;
            int yMax = Mathf.RoundToInt(vMax * (Height - 1)) - widthPx;
            int steps = Mathf.Max(xMax - xMin, 1);
            for (int s = 0; s <= steps; s++)
            {
                float t = s / (float)steps;
                int x = Mathf.RoundToInt(Mathf.Lerp(xMin, xMax, t));
                SetPixel(pixels, x, Mathf.RoundToInt(Mathf.Lerp(yMax, yMin, t)), ink);
                SetPixel(pixels, x, Mathf.RoundToInt(Mathf.Lerp(yMin, yMax, t)), ink);
            }
        }

        private static void SetPixel(Color[] pixels, int x, int y, Color ink)
        {
            if (x < 0 || x >= Width || y < 0 || y >= Height)
            {
                return;
            }
            pixels[y * Width + x] = ink;
        }

        private static void MultiplyPixel(Color[] pixels, int x, int y, float factor)
        {
            if (x < 0 || x >= Width || y < 0 || y >= Height)
            {
                return;
            }
            pixels[y * Width + x] *= factor;
        }

        private static Texture2D FinishTexture(string name, Color[] pixels)
        {
            var texture = new Texture2D(Width, Height, TextureFormat.RGBA32, true, false)
            {
                name = name,
                wrapMode = TextureWrapMode.Repeat,
                filterMode = FilterMode.Bilinear,
                anisoLevel = 4
            };
            texture.SetPixels(pixels);
            texture.Apply(true, false);
            return texture;
        }

        private static void SaveAsset(Object asset, string assetRoot, string fileName)
        {
            var path = assetRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(asset, path);
        }
    }
}
