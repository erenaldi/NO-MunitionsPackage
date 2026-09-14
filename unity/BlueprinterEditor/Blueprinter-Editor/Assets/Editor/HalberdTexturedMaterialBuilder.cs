using UnityEditor;
using UnityEngine;

namespace Erenaldi.Halberd
{
    /// <summary>
    /// Original vanilla-style textures for the AAM-44 Halberd, matched to the
    /// measured language of the game's shared munitions atlases
    /// (docs/TEXTURE_STYLE_FINDINGS.md): bright neutral grays over a wide
    /// value range, charcoal nose/tail bands, one ochre accent, thin dark
    /// panel seams with rivet rows, faint streak grunge, baked seam shading,
    /// low metallic, semi-matte paint via packed metallic(R)/smoothness(A)
    /// maps on URP Lit. Markings are purely geometric (panel lines, service
    /// panels, X-in-box marks) — no stencil text, per user preference.
    /// No vanilla texture data is used — everything is painted procedurally.
    /// </summary>
    internal static class HalberdTexturedMaterialBuilder
    {
        private const int Width = 2048;
        private const int Height = 1024;

        // Body (sustainer) axial zones: v 0 aft .. 1 nose.
        private const float TailCharcoalEnd = 0.055f;
        private const float OchreStart = 0.856f;
        private const float OchreEnd = 0.866f;
        private const float NoseCharcoalStart = 0.866f;

        private static readonly float[] BodySeamRings = { 0.055f, 0.40f, 0.856f };
        private static readonly float[] BodyAxialSeamsU = { 0.13f, 0.37f, 0.63f, 0.87f };
        private const float AxialSeamStartV = 0.06f;
        private const float AxialSeamEndV = 0.69f;

        // Booster axial zones: v 0 aft/nozzle .. 1 forward/stage seam.
        private const float BoosterCharcoalEnd = 0.12f;
        private static readonly float[] BoosterSeamRings = { 0.30f, 0.55f, 0.78f };
        private static readonly float[] BoosterAxialSeamsU = { 0.13f, 0.37f, 0.63f, 0.87f };
        private const float BoosterAxialStartV = 0.14f;
        private const float BoosterAxialEndV = 0.93f;
        private const float BoosterOchreStart = 0.94f;
        private const float BoosterOchreEnd = 0.95f;
        private const float BoosterSeamV = 0.965f;

        private static readonly Color Charcoal = new Color(38f / 255f, 37f / 255f, 36f / 255f);
        private static readonly Color BaseGray = new Color(194f / 255f, 196f / 255f, 195f / 255f);
        private static readonly Color LightGray = new Color(184f / 255f, 187f / 255f, 186f / 255f);
        private static readonly Color Ochre = new Color(228f / 255f, 193f / 255f, 94f / 255f);
        private static readonly Color SeamDark = new Color(30f / 255f, 29f / 255f, 28f / 255f);
        private static readonly Color InkBlack = new Color(22f / 255f, 22f / 255f, 22f / 255f);

        internal static Material CreateBodyMaterial(string assetRoot, string name)
        {
            var pixels = new Color[Width * Height];
            PaintBase(pixels, PaintBodyBase);
            StampBodyDetail(pixels);
            var albedo = FinishTexture("TexHalberdBodyAlbedo", pixels);
            var packed = CreateBodyPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        internal static Material CreateBoosterMaterial(string assetRoot, string name)
        {
            var pixels = new Color[Width * Height];
            PaintBase(pixels, PaintBoosterBase);
            StampBoosterDetail(pixels);
            var albedo = FinishTexture("TexHalberdBoosterAlbedo", pixels);
            var packed = CreateBoosterPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed);
        }

        /// <summary>Neutral microsurface; the material tint sets the part family tone.</summary>
        internal static Material CreatePlainMaterial(string assetRoot, string name, Color tint)
        {
            var pixels = new Color[Width * Height];
            PaintBase(pixels, PaintPlainBase);
            var albedo = FinishTexture("TexHalberdPlainAlbedo", pixels);
            var packed = CreatePlainPacked();
            return CreateTexturedMaterial(assetRoot, name, albedo, packed, tint);
        }

