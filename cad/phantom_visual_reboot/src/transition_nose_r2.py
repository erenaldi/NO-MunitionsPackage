"""Local visual prototype: square body -> shoulder -> projected sketch nose.

Millimetres; +X forward, +Z up. Dimensions other than overall length and
carriage envelope are visual-study assumptions, not engineering specifications.
"""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import square_section, tag

BODY_END = 760.0
NOSE_ROOT = 1010.0
TIP = (1400.0, 0.0, 40.0)


def nose_wire():
    return bd.Wire.make_polygon([
        (NOSE_ROOT, -75, 74), (NOSE_ROOT, 75, 74),
        (NOSE_ROOT, 47, -57), (NOSE_ROOT, 0, -83),
        (NOSE_ROOT, -47, -57),
    ], close=True)


def body():
    barrel = bd.loft([square_section(-1400, 172, 10),
                      square_section(BODY_END, 172, 10)], ruled=True)
    shoulder = bd.Solid.make_loft([
        square_section(BODY_END, 172, 10).faces()[0].outer_wire(),
        nose_wire()], ruled=True)
    nose = bd.Solid.make_loft([nose_wire(), bd.Vertex(*TIP)], ruled=True)
    return tag(barrel + shoulder + nose, 'RDM9_R2_square_transition_nose')


@step(out='../STEP/E_Transition_Nose_R2.step')
def model():
    return body()


@step(out='../STEP/E_Transition_Nose_R2_Close.step')
def close():
    return tag(body() & bd.Box(850, 400, 400).translate((975, 0, 0)),
               'nose_and_transition_closeup_cut_at_X550')


if __name__ == '__main__':
    model()
    close()
