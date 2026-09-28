"""R5: horizontal 10 mm wedge, 1 mm leading-edge radius.

Place the rounded leading edge at X=1400, Z=40. The underlying sharp
construction extends past it so the fillet does not shorten the vehicle.
"""
import math
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from transition_nose_r4 import body as previous_body

TIP_WIDTH = 10.0
TIP_RADIUS = 1.0
LEADING_X = 1400.0
CENTER_Z = 40.0
ROOT_X = 1010.0


def nose(width=TIP_WIDTH, radius=TIP_RADIUS):
    # Tangents from the retained roof/keel root to the selected radius circle.
    run = LEADING_X-radius-ROOT_X
    top_slope, bottom_slope = -34/run, 90/run
    for _ in range(20):
        top_slope = (CENTER_Z+radius*math.hypot(1, top_slope)-74)/run
        bottom_slope = (CENTER_Z-radius*math.hypot(1, bottom_slope)+50)/run
    sharp_x = ROOT_X+124/(bottom_slope-top_slope)
    sharp_z = 74+top_slope*(sharp_x-ROOT_X)
    a,b,c,d,e = [(ROOT_X,y,z) for y,z in
                 [(-75,74),(75,74),(47,-36),(0,-50),(-47,-36)]]
    # Set the side planes through the FINISHED edge endpoints, not through
    # nominal 10 mm sharp stock (the latter would widen after rounding).
    side_dy_dz = 28/110
    root_y_at_center = 47+side_dy_dz*(CENTER_Z+36)
    side_dy_dx = (width/2-root_y_at_center)/(LEADING_X-ROOT_X)
    sharp_half_width = 47+side_dy_dz*(sharp_z+36)+side_dy_dx*(sharp_x-ROOT_X)
    left,right = (sharp_x,-sharp_half_width,sharp_z),(sharp_x,sharp_half_width,sharp_z)
    faces = [bd.Face(bd.Wire.make_polygon(points, close=True)) for points in
             [(a,e,d,c,b),(a,b,right,left),(b,c,right),(c,d,right),
              (d,left,right),(d,e,left),(e,a,left)]]
    wedge = bd.Solid(bd.Shell(faces))
    leading = [edge for edge in wedge.edges()
               if all(abs(v.X-sharp_x)<.001 for v in edge.vertices())]
    if len(leading) != 1:
        raise ValueError('Expected one horizontal leading edge')
    return bd.fillet(leading, radius)


def body():
    retained = previous_body() & bd.Box(2410,400,400).translate((-195,0,0))
    return tag((retained+nose()).clean(), 'RDM9_R5_10mm_wedge_1mm_radius')


@step(out='../STEP/H_Transition_Nose_R5.step')
def model():
    return body()


@step(out='../STEP/H_Transition_Nose_R5_Close.step')
def close():
    return tag(body() & bd.Box(850,400,400).translate((975,0,0)),
               'R5_nose_transition_closeup_cut_at_X550')


@step(out='../STEP/H_Transition_Nose_R5_Tip.step')
def tip():
    return tag(body() & bd.Box(40,100,100).translate((1380,0,40)),
               'R5_tip_closeup_cut_at_X1360')


if __name__ == '__main__':
    model()
    close()
    tip()
