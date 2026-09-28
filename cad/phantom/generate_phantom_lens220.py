"""Build the RDM-9 Phantom 220 mm lens-width silhouette candidate."""

from cadgen import report, step

from phantom_geometry import make_phantom


@step(out="RDM-9_Phantom_Lens220.step")
def phantom_lens220():
    report("RDM-9 Phantom with 220 mm mid-body lens housing")
    return make_phantom(220.0)


if __name__ == "__main__":
    phantom_lens220()
