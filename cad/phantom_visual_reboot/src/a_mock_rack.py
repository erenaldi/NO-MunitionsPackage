"""Visual-only 700 x 80 mm R5-derived mock pad, not actual AGM1 donor rack."""

from cadgen import build123d as bd, step
from study_shapes import build_study, tag


@step(out="../STEP/A_Facet_Stowed_MockPad.step")
def model():
    missile = build_study("A", "stowed")
    pad = tag(bd.Box(700., 80., 20.).translate((0, 0, 88.)),
              "MOCK_700x80_pylon_pad_NOT_DONOR", "#444950")
    return bd.Compound(children=[*missile.children, pad], label="RDM9_A_MOCK_PAD")


if __name__ == "__main__":
    model()
