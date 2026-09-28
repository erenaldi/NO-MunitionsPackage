"""Sketch-versus-saved-A7 comparison; requires the user's Downloads screenshot."""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
USER_SKETCH = Path(r"C:\Users\erena\Downloads\Screenshot 2026-09-27 220011.png")
ROWS = (
    (("User's red A4 side markup", USER_SKETCH),
     ("A7 / level center and softened ends", ROOT / "A7_Filled_side.png")),
    (("A6 / early roof slope, ruled ends", ROOT / "A6_Filled_shaded_iso.png"),
     ("A7 / level roof, bounded eased ends", ROOT / "A7_Filled_iso.png")),
    (("A7 / bare frame", ROOT / "A7_Bare_iso.png"),
     ("A7 / four box placeholders", ROOT / "A7_Filled_iso.png")),
)


def main():
    if "--continuous" in sys.argv:
        rows = (
            (("User's marked continuous side envelope", USER_SKETCH),
             ("A9 / smooth ends, no aperture proxies", ROOT / "A9_Filled_side.png")),
            (("A8 / visible end-face cues", ROOT / "A8_Filled_iso.png"),
             ("A9 / continuous rounded end forms", ROOT / "A9_Filled_iso.png")),
            (("A9 / bare inverted-U housing", ROOT / "A9_Bare_iso.png"),
             ("A9 / four plain box volumes", ROOT / "A9_Filled_iso.png")),
        )
        title = "Palisade A9 — continuous end curves against the user's drawing"
        output = "A9_ContinuousEnds_Review.png"
    elif "--drooped" in sys.argv:
        rows = (
            (("User's marked continuous side envelope", USER_SKETCH),
             ("A10 / drooped front, stubbier rear", ROOT / "A10_Filled_side.png")),
            (("A9 / level continuous ends", ROOT / "A9_Filled_iso.png"),
             ("A10 / drooped front tip", ROOT / "A10_Filled_iso.png")),
            (("A10 / bare inverted-U housing", ROOT / "A10_Bare_iso.png"),
             ("A10 / four plain box volumes", ROOT / "A10_Filled_iso.png")),
        )
        title = "Palisade A10 — drooped front and stubbier rear against the user's drawing"
        output = "A10_DroopedEnds_Review.png"
    elif "--rounded" in sys.argv:
        rows = (
            (("A7 / side with larger end faces", ROOT / "A7_Filled_side.png"),
             ("A8 / smaller rounded tips", ROOT / "A8_Filled_side.png")),
            (("A7 / original end treatment", ROOT / "A7_Filled_iso.png"),
             ("A8 / rounded-tip treatment", ROOT / "A8_Filled_iso.png")),
            (("A8 / bare U-frame", ROOT / "A8_Bare_iso.png"),
             ("A8 / four box placeholders", ROOT / "A8_Filled_iso.png")),
            (("A8 / forward sensor cue", ROOT / "A8_Filled_front_edges.png"),
             ("A8 / aft sensor cue", ROOT / "A8_Filled_rear_edges.png")),
        )
        title = "Palisade A8 — rounded tips against A7 at matched cameras"
        output = "A8_RoundedTips_Review.png"
    else:
        rows = ROWS
        title = "Palisade A7 — annotated side and revised bare/filled housing"
        output = "A7_LevelBeam_Review.png"
    w, h = 1200, 800
    board = Image.new("RGB", (2*w, 54+len(rows)*(h+45)), "#edf1f6")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("arial.ttf", 29)
    draw.text((22, 12), title,
              fill="#223546", font=font)
    for row, pair in enumerate(rows):
        for col, (label, path) in enumerate(pair):
            view = Image.open(path).convert("RGB")
            view.thumbnail((w, h), Image.Resampling.LANCZOS)
            x, y = col*w, 54+row*(h+45)
            board.paste(view, (x+(w-view.width)//2, y+(h-view.height)//2))
            draw.text((x+24, y+h+8), label, fill="#223546", font=font)
    board.save(ROOT / output)


if __name__ == "__main__":
    main()
