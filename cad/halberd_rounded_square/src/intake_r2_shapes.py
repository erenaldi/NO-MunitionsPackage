"""R2 one-intake reference study: covered entry -> broad duct -> aft strake.

Exterior visual geometry only. Intake at 45 degrees; selected nose and A fins
remain source-identical. The removable cover is a reference-presentation part,
not a proposed runtime mechanism.
"""
import math
from cadgen import build123d as bd
from study_shapes import body, ogive, booster, fin, tag, STUDIES, ANGLES, SEPARATION, rotate

CLOCK=45.
OFFSET=math.sqrt(2)*30.+70.-100.
MOUTH=630.
# x, shoulder width, height above local corner, crest half-width fraction.
# A wide forward duct develops into a higher, narrow aft strake rather than
# fading into a thin strip. The root runs under the selected main-stage fin.
STATIONS=(
    (-1102.,12.,1.,.12),
    (-1000.,48.,23.,.10),
    (-805.,76.,48.,.075),
    (-550.,90.,48.,.10),
    (-180.,105.,45.,.22),
    (180.,110.,42.,.32),
    (470.,110.,40.,.36),
    (590.,108.,38.,.36),
    (690.,104.,38.,.36),
)


def profile(x,width,height,crest):
    return bd.Face(bd.Wire.make_polygon([
        (x,-width/2,78.),(x,width/2,78.),(x,width/2,84.),
        (x,width*crest,100.+height),(x,-width*crest,100.+height),
        (x,-width/2,84.),
    ],close=True))


def passage_profile(x,width,low,high):
    # Sloped sidewalls keep the cutter safely below the sculpted outer shoulder.
    return bd.Face(bd.Wire.make_polygon([
        (x,-width/2,low),(x,width/2,low),
        (x,width*.32,high),(x,-width*.32,high),
    ],close=True))


def place(shape):
    return rotate(shape.translate((0,0,OFFSET)),CLOCK)


def fairing():
    result=bd.loft([profile(*station) for station in STATIONS],ruled=False)
    # A backward-sloped entry face, following the reference's covered-mouth cue.
    wedge=bd.Face(bd.Wire.make_polygon([
        (647.5,-100.,75.),(850.,-100.,75.),(850.,-100.,190.),(567.,-100.,190.)],close=True))
    result=result-bd.extrude(wedge,amount=200.,dir=(0,1,0))
    # Respect the actual selected fin's leading edge rather than burying it.
    # A 2 mm axial seat keeps contact but leaves its exposed shape legible.
    _,root_front,_,tip_front,tip_radius=STUDIES["A"]["main"]
    root_radius=110.
    def edge_x(z):
        return root_front+(z+OFFSET-root_radius)*(tip_front-root_front)/(tip_radius-root_radius)-2.
    aft_cut=bd.Face(bd.Wire.make_polygon([
        (-1500.,-100.,60.),(edge_x(60.),-100.,60.),
        (edge_x(210.),-100.,210.),(-1500.,-100.,210.)],close=True))
    return result-bd.extrude(aft_cut,amount=200.,dir=(0,1,0))


def selected_body():
    shape=body()+place(fairing())
    duct=bd.loft([
        passage_profile(680.,64.,103.,128.),
        passage_profile(530.,64.,100.5,128.),
        passage_profile(360.,58.,94.,120.),
        passage_profile(300.,52.,93.,115.),
    ],ruled=True)
    return tag(shape-place(duct),"main_body_intake_r2")


def reference_cover():
    # Covers the same canted aperture with a thin perimeter overlap. Neutral
    # shading keeps the review about shape rather than the source image's red.
    yz=[(-36.,99.5),(36.,99.5),(26.,131.),(-26.,131.)]
    wire=bd.Wire.make_polygon([(MOUTH-.7*(z-100)-.8,y,z) for y,z in yz],close=True)
    plate=bd.extrude(bd.Face(wire),amount=3.2,dir=(1,0,0))
    # Remove the portion buried in the unmodified core; the perimeter still
    # seats in the added inlet rim, without an edge artifact on the nose side.
    return tag(place(plate)-body(),"intake_reference_cover","#7E8A93")


def build_r2(separated=False,covered=False):
    p=STUDIES["A"]
    parts=[selected_body(),tag(ogive(),"main_ogive","#C3C9CE")]
    for i,angle in enumerate(ANGLES,1):
        parts.append(fin(p["main"],110.,angle+45.,f"main_fin_{i}"))
    aft=[tag(booster(),"booster_body","#A7B0B7")]
    for i,angle in enumerate(ANGLES,1):
        aft.append(fin(p["boost"],108.,angle+45.,f"booster_fin_{i}"))
    for part in aft:
        parts.append(part.moved(bd.Location((-SEPARATION,0,0))) if separated else part)
    if covered:
        parts.append(reference_cover())
    return bd.Compound(children=parts,label="Halberd_Intake_R2"+("_Covered" if covered else "_Separated" if separated else "_Open"))
