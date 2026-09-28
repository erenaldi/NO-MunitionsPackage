"""One-station taller fin and intake-to-fin transition, exterior CAD only."""
from cadgen import build123d as bd
from study_shapes import fin, tag, rotate, SEAM, SEPARATION
from intake_r6_shapes import endpoint_points
from halberd_r8_shapes import build_r8, MATERIALS

ROOT_AFT=-1485.
ROOT_FORWARD=-1190.
MIDPOINT=(ROOT_AFT+ROOT_FORWARD)/2
ROOT_RADIUS=108.
HEIGHT=80.
TIP_CHORD=220.
CLOCK=45.


def transition_local():
    # Exact existing intake end at the stage joint. The other end is buried
    # inside the fin at its mid-chord, so the union has no exposed end cap.
    start=endpoint_points(SEAM,8.,1.6,136.)
    end=[(MIDPOINT,-1.,108.),(MIDPOINT,1.,108.),
         (MIDPOINT,1.,113.),(MIDPOINT,.6,136.),
         (MIDPOINT,-.6,136.),(MIDPOINT,-1.,113.)]
    rails=[]
    for a,b in zip(start,end):
        rails.append([(a[0]+(b[0]-a[0])*k/3,
                       a[1]+(b[1]-a[1])*ease,
                       a[2]+(b[2]-a[2])*ease)
                      for k,ease in enumerate((0.,.65,1.,1.))])
    faces=[bd.Face.make_bezier_surface([[rails[i][k],rails[(i+1)%6][k]]
                                       for k in range(4)]) for i in range(6)]
    faces.extend([bd.Face(bd.Wire.make_polygon(start,close=True)),
                  bd.Face(bd.Wire.make_polygon(list(reversed(end)),close=True))])
    result=bd.Solid(bd.Shell(faces))
    if not result.is_valid or result.volume<=0:
        raise ValueError("Invalid intake-to-fin transition")
    return result


def taller_fin():
    return fin((ROOT_AFT,ROOT_FORWARD,MIDPOINT-TIP_CHORD/2,
                MIDPOINT+TIP_CHORD/2,ROOT_RADIUS+HEIGHT),
               ROOT_RADIUS,CLOCK,"booster_fin_1")


def build_r9(separated=False):
    previous=build_r8()
    revised=tag(taller_fin()+rotate(transition_local(),CLOCK),
                "booster_fin_1","#929DA5")
    if len(revised.solids())!=1 or not revised.is_valid:
        raise ValueError("Fin and fairing must form one valid solid")
    parts=[revised if p.label=="booster_fin_1" else p for p in previous.children]
    if separated:
        parts=[p.moved(bd.Location((-SEPARATION,0,0)))
               if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts,label="Halberd_R9_One_Transition"+
                       ("_Separated" if separated else ""))


def focus(model):
    # Cropped context is review-only. Unclock the selected station to +Z.
    clip=bd.Box(640.,450.,450.).translate((-1240.,0,0))
    parts=[]
    for p in model.children:
        if p.label not in ("main_body_four_intakes_r8","booster_body","booster_fin_1"):
            continue
        shape=(p.rotate(bd.Axis.X,CLOCK) & clip)
        shape.label=p.label
        shape.color=p.color
        parts.append(shape)
    return bd.Compound(children=parts,label="Halberd_R9_Transition_Focus")
