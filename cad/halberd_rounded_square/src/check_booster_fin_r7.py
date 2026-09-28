"""Artifact-only R7 checks; run after all three explicit entrypoints succeed."""
import json
import math
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd, read_step
from check_intake_revision import parts, close, difference_volume

ROOT=Path(__file__).resolve().parents[1]
LABEL="booster_fin_r7_prototype"

if __name__=="__main__":
    output=ROOT/"reviews"/"booster_fin_R7_checks.json"
    output.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=parts("Selected_Halberd_R7.step")
    _,q=parts("Selected_Halberd_R7_Separated.step")
    _,old=parts("Selected_Intake_R6.step")
    assert len(p)==len(q)==17 and set(p)==set(q)
    assert set(p)==(set(old)-{"booster_fin_1"})|{LABEL}
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert restored.is_valid and len(restored.solids())==1
        assert difference_volume(shape,restored)<.01,name
        assert difference_volume(restored,shape)<.01,name
        if name in old:
            assert difference_volume(shape,old[name])<.01,name
            assert difference_volume(old[name],shape)<.01,name
            assert tuple(shape.color)==tuple(old[name].color),name
    blade=p[LABEL]
    local=blade.rotate(bd.Axis.X,45.)
    bounds=local.bounding_box()
    close(bounds.min.X,-1655.)
    close(bounds.max.X,-1360.)
    close(bounds.min.Z,108.)
    close(bounds.max.Z,161.)
    root=[v for v in local.vertices() if abs(v.Z-108.)<.002]
    tip=[v for v in local.vertices() if abs(v.Z-161.)<.002]
    root_chord=max(v.X for v in root)-min(v.X for v in root)
    tip_chord=max(v.X for v in tip)-min(v.X for v in tip)
    close(root_chord,295.)
    close(tip_chord,220.)
    close((max(v.X for v in root)+min(v.X for v in root))/2,-1507.5)
    close((max(v.X for v in tip)+min(v.X for v in tip))/2,-1507.5)
    close(max(v.Y for v in root)-min(v.Y for v in root),8.)
    close(max(v.Y for v in tip)-min(v.Y for v in tip),2.8)
    center=blade.center(bd.CenterOf.MASS)
    close(math.degrees(math.atan2(center.Y,center.Z)),45.,.001)
    contact=blade & p["booster_body"]
    assert contact and contact.volume>10,"fin is not attached"
    clearances={}
    for name in ("booster_nozzle_dark_recess","booster_nozzle_dark_floor"):
        gap=blade.distance_to(p[name])
        assert gap>.1,("nozzle interference",name,gap)
        clearances[name]=gap
    for i in (2,3,4):
        assert blade.distance_to(p[f"booster_fin_{i}"])>.1
    assert blade.bounding_box().min.X>=-1685.
    assert blade.bounding_box().max.X<=-3370/3
    close(model.bounding_box().size.X,3370.)
    isolated=read_step(ROOT/"STEP"/"Selected_Booster_Fin_R7.step")
    expected=local.translate((1507.5,0,-108.))
    assert difference_volume(isolated,expected)<.01
    assert difference_volume(expected,isolated)<.01
    print("R7 artifact geometry, attachment, clearance and preservation checks passed.",flush=True)
    native=[]
    for name in ("Selected_Halberd_R7","Selected_Halberd_R7_Separated","Selected_Booster_Fin_R7"):
        target=ROOT/"STEP"/(name+".step")
        command=[sys.executable,"-m","cadgen.cli","step","inspect"]
        print(f"Validating {name}",flush=True)
        run=subprocess.run(command+["validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(run.stdout)
        assert value["ok"],value
        native.append(value)
        print(f"{name}: strict validation passed; collecting facts",flush=True)
        facts=subprocess.run(command+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(json.loads(facts.stdout),indent=2)+"\n")
        print(f"{name}: facts saved",flush=True)
    report=dict(ok=True,root_chord_mm=root_chord,tip_chord_mm=tip_chord,height_mm=bounds.size.Z,
                setbacks_mm=[37.5,37.5],clock_degrees=45,contact_mm3=contact.volume,
                nozzle_clearances_mm=clearances,other_parts_unchanged=True,native_validation=native)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
