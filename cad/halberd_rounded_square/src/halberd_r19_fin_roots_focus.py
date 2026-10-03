"""Review-only crops of the saved R19 full body around the fin roots.

Main fins: X=-1130..-840. Booster fins: X=-1500..-1180. Reads the saved STEP
only (from the main copy, whose bytes match the sidecar hash); no geometry is
authored here. Every leaf is kept whole when it lies inside the crop, dropped
when disjoint, and intersected with the crop box when it straddles an edge.
"""
import os
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

ROOT = Path(__file__).resolve().parents[1]
SAVED = Path(os.environ.get(
    "R19_SAVED_STEP",
    r"C:\Users\erena\Desktop\Nuclear Option Munitions Package\cad\halberd_rounded_square\STEP\halberd_r19_surface.step"))
MAIN_X = (-1130.0, -840.0)
BOOSTER_X = (-1500.0, -1180.0)


def _crop(x0, x1, label):
    scene = read_scene(SAVED)
    clip = bd.Box(x1 - x0, 400.0, 400.0).translate(((x0 + x1) / 2.0, 0.0, 0.0))
    kept = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        box = shape.bounding_box()
        if box.max.X < x0 or box.min.X > x1:
            continue
        if x0 <= box.min.X and box.max.X <= x1:
            part = shape
        else:
            part = shape & clip
            if part is None or part.volume < 1e-6:
                continue
            part.label = f"{leaf.label}_crop"
            part.color = shape.color
        kept.append(part)
    return bd.Compound(children=kept, label=label)


@step(out="../STEP/halberd_r19_fin_roots_main_focus.step")
def halberd_r19_fin_roots_main_focus():
    return _crop(*MAIN_X, "Halberd_R19_FinRoots_Main_Focus")


@step(out="../STEP/halberd_r19_fin_roots_booster_focus.step")
def halberd_r19_fin_roots_booster_focus():
    return _crop(*BOOSTER_X, "Halberd_R19_FinRoots_Booster_Focus")


if __name__ == "__main__":
    halberd_r19_fin_roots_main_focus()
    halberd_r19_fin_roots_booster_focus()
