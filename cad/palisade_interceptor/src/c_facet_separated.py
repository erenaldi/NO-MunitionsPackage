"""Review-only detached turning cap for C; identical component geometry."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/C_Facet_Separated.step")
def c_facet_separated():
    return make_study("C", separated=True)

if __name__ == "__main__":
    c_facet_separated()
