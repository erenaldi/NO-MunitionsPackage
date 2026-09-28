"""Build the HKP-1 Palisade interceptor silhouette candidate (Gate 2)."""

from cadgen import report, step

from palisade_geometry import make_palisade_interceptor


@step(out="HKP-1_Palisade_Interceptor.step")
def palisade_interceptor():
    report("HKP-1 Palisade interceptor silhouette")
    return make_palisade_interceptor()


if __name__ == "__main__":
    palisade_interceptor()