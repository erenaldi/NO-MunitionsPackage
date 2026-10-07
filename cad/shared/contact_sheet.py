"""Combine several review renders into one small image (cuts image tokens per review roughly 4x).

Usage: python contact_sheet.py OUT.png IN1.png IN2.png ... [--cols 2] [--width 800] [--label]
Each tile is scaled to --width pixels wide; one sheet of 4 tiles costs about the same as one full-size render.
Crop first (--crop x0,y0,x1,y1 in source pixels, applied to every input) when only a region matters.
"""
import argparse

from PIL import Image, ImageDraw


def sheet(paths, out, cols=2, width=800, label=True, crop=None):
    tiles = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        if crop:
            im = im.crop(crop)
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        if label:
            ImageDraw.Draw(im).text((8, 6), p.replace("\\", "/").rsplit("/", 1)[-1], fill=(255, 255, 0))
        tiles.append(im)
    rows = (len(tiles) + cols - 1) // cols
    th = max(t.height for t in tiles)
    canvas = Image.new("RGB", (cols * width, rows * th), (20, 20, 24))
    for i, t in enumerate(tiles):
        canvas.paste(t, ((i % cols) * width, (i // cols) * th))
    canvas.save(out)
    return canvas.size


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--crop", help="x0,y0,x1,y1")
    ap.add_argument("--no-label", action="store_true")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    print(sheet(a.inputs, a.out, a.cols, a.width, not a.no_label, crop))
