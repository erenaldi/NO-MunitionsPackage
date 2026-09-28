"""R2 artifact-only checks. Preserve prior criteria, add cover and fin exposure."""
import json
import math
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd
from check_intake_revision import parts, close, point, difference_volume

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    report_path=ROOT/"reviews"/"intake_R2_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks have not completed"})+"\n")
    model,p=parts("Selected_Intake_R2.step")
    separated,q=parts("Selected_Intake_R2_Separated.step")
    covered,k=parts("Selected_Intake_R2_Covered.step")
    _,a=parts("A_Trace.step")
    _,c=parts("C_Shoulder.step")
    assert len(p)==len(q)==11 and len(k)==12
    assert set(p)==set(q)==set(k)-{"intake_reference_cover"}
    preserved={"main_ogive":c["main_ogive"],"booster_body":a["booster_body"]}
    preserved.update({f"{prefix}_{i}":a[f"{prefix}_{i}"] for prefix in ("main_fin","booster_fin") for i in range(1,5)})
    for name,original in preserved.items():
        close(p[name].volume,original.volume,.01)
        assert difference_volume(p[name],original)<.01,name
        assert difference_volume(original,p[name])<.01,name
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        for other in (restored,k[name]):
            assert difference_volume(shape,other)<.01,name
            assert difference_volume(other,shape)<.01,name
        b=shape.bounding_box()
        assert b.max.X<=-3370/3+.002 if name.startswith("booster") else b.min.X>=-3370/3-.002
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
    body=p["main_body_intake_r2"].solids()[0]
    assert body.is_inside(point(0,140))
    for angle in (135,225,315):
        assert not body.is_inside(point(0,130,angle=angle))
    for x,r in ((600,122),(500,121),(350,119)):
        assert not body.is_inside(point(x,r)),"mouth/passage blocked"
        assert body.is_inside(point(x,60)),"central core lost"
    # R2's enlarged reference-led aperture intentionally includes the old
    # +/-24 mm wall position. Verify the new width, then its actual sidewalls.
    for tangent in (-22,0,22):
        assert not body.is_inside(point(580,124,tangent)),"wide aperture not open"
    assert body.is_inside(point(500,122,tangent=38)),"missing widened mouth sidewall"
    assert body.is_inside(point(280,119)),"missing blind passage rear"
    radial_offset=math.sqrt(2)*30+70-100
    for x in (380,450,520,580):
        for tangent in (-10,0,10):
            assert body.is_inside(point(x,radial_offset+132,tangent)),"roof breakthrough"
        for tangent in (-38,38):
            assert body.is_inside(point(x,radial_offset+107,tangent)),"sidewall breakthrough"
    front=bd.Box(1100,600,600).translate((1250,0,0))
    assert difference_volume(body & front,a["main_body"] & front)<.01
    assert difference_volume(a["main_body"] & front,body & front)<.01
    # Verify long-form development, independently of the generator stations.
    assert body.is_inside(point(-550,157)),"aft strake did not rise"
    assert not body.is_inside(point(580,157)),"forward inlet is as tall as aft strake"
    # The forward cutter must not scratch the core ahead of the canted lip.
    for x in (650,665):
        assert body.is_inside(point(x,112.2)),"unintended notch ahead of inlet"
    cover=k["intake_reference_cover"]
    assert cover.is_valid and len(cover.solids())==1 and cover.volume>0
    contact=cover & body
    assert contact and contact.volume>1,"cover does not seat on rim"
    for z in (102,110,118,126):
        for tangent in (-9,0,9):
            x=630-.7*(z-100)+.6
            assert cover.solids()[0].is_inside(point(x,z+radial_offset,tangent)),"cover misses opening"
    exposed={}
    for i in range(1,5):
        old=difference_volume(a[f"main_fin_{i}"],a["main_body"])
        new=difference_volume(p[f"main_fin_{i}"],body)
        exposed[str(i)]=new/old
    print("Main-fin exposed-volume retention:",exposed,flush=True)
    # Do not let the new strake silently bury the selected fin silhouette.
    assert exposed["1"]>=.80,"new fairing buries too much selected fin"
    for i in ("2","3","4"):
        close(exposed[i],1,.001)
    validations=[]
    for suffix in ("","_Separated","_Covered"):
        target=ROOT/"STEP"/("Selected_Intake_R2"+suffix+".step")
        result=subprocess.run([sys.executable,"-m","cadgen.cli","step","inspect","validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(result.stdout)
        validations.append(value)
        assert value["ok"],value
    report=dict(ok=True,parts_open=11,parts_covered=12,length_mm=bb.size.X,
                booster_length_mm=p["booster_body"].bounding_box().size.X,
                preserved_exactly=list(preserved),fin_clock_degrees=angles,intake_clock_degrees=45,
                intakes_prototyped=1,open_passage_probes=3,roof_and_sidewall_probes=20,
                cover_overlap_mm3=contact.volume,cover_opening_probes=12,
                widened_aperture_probes=3,forward_notch_probes=2,
                main_fin_exposed_volume_retention=exposed,forward_transition_unchanged=True,
                native_validation=validations)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
