"""Saved R17 full-detail review and whole-model reference comparison."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reviews"


def view(name, direction, up=None, size=(2200, 850)):
    camera = {"projection": "orthographic", "direction": direction}
    if up is not None:
        camera["up"] = up
    return dict(path=str(REVIEWS / f"R17_{name}.png"), camera=camera,
                width=size[0], height=size[1])


def job(stem, outputs, fine=False):
    result = dict(input=str(ROOT / "STEP" / f"{stem}.step"), mode="view",
                  display={"mode": "shaded_edges"},
                  output={"padding": .08, "viewLabels": False}, outputs=outputs)
    if fine:
        result["quality"] = {"tessellation": {"chordTolerance": .00005, "angleTolerance": .05}}
    return result


def board(path, entries, columns, cell_size, heading):
    cw, ch = cell_size
    rows = (len(entries) + columns - 1) // columns
    image = Image.new("RGB", (columns * cw, rows * ch + 70), "#edf2f7")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    draw.text((20, 18), heading, font=font, fill="#24394a")
    for i, (filename, caption) in enumerate(entries):
        x, y = (i % columns) * cw, 70 + (i // columns) * ch
        draw.text((x + 20, y + 10), caption, font=font, fill="#24394a")
        tile = Image.open(REVIEWS / filename).convert("RGB")
        tile.thumbnail((cw - 20, ch - 65))
        image.paste(tile, (x + (cw - tile.width) // 2, y + 55))
    image.save(REVIEWS / path)


if __name__ == "__main__":
    macro = (1800, 1200)
    jobs = [
        job("halberd_r17", [
            view("whole", [.35, 1., .65]), view("opposite", [-.35, -1., -.65]),
            view("top", [0, 0, 1], [0, 1, 0]),
            view("bottom", [0, 0, -1], [0, -1, 0]),
            view("side", [0, 1, 0], [0, 0, 1]),
            view("side_opposite", [0, -1, 0], [0, 0, 1]),
            view("front", [1, 0, 0], [0, 0, 1], (1200, 1200)),
            view("aft", [-1, 0, 0], [0, 0, 1], (1200, 1200)),
        ]),
        job("halberd_r17_separated", [view("separated", [.3, 1., .65])]),
        job("halberd_r17_focus", [
            view("body_detail", [.3, -1., .65], size=macro),
            view("body_detail_opposite", [-.3, 1., -.65], size=macro),
        ], True),
        job("halberd_r17_main_fin_focus", [
            view("main_fin_detail", [-.02, -.69, .72], size=macro),
        ], True),
        job("halberd_r17_booster_fin_focus", [
            view("booster_fin_detail", [-.02, -.69, .72], size=macro),
        ], True),
        job("halberd_r17_nozzle_focus", [
            view("nozzles", [-1, 0, 0], [0, 0, 1], macro),
            view("nozzles_oblique", [-.22, .92, .20], size=macro),
        ], True),
        job("kris_full_reference", [view("Kris_whole", [.35, 1., .65])]),
    ]
    manifest = REVIEWS / "R17_snapshot.json"
    manifest.write_text(json.dumps(jobs, indent=2) + "\n")
    subprocess.run([sys.executable, "-m", "cadgen.cli", "step", "snapshot",
                    "--job", str(manifest)], cwd=ROOT, check=True)
    board("Halberd_R17_Kris_Comparison.png", [
        ("R17_Kris_whole.png", "KRIS HYBRID / 222 DETAIL INSTANCES"),
        ("R16_whole.png", "HALBERD R16 / BEFORE / 21 DETAIL INSTANCES"),
        ("R17_whole.png", "HALBERD R17 / AFTER / 223 DETAIL INSTANCES"),
    ], 1, (2400, 620), "WHOLE-MODEL DETAIL DENSITY / FIT-TO-FRAME, NOT EQUAL PHYSICAL SCALE")
    board("Halberd_R17_Detail_Review.png", [
        ("R17_body_detail.png", "RECESSED ACCESS COVERS AND FINE SEAMS"),
        ("R17_body_detail_opposite.png", "OPPOSITE FACES"),
        ("R17_main_fin_detail.png", "MAIN FIN ROOT INTERFACE"),
        ("R17_booster_fin_detail.png", "BOOSTER FIN ROOT INTERFACE"),
        ("R17_nozzles.png", "BOTH NOZZLE RIMS / REVIEW COUPONS"),
        ("R17_nozzles_oblique.png", "RECESSED RIMS AND OPEN FUNNELS"),
    ], 2, (1600, 1100), "HALBERD R17 / LOCAL DETAIL REVIEW")
