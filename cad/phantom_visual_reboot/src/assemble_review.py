"""Pair the actual STEP snapshots in matched-camera concept review boards."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reviews"
CAPTIONS = {
    "A": "A / Facet — moderate shoulder; straight tapered wings",
    "B": "B / Shoulder — wide shallow body; short broad nose; long wings",
    "C": "C / Keel — deeper waisted body; kinked diamondback wings",
}


def board(view):
    pane_w, pane_h = 920, 690
    canvas = Image.new("RGB", (pane_w*2, 3*(pane_h+60)+70), "#e9eef1")
    pen = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("arial.ttf", 22)
    small = ImageFont.truetype("arial.ttf", 16)
    pen.text((22, 14), "RDM-9: CLEAN-SHEET PAIRED SILHOUETTES — " + view.upper(),
             font=font, fill="#263238")
    pen.text((22, 46), "All designs are concept-stage; sources are TALD (nose), Kh-69 (body/tail), GBU-39 (folding wings).",
             font=small, fill="#475b65")
    for row, key in enumerate(("A", "B", "C")):
        for col, state in enumerate(("deployed", "stowed")):
            image = Image.open(REVIEWS / ("%s_%s_%s.png" % (key, state, view))).convert("RGB")
            image.thumbnail((pane_w-20, pane_h-20), Image.Resampling.LANCZOS)
            x = col*pane_w + (pane_w-image.width)//2
            y = 70 + row*(pane_h+60) + 46 + (pane_h-image.height)//2
            canvas.paste(image, (x, y))
            pen.text((col*pane_w+15, 70 + row*(pane_h+60)+8),
                     CAPTIONS[key] + " / " + state, font=small, fill="#263238")
    dest = REVIEWS / ("RDM9_ABC_%s.png" % view)
    canvas.save(dest)
    print(dest)


def true_scale_labels(pose):
    src = REVIEWS / ("R5_ABC_%s_true_scale.png" % pose)
    image = Image.open(src).convert("RGB")
    pen = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 36)
    # CAD top camera reverses display X: A | R5 above, C | B below.
    for x, y, label in ((350, 58, "A / Facet"), (1520, 58, "R5 / baseline"),
                        (350, 700, "C / Keel"), (1520, 700, "B / Shoulder")):
        pen.text((x, y), label, font=font, fill="#21343f")
    dest = REVIEWS / ("R5_ABC_%s_labeled.png" % pose)
    image.save(dest)
    print(dest)


if __name__ == "__main__":
    for camera in ("top", "side"):
        board(camera)
    # ISO snapshots use the same camera preset and dimensions. The later CAD
    # selection gate must also inspect the opposite/end views individually.
    board("iso")
    for state in ("deployed", "stowed"):
        true_scale_labels(state)
