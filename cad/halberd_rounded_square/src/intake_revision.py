from cadgen import step
from intake_revision_shapes import build_revision

@step(out="../STEP/Selected_Intake_Prototype.step")
def intake_revision():
    return build_revision()

if __name__ == "__main__":
    intake_revision()
