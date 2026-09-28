"""Generate the AGM-110 Ballista RC1 with wings swept to their deployed datums."""

from cadgen import step

from ballista_geometry import make_ballista


@step(out="AGM-110_Ballista_Deployed.step")
def ballista_deployed():
    return make_ballista(deployed=True)


if __name__ == "__main__":
    ballista_deployed()