        // ------------------------------------------------------------------
        // Albedo base fields
        // ------------------------------------------------------------------

        private static Color PaintBodyBase(float u, float v, float hash)
        {
            Color color;
            if (v <= TailCharcoalEnd || v >= NoseCharcoalStart)
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
            color = ApplyPanelLines(color, u, v, BodySeamRings, BodyAxialSeamsU, AxialSeamStartV, AxialSeamEndV);
            return color;
        }

        private static Color PaintBoosterBase(float u, float v, float hash)
        {
            Color color;
            if (v <= BoosterCharcoalEnd)
            {
                color = Charcoal;
            }
            else if (v >= BoosterOchreStart && v <= BoosterOchreEnd)
            {
                color = Ochre;
            }
            else
            {
                color = LightGray;
            }
            color = ApplyGrunge(color, u, v, hash);
            color = ApplyPanelLines(color, u, v, BoosterSeamRings, BoosterAxialSeamsU, BoosterAxialStartV, BoosterAxialEndV);
            if (Mathf.Abs(v - BoosterSeamV) < 0.0032f)
            {
                color = Color.Lerp(color, SeamDark, 0.62f);
            }
            if (Mathf.Abs(v - BoosterCharcoalEnd) < 0.0028f)
            {
                color = Color.Lerp(color, SeamDark, 0.55f);
            }
            for (int i = 0; i < 26; i++)
            {
                float rivetU = 0.02f + i * 0.0385f;
                if (NearDot(u, v, rivetU, 0.132f, 0.0012f) || NearDot(u, v, rivetU, 0.03f, 0.0012f))
                {
                    color = SeamDark;
                }
            }
            return color;
        }

        private static Color PaintPlainBase(float u, float v, float hash)
        {
            Color color = new Color(0.935f, 0.935f, 0.93f);
            color = ApplyGrunge(color, u, v, hash);
            if (Mathf.Abs(v - 0.5f) < 0.0022f || Mathf.Abs(v - 0.78f) < 0.0022f)
            {
                color = Color.Lerp(color, new Color(0.74f, 0.74f, 0.74f), 0.5f);
            }
            return color;
        }

        private static void PaintBase(Color[] pixels, System.Func<float, float, float, Color> painter)
        {
            for (int y = 0; y < Height; y++)
            {
                float v = y / (float)(Height - 1);
                for (int x = 0; x < Width; x++)
                {
                    float u = x / (float)(Width - 1);
                    pixels[y * Width + x] = painter(u, v, Hash(x, y));
                }
            }
        }

        // ------------------------------------------------------------------
        // Stamped markings
        // ------------------------------------------------------------------

