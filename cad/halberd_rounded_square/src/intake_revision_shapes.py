"""One corner-mounted, reference-led exterior intake study; no propagation."""
import math
from cadgen import build123d as bd
from study_shapes import (body, ogive, booster, fin, tag, STUDIES, ANGLES,
                          SEPARATION, rotate)

MOUTH=630.0
INTAKE_CLOCK=45.0
CORNER_OFFSET=math.sqrt(2)*30.+70.-100.
# Forward to aft: mouth narrower than the sculpted long shoulder behind it.
STATIONS=(
    (-1000., 10., .5), (-880., 39., 7.), (-680., 70., 22.),
    (-360., 86., 32.), (60., 82., 33.), (390., 67., 30.), (690., 56., 25.),
)


def arch(x,width,height):
    """Buried feet, swept shoulders and a broad crest; no constant-section rail."""
    return bd.Face(bd.Wire.make_polygon([
        (x,-width/2,80.), (x,width/2,80.), (x,width/2,84.),
        (x,width*.38,100.+height), (x,-width*.38,100.+height),
        (x,-width/2,84.),
    ],close=True))


def opening(x,width,low,high):
    return bd.Face(bd.Wire.make_polygon([(x,-width/2,low),(x,width/2,low),
                                       (x,width*.23,high),(x,-width*.23,high)],close=True))


def revised_body():
    fairing=bd.loft([arch(*s) for s in STATIONS],ruled=False)
    # Clip the fairing's front on a swept plane: x=630-.7*(z-100).
    wedge=bd.Face(bd.Wire.make_polygon([
        (644.,-100.,80.),(850.,-100.,80.),(850.,-100.,180.),(574.,-100.,180.)],close=True))
    fairing=fairing-bd.extrude(wedge,amount=200.,dir=(0,1,0))
    fairing=rotate(fairing.translate((0,0,CORNER_OFFSET)),INTAKE_CLOCK)
    merged=body()+fairing
    passage=bd.loft([opening(680.,38.,101.,118.),
                     opening(500.,40.,99.,118.),
                     opening(340.,34.,94.,114.)],ruled=True)
    passage=rotate(passage.translate((0,0,CORNER_OFFSET)),INTAKE_CLOCK)
    return tag(merged-passage,"main_body_intake_prototype")


def build_revision(separated=False):
    p=STUDIES["A"]
    parts=[revised_body(),tag(ogive(),"main_ogive","#C3C9CE")]
    for i,angle in enumerate(ANGLES,1):
        parts.append(fin(p["main"],110.,angle+45.,f"main_fin_{i}"))
    aft=[tag(booster(),"booster_body","#A7B0B7")]
    for i,angle in enumerate(ANGLES,1):
        aft.append(fin(p["boost"],108.,angle+45.,f"booster_fin_{i}"))
    for part in aft:
        parts.append(part.moved(bd.Location((-SEPARATION,0,0))) if separated else part)
    return bd.Compound(children=parts,label="Halberd_Selected_One_Intake"+("_Separated" if separated else ""))
