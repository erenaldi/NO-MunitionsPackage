"""Master-derived close reviews and matched cameras for the five B variants."""
import json
from pathlib import Path
from cadgen import step, read_step, build123d as bd
from halberd_shoulder_variants import VARIANTS

ROOT=Path(__file__).resolve().parent


def crop(key, mode):
    cfg=VARIANTS[key]
    if mode=="Seam":
        center, length = -cfg["length"]*.1, 240
    else:
        center = cfg["inlet_x"]-cfg["inlet_length"]/2
        length = cfg["inlet_length"]+100
    box=bd.Box(length,700,700).translate((center,0,0))
    master=read_step(ROOT/f"Halberd_{key}.step")
    parts=[]
    for part in master.children:
        clipped=part & box
        if clipped is not None and clipped.volume>1e-6:
            clipped.label,clipped.color=part.label,part.color
            parts.append(clipped)
    return bd.Compound(children=parts,label=f"{key}_{mode}")


@step(out="Halberd_B1_Needle_Seam.step")
def b1_seam(): return crop("B1_Needle","Seam")
@step(out="Halberd_B2_Broadhead_Seam.step")
def b2_seam(): return crop("B2_Broadhead","Seam")
@step(out="Halberd_B3_Chisel_Seam.step")
def b3_seam(): return crop("B3_Chisel","Seam")
@step(out="Halberd_B4_Manta_Seam.step")
def b4_seam(): return crop("B4_Manta","Seam")
@step(out="Halberd_B5_Sculpted_Seam.step")
def b5_seam(): return crop("B5_Sculpted","Seam")
@step(out="Halberd_B1_Needle_Intakes.step")
def b1_intakes(): return crop("B1_Needle","Intakes")
@step(out="Halberd_B2_Broadhead_Intakes.step")
def b2_intakes(): return crop("B2_Broadhead","Intakes")
@step(out="Halberd_B3_Chisel_Intakes.step")
def b3_intakes(): return crop("B3_Chisel","Intakes")
@step(out="Halberd_B4_Manta_Intakes.step")
def b4_intakes(): return crop("B4_Manta","Intakes")
@step(out="Halberd_B5_Sculpted_Intakes.step")
def b5_intakes(): return crop("B5_Sculpted","Intakes")


def jobs():
    packet=[]
    for key in VARIANTS:
        for suffix, display, views in (
            ("","rendered",{"iso":[-1,-1,.7],"opposite":[1,1,-.7],"side":[0,-1,0],
                            "top":[0,0,1],"nose":[1,0,0],"tail":[-1,0,0]}),
            ("_Separated","rendered",{"separated":[-1,-1,.7],"separated_front":[1,1,.5]}),
            ("_Seam","solid",{"seam":[-1,-1,.6],"seam_side":[0,-1,0]}),
            ("_Intakes","rendered",{"intakes":[1,-1,.7],"grazing":[.15,-1,.12]}),
        ):
            packet.append({"input":f"Halberd_{key}{suffix}.step","mode":"view","theme":"snapshot",
                           "display":{"mode":display},"outputs":[
                               {"path":f"Halberd_{key}_{view}.png","camera":{"direction":direction}}
                               for view,direction in views.items()],
                           "render":{"sizeProfile":"diagnostic","padding":.1,"viewLabels":False}})
    (ROOT/"halberd_shoulder_variants_snapshot_job.json").write_text(json.dumps(packet,indent=2)+"\n")


if __name__=="__main__":
    for model in (b1_seam,b2_seam,b3_seam,b4_seam,b5_seam,b1_intakes,b2_intakes,b3_intakes,b4_intakes,b5_intakes):
        model()
    jobs()
