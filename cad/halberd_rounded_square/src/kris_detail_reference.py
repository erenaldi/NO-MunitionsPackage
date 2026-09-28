"""Read-only crop of the user-selected Kris CAD, aligned for panel review."""
from pathlib import Path
from cadgen import build123d as bd, read_step, step

SOURCE=Path(__file__).resolve().parents[2]/"IRM-S4_Kris_PL10_Hybrid.step"


@step(out="../STEP/kris_detail_reference.step")
def kris_detail_reference():
    model=read_step(SOURCE)
    clip=bd.Box(500.,500.,170.).translate((0,0,2245.))
    parts=[]
    for p in model.children:
        bb=p.bounding_box()
        if bb.max.Z<=2160. or bb.min.Z>=2330.:
            continue
        cropped=p & clip
        if not cropped or cropped.volume<=0:
            continue
        cropped=cropped.rotate(bd.Axis.Y,-90.).translate((2245.,0,0))
        cropped.label=p.label
        cropped.color=p.color
        parts.append(cropped)
    return bd.Compound(children=parts,label="Kris_Hybrid_Service_Panel_Reference")


if __name__=="__main__":
    kris_detail_reference()
