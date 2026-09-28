"""Matched button-nozzle and actual inset-port CAD review."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("whole Spear, port-facing side", "Spear_UniformBarrel_ACM_oldside.png", "Spear_ACMPortGroup0_side.png"),
    ("cap alone / same scale", "Spear_UniformBarrel_nozzle_mouth.png", "Spear_ACMPortGroup0_cap_mouth.png"),
    ("cap side", "Spear_UniformBarrel_cap_side.png", "Spear_ACMPortGroup0_cap_side.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(PAIRS)*555+70), "white")
    draw = ImageDraw.Draw(board)
    draw.text((20, 18), "Reference cue: PAC-3 dummy-model side thruster photo (Commons/Hunini). Six inset ports depict ONE Palisade ACM group.", fill="#172736")
    for row, (name, before, after) in enumerate(PAIRS):
        for col, filename in enumerate((before, after)):
            image = tight(REVIEWS / filename)
            tile = ImageOps.contain(image, (945, 480), Image.Resampling.LANCZOS)
            x, y = col*1000+(1000-tile.width)//2, 70+row*555+(490-tile.height)//2
            board.paste(tile, (x, y))
            title = "Old raised tube" if col == 0 else "One 6-port recessed ACM group"
            draw.text((col*1000+24, 70+row*555+515), f"{title} | {name}", fill="#172736")
    path = REVIEWS / "Spear_ACMPortGroup0_Comparison.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
