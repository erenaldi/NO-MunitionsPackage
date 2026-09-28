"""Drawing-led R3: thin curved-floor inlet, seam-reaching taper, fin on housing.

mm; +X forward, local Y tangent / Z radial before rotation about X.
The user annotations specify silhouettes; numerical profile dimensions below
are explicit editable visual inferences, not physical propulsion design.
"""
import math
from cadgen import build123d as bd
from study_shapes import body, ogive, booster, fin, tag, STUDIES, ANGLES, SEPARATION, SEAM, rotate

CLOCK=45.
CORNER_CENTER=30.*math.sqrt(2)
CORE_RADIUS=70.
CORNER_RADIUS=CORNER_CENTER+CORE_RADIUS
MOUTH_FOOT_X=665.
ENTRY_SWEEP=1.8
WALL=3.

# x, full shoulder width, roof half-width, radial roof height.
# Separate planform taper and side-elevation height avoid the prior pointed
# termination at the fin leading edge.
STATIONS=(
    (SEAM,8.,1.6,136.),
    (-1060.,13.,2.4,138.),
    (-900.,26.,4.4,147.),
    (-760.,38.,6.,153.),
    (-450.,56.,9.,151.5),
    (-50.,74.,12.,149.),
    (350.,86.,16.,146.5),
    (560.,88.,16.,145.),
    (715.,88.,16.,145.),
)


def core_height(tangent,radius=CORE_RADIUS):
    return CORNER_CENTER+math.sqrt(radius*radius-tangent*tangent)


def roof_at(x):
    for a,b in zip(STATIONS,STATIONS[1:]):
        if a[0]<=x<=b[0]:
            t=(x-a[0])/(b[0]-a[0])
            return a[3]+t*(b[3]-a[3])
    raise ValueError(f"No roof station at X={x}")


def outer_profile(x,width,roof_half,roof):
    half=width/2
    foot=core_height(half)-.4
    return bd.Face(bd.Wire.make_polygon([
        (x,-half,78.),(x,half,78.),(x,half,foot),
        (x,roof_half,roof),(x,-roof_half,roof),(x,-half,foot),
    ],close=True))


def inner_profile(x,floor_half,roof_half,roof):
    # Concentric lower edge follows the actual rounded airframe corner.
    radius=CORE_RADIUS+WALL
    floor=core_height(floor_half,radius)
    left=(x,-floor_half,floor)
    right=(x,floor_half,floor)
    upper_left=(x,-roof_half,roof)
    upper_right=(x,roof_half,roof)
    return bd.Face(bd.Wire([
        bd.Edge.make_line(left,upper_left),
        bd.Edge.make_line(upper_left,upper_right),
        bd.Edge.make_line(upper_right,right),
        bd.Edge.make_three_point_arc(right,(x,0,CORNER_CENTER+radius),left),
    ]))


def fairing_outer():
    # Compatible vertex order gives a continuous long fairing. Export checks
    # verify monotonic taper and seam bounds rather than assuming the loft fits.
    shape=bd.loft([outer_profile(*s) for s in STATIONS],ruled=False)
    def front_x(radial):
        return MOUTH_FOOT_X-ENTRY_SWEEP*(radial-CORNER_RADIUS)
    cutter=bd.Face(bd.Wire.make_polygon([
        (front_x(75.),-120.,75.),(850.,-120.,75.),
        (850.,-120.,200.),(front_x(200.),-120.,200.),
    ],close=True))
    return shape-bd.extrude(cutter,amount=240.,dir=(0,1,0))


def passage():
    # Hollow forward housing is visually deep; its floor stays above the core.
    return bd.loft([
        inner_profile(100.,12.,8.,125.),
        inner_profile(210.,35.,12.,143.8),
        inner_profile(350.,36.,13.,143.5),
        inner_profile(560.,38.,13.5,142.),
        inner_profile(735.,38.,13.5,142.),
    ],ruled=True)


def revised_body():
    core=body()
    housing=rotate(fairing_outer(),CLOCK)
    opening=rotate(passage(),CLOCK)
    return tag((core+housing)-opening,"main_body_intake_r3")


def mounted_fin():
    # The red silhouette governs the exposed portion. The buried root is
    # entirely above the original core and seats along the rear housing roof.
    aft=-1075.
    forward=-855.
    root=min(roof_at(aft),roof_at(forward))-2.
    return fin((aft,forward,aft,-945.,212.),root,CLOCK,"main_fin_housing_r3")


def build_r3(separated=False):
    parts=[revised_body(),tag(ogive(),"main_ogive","#C3C9CE"),mounted_fin()]
    # Other stations are retained context only. The new intake + fin assembly
    # is not copied fourfold before the user's local visual gate.
    for i,angle in enumerate(ANGLES[1:],2):
        parts.append(fin(STUDIES["A"]["main"],110.,angle+45.,f"main_fin_{i}"))
    aft=[tag(booster(),"booster_body","#A7B0B7")]
    for i,angle in enumerate(ANGLES,1):
        aft.append(fin(STUDIES["A"]["boost"],108.,angle+45.,f"booster_fin_{i}"))
    for part in aft:
        parts.append(part.moved(bd.Location((-SEPARATION,0,0))) if separated else part)
    return bd.Compound(children=parts,label="Halberd_R3_Drawing_Prototype"+("_Separated" if separated else ""))
