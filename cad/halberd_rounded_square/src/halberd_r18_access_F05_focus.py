"""Saved exact crop: lower F05 center strip, two terminals and two heads."""
from cadgen import step

from halberd_r18_access import halberd_r18_access
from halberd_r18_access_build import (
    crop_access_variant,
    materials_for_labels,
    metadata_crop_labels,
)


MATERIALS = materials_for_labels(metadata_crop_labels("F05"))


@step(out="../STEP/halberd_r18_access_F05_focus.step", materials=MATERIALS)
def halberd_r18_access_F05_focus():
    return crop_access_variant(halberd_r18_access(), "F05")[0]


if __name__ == "__main__":
    halberd_r18_access_F05_focus()
