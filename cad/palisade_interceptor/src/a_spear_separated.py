"""Review-only detached turning cap for A; identical component geometry."""
from cadgen import step
from concept_shapes import make_study

@step(out="../STEP/A_Spear_Separated.step")
def a_spear_separated():
    return make_study("A", separated=True)

if __name__ == "__main__":
    a_spear_separated()
