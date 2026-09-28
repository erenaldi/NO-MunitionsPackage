"""R15 four-face service-cover review packet (run after checks, serially)."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def render():
    views = {
        "whole": ("halberd_r15", [.35, 1, .65], None, 2200, 850),
        "opposite": ("halberd_r15", [-.35, -1, .65], None, 2200, 850),
        "separated": ("halberd_r15_separated", [.3, 1, .65], None, 2200, 850),
        "focus_oblique": ("halberd_r15_focus", [.3, -1, .6], None, 1800, 850),
        "focus_oblique_opposed": ("halberd_r15_focus", [-.3, 1, .6], None, 1800, 850),
        "focus_top": ("halberd_r15_focus", [0, 0, 1], [0, 1, 0], 1600, 1100),
        "focus_side": ("halberd_r15_focus", [0, 1, 0], [0, 0, 1], 1600, 1100),
        "focus_bottom": ("halberd_r15_focus", [0, 0, -1], [0, 1, 0], 1600, 1100),
        "focus_side_opposite": ("halberd_r15_focus", [0, -1, 0], [0, 0, 1], 1600, 1100),
        "focus_axial": ("halberd_r15_focus", [-1, 0, 0], [0, 1, 0], 1400, 1400),
    }
    jobs = []
    for name, (stem, direction, up, w, h) in views.items():
        camera = {"projection": "orthographic", "direction": direction}
        if up:
            camera["up"] = up
        jobs.append(dict(input=str(ROOT / "STEP" / (stem + ".step")), mode="view",
                         display={"mode": "shaded_edges"}, output={"padding": .08, "viewLabels": False},
                         outputs=[dict(path=str(ROOT / "reviews" / f"R15_{name}.png"),
                                       camera=camera, width=w, height=h)]))
    job = ROOT / "reviews" / "halberd_R15_snapshot.json"
    job.write_text(json.dumps(jobs, indent=2) + "\n")
    subprocess.run([sys.executable, "-m", "cadgen.cli", "step", "snapshot", "--job", str(job)], check=True)
    board = Image.new("RGB", (3600, 2500), "#edf2f7")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    draw.text((20, 15), "HALBERD R15 / FOUR-FACE SERVICE-COVER FAMILY (0/90/180/270)",
              font=font, fill="#24394a")
    y = 70
    draw.text((20, y), "CARDINAL FACES  +Z cover_1 | +Y cover_2 | -Z cover_3 | -Y cover_4",
              font=small, fill="#24394a")
    y += 30
    for name in ("focus_top", "focus_side", "focus_bottom", "focus_side_opposite"):
        image = Image.open(ROOT / "reviews" / f"R15_{name}.png").convert("RGB")
        image.thumbnail((850, 585))
        board.paste(image, (20 + 850 * ("focus_top", "focus_side", "focus_bottom", "focus_side_opposite").index(name), y))
    y += 620
    draw.text((20, y), "FOCUS OBLIQUES + AXIAL CROSS-SECTION", font=small, fill="#24394a")
    y += 30
    for name in ("focus_oblique", "focus_oblique_opposed", "focus_axial"):
        image = Image.open(ROOT / "reviews" / f"R15_{name}.png").convert("RGB")
        image.thumbnail((1100, 520))
        board.paste(image, (20 + 1100 * ("focus_oblique", "focus_oblique_opposed", "focus_axial").index(name), y))
    y += 560
    draw.text((20, y), "FULL STATES  assembled | opposite | separated", font=small, fill="#24394a")
    y += 30
    for name in ("whole", "opposite", "separated"):
        image = Image.open(ROOT / "reviews" / f"R15_{name}.png").convert("RGB")
        image.thumbnail((1100, 425))
        board.paste(image, (20 + 1100 * ("whole", "opposite", "separated").index(name), y))
    board.save(ROOT / "reviews" / "Halberd_R15_Four_Face_Covers.png")
    print(ROOT / "reviews" / "Halberd_R15_Four_Face_Covers.png")


if __name__ == "__main__":
    render()