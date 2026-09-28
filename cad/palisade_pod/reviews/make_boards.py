"""Matched image grids; input PNGs remain the unmodified saved-STEP views."""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
NAMES = {"A": "A / Straight bridge", "B": "B / Open crown", "C": "C / Slotted shell"}


def board(filename, views):
    tile_w, tile_h = 900, 600
    sheet = Image.new("RGB", (tile_w * 2, (tile_h + 44) * 3 + 54), "#edf1f6")
    ink = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("arial.ttf", 25)
    ink.text((22, 12), filename.replace(".png", "").replace("_", " — "), fill="#223546", font=font)
    for row, direction in enumerate(NAMES):
        for col, state in enumerate(("Bare", "Filled")):
            image = Image.open(ROOT / views[direction][col]).convert("RGB")
            image.thumbnail((tile_w, tile_h), Image.Resampling.LANCZOS)
            x, y = col * tile_w, 54 + row * (tile_h + 44)
            sheet.paste(image, (x + (tile_w - image.width)//2, y))
            ink.text((x+20, y+tile_h+8), f"{NAMES[direction]}  |  {state}",
                     fill="#223546", font=font)
    sheet.save(ROOT / filename)


if __name__ == "__main__":
    if "--revision-only" not in sys.argv and "--front-only" not in sys.argv:
        board("Palisade_Underside_Comparison.png", {
            "A": ("A_Bare_opposed.png", "A_Filled_opposed.png"),
            "B": ("B_Bare_underside_iso.png", "B_Filled_underside_iso.png"),
            "C": ("C_Bare_underside_iso.png", "C_Filled_underside_iso.png")})
        board("Palisade_Dorsal_Comparison.png", {
            "A": ("A_Bare_iso.png", "A_Filled_iso.png"),
            "B": ("B_Bare_iso.png", "B_Filled_iso.png"),
            "C": ("C_Bare_iso.png", "C_Filled_iso.png")})
    if "--front-only" in sys.argv:
        front_rows = (
            ("A2 / approved side treatment, block front", "A2_Bare_iso.png", "A2_Filled_iso.png"),
            ("A3 / tapered mount-front proposal", "A3_Bare_front_iso.png", "A3_Filled_front_iso.png"),
            ("A3 / close fairing from above / from front", "A3_Front_isolated_iso.png", "A3_Front_isolated_end.png"),
        )
        w, h = 900, 600
        image = Image.new("RGB", (w*2, (h+44)*len(front_rows)+54), "#edf1f6")
        painter = ImageDraw.Draw(image)
        typeface = ImageFont.truetype("arial.ttf", 25)
        painter.text((22, 12), "Palisade — mount-front only: A2 versus A3", fill="#223546", font=typeface)
        for row, (label, first, second) in enumerate(front_rows):
            for col, file in enumerate((first, second)):
                view = Image.open(ROOT / file).convert("RGB")
                view.thumbnail((w, h), Image.Resampling.LANCZOS)
                x, y = col*w, 54+row*(h+44)
                image.paste(view, (x+(w-view.width)//2, y))
                painter.text((x+20, y+h+8), label, fill="#223546", font=typeface)
        image.save(ROOT / "A3_MountFront_Review.png")
        sys.exit(0)
    rows = (
        ("Original A / full-height side covers", "A_Bare_iso.png", "A_Filled_iso.png"),
        ("A2 / open sides, boxes fill the skin", "A2_Bare_iso.png", "A2_Filled_iso.png"),
        ("A2 / underside", "A2_Bare_under_iso.png", "A2_Filled_under_iso.png"),
    )
    width, height = 900, 600
    sheet = Image.new("RGB", (width*2, (height+44)*len(rows)+54), "#edf1f6")
    ink = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("arial.ttf", 25)
    ink.text((22, 12), "Palisade — selected A / open-side revision", fill="#223546", font=font)
    for row, (label, bare, filled) in enumerate(rows):
        for col, filename in enumerate((bare, filled)):
            image = Image.open(ROOT / filename).convert("RGB")
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            x, y = col*width, 54+row*(height+44)
            sheet.paste(image, (x+(width-image.width)//2, y))
            ink.text((x+20, y+height+8), f"{label}  |  {'Bare' if col == 0 else 'Filled'}",
                     fill="#223546", font=font)
    sheet.save(ROOT / "A2_OpenSides_Review.png")
