"""Review-only crop of the saved R19 full body: mid-section X=-160..440.

Holds both raised F05 strips, the mid vent grille and boss. Reads the saved
STEP only; no geometry is authored here.
"""
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

from halberd_r19_surface import HARDWARE_GROUP, MAIN_HOST, RAISED_GROUP, _materials

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "halberd_r19_surface.step"
CROP_X = (-160.0, 440.0)


def _materials_crop():
    materials = _materials()
    materials["assignments"] = [a for a in materials["assignments"]
                                if a["targets"] in ([f"#{HARDWARE_GROUP}"],
                                                    [f"#{RAISED_GROUP}"])]
    return materials


@step(out="../STEP/halberd_r19_surface_mid_focus.step", materials=_materials_crop())
def halberd_r19_surface_mid_focus():
    scene = read_scene(SAVED)
    leaves = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in scene.leaves()}
    clip = bd.Box(CROP_X[1] - CROP_X[0], 400.0, 400.0).translate(
        ((CROP_X[0] + CROP_X[1]) / 2.0, 0.0, 0.0))
    body = leaves[MAIN_HOST] & clip
    body.label = f"{MAIN_HOST}_r19_crop_mid"
    body.color = leaves[MAIN_HOST].color

    def inside(part):
        box = part.bounding_box()
        return CROP_X[0] <= box.min.X and box.max.X <= CROP_X[1]

    hardware = [p for label, p in leaves.items() if label.startswith(("main_r19_",))
                and "_fastener_" in label and inside(p)]
    raised = [p for label, p in leaves.items() if label.startswith("main_r19_")
              and label.endswith(("_raised", "_plate", "_boss")) and inside(p)]
    return bd.Compound(children=[body,
                                 bd.Compound(children=hardware, label=HARDWARE_GROUP),
                                 bd.Compound(children=raised, label=RAISED_GROUP)],
                       label="Halberd_R19_Surface_Mid_Focus")


if __name__ == "__main__":
    halberd_r19_surface_mid_focus()
