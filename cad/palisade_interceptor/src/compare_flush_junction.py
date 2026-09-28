"""Show the CAD seam at matched scale and its actual saved-section radii."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("full side", "Spear_CylinderFillet_side.png", "Spear_FlushJunction_side.png"),
    ("seam / fin-root grazing", "Spear_CylinderFillet_iso.png", "Spear_FlushJunction_iso.png"),
    ("cap separated", "Spear_CylinderFillet_separated.png", "Spear_FlushJunction_separated.png"),
)


def chart(draw, evidence, col, y):
    left, right = col*1000+95, col*1000+905
    x0, x1 = -500., -350.
    bottom, top = y+360, y+160
    def coords(x, radius):
        return (left+(x-x0)/(x1-x0)*(right-left), bottom-(radius-59.)/4.*(bottom-top))
    draw.line((left, bottom, right, bottom), fill="#273644", width=2)
    draw.line((left, top, left, bottom), fill="#273644", width=2)
    old = evidence["prior_body_stations_mm"]
    new = evidence["new_body_stations_mm"]
    samples = [-419.5, -409., -399., -398.5, -380.]
    cap_radius = 60.76 if col == 0 else evidence["new_cap_radius_at_minus420_5_mm"]
    draw.line((*coords(-500., cap_radius), *coords(-420., cap_radius)), fill="#304B5C", width=4)
    series = old if col == 0 else new
    values = [(-420., cap_radius)] + [(x, series[str(x)]) for x in samples]
    draw.line([coords(x, r) for x, r in values], fill="#2171A4", width=5)
    draw.line((*coords(-420., 59.), *coords(-420., 63.)), fill="#B44242", width=2)
    draw.text((left, y+405), "X=-420 seam | cap-to-body radial profile from saved STEP (mm)", fill="#172733")
    draw.text((left, y+430), "Blue: actual outer radius; red: separation datum. Only the first 22 mm changes.", fill="#172733")


def main():
    evidence = json.loads((REVIEWS / "spear_flush_junction_checks.json").read_text(encoding="utf-8"))
    board = Image.new("RGB", (2*1000, (len(PAIRS)+1)*535), "white")
    draw = ImageDraw.Draw(board)
    for row, (label, old, fresh) in enumerate(PAIRS):
        for col, filename in enumerate((old, fresh)):
            image = tight(REVIEWS / filename)
            tile = ImageOps.contain(image, (945, 465), Image.Resampling.LANCZOS)
            x, y = col*1000+(1000-tile.width)//2, row*535+(475-tile.height)//2
            board.paste(tile, (x, y))
            title = "Prior 60.76→62 mm rise" if col == 0 else "Flush 62 mm cap/body join"
            draw.text((col*1000+20, row*535+496), f"{title} | {label}", fill="#152432")
    for col in range(2):
        chart(draw, evidence, col, len(PAIRS)*535)
    out = REVIEWS / "Spear_FlushJunction_Comparison.png"
    board.save(out)
    print(out)


if __name__ == "__main__":
    main()
