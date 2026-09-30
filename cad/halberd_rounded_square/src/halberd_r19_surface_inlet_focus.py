"""Review-only crop of the saved R19 full body: inlet mouths X=500..760.

Holds all four inlet mouths with the even R19 side walls. Reads the saved
STEP only; no geometry is authored here.
"""
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

from halberd_r19_surface import HARDWARE_GROUP, MAIN_HOST, RAISED_GROUP, _materials

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "halberd_r19_surface.step"
CROP_X = (500.0, 760.0)


def _materials_crop():
    materials = _materials()
    materials["assignments"] = [a for a in materials["assignments"]
                                if a["targets"] in ([f"#{HARDWARE_GROUP}"],
                                                    [f"#{RAISED_GROUP}"])]
    return materials


@step(out="../STEP/halberd_r19_surface_inlet_focus.step", materials=_materials_crop())
def halberd_r19_surface_inlet_focus():
    scene = read_scene(SAVED)
    leaves = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in scene.leaves()}
    clip = bd.Box(CROP_X[1] - CROP_X[0], 400.0, 400.0).translate(
        ((CROP_X[0] + CROP_X[1]) / 2.0, 0.0, 0.0))
    body = leaves[MAIN_HOST] & clip
    body.label = f"{MAIN_HOST}_r19_crop_inlet"
    body.color = leaves[MAIN_HOST].color

    def inside(part):
        box = part.bounding_box()
        return CROP_X[0] <= box.min.X and box.max.X <= CROP_X[1]

    hardware = [p for label, p in leaves.items() if label.startswith(("main_r19_",))
                and "_fastener_" in label and inside(p)]
    raised = [p for label, p in leaves.items() if label.startswith("main_r19_")
              and label.endswith(("_raised", "_plate", "_boss")) and inside(p)]
    # R18 hatches in the crop (e.g. F03A) so their pockets do not read as holes.
    others = [p for label, p in leaves.items() if label.startswith("main_r18_") and inside(p)]
    return bd.Compound(children=[body, *others,
                                 bd.Compound(children=hardware, label=HARDWARE_GROUP),
                                 bd.Compound(children=raised, label=RAISED_GROUP)],
                       label="Halberd_R19_Surface_Inlet_Focus")


if __name__ == "__main__":
    halberd_r19_surface_inlet_focus()
