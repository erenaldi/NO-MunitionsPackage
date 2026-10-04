"""R26 material pass: rusty dark red on the nozzle dark recesses (booster and 2nd stage), on the accepted R24.

Supersedes R25 (which wrongly coloured the outside booster nozzle skirt). Geometry is unchanged: the
outside nozzle skirt keeps its R24 colour; only the two existing recess leaves (dark floors unchanged) are recoloured.
Reads the saved R24 STEP only. Short output name (Windows path limit).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb, step

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent / "shared"))
sys.path.insert(0, str(HERE))

import halberd_r24_booster_seats as r24  # noqa: E402

SAVED = ROOT / "STEP" / "r24_booster_seats.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r26_nozzle_recess.json"
RUST = "#52342C"   # dark rust-maroon (user-picked shade D #5A3A32, slightly darker); brighter tones render vivid red
TARGETS = ("main_nozzle_dark_recess", "booster_nozzle_dark_recess")  # dark floors keep their R24 black


def _rebuild(scene, node):
    if node.children:
        return bd.Compound(children=[_rebuild(scene, c) for c in node.children], label=node.label)
    shape = scene.resolve(node.ref).shape()
    if node.label in TARGETS:
        shape.color = srgb(RUST)
    return shape


def build_r26():
    scene = read_scene(SAVED)
    labels = {r.label for r in scene.leaves()}
    missing = [t for t in TARGETS if t not in labels]
    if missing:
        raise ValueError(("recess leaves missing from R24", missing))
    OUTPUT_METADATA.write_text(json.dumps({"source_step": str(SAVED.relative_to(ROOT)),
                                           "source_document_hash": scene.document_hash,
                                           "color": RUST, "recoloured": list(TARGETS)}, indent=2) + "\n",
                               encoding="utf-8")
    return bd.Compound(children=[_rebuild(scene, n) for n in scene.roots[0].children],
                       label="halberd_r26_nozzle_recess")


def _materials():
    materials = copy.deepcopy(r24.MATERIALS)
    for assignment in materials["assignments"]:
        assignment["targets"] = [t for t in assignment["targets"] if t.lstrip("#") not in TARGETS]
    materials["assignments"] = [a for a in materials["assignments"] if a["targets"]]
    materials["definitions"]["nozzle_rust"] = {"name": "Rusty nozzle recess", "roughness": 0.85, "metalness": 0.1}
    materials["assignments"].append({"targets": [f"#{t}" for t in TARGETS], "material": "nozzle_rust"})
    return materials


@step(out="../STEP/r26_nozzle_recess.step", materials=_materials())
def r26_nozzle_recess():
    return build_r26()


if __name__ == "__main__":
    r26_nozzle_recess()
