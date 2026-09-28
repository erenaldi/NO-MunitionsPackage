"""Arrange inspected CAD snapshots beside the two user-drawn view intents."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews"
FONT = ImageFont.truetype("arial.ttf", 21)
HEADING = ImageFont.truetype("arial.ttf", 30)


def load(name, width=920, height=630, crop=None):
    image = Image.open(OUT / name).convert("RGB")
    if crop is not None:
        image = image.crop(crop)
        scale = min(width/image.width, height/image.height)
        image = image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    return image


def sheet(name, heading, panels):
    tile_w, tile_h = 960, 710
    board = Image.new("RGB", (tile_w*2, tile_h*2+90), "#e9eef1")
    pen = ImageDraw.Draw(board)
    pen.text((24, 18), heading, font=HEADING, fill="#243740")
    for slot, (title, path, crop) in enumerate(panels):
        col, row = slot % 2, slot // 2
        pen.text((col*tile_w+20, row*tile_h+104), title, font=FONT, fill="#243740")
        image = load(path, crop=crop)
        x = col*tile_w + (tile_w-image.width)//2
        y = row*tile_h + 145 + (tile_h-85-image.height)//2
        board.paste(image, (x,y))
    target=OUT/name
    board.save(target)
    print(target)


if __name__ == "__main__":
    sheet("D_SketchNose_R1_Drawing_Match.png", "RDM-9 D / DRAWING-LED NOSE AND SQUARE SECTION", [
        ("BOTTOM / sharp planform and center chine", "D_deployed_bottom.png", (600,85,1000,390)),
        ("FRONT / pointed lower V at the nose", "D_nose_section_front.png", None),
        ("MAIN BODY / lightly filleted 172 mm square", "D_midsection_front.png", None),
        ("DEPLOYED CONTEXT / pointed wedge on square body", "D_deployed_iso.png", None),
    ])
    sheet("D_SketchNose_R1_Paired.png", "RDM-9 D / SAME PARTS, TWO POSES", [
        ("DEPLOYED / rear-biased oblique", "D_deployed_iso.png", None),
        ("STOWED / rear-biased oblique", "D_stowed_iso.png", None),
        ("DEPLOYED / bottom planform", "D_deployed_bottom.png", None),
        ("STOWED / bottom planform", "D_stowed_bottom.png", None),
    ])
