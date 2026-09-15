"""Build the compact ADM-160-inspired RDM-9 Phantom silhouette candidate."""

from cadgen import report, step

from phantom_mald_geometry import make_phantom_mald_hybrid


@step(out="RDM-9_Phantom_MALD_Hybrid.step")
def phantom_mald_hybrid():
    report("compact ADM-160-inspired Phantom silhouette")
    return make_phantom_mald_hybrid()


if __name__ == "__main__":
    phantom_mald_hybrid()
