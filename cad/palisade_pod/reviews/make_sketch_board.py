"""A4/A6 same physical-scale side and A6 paired-state selection board."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
TILE = (1200, 800)
ROW = 848


def image(name, scale=1):
    source = Image.open(ROOT / name).convert("RGB")
    box = (int(TILE[0]*scale), int(TILE[1]*scale))
    source = source.resize(box, Image.Resampling.LANCZOS)
    tile = Image.new("RGB", TILE, "#edf1f6")
    tile.paste(source, ((TILE[0]-box[0])//2, (TILE[1]-box[1])//2))
    return tile


def main():
    rows = (
        (("A4 / 2980 mm long", "A4_Filled_side.png", 2980/3500),
         ("A6 / 3500 mm long", "A6_Filled_side.png", 1)),
        (("A6 / bare U-frame", "A6_Bare_iso.png", 1),
         ("A6 / four box placeholders", "A6_Filled_iso.png", 1)),
        (("A6 / front sensor end", "A6_Filled_front.png", 1),
         ("A6 / aft sensor end", "A6_Filled_rear.png", 1)),
    )
    canvas = Image.new("RGB", (TILE[0]*2, 54+len(rows)*ROW), "#edf1f6")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("arial.ttf", 29)
    draw.text((24, 10), "Palisade — two-end sketch study (side row at common physical scale)",
              fill="#223546", font=font)
    for row, pair in enumerate(rows):
        y = 54+ROW*row
        for col, (label, filename, scale) in enumerate(pair):
            x = col*TILE[0]
            canvas.paste(image(filename, scale), (x, y))
            draw.text((x+24, y+TILE[1]+8), label, fill="#223546", font=font)
    canvas.save(ROOT / "A6_SketchedEnds_Review.png")


if __name__ == "__main__":
    main()
