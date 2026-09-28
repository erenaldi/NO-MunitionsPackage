"""Palisade B: shortened shouldered body, small forward control planes."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/B_Shoulder.step")
def b_shoulder():
    return make_study("B")

if __name__ == "__main__":
    b_shoulder()
