"""Saved exact crop: paired forward F04A door and F03A circular cap."""
from cadgen import step

from halberd_r18_access import halberd_r18_access
from halberd_r18_access_build import (
    crop_access_variant,
    materials_for_labels,
    metadata_crop_labels,
)


MATERIALS = materials_for_labels(metadata_crop_labels("forward_F04A_F03A"))


@step(out="../STEP/halberd_r18_access_forward_F04A_F03A.step", materials=MATERIALS)
def halberd_r18_access_forward_F04A_F03A():
    return crop_access_variant(halberd_r18_access(), "forward_F04A_F03A")[0]


if __name__ == "__main__":
    halberd_r18_access_forward_F04A_F03A()
