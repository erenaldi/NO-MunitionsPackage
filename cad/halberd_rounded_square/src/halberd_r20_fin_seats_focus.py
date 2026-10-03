"""Review-only crops of the saved R20 model around the main-fin root seats.

Main: X=-1130..-840 (same window as the R19 fin-root review crops). Macro:
one seat pair (main_fin_1, clock 45) in a 44 x 44 x 44 mm box centred on the
fin root at X=-970. Reads the saved R20 STEP only; no geometry is authored.
Every leaf is kept whole when inside the crop, dropped when disjoint, and
intersected with the crop box when it straddles an edge.
"""
import math
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "halberd_r20_fin_seats.step"
MAIN_X = (-1130.0, -840.0)
MACRO_CENTRE = (-970.0, 138.8 * math.sin(math.radians(45.0)),
                138.8 * math.cos(math.radians(45.0)))
MACRO_SIZE = 44.0


def _crop(clip, label):
    scene = read_scene(SAVED)
    cb = clip.bounding_box()
    kept = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        box = shape.bounding_box()
        if (box.max.X < cb.min.X or box.min.X > cb.max.X or box.max.Y < cb.min.Y or
                box.min.Y > cb.max.Y or box.max.Z < cb.min.Z or box.min.Z > cb.max.Z):
            continue
        if (cb.min.X <= box.min.X and box.max.X <= cb.max.X and cb.min.Y <= box.min.Y and
                box.max.Y <= cb.max.Y and cb.min.Z <= box.min.Z and box.max.Z <= cb.max.Z):
            part = shape
        else:
            part = shape & clip
            if part is None or part.volume < 1e-6:
                continue
            part.label = f"{leaf.label}_crop"
            part.color = shape.color
        kept.append(part)
    return bd.Compound(children=kept, label=label)


@step(out="../STEP/halberd_r20_fin_seats_main_focus.step")
def halberd_r20_fin_seats_main_focus():
    x0, x1 = MAIN_X
    clip = bd.Box(x1 - x0, 400.0, 400.0).translate(((x0 + x1) / 2.0, 0.0, 0.0))
    return _crop(clip, "Halberd_R20_FinSeats_Main_Focus")


@step(out="../STEP/halberd_r20_fin_seats_macro_focus.step")
def halberd_r20_fin_seats_macro_focus():
    clip = bd.Box(MACRO_SIZE, MACRO_SIZE, MACRO_SIZE).translate(MACRO_CENTRE)
    return _crop(clip, "Halberd_R20_FinSeats_Macro_Focus")


if __name__ == "__main__":
    halberd_r20_fin_seats_main_focus()
    halberd_r20_fin_seats_macro_focus()
