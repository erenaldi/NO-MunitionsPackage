"""Rounded-boattail vs screenshot-led cylindrical band, one-nozzle detail."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("full missile, side", "Spear_RoundedTip_side.png", "Spear_BandedCap_side.png"),
    ("isolated cap, side", "Spear_RoundedTip_reference_cap_side.png", "Spear_BandedCap_cap_side.png"),
    ("lateral nozzle, mouth", "Spear_RoundedTip_reference_nozzle_mouth.png", "Spear_BandedCap_nozzle_mouth.png"),
    ("cap detached", "Spear_RoundedTip_separated.png", "Spear_BandedCap_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(PAIRS)*560), "white")
    draw = ImageDraw.Draw(board)
    for row, (name, before, after) in enumerate(PAIRS):
        for column, filename in enumerate((before, after)):
            image = tight(REVIEWS / filename)
            tile = ImageOps.contain(image, (945, 490), Image.Resampling.LANCZOS)
            x, y = column*1000+(1000-tile.width)//2, row*560+(495-tile.height)//2
            board.paste(tile, (x, y))
            label = "Prior long taper" if column == 0 else "Reference band / 1 detailed nozzle"
            draw.text((column*1000+22, row*560+520), f"{label} | {name}", fill="#192733")
    target = REVIEWS / "Spear_BandedCap_Comparison.png"
    board.save(target)
    print(target)


if __name__ == "__main__":
    main()
