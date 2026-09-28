"""Original tapered shaft vs user-selected smaller constant barrel/cap."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import tight


REVIEWS = Path(__file__).resolve().parents[1] / "reviews"
PAIRS = (
    ("assembled iso", "Spear_ShortCap_iso.png", "Spear_UniformBarrel_iso.png"),
    ("assembled side", "Spear_ShortCap_side.png", "Spear_UniformBarrel_side.png"),
    ("cap removed / main nozzle", "Spear_ShortCap_separated.png", "Spear_UniformBarrel_separated.png"),
    ("cap at equal 130 mm length", "Spear_ShortCap_cap_side.png", "Spear_UniformBarrel_cap_side.png"),
)


def chart(draw, column, top):
    left, right = column*1000+90, column*1000+900
    baseline, roof = top+340, top+100
    def point(x, r):
        return left+(x+600.)/1000.*(right-left), baseline-(r-52.)/12.*(baseline-roof)
    draw.line((left, baseline, right, baseline), fill="#283B47", width=2)
    draw.line((left, roof, left, baseline), fill="#283B47", width=2)
    if column == 0:
        rows = [(-600,62.),(-470,62.),(-420,62.),(-398,62.),(-255,57.04),
                (190,55.18),(355,54.56)]
    else:
        rows = [(-600,54.56),(-470,54.56),(-255,54.56),(0,54.56),(355,54.56)]
    draw.line([point(x,r) for x,r in rows], fill="#27729A", width=5)
    draw.line((*point(355,52),*point(355,64)), fill="#AF4545", width=2)
    draw.text((left, top+385), "Saved-geometry radius along X (mm); red = preserved nose base", fill="#172633")


def main():
    report = json.loads((REVIEWS / "spear_uniform_barrel_checks.json").read_text(encoding="utf-8"))
    assert report["barrel_and_cap_radius_mm"] == 54.56
    board = Image.new("RGB", (2*1000, len(PAIRS)*520+495), "white")
    draw = ImageDraw.Draw(board)
    for row, (view, old_name, new_name) in enumerate(PAIRS):
        for column, name in enumerate((old_name, new_name)):
            image = tight(REVIEWS / name)
            if row == 3:
                # Equal cap length means equal image width on this row.
                image = image.resize((780, round(image.height*780/image.width)), Image.Resampling.LANCZOS)
            tile = ImageOps.contain(image, (940, 455), Image.Resampling.LANCZOS)
            x, y = column*1000+(1000-tile.width)//2, row*520+(462-tile.height)//2
            board.paste(tile, (x, y))
            title = "Prior taper / 62 mm cap" if column == 0 else "Uniform 54.56 mm body + cap"
            draw.text((column*1000+20, row*520+478), f"{title} | {view}", fill="#172633")
    for column in range(2):
        chart(draw, column, len(PAIRS)*520)
    out = REVIEWS / "Spear_UniformBarrel_Comparison.png"
    board.save(out)
    print(out)


if __name__ == "__main__":
    main()
