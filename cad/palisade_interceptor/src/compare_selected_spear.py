"""Matched original-versus-selected four-fin Spear silhouettes."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
VIEWS = (
    ("iso", "A_Spear_revision_iso.png", "Spear_Selected_iso.png"),
    ("side", "A_Spear_side.png", "Spear_Selected_side.png"),
    ("top", "A_Spear_top.png", "Spear_Selected_top.png"),
    ("tail", "A_Spear_tail.png", "Spear_Selected_tail.png"),
    ("separated", "A_Spear_Separated_revision_separated.png", "Spear_Selected_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(VIEWS)*560+64), "white")
    draw = ImageDraw.Draw(board)
    draw.text((25, 20), "A/SPEAR: original 101 mm fins vs selected image-led 79 mm fins + boattail", fill="#15202A")
    for row, (view, old_path, new_path) in enumerate(VIEWS):
        for col, filename in enumerate((old_path, new_path)):
            image = tight(REVIEWS / filename)
            tile = ImageOps.contain(image, (940, 480), Image.Resampling.LANCZOS)
            x, y = col*1000+(1000-tile.width)//2, 64+row*560+(490-tile.height)//2
            board.paste(tile, (x, y))
            label = "Original A" if col == 0 else "Fourfold SketchLow + boattail"
            draw.text((col*1000+25, 64+row*560+510), f"{label} | {view}", fill="#15202A")
    output = REVIEWS / "Spear_Selected_Original_Comparison.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    main()
