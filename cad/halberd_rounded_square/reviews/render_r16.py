"""R16 focused joint snapshot packet; review evidence only, not an approval."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STEP_DIR = ROOT / "STEP"
REVIEW_DIR = ROOT / "reviews"


def output(path, direction, up=None, width=1800, height=1200):
    camera = {"projection": "orthographic", "direction": direction}
    if up is not None:
        camera["up"] = up
    return {
        "path": str(REVIEW_DIR / path),
        "camera": camera,
        "width": width,
        "height": height,
    }


def job(stem, outputs, width=1800, height=1200):
    return {
        "input": str(STEP_DIR / f"{stem}.step"),
        "mode": "view",
        "display": {"mode": "shaded_edges"},
        "output": {"padding": .08, "viewLabels": False},
        "outputs": outputs,
    }


def preview_jobs():
    return [job("halberd_r16_focus", [output(
        "R16_focus_oblique_preview.png", [.3, -1., .65])])]


def shaded_jobs():
    # Separate finish review from CAD face-boundary overlays near the screws.
    result = job("halberd_r16_focus", [
        output("R16_focus_shaded.png", [.3, -1., .65]),
        output("R16_focus_shaded_grazing.png", [.18, 1., .08], [0., 0., 1.]),
    ])
    result["display"]["mode"] = "shaded"
    result["quality"] = {"tessellation": {"chordTolerance": .00005, "angleTolerance": .05}}
    return [result]


def packet_jobs():
    return [
        job("halberd_r16_focus", [
            output("R16_focus_oblique.png", [.3, -1., .65]),
            output("R16_focus_oblique_opposed.png", [-.3, 1., .65]),
            output("R16_focus_side.png", [0., 1., 0.], [0., 0., 1.]),
            output("R16_focus_grazing.png", [.18, 1., .08], [0., 0., 1.]),
            output("R16_focus_end.png", [1., 0., 0.], [0., 0., 1.], 1500, 1500),
        ]),
        job("halberd_r16", [
            output("R16_whole.png", [.35, 1., .65], width=2200, height=850),
            output("R16_opposite.png", [-.35, -1., .65], width=2200, height=850),
        ]),
        job("halberd_r16_separated", [
            output("R16_separated.png", [.3, 1., .65], width=2200, height=850),
        ]),
        job("kris_joint_reference", [
            output("R16_Kris_joint_oblique.png", [.35, 1., .65]),
            output("R16_Kris_joint_side.png", [0., 1., 0.], [0., 0., 1.]),
        ]),
    ]


def run_snapshot(jobs, manifest):
    manifest.write_text(json.dumps(jobs, indent=2) + "\n")
    subprocess.run([
        sys.executable, "-m", "cadgen.cli", "step", "snapshot", "--job", str(manifest)
    ], cwd=ROOT, check=True)


def make_board():
    names = (
        "R16_focus_oblique.png", "R16_focus_oblique_opposed.png", "R16_focus_side.png",
        "R16_focus_grazing.png", "R16_focus_end.png", "R16_Kris_joint_oblique.png",
        "R16_Kris_joint_side.png", "R16_whole.png", "R16_opposite.png", "R16_separated.png",
    )
    columns, cell_w, cell_h, margin, header = 2, 1740, 610, 30, 86
    rows = (len(names) + columns - 1) // columns
    board = Image.new("RGB", (columns * cell_w + margin, rows * cell_h + header), "#edf2f7")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    draw.text((20, 18), "HALBERD R16 / NOSE-BODY JOINT PROTOTYPE — REVIEW EVIDENCE", font=font,
              fill="#24394a")
    for index, name in enumerate(names):
        col, row = index % columns, index // columns
        x, y = margin // 2 + col * cell_w, header + row * cell_h
        draw.text((x + 6, y + 2), name.removesuffix(".png"), font=small, fill="#24394a")
        image = Image.open(REVIEW_DIR / name).convert("RGB")
        image.thumbnail((cell_w - 18, cell_h - 42))
        board.paste(image, (x + 6, y + 34))
    board.save(REVIEW_DIR / "Halberd_R16_Nose_Body_Joint.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="render one representative view")
    parser.add_argument("--shaded", action="store_true", help="render finish review without CAD edge overlays")
    args = parser.parse_args()
    if args.shaded:
        run_snapshot(shaded_jobs(), REVIEW_DIR / "R16_shaded_snapshot.json")
        return
    if args.preview:
        run_snapshot(preview_jobs(), REVIEW_DIR / "R16_preview_snapshot.json")
        print(REVIEW_DIR / "R16_focus_oblique_preview.png")
        return
    run_snapshot(packet_jobs(), REVIEW_DIR / "R16_snapshot.json")
    make_board()
    print(REVIEW_DIR / "Halberd_R16_Nose_Body_Joint.png")


if __name__ == "__main__":
    main()
