"""True-scale Spear cap-length comparison, plus invariant notes."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("assembled iso", "Spear_FlushJunction_iso.png", "Spear_ShortCap_iso.png"),
    ("assembled side", "Spear_FlushJunction_side.png", "Spear_ShortCap_side.png"),
    ("isolated cap side, true 180:130 length ratio",
     "Spear_FlushJunction_cap_side.png", "Spear_ShortCap_cap_side.png"),
    ("separated / main nozzle", "Spear_FlushJunction_separated.png", "Spear_ShortCap_separated.png"),
)


def main():
    board = Image.new("RGB", (2*1000, len(PAIRS)*565+85), "white")
    draw = ImageDraw.Draw(board)
    draw.text((20, 24), "SPEAR 1200 mm fixed length | new cap 130 vs old 180 mm | fin root/tip thickness 6/2 vs 7/2.4 mm", fill="#172937")
    for row, (view, old, fresh) in enumerate(PAIRS):
        for col, name in enumerate((old, fresh)):
            image = tight(REVIEWS / name)
            if row == 2:
                # Pixel/mm equal across the two cap tiles: new 130 mm cap
                # occupies 130/180 of the old cap's pictured axial length.
                width = 760 if col == 0 else round(760*130/180)
                size = (width, round(image.height*width/image.width))
                tile = image.resize(size, Image.Resampling.LANCZOS)
                tile = ImageOps.contain(tile, (940, 485), Image.Resampling.LANCZOS)
            else:
                tile = ImageOps.contain(image, (945, 485), Image.Resampling.LANCZOS)
            x, y = col*1000+(1000-tile.width)//2, 85+row*565+(490-tile.height)//2
            board.paste(tile, (x, y))
            label = "Old 180 mm cap" if col == 0 else "New 130 mm cap"
            draw.text((col*1000+25, 85+row*565+518), f"{label} | {view}", fill="#172937")
    path = REVIEWS / "Spear_ShortCap_Comparison.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
