"""Build the RDM-9 Phantom round-2 candidate B: raised-rail slivers."""

from cadgen import report, step

from phantom_r2_lib import make_r2


@step(out="RDM-9_Phantom_R2_Rails.step")
def phantom_r2_rails():
    report("candidate B: heavier mid-body slivers and tail surfaces")
    return make_r2("rails")


if __name__ == "__main__":
    phantom_r2_rails()
