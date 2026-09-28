"""Compare visual honeycomb boundary uniformity, not functional performance.

Search clear cell widths 24–32 mm (1.5–2x the original 16 mm), two regular
orientations and symmetric lattice phases. No model files are changed here.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from cadgen import build123d as bd
import generate_kris_hybrid as model


def area(points):
    return abs(sum(a[0] * b[1] - a[1] * b[0]
                   for a, b in zip(points, points[1:] + points[:1]))) / 2


def clip(polygon, boundary):
    for a, b in zip(boundary, boundary[1:] + boundary[:1]):
        if not polygon:
            break
        def distance(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        result = []
        for p, q in zip(polygon, polygon[1:] + polygon[:1]):
            dp, dq = distance(p), distance(q)
            if dp >= -1e-9:
                result.append(p)
            if (dp >= -1e-9) != (dq >= -1e-9):
                t = dp / (dp - dq)
                result.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        polygon = result
    return polygon


def aperture():
    old_tip = math.sqrt(263 ** 2 - 21 ** 2) * model.GRID_SCALE
    unit = (old_tip - model.HINGE_RADIUS) / 662
    old_neck = model.HINGE_RADIUS + 51 * unit
    roof = model.BODY_RADIUS + 16 + model.GROUP_RADIAL_OFFSETS[2]
    neck = roof + (old_neck - roof) * model.PROTOTYPE_FOOT_HEIGHT_SCALE
    tip = neck + (old_tip - old_neck) * model.PROTOTYPE_SPAN_SCALE
    shoulder = neck + 99 * unit * model.PROTOTYPE_SPAN_SCALE
    nh = model.PROTOTYPE_FOOT_WIDTH * 95 / 225
    sh, th = 200 * unit * model.PROTOTYPE_WIDTH_SCALE, 89 * unit * model.PROTOTYPE_WIDTH_SCALE
    outer = [(neck, -nh), (shoulder, -sh), (tip, -th), (tip, th), (shoulder, sh), (neck, nh)]
    wire = bd.Wire.make_polygon([(x, y, 0) for x, y in outer], close=True)
    inner = wire.offset_2d(-model.GRID_FRAME_WIDTH, kind=bd.Kind.INTERSECTION)
    vertices = inner.vertices()
    cx, cy = sum(v.X for v in vertices) / len(vertices), sum(v.Y for v in vertices) / len(vertices)
    boundary = [(v.X, v.Y) for v in sorted(vertices, key=lambda v: math.atan2(v.Y - cy, v.X - cx))]
    return outer, boundary, (neck + tip) / 2


def layout(boundary, origin, clear, orientation, phase_x, phase_y):
    pitch = clear + 2
    step = pitch * math.sqrt(3) / 2
    radius = clear / math.sqrt(3)
    dx, dy = (step, pitch) if orientation == 0 else (pitch, step)
    xmin, xmax = min(p[0] for p in boundary), max(p[0] for p in boundary)
    ymax = max(abs(p[1]) for p in boundary)
    holes, fractions = [], []
    full_area = 3 * math.sqrt(3) * radius * radius / 2
    for column in range(math.floor((xmin - origin) / dx) - 2, math.ceil((xmax - origin) / dx) + 3):
        for row in range(math.floor(-ymax / dy) - 2, math.ceil(ymax / dy) + 3):
            x = origin + (column + phase_x) * dx
            y = (row + phase_y) * dy
            if orientation == 0:
                y += (column % 2) * pitch / 2
            else:
                x += (row % 2) * pitch / 2
            polygon = [(x + radius * math.cos(math.radians(orientation + 60 * k)),
                        y + radius * math.sin(math.radians(orientation + 60 * k))) for k in range(6)]
            clipped = clip(polygon, boundary)
            value = area(clipped) if clipped else 0
            if value > 1e-8:
                holes.append(clipped)
                fractions.append(min(1.0, value / full_area))
    partial = [f for f in fractions if f < 0.999]
    mean = sum(partial) / len(partial) if partial else 1
    variance = sum((f - mean) ** 2 for f in partial) / len(partial) if partial else 0
    slivers = sum(f < 0.15 for f in fractions)
    minimum = min(fractions)
    full = sum(f >= 0.999 for f in fractions)
    result = {"clear_mm": clear, "scale": clear / 16, "pitch_mm": pitch,
              "orientation_deg": orientation, "phase_x": phase_x, "phase_y": phase_y,
              "cells": len(holes), "full_cells": full, "slivers_below_15_percent": slivers,
              "smallest_cell_fraction": minimum, "partial_variance": variance}
    score = (slivers, -minimum, variance, -full)
    return score, result, holes


def main():
    folder = Path(__file__).resolve().parent
    outer, boundary, origin = aperture()
    candidates = []
    for tick in range(33):
        clear = 24 + tick * 0.25
        for orientation in (0, 30):
            for phase_y in ((0, 0.5) if orientation == 0 else (0,)):
                for phase in range(16):
                    candidates.append(layout(boundary, origin, clear, orientation, phase / 16, phase_y))
    candidates.sort(key=lambda candidate: candidate[0])
    baseline = layout(boundary, origin, 16, 0, 0, 0)[1]
    best = min(candidates[:6], key=lambda entry: (entry[1]["slivers_below_15_percent"],
                                                entry[1]["partial_variance"], entry[1]["cells"]))[1]
    report = {"criterion": "Shortlist six layouts with fewest sub-15% fragments and largest minimum retained cells; select least partial-cell area variation within that shortlist, checked visually.",
              "candidate_count": len(candidates), "baseline": baseline, "selected": best,
              "top_six": [entry[1] for entry in candidates[:6]]}
    (folder / "Kris_hex_layout_comparison.json").write_text(json.dumps(report, indent=2))
    image = Image.new("RGB", (1200, 1080), "white")
    draw = ImageDraw.Draw(image)
    xmin, xmax = min(p[0] for p in outer), max(p[0] for p in outer)
    ymax = max(abs(p[1]) for p in outer)
    scale = min(520 / (xmax - xmin), 275 / (2 * ymax))
    for index, (_, result, holes) in enumerate(candidates[:6]):
        left, top = (index % 2) * 600, (index // 2) * 360
        def point(p):
            return (left + 40 + (p[0] - xmin) * scale, top + 55 + (p[1] + ymax) * scale)
        draw.polygon([point(p) for p in outer], fill=(40, 44, 47))
        for hole in holes:
            draw.polygon([point(p) for p in hole], fill="white")
        label = f"{index+1}: {result['scale']:.3f}x / clear {result['clear_mm']} mm / {result['orientation_deg']} deg"
        draw.text((left + 20, top + 15), label, fill="black")
        draw.text((left + 20, top + 32), f"Slivers {result['slivers_below_15_percent']}; smallest cell {result['smallest_cell_fraction']:.0%}", fill="black")
    image.save(folder / "Kris_hex_layout_candidates.png")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
