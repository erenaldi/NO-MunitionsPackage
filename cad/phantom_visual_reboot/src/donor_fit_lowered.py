"""Asset-frame placement of the B2H baseline for the donor pylon (decision 2026-09-29: lower the whole model by 9.574 mm in the
asset frame; game mount transform untouched).  Rigid translation only: all internal geometry, envelope and checks are unchanged.

`S_EngineBay_B2H_Stowed_Placed.step`  : B2H Stowed with every leaf translated by DZ (design-frame sources are NOT edited).
`reference/agm1_mount/Phantom_DonorFit_Lowered_9574.step` : reference-only view with the recovered donor pylon surface; never shipped.
"""
from pathlib import Path

from cadgen import build123d as bd, read_step, step

ROOT = Path(__file__).resolve().parents[1]
DZ = -9.574


def leaves(node):
    kids = list(getattr(node, "children", ()) or ())
    return [l for k in kids for l in leaves(k)] if kids else [node]


def placed_leaves():
    out = []
    for p in leaves(read_step(str(ROOT / "STEP" / "S_EngineBay_B2H_Stowed_Full.step"))):
        q = p.translate((0.0, 0.0, DZ))
        q.label, q.color = p.label, p.color
        out.append(q)
    return out


@step(out="../STEP/S_EngineBay_B2H_Stowed_Placed.step")
def placed():
    return bd.Compound(children=placed_leaves(), label="S_EngineBay_B2H_Stowed_Placed_dz_-9.574")


@step(out="../reference/agm1_mount/Phantom_DonorFit_Lowered_9574.step")
def fit_view():
    pylon = []
    for p in leaves(read_step(str(ROOT / "reference" / "agm1_mount" / "DonorPylon_Surface.step"))):
        p.label = "REFERENCE_ONLY_" + str(p.label)
        pylon.append(p)
    return bd.Compound(children=placed_leaves() + pylon, label="Phantom_DonorFit_Lowered_9574_REFERENCE_ONLY")


if __name__ == "__main__":
    placed()
    fit_view()
