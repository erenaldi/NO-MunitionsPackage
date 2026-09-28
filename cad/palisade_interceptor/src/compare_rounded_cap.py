"""Matched flat-ended versus rounded closed boattail review board."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("whole iso", "Spear_Selected_iso.png", "Spear_RoundedTip_iso.png"),
    ("whole side", "Spear_Selected_side.png", "Spear_RoundedTip_side.png"),
    ("cap only", "Spear_Boattail_Cap_Focus_cap_focus.png", "Spear_RoundedTip_cap_iso.png"),
    ("cap separated", "Spear_Selected_separated.png", "Spear_RoundedTip_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(PAIRS)*540), "white")
    draw = ImageDraw.Draw(board)
    for row, (name, before, after) in enumerate(PAIRS):
        for column, path in enumerate((before, after)):
            image = tight(REVIEWS / path)
            tile = ImageOps.contain(image, (945, 470), Image.Resampling.LANCZOS)
            x, y = column*1000+(1000-tile.width)//2, row*540+(475-tile.height)//2
            board.paste(tile, (x, y))
            label = "Prior flat-ended cap" if column == 0 else "Rounded closed end"
            draw.text((column*1000+20, row*540+504), f"{label} | {name}", fill="#162334")
    output = REVIEWS / "Spear_RoundedTip_Comparison.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    main()
