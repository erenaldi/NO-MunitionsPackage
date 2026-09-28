"""Artifact-only checks for selected shapes and the single 45-degree intake."""
import json
import math
from pathlib import Path
from cadgen import build123d as bd, read_step

ROOT=Path(__file__).resolve().parents[1]


def parts(filename):
    shape=read_step(ROOT/"STEP"/filename)
    return shape,{p.label:p for p in shape.children}


def close(a,b,tol=.002):
    assert abs(a-b)<tol,(a,b)


def point(x,radius,tangent=0,angle=45):
    a=math.radians(angle)
    return (x,radius*math.sin(a)+tangent*math.cos(a),
            radius*math.cos(a)-tangent*math.sin(a))


def difference_volume(a,b):
    result=a-b
    return result.volume if result else 0


if __name__=="__main__":
    report_path=ROOT/"reviews"/"intake_revision_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks have not completed"})+"\n")
    model,p=parts("Selected_Intake_Prototype.step")
    separated,q=parts("Selected_Intake_Prototype_Separated.step")
    _,a=parts("A_Trace.step")
    _,c=parts("C_Shoulder.step")
    assert len(p)==len(q)==11
    assert set(p)==set(q)
    preserved={"main_ogive":c["main_ogive"],"booster_body":a["booster_body"]}
    preserved.update({f"{prefix}_{i}":a[f"{prefix}_{i}"] for prefix in ("main_fin","booster_fin") for i in range(1,5)})
    for name,original in preserved.items():
        close(p[name].volume,original.volume,.01)
        assert difference_volume(p[name],original)<.01,name
        assert difference_volume(original,p[name])<.01,name
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert difference_volume(shape,restored)<.01,name
        assert difference_volume(restored,shape)<.01,name
        bb=shape.bounding_box()
        if name.startswith("booster"):
            assert bb.max.X<=-3370/3+.002,name
        else:
            assert bb.min.X>=-3370/3-.002,name
    bb=model.bounding_box()
    close(bb.size.X,3370)
    close(p["booster_body"].bounding_box().size.X,3370/6)
    angles=[]
    for prefix in ("main_fin","booster_fin"):
        for i in range(1,5):
            center=p[f"{prefix}_{i}"].center(bd.CenterOf.MASS)
            angle=math.degrees(math.atan2(center.Y,center.Z))%360
            close(angle,45+(i-1)*90,.001)
            angles.append(angle)
    body=p["main_body_intake_prototype"].solids()[0]
    # One corner only; the other three are intentionally not propagated.
    assert body.is_inside(point(0,140))
    for angle in (135,225,315):
        assert not body.is_inside(point(0,130,angle=angle))
    for x,r in ((600,122),(500,121),(350,119)):
        assert not body.is_inside(point(x,r)),"mouth/passage blocked"
        assert body.is_inside(point(x,60)),"central core lost"
    assert body.is_inside(point(500,122,tangent=24)),"missing mouth sidewall"
    assert body.is_inside(point(310,119)),"missing blind passage rear"
    # The first prototype passed simple mouth probes but broke through its
    # curved roof/shoulders. Verify a continuous ceiling and both sidewalls.
    radial_offset=math.sqrt(2)*30+70-100
    for x in (380,450,520,580):
        for tangent in (-10,0,10):
            assert body.is_inside(point(x,radial_offset+122,tangent)),"roof breakthrough"
        for tangent in (-22,22):
            assert body.is_inside(point(x,radial_offset+107,tangent)),"sidewall breakthrough"
    # Nose/forward transition must be exactly the original outside the intake zone.
    front=bd.Box(1100,600,600).translate((1250,0,0)) # X >= 700
    assert difference_volume(p["main_body_intake_prototype"] & front,a["main_body"] & front)<.01
    assert difference_volume(a["main_body"] & front,p["main_body_intake_prototype"] & front)<.01
    report=dict(ok=True,parts=11,length_mm=bb.size.X,booster_length_mm=p["booster_body"].bounding_box().size.X,
                preserved_exactly=list(preserved),fin_clock_degrees=angles,
                intake_clock_degrees=45,intakes_prototyped=1,open_passage_probes=3,
                protected_core=True,roof_and_sidewalls_continuous=True,
                forward_transition_unchanged=True,separated_shapes_unchanged=True)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
