"""R6: finished 20 mm horizontal wedge, radius 4 mm; center (1400,0,40)."""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from transition_nose_r4 import body as shoulder_body
from transition_nose_r5 import nose


def body():
    retained = shoulder_body() & bd.Box(2410,400,400).translate((-195,0,0))
    return tag((retained+nose(width=20, radius=4)).clean(),
               'RDM9_R6_20mm_wedge_4mm_radius')


@step(out='../STEP/I_Transition_Nose_R6.step')
def model():
    return body()


@step(out='../STEP/I_Transition_Nose_R6_Close.step')
def close():
    return tag(body() & bd.Box(850,400,400).translate((975,0,0)),
               'R6_nose_transition_closeup_cut_at_X550')


@step(out='../STEP/I_Transition_Nose_R6_Tip.step')
def tip():
    return tag(body() & bd.Box(40,100,100).translate((1380,0,40)),
               'R6_tip_closeup_cut_at_X1360')


if __name__ == '__main__':
    model()
    close()
    tip()
