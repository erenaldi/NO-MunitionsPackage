"""Actual longitudinal slice exposing the longer channel and its dark rear cup."""
from cadgen import build123d as bd, step
from intake_r4_shapes import build_r4, dark
from study_shapes import tag

@step(out="../STEP/Selected_Intake_R4_Cutaway.step")
def intake_r4_cutaway():
    model=build_r4()
    slab=bd.Box(1280.,8.,85.).translate((110.,0,122.5))
    pieces=[]
    for part in model.children:
        if part.label not in ("main_body_intake_r4","main_intake_dark_recess"):
            continue
        cut=part.rotate(bd.Axis.X,45.) & slab
        pieces.append(dark(cut,"section_rear_cup") if part.label.endswith("dark_recess") else tag(cut,"section_housing"))
    return bd.Compound(children=pieces,label="R4_actual_longitudinal_slice")

if __name__=="__main__":
    intake_r4_cutaway()
