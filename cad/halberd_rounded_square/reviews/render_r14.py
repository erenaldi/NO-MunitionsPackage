"""R14 matched before/after review of the booster fin/fairing cleanup."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def render():
    views = {
        "before_oblique": ("halberd_r13_booster_focus", [.3, -1, .6], None, 1800, 850),
        "after_oblique": ("halberd_r14_focus", [.3, -1, .6], None, 1800, 850),
        "before_side": ("halberd_r13_booster_focus", [0, -1, 0], None, 1800, 800),
        "after_side": ("halberd_r14_focus", [0, -1, 0], None, 1800, 800),
        "before_top": ("halberd_r13_booster_focus", [0, 0, 1], [0, 1, 0], 1800, 650),
        "after_top": ("halberd_r14_focus", [0, 0, 1], [0, 1, 0], 1800, 650),
        "after_opposite_oblique": ("halberd_r14_focus", [-.3, 1, .6], None, 1800, 850),
        "whole": ("halberd_r14", [.35, 1, .65], None, 2200, 850),
        "separated": ("halberd_r14_separated", [.3, 1, .65], None, 2200, 850),
    }
    jobs = []
    for name, (stem, direction, up, w, h) in views.items():
        camera = {"projection": "orthographic", "direction": direction}
        if up:
            camera["up"] = up
        jobs.append(dict(input=str(ROOT / "STEP" / (stem + ".step")), mode="view",
                         display={"mode": "shaded_edges"}, output={"padding": .08, "viewLabels": False},
                         outputs=[dict(path=str(ROOT / "reviews" / f"R14_{name}.png"),
                                       camera=camera, width=w, height=h)]))
    job = ROOT / "reviews" / "halberd_R14_snapshot.json"
    job.write_text(json.dumps(jobs, indent=2) + "\n")
    subprocess.run([sys.executable, "-m", "cadgen.cli", "step", "snapshot", "--job", str(job)], check=True)
    board = Image.new("RGB", (3600, 2500), "#edf2f7")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    draw.text((20, 15), "HALBERD R14 / BOOSTER FIN-FAIRING TOPOLOGY CLEANUP (BEFORE vs AFTER)",
              font=font, fill="#24394a")
    y = 65
    for name in ("oblique", "side", "top"):
        draw.text((20, y), f"{name.upper()}  BEFORE | AFTER", font=font, fill="#24394a")
        before = Image.open(ROOT / "reviews" / f"R14_before_{name}.png").convert("RGB")
        after = Image.open(ROOT / "reviews" / f"R14_after_{name}.png").convert("RGB")
        board.paste(before, (0, y + 35))
        board.paste(after, (1800, y + 35))
        y += before.height + 45
    board.save(ROOT / "reviews" / "Halberd_R14_Booster_Junction.png")
    print(ROOT / "reviews" / "Halberd_R14_Booster_Junction.png")


if __name__ == "__main__":
    render()