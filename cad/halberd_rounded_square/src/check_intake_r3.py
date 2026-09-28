"""Independent artifact checks for the user's clarified R3 drawing contract.

R2's exact A-main-fin and exposure assertions are intentionally NOT repurposed:
the user authorized a new fin seated on the intake housing. Original R2 tests
remain intact, while this checker proves the new interface and red profile.
"""
import json
import math
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd
from check_intake_revision import parts, close, point, difference_volume

ROOT=Path(__file__).resolve().parents[1]
SEAM=-3370/3
R0=30*math.sqrt(2)


def section(shape,x):
    return bd.section(shape,section_by=bd.Plane(origin=(x,0,0),x_dir=(0,1,0),z_dir=(1,0,0)))


if __name__=="__main__":
    report_path=ROOT/"reviews"/"intake_R3_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks have not completed"})+"\n")
    model,p=parts("Selected_Intake_R3.step")
    separated,q=parts("Selected_Intake_R3_Separated.step")
    _,a=parts("A_Trace.step")
    _,c=parts("C_Shoulder.step")
    assert len(p)==len(q)==11 and set(p)==set(q)
    original_core=a["main_body"]
    body=p["main_body_intake_r3"]
    fin=p["main_fin_housing_r3"]
    preserved={"main_ogive":c["main_ogive"],"booster_body":a["booster_body"]}
    preserved.update({f"booster_fin_{i}":a[f"booster_fin_{i}"] for i in range(1,5)})
    preserved.update({f"main_fin_{i}":a[f"main_fin_{i}"] for i in range(2,5)})
    for name,old in preserved.items():
        assert difference_volume(p[name],old)<.01,name
        assert difference_volume(old,p[name])<.01,name
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        other=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert other.is_valid and len(other.solids())==1 and other.volume>0,name
        assert difference_volume(shape,other)<.01,name
        assert difference_volume(other,shape)<.01,name
        bb=shape.bounding_box()
        if name.startswith("booster"):
            assert bb.max.X<=SEAM+.002,name
        else:
            assert bb.min.X>=SEAM-.002,name
    close(model.bounding_box().size.X,3370)
    close(p["booster_body"].bounding_box().size.X,3370/6)
    # The new channel is above the curved skin, not a cut into the core.
    removed_core=difference_volume(original_core,body)
    assert removed_core<.01,"original core was cut"
    forward=bd.Box(1100,600,600).translate((1250,0,0))
    assert difference_volume(body & forward,original_core & forward)<.01,"nose transition changed"
    added=body-original_core
    local_added=added.rotate(bd.Axis.X,45)
    close(local_added.bounding_box().min.X,SEAM)
    assert body.solids()[0].is_inside(point(SEAM+.1,130)),"housing ends before seam"
    terminal=section(local_added,SEAM+.1)
    end_width=terminal.bounding_box().size.Y
    assert 6.<end_width<9.,("terminal width",end_width)
    taper_widths=[]
    for x in (-1120.,-1000.,-850.,-500.,0.,450.):
        s=section(local_added,x)
        taper_widths.append(s.bounding_box().size.Y)
    assert all(b>a for a,b in zip(taper_widths,taper_widths[1:])),"taper reverses before the seam"
    dense_taper=[(x,section(local_added,x).bounding_box().size.Y) for x in range(-1100,601,50)]
    assert all(b[1]>=a[1] for a,b in zip(dense_taper,dense_taper[1:])),"smoothed taper has a local width reversal"
    # One station only until approval; opposite corners remain unchanged.
    for angle in (135,225,315):
        assert not body.solids()[0].is_inside(point(450,135,angle=angle))
    solid=body.solids()[0]
    # The body-following floor is a true arc, offset about 3 mm from the skin.
    for tangent in (-30.,0.,30.):
        floor=R0+math.sqrt(73*73-tangent*tangent)
        core=R0+math.sqrt(70*70-tangent*tangent)
        assert solid.is_inside(point(550,core+1.,tangent)),"missing curved floor material"
        assert not solid.is_inside(point(550,floor+1.,tangent)),"curved-floor opening blocked"
    for x in (360,450,560):
        assert not solid.is_inside(point(x,130)),"intake passage blocked"
        assert solid.is_inside(point(x,144)),"roof broken"
        for tangent in (-30,30):
            assert solid.is_inside(point(x,120,tangent)),"flank broken"
    # Actual hole area compared to actual outer area above the original core.
    cross=section(body,560)
    core_cross=section(original_core,560)
    hole_area=sum(bd.Face(w).area for face in cross.faces() for w in face.inner_wires())
    filled_area=sum(bd.Face(face.outer_wire()).area for face in cross.faces())
    envelope_area=filled_area-core_cross.area
    aperture_fraction=hole_area/envelope_area
    print("Aperture fraction of above-core envelope:",aperture_fraction,flush=True)
    assert aperture_fraction>=.65,"small-hole/thick-block interpretation returned"
    # Fin must sit on the housing rather than directly on the original core.
    contact=fin & body
    core_contact=fin & original_core
    core_contact_volume=core_contact.volume if core_contact else 0
    assert contact and contact.volume>10,"fin floats above housing"
    assert core_contact_volume<.01,"fin still rooted in airframe core"
    local_fin=fin.rotate(bd.Axis.X,45)
    fb=local_fin.bounding_box()
    close(fb.min.X,-1075.)
    close(fb.max.X,-855.)
    close(fb.max.Z,212.)
    assert fb.min.Z>130.,"old low fin root retained"
    mass=fin.center(bd.CenterOf.MASS)
    close(math.degrees(math.atan2(mass.Y,mass.Z)),45.,.001)
    exposed=fin-body
    assert exposed and exposed.volume/fin.volume>.70,"housing obscures red target silhouette"
    checks=[]
    for name in ("Selected_Intake_R3","Selected_Intake_R3_Separated","Selected_Intake_R3_Section"):
        target=ROOT/"STEP"/(name+".step")
        command=[sys.executable,"-m","cadgen.cli","step","inspect"]
        run=subprocess.run(command+["validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(run.stdout)
        assert value["ok"],value
        checks.append(value)
        facts=subprocess.run(command+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(json.loads(facts.stdout),indent=2)+"\n")
    report=dict(ok=True,length_mm=model.bounding_box().size.X,booster_length_mm=p["booster_body"].bounding_box().size.X,
                unchanged=list(preserved),core_removed_mm3=removed_core,terminal_width_mm=end_width,
                taper_widths_aft_to_front_mm=taper_widths,aperture_area_mm2=hole_area,
                dense_taper_samples=dense_taper,
                envelope_area_mm2=envelope_area,aperture_fraction=aperture_fraction,
                fin_housing_contact_mm3=contact.volume,fin_core_contact_mm3=core_contact_volume,
                fin_tip_radius_mm=fb.max.Z,fin_root_min_radius_mm=fb.min.Z,
                fin_exposed_volume_fraction=exposed.volume/fin.volume,clock_degrees=45,
                intakes_prototyped=1,separated_shapes_unchanged=True,native_validation=checks)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
