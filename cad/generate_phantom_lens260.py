"""Build the RDM-9 Phantom 260 mm lens-width silhouette candidate."""

from cadgen import report, step

from phantom_geometry import make_phantom


@step(out="RDM-9_Phantom_Lens260.step")
def phantom_lens260():
    report("RDM-9 Phantom with 260 mm mid-body lens housing")
    return make_phantom(260.0)


if __name__ == "__main__":
    phantom_lens260()
