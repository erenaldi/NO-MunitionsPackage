"""Build the RDM-9 Phantom 180 mm lens-width silhouette candidate."""

from cadgen import report, step

from phantom_geometry import make_phantom


@step(out="RDM-9_Phantom_Lens180.step")
def phantom_lens180():
    report("RDM-9 Phantom with 180 mm mid-body lens housing")
    return make_phantom(180.0)


if __name__ == "__main__":
    phantom_lens180()
