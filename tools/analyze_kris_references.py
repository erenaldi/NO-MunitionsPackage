#!/usr/bin/env python3
"""Analyze missiles3 (IRM-S2/AAM3) and missiles1 (MMR-S3/AAM1) albedo atlases
to derive the Kris redesign palette/detail hierarchy.

Writes docs/kris_reference_analysis.json with:
  - per-atlas luminance histogram peaks (value bands)
  - per-atlas dominant colors (k-means, luminance-sorted)
  - per-atlas detail density (edge fraction) and seam/band v-profile
  - per-atlas packed-map stats (metallic/smoothness)
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "vanilla_textures"
OUT = ROOT / "docs" / "kris_reference_analysis.json"

ATLASES = {
    "missiles3_IRMS2_AAM3": ("missiles3_b.png", "missiles3_m.png"),
    "missiles1_MMRS3_AAM1": ("missiles1_b.png", "missiles1_m.png"),
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


def luminance_histogram_peaks(img, bins=32):
    gray = img.convert("L")
    hist = gray.histogram()
    width = 256 // bins
    counts = [sum(hist[i * width:(i + 1) * width]) for i in range(bins)]
    total = sum(counts)
    peaks = []
    for i in range(1, bins - 1):
        if counts[i] >= counts[i - 1] and counts[i] >= counts[i + 1] and counts[i] > total * 0.01:
            peaks.append((i * width + width // 2, round(counts[i] / total, 4)))
    return peaks


def edge_fraction(img):
    gray = img.convert("L")
    w, h = gray.size
    px = gray.load()
    edges = 0
    total = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            v = px[x, y]
            if x + 1 < w:
                total += 1
                if abs(v - px[x + 1, y]) > 24:
                    edges += 1
            if y + 1 < h:
                total += 1
                if abs(v - px[x, y + 1]) > 24:
                    edges += 1
    return round(edges / max(1, total), 4)


def v_profile(img, bands=48):
    """Mean luminance per v band (rows), to locate seam rings / value zones."""
    gray = img.convert("L")
    w, h = gray.size
    px = gray.load()
    profile = []
    band_h = h // bands
    for b in range(bands):
        total = 0
        count = 0
        for y in range(b * band_h, (b + 1) * band_h):
            for x in range(0, w, 2):
                total += px[x, y]
                count += 1
        profile.append(round(total / max(1, count), 1))
    return profile


def packed_stats(path):
    img = Image.open(path).convert("RGBA")
    data = list(img.getdata())
    step = max(1, len(data) // 40000)
    sel = data[::step]
    return {
        "meanR": round(sum(p[0] for p in sel) / len(sel) / 255.0, 3),
        "meanA": round(sum(p[3] for p in sel) / len(sel) / 255.0, 3),
    }


def main():
    results = {}
    for label, (albedo_name, m_name) in ATLASES.items():
        albedo = Image.open(SRC / albedo_name)
        results[label] = {
            "size": list(albedo.size),
            "dominantRGB": [list(c) for c in dominant_colors(albedo)],
            "luminancePeaks": luminance_histogram_peaks(albedo),
            "edgeFraction": edge_fraction(albedo),
            "vProfile48": v_profile(albedo),
            "packed": packed_stats(SRC / m_name),
        }
        print(label, albedo.size)
        print("  dominant:", [tuple(c) for c in results[label]["dominantRGB"]])
        print("  peaks:", results[label]["luminancePeaks"])
        print("  edges:", results[label]["edgeFraction"], "packed:", results[label]["packed"])
        print("  vProfile:", results[label]["vProfile48"])

    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()