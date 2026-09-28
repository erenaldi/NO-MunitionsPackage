#!/usr/bin/env python3
"""Render the actual IRM-S2 (AAM3) and MMR-S3 (AAM1) runtime meshes with their
runtime atlas textures, and measure the palette/detail of the UV-covered
regions. Evidence for the Kris redesign.

Outputs:
  - cad/kris/kris_reference_IRMS2_AAM3.png   rendered AAM3 with missiles3 atlas
  - cad/kris/kris_reference_MMRS3_AAM1.png   rendered AAM1 with missiles1 atlas
  - docs/kris_reference_uv_regions.json UV-region palette measurements
"""

import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DUMP = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\config\Erenaldi.MunitionsPackage")
SRC = ROOT / "reference" / "vanilla_textures"
OUT = ROOT / "docs" / "kris_reference_uv_regions.json"

TARGETS = {
    "IRMS2_AAM3": ("AAM3.geometry.obj", "missiles3_b.png", "missiles3_m.png"),
    "MMRS3_AAM1": ("AAM1.geometry.obj", "missiles1_b.png", "missiles1_m.png"),
}


def load_obj(path):
    verts, uvs, faces = [], [], []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            p = line.split()
            verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif line.startswith("vt "):
            p = line.split()
            uvs.append((float(p[1]), float(p[2])))
        elif line.startswith("f "):
            p = line.split()
            tri = []
            for tok in p[1:4]:
                idx = int(tok.split("/")[0]) - 1
                tri.append(idx)
            faces.append(tri)
    return verts, uvs, faces


def project(v):
    """Simple orthographic side projection: x -> screen x, z -> screen y."""
    return v[0], v[2]


def render(verts, uvs, faces, albedo, size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    xs = [v[0] for v in verts]
    zs = [v[2] for v in verts]
    xmin, xmax = min(xs), max(xs)
    zmin, zmax = min(zs), max(zs)
    sx = (size - 8) / max(1e-6, xmax - xmin)
    sz = (size - 8) / max(1e-6, zmax - zmin)
    scale = min(sx, sz)
    cx = (xmin + xmax) / 2
    cz = (zmin + zmax) / 2
    aw, ah = albedo.size
    for tri in faces:
        pts = []
        for idx in tri:
            x, z = project(verts[idx])
            u, v = uvs[idx]
            sx_p = int((x - cx) * scale + size / 2)
            sy_p = int((z - cz) * scale + size / 2)
            pts.append((sx_p, sy_p, u, v))
        # rasterize triangle via bounding box
        minx = max(0, min(p[0] for p in pts))
        maxx = min(size - 1, max(p[0] for p in pts))
        miny = max(0, min(p[1] for p in pts))
        maxy = min(size - 1, max(p[1] for p in pts))
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                if point_in_tri(x, y, pts):
                    u, v = bary_uv(x, y, pts)
                    tx = int(u * (aw - 1)) % aw
                    ty = int((1 - v) * (ah - 1)) % ah
                    px[x, y] = albedo.getpixel((tx, ty))
    return img


def point_in_tri(x, y, pts):
    (x0, y0, _, _), (x1, y1, _, _), (x2, y2, _, _) = pts
    d1 = (x - x1) * (y0 - y2) - (x0 - x2) * (y - y1)
    d2 = (x - x2) * (y1 - y0) - (x1 - x0) * (y - y2)
    d3 = (x - x0) * (y2 - y1) - (x2 - x1) * (y - y0)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_neg and has_pos)


def bary_uv(x, y, pts):
    (x0, y0, u0, v0), (x1, y1, u1, v1), (x2, y2, u2, v2) = pts
    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denom) < 1e-9:
        return u0, v0
    w0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / denom
    w1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / denom
    w2 = 1 - w0 - w1
    return w0 * u0 + w1 * u1 + w2 * u2, w0 * v0 + w1 * v1 + w2 * v2


def uv_region_stats(uvs, albedo):
    """Measure the palette of the atlas region actually covered by the mesh UVs."""
    aw, ah = albedo.size
    samples = []
    for u, v in uvs:
        tx = int(u * (aw - 1)) % aw
        ty = int((1 - v) * (ah - 1)) % ah
        samples.append(albedo.getpixel((tx, ty))[:3])
    # k-means lite on sampled colors
    k = 6
    pts = sorted(samples, key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
    centers = [pts[int(i * (len(pts) - 1) / max(1, k - 1))] for i in range(k)]
    for _ in range(6):
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
        centers = new_centers
    return [list(c) for c in sorted(centers, key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])]


def main():
    results = {}
    for label, (obj_name, albedo_name, m_name) in TARGETS.items():
        verts, uvs, faces = load_obj(DUMP / obj_name)
        albedo = Image.open(SRC / albedo_name).convert("RGBA")
        img = render(verts, uvs, faces, albedo)
        out_png = ROOT / "cad" / f"kris_reference_{label}.png"
        img.save(out_png)
        stats = {
            "obj": obj_name,
            "atlas": albedo_name,
            "vertices": len(verts),
            "uvBounds": [round(min(u for u, _ in uvs), 4), round(min(v for _, v in uvs), 4),
                         round(max(u for u, _ in uvs), 4), round(max(v for _, v in uvs), 4)],
            "uvRegionDominantRGB": uv_region_stats(uvs, albedo),
        }
        results[label] = stats
        print(label, stats)
        print("  rendered", out_png)

    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()