"""Palisade C: octagonal faceted fuselage, swept aft fins, tapered cap."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/C_Facet.step")
def c_facet():
    return make_study("C")

if __name__ == "__main__":
    c_facet()
