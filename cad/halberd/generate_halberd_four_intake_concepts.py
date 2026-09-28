"""Build the four locked-envelope Halberd concept masters."""
from cadgen import step

from halberd_four_intake_concepts import build_concept


@step(out="Halberd_C1_Razorback.step")
def razorback():
    return build_concept("Razorback")


@step(out="Halberd_C2_Manta.step")
def manta():
    return build_concept("Manta")


@step(out="Halberd_C3_Citadel.step")
def citadel():
    return build_concept("Citadel")


@step(out="Halberd_C4_Petal.step")
def petal():
    return build_concept("Petal")


if __name__ == "__main__":
    razorback()
    manta()
    citadel()
    petal()
