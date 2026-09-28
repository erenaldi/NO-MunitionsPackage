"""Review-only true transverse section of the generated intake, not a new design."""
from cadgen import build123d as bd, step
from intake_r3_shapes import revised_body
from study_shapes import tag

@step(out="../STEP/Selected_Intake_R3_Section.step")
def intake_r3_section():
    slab=bd.Box(16.,400.,400.).translate((560.,0,0))
    return tag(revised_body() & slab,"R3_actual_intake_section")

if __name__=="__main__":
    intake_r3_section()
