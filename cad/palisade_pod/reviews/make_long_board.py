"""Review A3 and longer/lower A4 at matched framing."""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ROWS = (
    ("A3 short front / filled", "A3_Filled_front_iso.png", "A4_Filled_iso.png", "A4 long front / filled"),
    ("A3 short side / filled", "A3_Filled_side.png", "A4_Filled_side.png", "A4 lower side / filled"),
    ("A4 long front / bare", "A4_Bare_under_iso.png", "A4_Filled_under_iso.png", "A4 long front / filled"),
)


def main():
    if "--shoulder" in sys.argv:
        rows = (
            ("A4 bare / shallow foredeck", "A4_Bare_iso.png",
             "A5_Bare_iso.png", "A5 bare / raised shoulder"),
            ("A4 filled / short cap read", "A4_Filled_iso.png",
             "A5_Filled_iso.png", "A5 filled / front cover"),
            ("A4 side / restrained slope", "A4_Filled_side.png",
             "A5_Filled_side.png", "A5 side / visible shoulder"),
        )
        title = "Palisade — reference-led mount-front: A4 / A5"
        output = "A5_ShoulderFront_Review.png"
    else:
        rows = ROWS
        title = "Palisade — front-length and height study: A3 / A4"
        output = "A4_LongFront_Review.png"
    w, h = 900, 600
    sheet = Image.new("RGB", (w*2, 54+len(rows)*(h+44)), "#edf1f6")
    ink = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("arial.ttf", 25)
    ink.text((22, 12), title,
             fill="#223546", font=font)
    for row, (left_label, left_file, right_file, right_label) in enumerate(rows):
        for col, (label, filename) in enumerate(((left_label, left_file),
                                                 (right_label, right_file))):
            image = Image.open(ROOT / filename).convert("RGB")
            image.thumbnail((w, h), Image.Resampling.LANCZOS)
            x, y = col*w, 54+row*(h+44)
            sheet.paste(image, (x+(w-image.width)//2, y))
            ink.text((x+20, y+h+8), label, fill="#223546", font=font)
    sheet.save(ROOT / output)


if __name__ == "__main__":
    main()
