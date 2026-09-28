"""Generate the AGM-110 Ballista RC1 with both wings physically stowed."""

from cadgen import step

from ballista_geometry import make_ballista


@step(out="AGM-110_Ballista_Stowed.step")
def ballista_stowed():
    return make_ballista(deployed=False)


if __name__ == "__main__":
    ballista_stowed()
