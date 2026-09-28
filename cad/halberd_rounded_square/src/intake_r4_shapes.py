"""Interior-only R4 derived from the approved R3 silhouette. Dimensions in mm."""
import math
from cadgen import build123d as bd
from study_shapes import body, disk, tag, rotate, SEAM, HALF, SEPARATION
from intake_r3_shapes import build_r3, inner_profile, CORNER_CENTER, CLOCK

EXTENSION_FRACTION=.30
ORIGINAL_CHANNEL_BACK=100.
BACKING_SEAT=2.
INTAKE_LINING_LENGTH=80.


def dark(shape,label,shade="#242B30"):
    shape=tag(shape,label,shade)
    shape.cad_material={"roughness":.90,"metalness":.08}
    return shape


def housing_extension(approved_body):
    visible=approved_body-body()
    length=visible.bounding_box().size.X
    return length,ORIGINAL_CHANNEL_BACK-EXTENSION_FRACTION*length


def extended_passage(back):
    # Cut 2 mm behind the target clear floor to seat the dark backing. The
    # backing's visible inner face, not the raw Boolean cut, owns channel depth.
    return bd.loft([
        inner_profile(back-BACKING_SEAT,12.,8.,125.),
        inner_profile(210.,35.,12.,143.8),
        inner_profile(350.,36.,13.,143.5),
        inner_profile(560.,38.,13.5,142.),
        inner_profile(735.,38.,13.5,142.),
    ],ruled=True)


def lining_profile(x,floor_half,roof_half,roof,floor_radius):
    floor=CORNER_CENTER+math.sqrt(floor_radius**2-floor_half**2)
    left=(x,-floor_half,floor)
    right=(x,floor_half,floor)
    upper_left=(x,-roof_half,roof)
    upper_right=(x,roof_half,roof)
    return bd.Face(bd.Wire([
        bd.Edge.make_line(left,upper_left),bd.Edge.make_line(upper_left,upper_right),
        bd.Edge.make_line(upper_right,right),
        bd.Edge.make_three_point_arc(right,(x,0,CORNER_CENTER+floor_radius),left),
    ]))


def intake_back_cup(back):
    def dims(x):
        t=(x-(back-BACKING_SEAT))/(210.-(back-BACKING_SEAT))
        return (12.+23.*t,8.+4.*t,125.+18.8*t)
    front=back+INTAKE_LINING_LENGTH
    outside=[]
    for x in (back-2.7,back,front):
        f,r,h=dims(x)
        outside.append(lining_profile(x,f+.35,r+.35,h+.35,72.6))
    outer=bd.loft(outside,ruled=True)
    inside=[]
    for x in (back,front+1.):
        f,r,h=dims(x)
        inside.append(lining_profile(x,f-.75,r-.65,h-1.,74.))
    cup=outer-bd.loft(inside,ruled=True)
    return dark(rotate(cup,CLOCK),"main_intake_dark_recess")


def nozzle_liner(entrance,mouth_radius,throat_radius,throat_depth,back_depth,label):
    # Original recess starts one millimeter ahead of the actual opening.
    # Seat outer skin 0.4 mm into the existing cavity wall; expose a charcoal
    # inner funnel 1.0 mm inward. The neutral lip remains 9 mm ahead of it.
    def radius(depth):
        return throat_radius if depth>=throat_depth else mouth_radius+(throat_radius-mouth_radius)*(depth+1)/(throat_depth+1)
    start=9.
    outer=bd.loft([disk(entrance+start,radius(start)+.4),
                   disk(entrance+throat_depth,throat_radius+.4),
                   disk(entrance+back_depth+1,throat_radius+.4)],ruled=True)
    bore=bd.loft([disk(entrance+start-1,radius(start)-1.),
                  disk(entrance+throat_depth,throat_radius-1.),
                  disk(entrance+back_depth-1.4,throat_radius-1.)],ruled=True)
    # Distinguish the charcoal funnel from its darker recessed back face. The
    # visible floor remains exactly 2 mm ahead of the original blind depth.
    floor=bd.loft([disk(entrance+back_depth-2,throat_radius-.7),
                   disk(entrance+back_depth-1,throat_radius-.7)],ruled=True)
    return [dark(outer-bore,label,"#505050"),
            dark(floor,label.replace("_recess","_floor"))]


def build_r4(separated=False):
    approved=build_r3()
    approved_parts={part.label:part for part in approved.children}
    approved_body=approved_parts["main_body_intake_r3"]
    _,back=housing_extension(approved_body)
    # Subtraction from the approved body also preserves every original void.
    extended=tag(approved_body-rotate(extended_passage(back),CLOCK),"main_body_intake_r4")
    parts=[extended]
    parts.extend(part for label,part in approved_parts.items() if label!="main_body_intake_r3")
    parts.append(intake_back_cup(back))
    parts.extend(nozzle_liner(SEAM,65.,37.,36.,42.,"main_nozzle_dark_recess"))
    parts.extend(nozzle_liner(-HALF,69.,33.,64.,72.,"booster_nozzle_dark_recess"))
    placed=[]
    for part in parts:
        placed.append(part.moved(bd.Location((-SEPARATION,0,0))) if separated and part.label.startswith("booster") else part)
    return bd.Compound(children=placed,label="Halberd_R4_Deep_Interiors"+("_Separated" if separated else ""))
