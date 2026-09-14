"""Close-review model for the AAM-44 Halberd booster nozzle."""

from cadgen import build123d as bd
from cadgen import step

from generate_halberd_detailed import (
    BODY_COLOR,
    BODY_RADIUS,
    BOOSTER_COLOR,
    BOOSTER_NOZZLE_START_X,
    cylinder_x,
    make_booster_nozzle,
    style,
)


@step(out="AAM-44_Halberd_Nozzle_Review.step")
def halberd_nozzle_review():
    body = style(
        cylinder_x(BOOSTER_NOZZLE_START_X, -1430.0, BODY_RADIUS),
        "review_booster_body",
        BOOSTER_COLOR,
    )
    return bd.Compound(
        children=[body, *make_booster_nozzle()],
        label="AAM-44_Halberd_Nozzle_Review",
    )


if __name__ == "__main__":
    halberd_nozzle_review()
