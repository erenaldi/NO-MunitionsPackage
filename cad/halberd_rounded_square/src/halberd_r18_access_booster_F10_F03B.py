"""Saved exact crop: booster F10 hatch and F03B keyed, slotted cap."""
from cadgen import step

from halberd_r18_access import halberd_r18_access
from halberd_r18_access_build import (
    crop_access_variant,
    materials_for_labels,
    metadata_crop_labels,
)


MATERIALS = materials_for_labels(metadata_crop_labels("booster_F10_F03B"))


@step(out="../STEP/halberd_r18_access_booster_F10_F03B.step", materials=MATERIALS)
def halberd_r18_access_booster_F10_F03B():
    return crop_access_variant(halberd_r18_access(), "booster_F10_F03B")[0]


if __name__ == "__main__":
    halberd_r18_access_booster_F10_F03B()
