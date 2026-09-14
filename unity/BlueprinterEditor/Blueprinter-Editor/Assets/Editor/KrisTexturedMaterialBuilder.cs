using UnityEditor;
using UnityEngine;

namespace Erenaldi.Kris
{
    /// <summary>
    /// Original vanilla-style textures for the IRM-S4 Kris, matched to the
    /// measured language of the game's Missiles1 atlas (the vanilla IR-missile
    /// family, per the runtime material dump): light neutral gray body over a
    /// wide value range, sparse yellow-ochre accent, thin dark ring seams with
    /// rivet dots, faint streak grunge, low metallic, semi-matte paint via
    /// packed metallic(R)/smoothness(A) on URP Lit. Markings are purely
    /// geometric — no stencil text, per user preference. No vanilla texture
    /// data is used — everything is painted procedurally.
    /// </summary>
    internal static class KrisTexturedMaterialBuilder
    {
        private const int Width = 2048;
        private const int Height = 1024;

        // Body axial zones: v 0 tail .. 1 nose (full 2*pi unwrap; the Kris body
        // spans -TotalLength/2 .. +TotalLength/2, but UVs are normalized to the
        // body mesh bounds so the texture stays resolution-independent).
        private const float TailDarkEnd = 0.05f;
        private const float OchreStart = 0.885f;
        private const float OchreEnd = 0.90f;
        private const float NoseDarkStart = 0.96f;

        private static readonly float[] SeamRings = { 0.05f, 0.42f, 0.885f, 0.96f };
        private static readonly float[] AxialSeamsU = { 0.13f, 0.37f, 0.63f, 0.87f };
        private const float AxialSeamStartV = 0.07f;
        private const float AxialSeamEndV = 0.95f;

        private static readonly Color Charcoal = new Color(53f / 255f, 53f / 255f, 52f / 255f);
        private static readonly Color BaseGray = new Color(196f / 255f, 197f / 255f, 195f / 255f);
        private static readonly Color Ochre = new Color(244f / 255f, 180f / 255f, 19f / 255f);
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
            StampBodyDetail(pixels);
            var albedo = FinishTexture("TexKrisBodyAlbedo", pixels);
            var packed = CreateBodyPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        /// <summary>Neutral microsurface; the material tint sets the part family tone.</summary>
        internal static Material CreatePlainMaterial(string assetRoot, string name, Color tint)
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float u = x / (float)(Width - 1);
                    pixels[y * Width + x] = PaintPlain(u, v, Hash(x, y));
                }
            }
            var albedo = FinishTexture("TexKrisPlainAlbedo", pixels);
            var packed = CreatePlainPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed, tint);
        }

        private static Color PaintBody(float u, float v, float hash)
        {
            Color color;
            if (v <= TailDarkEnd || v >= NoseDarkStart)
            {
                color = Charcoal;
            }
            else if (v >= OchreStart && v <= OchreEnd)
            {
                color = Ochre;
            }
            else
            {
                color = BaseGray;
            }
            color = ApplyGrunge(color, u, v, hash);
            color = ApplyPanelLines(color, u, v);
            return color;
        }

        private static Color PaintPlain(float u, float v, float hash)
        {
            Color color = new Color(0.935f, 0.935f, 0.93f);
            color = ApplyGrunge(color, u, v, hash);
            if (Mathf.Abs(v - 0.5f) < 0.0022f || Mathf.Abs(v - 0.78f) < 0.0022f)
            {
                color = Color.Lerp(color, new Color(0.74f, 0.74f, 0.74f), 0.5f);
            }
            return color;
        }

        private static void StampBodyDetail(Color[] pixels)
        {
            StampRectBorder(pixels, 0.40f, 0.56f, 0.30f, 0.38f, 2, InkBlack);
            StampXInBox(pixels, 0.44f, 0.52f, 0.318f, 0.362f, 2, InkBlack);

            foreach (float ring in SeamRings)
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
                    if (v <= TailDarkEnd || v >= NoseDarkStart)
                    {
                        metal = 0.12f;
                        smooth = 0.55f;
                    }
                    else if (v >= OchreStart && v <= OchreEnd)
                    {
                        metal = 0.05f;
                        smooth = 0.50f;
                    }
                    else
                    {
                        metal = 0.06f;
                        smooth = 0.46f;
                    }
                    smooth += (hash - 0.5f) * 0.05f;
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth));
                }
            }
            return FinishTexture("TexKrisBodyMS", pixels);
        }

        private static Texture2D CreatePlainPacked()
        {
            var pixels = new Color[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    float hash = Hash(x, y);
                    float metal = 0.06f;
                    float smooth = 0.44f + (hash - 0.5f) * 0.05f;
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth));
                }
            }
            return FinishTexture("TexKrisPlainMS", pixels);
        }

        private static Material CreateTexturedMaterial(string assetRoot, string name, Texture2D albedo, Texture2D packed, Color? tint = null)
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
            material.color = tint ?? Color.white;
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
            // Longitudinal panel seams on the upper/lower flanks only.
            if (v > 0.07f && v < 0.88f && v < NoseDarkStart &&
                (Mathf.Abs(u - 0.25f) < 0.0014f || Mathf.Abs(u - 0.75f) < 0.0014f))
            {
                color = Color.Lerp(color, SeamDark, 0.5f);
            }
            // Rivet dots flanking each ring at the axial seams.
            foreach (float ring in SeamRings)
            {
                foreach (float seamU in new[] { 0.13f, 0.37f, 0.63f, 0.87f })
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
