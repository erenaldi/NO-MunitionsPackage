"""Close-review model for one AAM-44 Halberd booster-fin module."""

from cadgen import build123d as bd
from cadgen import step

from generate_halberd_detailed import (
    BODY_RADIUS,
    BOOSTER_COLOR,
    cylinder_x,
    make_booster_fin,
    style,
)


@step(out="AAM-44_Halberd_BoosterFin_Review.step")
def halberd_booster_fin_review():
    body = style(
        cylinder_x(-1560.0, -500.0, BODY_RADIUS),
        "review_booster_body",
        BOOSTER_COLOR,
    )
    return bd.Compound(
        children=[body, *make_booster_fin(1, 0.0)],
        label="AAM-44_Halberd_BoosterFin_Review",
    )


if __name__ == "__main__":
    halberd_booster_fin_review()
