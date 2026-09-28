"""Produce deterministic CAD snapshots and a scale-matched selection board."""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reviews"
BASE = ROOT.parent
STUDIES = (("A_Spear", 1200), ("B_Shoulder", 1120), ("C_Facet", 1280))
CAMERAS = {
    "iso": {"direction": [-1, -1, .7]},
    "opposed": {"direction": [1, 1, -.7]},
    "side": {"direction": [0, -1, 0]},
    "top": {"direction": [0, 0, 1]},
    "nose": {"direction": [1, 0, 0]},
    "tail": {"direction": [-1, 0, 0]},
}


def render():
    for stem, _ in STUDIES:
        for state in ("", "_Separated"):
            input_path = f"STEP/{stem}{state}.step"
            cameras = (CAMERAS if not state else
                       {"separated": CAMERAS["iso"], "separated_opposed": CAMERAS["opposed"]})
            job = {"input": input_path, "mode": "view", "theme": "snapshot",
                   "display": {"mode": "rendered"},
                   "outputs": [{"path": f"reviews/{stem}_{name}.png", "camera": camera}
                               for name, camera in cameras.items()],
                   "render": {"sizeProfile": "diagnostic", "padding": .1,
                              "viewLabels": False}}
            job_path = REVIEWS / f"{stem}{state}_snapshot_job.json"
            job_path.write_text(json.dumps(job, indent=2)+"\n", encoding="utf-8")
            subprocess.run([sys.executable, "-m", "cadgen.cli", "step", "snapshot",
                            "--job", str(job_path)], cwd=ROOT, check=True)


def crop_geometry(path):
    with Image.open(path) as image:
        img = image.convert("RGB")
    bg = img.getpixel((0, 0))
    from PIL import ImageChops
    mask = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L")
    box = mask.point(lambda x: 255 if x > 28 else 0).getbbox()
    assert box, f"empty snapshot: {path}"
    return img.crop(box)


def board():
    baseline = {
        "iso": BASE / "Palisade_iso.png", "side": BASE / "Palisade_side.png",
        "tail": BASE / "Palisade_tail.png", "separated": BASE / "Palisade_separated.png",
    }
    columns = [("Baseline / prior", 1200, baseline)] + [
        (stem.replace("_", " / "), length,
         {view: REVIEWS / f"{stem}_{view}.png" for view in baseline})
        for stem, length in STUDIES
    ]
    board_image = Image.new("RGB", (4*800, 4*510), "white")
    draw = ImageDraw.Draw(board_image)
    scale = {"iso": 680/1280, "side": 680/1280,
             "tail": 245/165, "separated": 680/1550}
    for c, (title, length, views) in enumerate(columns):
        for r, view in enumerate(("iso", "side", "tail", "separated")):
            tile = crop_geometry(views[view])
            # Per-view common physical scale: each candidate occupies pixels
            # proportional to its real length; end views use a common diameter.
            dimension = (length if view != "tail" else (164 if c == 0 else
                         (124 if c == 1 else (146 if c == 2 else 132))))
            desired = int(dimension*scale[view])
            if view == "tail":
                factor = desired/max(tile.size)
            else:
                factor = desired/max(tile.size)
            size = (max(1, round(tile.width*factor)), max(1, round(tile.height*factor)))
            tile = tile.resize(size, Image.Resampling.LANCZOS)
            tile = ImageOps.contain(tile, (750, 440))
            x, y = c*800+(800-tile.width)//2, r*510+(455-tile.height)//2
            board_image.paste(tile, (x, y))
            draw.text((c*800+18, r*510+470), f"{title} | {view} | L {length} mm", fill="#101820")
    dest = REVIEWS / "Palisade_Selection_Board.png"
    board_image.save(dest)
    print(dest)


if __name__ == "__main__":
    render()
    board()
