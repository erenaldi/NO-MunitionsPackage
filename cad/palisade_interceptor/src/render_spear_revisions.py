"""Matched local Spear boattail and one-fin review packet."""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reviews"
CAMERA = {"direction": [-1, -1, .8]}
STUDIES = ("Trim", "Rake", "Broad")


def snapshot(stem, views):
    job = {"input": f"STEP/{stem}.step", "mode": "view", "theme": "snapshot",
           "display": {"mode": "rendered"},
           "outputs": [{"path": f"reviews/{stem}_{label}.png", "camera": CAMERA}
                       for label in views],
           "render": {"sizeProfile": "diagnostic", "padding": .1,
                      "viewLabels": False}}
    job_path = REVIEWS / f"{stem}_packet_job.json"
    job_path.write_text(json.dumps(job, indent=2)+"\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "cadgen.cli", "step", "snapshot",
                    "--job", str(job_path)], cwd=ROOT, check=True)


def tight(path):
    with Image.open(path) as src:
        image = src.convert("RGB")
    color = image.getpixel((0, 0))
    diff = ImageChops.difference(image, Image.new("RGB", image.size, color)).convert("L")
    bounds = diff.point(lambda value: 255 if value > 25 else 0).getbbox()
    assert bounds, path
    return image.crop(bounds)


def render():
    snapshot("A_Spear", ("revision_iso",))
    snapshot("A_Spear_Separated", ("revision_separated",))
    snapshot("Spear_Original_Fin_Focus", ("fin_focus",))
    snapshot("Spear_Original_Cap_Focus", ("cap_focus",))
    for name in STUDIES:
        snapshot(f"Spear_{name}_Boattail", ("revision_iso",))
        snapshot(f"Spear_{name}_Boattail_Separated", ("revision_separated",))
        snapshot(f"Spear_{name}_Fin_Focus", ("fin_focus",))
    snapshot("Spear_Boattail_Cap_Focus", ("cap_focus",))


def board():
    old = {
        "iso": REVIEWS / "A_Spear_revision_iso.png",
        "separated": REVIEWS / "A_Spear_Separated_revision_separated.png",
        "fin": REVIEWS / "Spear_Original_Fin_Focus_fin_focus.png",
        "cap": REVIEWS / "Spear_Original_Cap_Focus_cap_focus.png",
    }
    columns = [("Selected A (original)", old)]
    for name in STUDIES:
        columns.append((f"{name} (one fin + boattail)", {
            "iso": REVIEWS / f"Spear_{name}_Boattail_revision_iso.png",
            "separated": REVIEWS / f"Spear_{name}_Boattail_Separated_revision_separated.png",
            "fin": REVIEWS / f"Spear_{name}_Fin_Focus_fin_focus.png",
            "cap": REVIEWS / "Spear_Boattail_Cap_Focus_cap_focus.png",
        }))
    canvas = Image.new("RGB", (4*800, 4*465), "white")
    draw = ImageDraw.Draw(canvas)
    for col, (title, views) in enumerate(columns):
        for row, key in enumerate(("iso", "fin", "cap", "separated")):
            image = tight(views[key])
            if key == "fin":
                # Nose points right: crop and enlarge the common aft station.
                image = image.crop((0, int(image.height*.22),
                                    int(image.width*.44), int(image.height*.82)))
            tile = ImageOps.contain(image, (765, 405), Image.Resampling.LANCZOS)
            x, y = col*800+(800-tile.width)//2, row*465+(415-tile.height)//2
            canvas.paste(tile, (x, y))
            draw.text((col*800+17, row*465+430), f"{title} | {key}", fill="#131B20")
    target = REVIEWS / "Spear_Fin_Boattail_Comparison.png"
    canvas.save(target)
    print(target)


if __name__ == "__main__":
    render()
    board()
