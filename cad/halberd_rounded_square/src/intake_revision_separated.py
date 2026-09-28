from cadgen import step
from intake_revision_shapes import build_revision

@step(out="../STEP/Selected_Intake_Prototype_Separated.step")
def intake_revision_separated():
    return build_revision(separated=True)

if __name__ == "__main__":
    intake_revision_separated()
