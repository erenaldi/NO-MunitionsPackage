"""Review-only detached turning cap for B; identical component geometry."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/B_Shoulder_Separated.step")
def b_shoulder_separated():
    return make_study("B", separated=True)

if __name__ == "__main__":
    b_shoulder_separated()
