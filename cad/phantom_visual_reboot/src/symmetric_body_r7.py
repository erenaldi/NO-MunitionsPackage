"""R7: use the cleaner starboard half for identical lower shoulder transitions."""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from transition_nose_r6 import body as prior_body


def body():
    right = prior_body() & bd.Box(3000,200,400).translate((0,100,0))
    return tag((right+right.mirror(bd.Plane.XZ)).clean(),
               'RDM9_R7_symmetric_body_20mm_wedge_R4')


@step(out='../STEP/J_Symmetric_Body_R7.step')
def model():
    return body()


@step(out='../STEP/J_Symmetric_Body_R7_Close.step')
def close():
    return tag(body() & bd.Box(850,400,400).translate((975,0,0)),
               'R7_symmetric_nose_shoulders_cut_at_X550')


if __name__ == '__main__':
    model()
    close()
