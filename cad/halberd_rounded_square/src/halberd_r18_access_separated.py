"""R18 access full assembly with booster translated 340 mm aft (-X)."""
from cadgen import step

from halberd_r18_access import ACCESS_LABELS, halberd_r18_access
from halberd_r18_access_build import materials_for_labels, moved_booster_variant


MATERIALS = materials_for_labels(ACCESS_LABELS, include_all_base=True)


@step(out="../STEP/halberd_r18_access_separated.step", materials=MATERIALS)
def halberd_r18_access_separated():
    return moved_booster_variant(halberd_r18_access(), -340.0)


if __name__ == "__main__":
    halberd_r18_access_separated()
