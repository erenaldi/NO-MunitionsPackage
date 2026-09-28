"""R6: exact Bezier late-taper planform, retaining R5 inlet and side profile."""
from cadgen import build123d as bd
from study_shapes import body, tag, rotate, SEAM, SEPARATION
from intake_r3_shapes import outer_profile, passage, CLOCK, CORNER_RADIUS, MOUTH_FOOT_X, ENTRY_SWEEP
from intake_r4_shapes import extended_passage
from intake_r5_shapes import build_r5, TAPER_START, FRONT_END


def endpoint_points(x,width,roof_half,roof):
    # Reuse the exact front/end profile construction, including its buried foot.
    from intake_r3_shapes import core_height
    half=width/2
    foot=core_height(half)-.4
    return [(x,-half,78.),(x,half,78.),(x,half,foot),
            (x,roof_half,roof),(x,-roof_half,roof),(x,-half,foot)]


def curved_rear(end_x=SEAM,end_lean=0.):
    start=endpoint_points(TAPER_START,88.,16.,147.5)
    end=endpoint_points(end_x,8.,1.6,136.)
    # Optional terminal-plane lean in X per radial mm, referenced at the roof.
    # Zero retains the original plane normal to X for every historical caller.
    end=[(x+end_lean*(z-136.),y,z) for x,y,z in end]
    rails=[]
    for i,(a,b) in enumerate(zip(start,end)):
        poles=[]
        for k in range(4):
            x=a[0]+(b[0]-a[0])*k/3
            # Three equal initial Y poles give width = start + delta*u^3.
            y=a[1] if k<3 else b[1]
            if i in (3,4):
                z=a[2]+(b[2]-a[2])*k/3 # side-view roof unchanged
            else:
                z=a[2] if k<3 else b[2]
            poles.append((x,y,z))
        rails.append(poles)
    faces=[]
    for i in range(6):
        j=(i+1)%6
        faces.append(bd.Face.make_bezier_surface([[rails[i][k],rails[j][k]] for k in range(4)]))
    faces.append(bd.Face(bd.Wire.make_polygon(start,close=True)))
    faces.append(bd.Face(bd.Wire.make_polygon(list(reversed(end)),close=True)))
    shape=bd.Solid(bd.Shell(faces))
    if not shape.is_valid or shape.volume<=0:
        raise ValueError("Bezier rear housing is not a valid positive solid")
    return shape


def curved_outer(end_x=SEAM,end_lean=0.):
    front=bd.loft([outer_profile(TAPER_START,88.,16.,147.5),
                   outer_profile(FRONT_END,88.,16.,145.)],ruled=True)
    shape=curved_rear(end_x,end_lean)+front
    def front_x(radial):
        return MOUTH_FOOT_X-ENTRY_SWEEP*(radial-CORNER_RADIUS)
    cutter=bd.Face(bd.Wire.make_polygon([
        (front_x(75.),-120.,75.),(850.,-120.,75.),
        (850.,-120.,200.),(front_x(200.),-120.,200.)],close=True))
    return shape-bd.extrude(cutter,amount=240.,dir=(0,1,0))


def build_r6(separated=False):
    baseline=build_r5()
    previous={p.label:p for p in baseline.children}
    # Read the already approved cap's exact front plane from source geometry;
    # this retains the clear channel length rather than recomputing it from R6.
    back=max(v.X for v in previous["main_intake_dark_floor"].vertices())
    main=(body()+rotate(curved_outer(),CLOCK))-rotate(passage(),CLOCK)-rotate(extended_passage(back),CLOCK)
    parts=[tag(main,"main_body_intake_r6")]
    parts.extend(p for label,p in previous.items() if label!="main_body_intake_r5")
    placed=[p.moved(bd.Location((-SEPARATION,0,0))) if separated and p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=placed,label="Halberd_R6_Late_Curved_Taper"+("_Separated" if separated else ""))
