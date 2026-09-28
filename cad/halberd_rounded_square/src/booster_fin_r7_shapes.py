"""R7 one-fin prototype from the user's low trapezoid outline; mm, X forward."""
from cadgen import build123d as bd
from intake_r6_shapes import build_r6
from study_shapes import fin, SEPARATION

ROOT_AFT=-1655.
ROOT_FORWARD=-1360.
ROOT_RADIUS=108.
HEIGHT=53.
TIP_CHORD=220.
MIDPOINT=(ROOT_AFT+ROOT_FORWARD)/2
PROTOTYPE_LABEL="booster_fin_r7_prototype"


def trapezoid_fin():
    return fin((ROOT_AFT,ROOT_FORWARD,MIDPOINT-TIP_CHORD/2,
                MIDPOINT+TIP_CHORD/2,ROOT_RADIUS+HEIGHT),
               ROOT_RADIUS,45.,PROTOTYPE_LABEL)


def build_r7(separated=False):
    previous=build_r6()
    parts=[]
    for p in previous.children:
        shape=trapezoid_fin() if p.label=="booster_fin_1" else p
        if separated and shape.label.startswith("booster"):
            shape=shape.moved(bd.Location((-SEPARATION,0,0)))
        parts.append(shape)
    return bd.Compound(children=parts,label="Halberd_R7_One_Trapezoid_Booster_Fin"+("_Separated" if separated else ""))
