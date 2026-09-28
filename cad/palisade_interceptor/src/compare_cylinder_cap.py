"""Previous tapered cap versus user-requested plain cylinder and aft fillet."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
ROWS = (
    ("full side", "Spear_BandedCap_side.png", "Spear_CylinderFillet_side.png"),
    ("cap side", "Spear_BandedCap_cap_side.png", "Spear_CylinderFillet_cap_side.png"),
    ("cap rear", "Spear_BandedCap_cap_aft.png", "Spear_CylinderFillet_cap_aft.png"),
    ("one detailed nozzle", "Spear_BandedCap_nozzle_mouth.png", "Spear_CylinderFillet_nozzle_mouth.png"),
    ("cap separated", "Spear_BandedCap_separated.png", "Spear_CylinderFillet_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(ROWS)*535), "white")
    draw = ImageDraw.Draw(board)
    for row, (label, before, after) in enumerate(ROWS):
        for col, path in enumerate((before, after)):
            image = tight(REVIEWS / path)
            tile = ImageOps.contain(image, (940, 465), Image.Resampling.LANCZOS)
            x, y = col*1000+(1000-tile.width)//2, row*535+(475-tile.height)//2
            board.paste(tile, (x, y))
            title = "Prior tapered cap" if col == 0 else "Straight cap + aft fillet"
            draw.text((col*1000+22, row*535+497), f"{title} | {label}", fill="#172633")
    path = REVIEWS / "Spear_CylinderFillet_Comparison.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
