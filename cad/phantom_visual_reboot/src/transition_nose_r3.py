"""R3 local underside refinement; mm, +X forward, +Z up.

Raise the shoulder keel 33 mm and lower-side corners 21 mm to reduce
front-view V depth and the side-view belly while retaining the upper nose.
"""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import square_section, tag
from transition_nose_r2 import BODY_END, NOSE_ROOT, TIP


def body():
    root = bd.Wire.make_polygon([
        (NOSE_ROOT, -75, 74), (NOSE_ROOT, 75, 74),
        (NOSE_ROOT, 47, -36), (NOSE_ROOT, 0, -50),
        (NOSE_ROOT, -47, -36),
    ], close=True)
    barrel = bd.loft([square_section(-1400, 172, 10),
                      square_section(BODY_END, 172, 10)], ruled=True)
    shoulder = bd.Solid.make_loft([
        square_section(BODY_END, 172, 10).faces()[0].outer_wire(),
        root], ruled=True)
    nose = bd.Solid.make_loft([root, bd.Vertex(*TIP)], ruled=True)
    return tag(barrel + shoulder + nose, 'RDM9_R3_reduced_nose_belly')


@step(out='../STEP/F_Transition_Nose_R3.step')
def model():
    return body()


@step(out='../STEP/F_Transition_Nose_R3_Close.step')
def close():
    return tag(body() & bd.Box(850, 400, 400).translate((975, 0, 0)),
               'R3_nose_transition_closeup_cut_at_X550')


if __name__ == '__main__':
    model()
    close()