        private static void StampBodyDetail(Color[] pixels)
        {
            StampRectBorder(pixels, 0.42f, 0.58f, 0.30f, 0.395f, 3, InkBlack);
            StampXInBox(pixels, 0.45f, 0.55f, 0.325f, 0.372f, 2, InkBlack);
            StampXInBox(pixels, 0.08f, 0.17f, 0.315f, 0.365f, 2, InkBlack);

            // Baked seam shading (AO) around ring seams.
            foreach (float ring in BodySeamRings)
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

        private static void StampBoosterDetail(Color[] pixels)
        {
            StampRectBorder(pixels, 0.30f, 0.50f, 0.38f, 0.47f, 2, InkBlack);
            StampXInBox(pixels, 0.335f, 0.465f, 0.395f, 0.455f, 2, InkBlack);
            StampRectBorder(pixels, 0.62f, 0.74f, 0.60f, 0.68f, 2, InkBlack);

            // Baked seam shading (AO) around ring seams.
            foreach (float ring in BoosterSeamRings)
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

        // ------------------------------------------------------------------
        // Packed metallic(R) / smoothness(A) maps
        // ------------------------------------------------------------------

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
                    if (v <= TailCharcoalEnd || v >= NoseCharcoalStart)
                    {
                        metal = 0.14f;
                        smooth = 0.58f;
                    }
                    else if (v >= OchreStart && v <= OchreEnd)
                    {
                        metal = 0.05f;
                        smooth = 0.50f;
                    }
                    else
                    {
                        metal = 0.06f;
                        smooth = 0.45f;
                    }
                    if (v > AxialSeamStartV && v < AxialSeamEndV &&
                        NearOneOf(x / (float)(Width - 1), BodyAxialSeamsU, 0.0016f))
                    {
                        smooth += 0.02f;
                    }
                    smooth += (hash - 0.5f) * 0.05f;
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth));
                }
            }
            return FinishTexture("TexHalberdBodyMS", pixels);
        }

        private static Texture2D CreateBoosterPacked()
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
                    if (v <= BoosterCharcoalEnd)
                    {
                        metal = 0.14f;
                        smooth = 0.58f;
                    }
                    else if (v >= BoosterOchreStart && v <= BoosterOchreEnd)
                    {
                        metal = 0.05f;
                        smooth = 0.50f;
                    }
                    else
                    {
                        metal = 0.06f;
                        smooth = 0.46f;
                    }
                    if (Mathf.Abs(v - BoosterSeamV) < 0.0016f ||
                        NearOneOf(v, BoosterSeamRings, 0.0016f))
                    {
                        smooth += 0.02f;
                    }
                    smooth += (hash - 0.5f) * 0.05f;
                    pixels[y * Width + x] = new Color(metal, metal, metal, Mathf.Clamp01(smooth));
                }
            }
            return FinishTexture("TexHalberdBoosterMS", pixels);
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
            return FinishTexture("TexHalberdPlainMS", pixels);
        }

        // ------------------------------------------------------------------
        // Material assembly
        // ------------------------------------------------------------------

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

        // ------------------------------------------------------------------
        // Surface detail helpers
        // ------------------------------------------------------------------

        private static Color ApplyGrunge(Color color, float u, float v, float hash)
        {
            color *= Mathf.Lerp(0.965f, 1.035f, hash);
            float column = Hash(Mathf.FloorToInt(u * Width / 3f), 7);
            color *= Mathf.Lerp(0.965f, 1.01f, column);
            float blotch = ValueNoise(u * 9f, v * 5f, 13);
            color *= Mathf.Lerp(0.975f, 1.02f, blotch);
            return color;
        }

        private static Color ApplyPanelLines(Color color, float u, float v, float[] rings, float[] axialSeamsU, float axialStartV, float axialEndV)
        {
            foreach (float ring in rings)
            {
                if (Mathf.Abs(v - ring) < 0.0032f)
                {
                    color = Color.Lerp(color, SeamDark, 0.62f);
                }
            }
            if (v > axialStartV && v < axialEndV)
            {
                foreach (float seamU in axialSeamsU)
                {
                    if (Mathf.Abs(u - seamU) < 0.0016f)
                    {
                        color = Color.Lerp(color, SeamDark, 0.55f);
                    }
                }
            }
            foreach (float ring in rings)
            {
                foreach (float seamU in axialSeamsU)
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

        private static bool NearOneOf(float value, float[] targets, float tolerance)
        {
            foreach (float target in targets)
            {
                if (Mathf.Abs(value - target) < tolerance)
                {
                    return true;
                }
            }
            return false;
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

        // ------------------------------------------------------------------
        // Marking primitives
        // ------------------------------------------------------------------

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
                int yDown = Mathf.RoundToInt(Mathf.Lerp(yMax, yMin, t));
                int yUp = Mathf.RoundToInt(Mathf.Lerp(yMin, yMax, t));
                SetPixel(pixels, x, yDown, ink);
                SetPixel(pixels, x, yUp, ink);
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
