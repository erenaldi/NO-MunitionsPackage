"""Saved exact crop: main shoulder F02 and its five access components."""
from cadgen import step

from halberd_r18_access import halberd_r18_access
from halberd_r18_access_build import (
    crop_access_variant,
    materials_for_labels,
    metadata_crop_labels,
)


MATERIALS = materials_for_labels(metadata_crop_labels("F02"))


@step(out="../STEP/halberd_r18_access_F02_focus.step", materials=MATERIALS)
def halberd_r18_access_F02_focus():
    return crop_access_variant(halberd_r18_access(), "F02")[0]


if __name__ == "__main__":
    halberd_r18_access_F02_focus()
