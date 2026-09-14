"""Close-review model for the AAM-44 Halberd dorsal mounting hardware."""

from cadgen import build123d as bd
from cadgen import step

from generate_halberd_detailed import (
    BODY_COLOR,
    BODY_RADIUS,
    cylinder_x,
    make_mounting_hardware,
    style,
)


@step(out="AAM-44_Halberd_Mount_Review.step")
def halberd_mount_review():
    body = style(cylinder_x(-360.0, 860.0, BODY_RADIUS), "review_body", BODY_COLOR)
    return bd.Compound(
        children=[body, *make_mounting_hardware()],
        label="AAM-44_Halberd_Mount_Review",
    )


if __name__ == "__main__":
    halberd_mount_review()
