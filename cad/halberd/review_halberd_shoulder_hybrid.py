"""Current-master review documents and cameras for the selected hybrid."""
import json
from pathlib import Path
from cadgen import step, read_step, build123d as bd

ROOT=Path(__file__).resolve().parent


def review(mode):
    model=read_step(ROOT/"Halberd_Shoulder_Hybrid.step")
    children=[]
    ranges={"Intakes":(300,1130),"Seam":(-460,-190),"Nose":(620,1683.5),"Toe":(680,1000)}
    for part in model.children:
        booster=part.label.startswith("booster_")
        if mode=="Separated":
            children.append(part.moved(bd.Location((-350,0,0))) if booster else part)
        elif mode=="Upper" and not booster or mode=="Booster" and booster:
            children.append(part)
        elif mode in ranges:
            a,b=ranges[mode]
            shape=part & bd.Box(b-a,700,700).translate(((a+b)/2,0,0))
            if shape is not None and shape.volume>1e-6:
                shape.label,shape.color=part.label,part.color
                children.append(shape)
    return bd.Compound(children=children,label=f"Halberd_Hybrid_{mode}")


@step(out="Halberd_Shoulder_Hybrid_Separated.step")
def separated(): return review("Separated")
@step(out="Halberd_Shoulder_Hybrid_Upper.step")
def upper(): return review("Upper")
@step(out="Halberd_Shoulder_Hybrid_Booster.step")
def booster(): return review("Booster")
@step(out="Halberd_Shoulder_Hybrid_Intakes.step")
def intakes(): return review("Intakes")
@step(out="Halberd_Shoulder_Hybrid_Seam.step")
def seam(): return review("Seam")
@step(out="Halberd_Shoulder_Hybrid_Nose.step")
def nose(): return review("Nose")
@step(out="Halberd_Shoulder_Hybrid_Toe.step")
def toe(): return review("Toe")


@step(out="Halberd_Shoulder_Hybrid_InternalPath.step")
def internal_path():
    """Display-only longitudinal cut through the actual first intake, not a proxy path."""
    model=read_step(ROOT/"Halberd_Shoulder_Hybrid.step")
    cutter=bd.Box(665,12,170).translate((647.5,6,85))
    children=[]
    for part in model.children:
        if part.label not in ("sustainer_body","intake_floor_1"):
            continue
        clipped=part.rotate(bd.Axis.X,45) & cutter
        if clipped is not None and clipped.volume>1e-6:
            clipped.label,clipped.color=part.label,part.color
            children.append(clipped)
    return bd.Compound(children=children,label="Hybrid_intake_actual_longitudinal_cut")


def jobs():
    packet=[]
    for suffix,mode,views in (
        ("","rendered",{"iso":[-1,-1,.7],"opposite":[1,1,-.7],"side":[0,-1,0],"top":[0,0,1],
                         "nose":[1,0,0],"tail":[-1,0,0]}),
        ("","solid",{"nose_edges":[1,0,0]}),
        ("_Separated","rendered",{"separated":[-1,-1,.7],"separated_front":[1,1,.5]}),
        ("_Intakes","rendered",{"intakes":[1,-1,.7],"intakes_opposite":[1,1,-.7],
                               "intake_grazing":[.15,-1,.12],"intake_mouths":[1,0,0],
                               "intake_roofs":[0,0,1]}),
        ("_Nose","rendered",{"nose_transition":[1,-1,.5],"nose_side":[0,-1,0]}),
        ("_Seam","solid",{"seam":[-1,-1,.6],"seam_side":[0,-1,0]}),
        ("_Upper","rendered",{"upper_aft":[-1,-.5,.4]}),
        ("_Booster","rendered",{"booster":[-1,-1,.6],"booster_front":[1,-1,.6]}),
        ("_InternalPath","solid",{"internal_path":[0,-1,0],"internal_path_iso":[.2,-1,.25]}),
        ("_Toe","rendered",{"toe_blend":[1,-1,.6],"toe_grazing":[.15,-1,.12],"toe_reference":[1,1,.6]}),
        ("_Toe","solid",{"toe_edges":[1,-1,.6],"toe_reference_edges":[1,1,.6]}),
    ):
        packet.append({"input":f"Halberd_Shoulder_Hybrid{suffix}.step","mode":"view","theme":"snapshot",
                       "display":{"mode":mode},"outputs":[
                           {"path":f"Halberd_Hybrid_{view}.png","camera":{"direction":direction}}
                           for view,direction in views.items()],
                       "render":{"sizeProfile":"diagnostic","padding":.1,"viewLabels":False}})
    (ROOT/"halberd_shoulder_hybrid_snapshot_job.json").write_text(json.dumps(packet,indent=2)+"\n")


if __name__=="__main__":
    for model in (separated,upper,booster,intakes,seam,nose,internal_path,toe): model()
    jobs()
