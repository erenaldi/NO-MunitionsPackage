"""Compare rendered CAD with an explicitly manual attachment trace.

Only uniform scaling and centerline translation are used. This is an artistic
diagnostic, not photographic metrology; the source image itself is not reproduced.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from compare_kris_stencil import largest_component


def outline(mask):
    return ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)),
                               mask.filter(ImageFilter.MinFilter(3)))


def compare(render_path, trace, output_path):
    reference = Image.new("L", tuple(trace["canvas"]))
    draw = ImageDraw.Draw(reference)
    for polygon in trace["silhouette_polygons"].values():
        draw.polygon([tuple(p) for p in polygon], fill=255)
    ref_bbox = reference.getbbox()
    if ref_bbox is None:
        raise ValueError("Empty manual reference trace")
    reference = reference.crop(ref_bbox)

    # Snapshot camera keeps +Z upward. Clockwise rotation puts the nose at right.
    render = Image.open(render_path).convert("RGB").transpose(Image.Transpose.ROTATE_270)
    background = Image.new("RGB", render.size, render.getpixel((0, 0)))
    delta = ImageChops.difference(render, background).convert("L")
    mask = largest_component(delta.point(lambda p: 255 if p > 15 else 0))
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError(f"No CAD silhouette in {render_path}")
    render, mask = render.crop(bbox), mask.crop(bbox)

    # Normalize to the source width. Never stretch height independently.
    scale = reference.width / render.width
    target = (reference.width, max(1, round(render.height * scale)))
    render = render.resize(target, Image.Resampling.LANCZOS)
    mask = mask.resize(target, Image.Resampling.NEAREST)
    pixels = np.asarray(mask) > 0
    center_samples = []
    for x in range(round(mask.width * 0.68), round(mask.width * 0.78)):
        ys = np.flatnonzero(pixels[:, x])
        if len(ys):
            center_samples.append((float(ys[0]) + float(ys[-1])) * 0.5)
    if not center_samples:
        raise ValueError("Could not identify the body centerline")
    model_center = float(np.median(center_samples))
    reference_center = sum(p[1] for p in trace["axis"]) / 2 - ref_bbox[1]
    padding, height = 35, 180
    model_y = round(height / 2 - model_center)
    ref_y = round(height / 2 - reference_center)
    if min(model_y, ref_y) < 0 or max(model_y + mask.height, ref_y + reference.height) > height:
        raise ValueError("Comparison canvas clips the silhouettes")
    canvas = Image.new("RGB", (reference.width + padding * 2, height), "white")
    canvas.paste(render, (padding, model_y))
    red = outline(reference)
    canvas.paste((220, 30, 30), (padding, ref_y), red)
    features = Image.new("L", reference.size)
    features_draw = ImageDraw.Draw(features)
    for line in trace["feature_lines"].values():
        points = [(x - ref_bbox[0], y - ref_bbox[1]) for x, y in line]
        features_draw.line(points, fill=130, width=1)
    canvas.paste((220, 30, 30), (padding, ref_y), features)
    ImageDraw.Draw(canvas).text((12, 8), "RED: manual attachment trace | GRAY: CAD | NOT pixel-extracted", fill="black")

    aligned_ref = Image.new("L", canvas.size)
    aligned_model = Image.new("L", canvas.size)
    aligned_ref.paste(reference, (padding, ref_y))
    aligned_model.paste(mask, (padding, model_y))
    a, b = np.asarray(aligned_ref) > 0, np.asarray(aligned_model) > 0
    iou = np.count_nonzero(a & b) / np.count_nonzero(a | b)
    canvas.resize((canvas.width * 3, canvas.height * 3), Image.Resampling.NEAREST).save(output_path)
    return {"render": str(render_path), "overlay": str(output_path),
            "manual_trace_iou": round(float(iou), 4),
            "uniform_scale": scale, "source_uncertainty_pixels": trace["uncertainty_pixels"],
            "caveat": "Overlap with manual interpretation only; not a source-image fidelity score."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("render", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    trace = json.loads(Path(__file__).with_name("pl10_stencil_landmarks.json").read_text())
    print(json.dumps(compare(args.render, trace, args.output)))


if __name__ == "__main__":
    main()
