#!/usr/bin/env python3
"""Measure the vanilla weapon atlas palettes for the style findings doc.

Reads the extracted atlas PNGs from reference/vanilla_textures and writes:
  - palette_measurements.json  per-atlas dominant colors + packed-map stats
  - palette_swatch.png         one row per atlas, 8 dominant colors each
  - docs/palette_swatch.png    downscaled committed copy for the findings doc
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "vanilla_textures"
DOCS = ROOT / "docs"

ATLASES = {
    "weapons1": ("weapons1_AlbedoTransparency.png", "weapons1_MetallicSmoothness.png", "weapons1_AO.png"),
    "weapons2": ("weapons2_b.png", "weapons2_m.png", "weapons2_ao.png"),
    "weapons3": ("weapons3_b.png", "weapons3_m.png", "weapons3_ao.png"),
    "weapons4": ("weapons4_b.png", "weapons4_m.png", "weapons4_ao.png"),
    "weapons5": ("weapons5_b.png", "weapons5_m.png", "weapons5_ao.png"),
    "missiles1": ("missiles1_b.png", "missiles1_m.png", "missiles1_ao.png"),
    "missiles2": ("missiles2_b.png", "missiles2_m.png", "missiles2_ao.png"),
    "missiles3": ("missiles3_b.png", "missiles3_m.png", "missiles3_ao.png"),
    "missiles4": ("missiles4_b.png", "missiles4_m.png", "missiles4_ao.png"),
    "bombs1": ("bombs1_b.png", "bombs1_m.png", "bombs1_ao.png"),
    "ballisticMissile1": ("ballisticMissile1_b.png", "ballisticMissile1_m.png", "ballisticMissile1_ao.png"),
}


def luminance(px):
    return 0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]


def dominant_colors(img, k=8, samples=60000):
    rgba = img.convert("RGBA")
    data = list(rgba.getdata())
    opaque = [(r, g, b) for r, g, b, a in data if a > 128 and (r + g + b) > 24]
    if not opaque:
        return []
    step = max(1, len(opaque) // samples)
    pts = opaque[::step]
    pts.sort(key=luminance)
    centers = [pts[int(i * (len(pts) - 1) / max(1, k - 1))] for i in range(k)]
    for _ in range(8):
        buckets = [[] for _ in range(k)]
        for p in pts:
            best, best_d = 0, None
            for i, c in enumerate(centers):
                d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                if best_d is None or d < best_d:
                    best, best_d = i, d
            buckets[best].append(p)
        new_centers = []
        for i, bucket in enumerate(buckets):
            if bucket:
                n = len(bucket)
                new_centers.append((sum(p[0] for p in bucket) // n, sum(p[1] for p in bucket) // n, sum(p[2] for p in bucket) // n))
            else:
                new_centers.append(centers[i])
        if new_centers == centers:
            break
        centers = new_centers
    return sorted(centers, key=luminance)


def packed_stats(path):
    if not path.is_file():
        return None
    img = Image.open(path).convert("RGBA")
    data = list(img.getdata())
    step = max(1, len(data) // 40000)
    sel = data[::step]
    return {
        "meanR": round(sum(p[0] for p in sel) / len(sel) / 255.0, 3),
        "meanG": round(sum(p[1] for p in sel) / len(sel) / 255.0, 3),
        "meanB": round(sum(p[2] for p in sel) / len(sel) / 255.0, 3),
        "meanA": round(sum(p[3] for p in sel) / len(sel) / 255.0, 3),
    }


def main():
    results = {}
    rows = []
    for atlas, (albedo_name, m_name, ao_name) in ATLASES.items():
        albedo_path = SRC / albedo_name
        if not albedo_path.is_file():
            print("missing albedo:", albedo_path)
            continue
        albedo = Image.open(albedo_path)
        colors = dominant_colors(albedo)
        m_stats = packed_stats(SRC / m_name)
        ao_stats = packed_stats(SRC / ao_name)
        results[atlas] = {
            "albedo": albedo_name,
            "size": list(albedo.size),
            "dominantRGB": [list(c) for c in colors],
            "metallicSmoothnessMap": {"path": m_name, "stats": m_stats},
            "aoMap": {"path": ao_name, "stats": ao_stats},
        }
        rows.append((atlas, colors))
        print(atlas, albedo.size, [tuple(c) for c in colors], "| m:", m_stats)

    (SRC / "palette_measurements.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    cell = 56
    label_w = 260
    width = label_w + 8 * cell
    height = 20 + len(rows) * cell + 20
    sheet = Image.new("RGB", (width, height), (18, 20, 23))
    draw = ImageDraw.Draw(sheet)
    for row_index, (atlas, colors) in enumerate(rows):
        y = 20 + row_index * cell
        draw.text((10, y + cell // 2 - 6), atlas, fill=(220, 224, 228))
        for i, color in enumerate(colors):
            draw.rectangle([label_w + i * cell, y, label_w + (i + 1) * cell - 2, y + cell - 2], fill=tuple(color))
    sheet.save(SRC / "palette_swatch.png")
    sheet.resize((width // 2, height // 2)).save(DOCS / "palette_swatch.png")
    print("wrote palette_swatch.png x2")


if __name__ == "__main__":
    main()
