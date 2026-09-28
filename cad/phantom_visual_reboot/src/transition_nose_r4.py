"""Clean the two upper shoulder corners using explicit surface correspondence.

R3's generic 8-edge square -> 5-edge nose loft redistributes the upper
corner arcs across the roof edge. Replace only its five upper shoulder
faces: full-width roof, and two arc/short-side profiles tapering to their
own nose corner. Every remaining R3 face is retained.
"""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from transition_nose_r3 import body as previous_body
from transition_nose_r2 import BODY_END, NOSE_ROOT


def body():
    previous = previous_body()
    retained, replaced = [], []
    for face in previous.faces():
        box = face.bounding_box()
        is_upper_shoulder = (
            box.min.X > BODY_END-.001 and box.max.X < NOSE_ROOT+.001
            and min(v.Z for v in face.vertices()) > 50)
        (replaced if is_upper_shoulder else retained).append(face)
    if len(replaced) != 5:
        raise ValueError(f'Expected five upper shoulder faces, got {len(replaced)}')
    lower_z = min(v.Z for f in replaced for v in f.vertices()
                  if abs(v.X-BODY_END) < .001)
    roof = bd.Face(bd.Wire.make_polygon([
        (BODY_END, -76, 86), (BODY_END, 76, 86),
        (NOSE_ROOT, 75, 74), (NOSE_ROOT, -75, 74)], close=True))
    retained.append(roof)
    for side in (-1, 1):
        arc = bd.Edge.make_three_point_arc(
            (BODY_END, side*76, 86),
            (BODY_END, side*(76+10/2**.5), 76+10/2**.5),
            (BODY_END, side*86, 76))
        short_side = bd.Edge.make_line((BODY_END, side*86, 76),
                                       (BODY_END, side*86, lower_z))
        corner = bd.Shell.make_loft([
            bd.Wire([arc, short_side]), bd.Vertex(NOSE_ROOT, side*75, 74)
        ], ruled=True)
        retained.extend(corner.faces())
    # Sewing inherits redundant collinear nose-edge split vertices from R3.
    # Unify them so the full-width roof also has a clean four-edge boundary.
    result = bd.Solid(bd.Shell(retained)).clean()
    if not result.is_valid or result.volume <= 0:
        raise ValueError('Controlled upper shoulder did not form a valid positive solid')
    return tag(result, 'RDM9_R4_clean_upper_shoulder_corners')


@step(out='../STEP/G_Transition_Nose_R4.step')
def model():
    return body()


@step(out='../STEP/G_Transition_Nose_R4_Close.step')
def close():
    return tag(body() & bd.Box(850, 400, 400).translate((975, 0, 0)),
               'R4_nose_transition_closeup_cut_at_X550')


if __name__ == '__main__':
    model()
    close()
