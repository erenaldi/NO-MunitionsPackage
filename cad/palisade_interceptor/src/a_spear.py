"""Palisade A: slim ogive, tapered skin, broad swept aft fins."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/A_Spear.step")
def a_spear():
    return make_study("A")

if __name__ == "__main__":
    a_spear()
