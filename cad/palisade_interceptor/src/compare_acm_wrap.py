"""Full circumferential ACM cap versus rejected four-cluster precursor."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("full, +Y", "Spear_ACMPortGroup0_side.png", "Spear_ACMWrap_side_plus_y.png"),
    ("isolated cap, +Y", "Spear_ACMPortGroup0_cap_side.png", "Spear_ACMWrap_cap_plus_y.png"),
    ("isolated cap, -Y", "Spear_ACMPortGroup0_cap_minus_y.png", "Spear_ACMWrap_cap_minus_y.png"),
    ("isolated cap, +Z", "Spear_ACMPortGroup0_cap_plus_z.png", "Spear_ACMWrap_cap_plus_z.png"),
    ("separated missile", "Spear_ACMPortGroup0_separated.png", "Spear_ACMWrap_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(PAIRS)*535+90), "white")
    draw = ImageDraw.Draw(board)
    draw.text((22, 15), "PAC-3 port vocabulary around the full detachable cap; drawing used for distribution, not exact sizing.", fill="#172737")
    draw.text((22, 42), "Left: one six-port cluster + three old pegs. Right: six staggered rows x 16 inset ports. Same Spear body and fins.", fill="#172737")
    for row, (label, before, after) in enumerate(PAIRS):
        for column, name in enumerate((before, after)):
            image = tight(REVIEWS / name)
            tile = ImageOps.contain(image, (945, 465), Image.Resampling.LANCZOS)
            x, y = column*1000+(1000-tile.width)//2, 90+row*535+(470-tile.height)//2
            board.paste(tile, (x, y))
            title = "One local group" if column == 0 else "Full ACM port wrap"
            draw.text((column*1000+20, 90+row*535+490), f"{title} | {label}", fill="#172737")
    path = REVIEWS / "Spear_ACMWrap_Comparison.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
