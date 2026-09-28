"""Independent R4 extension, exterior-preservation and recessed-liner checks."""
import json
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd
from check_intake_revision import parts, close, point, difference_volume
from check_intake_r3 import section

ROOT=Path(__file__).resolve().parents[1]


def outer_area(shape,x):
    return sum(bd.Face(f.outer_wire()).area for f in section(shape,x).faces())


def occupied(point_xyz,shapes):
    return any(s.is_inside(point_xyz) for shape in shapes for s in shape.solids())


if __name__=="__main__":
    path=ROOT/"reviews"/"intake_R4_checks.json"
    path.write_text(json.dumps({"ok":False,"status":"Checks have not completed"})+"\n")
    model,p=parts("Selected_Intake_R4.step")
    separated,q=parts("Selected_Intake_R4_Separated.step")
    _,old=parts("Selected_Intake_R3.step")
    _,a=parts("A_Trace.step")
    assert len(p)==len(q)==16 and set(p)==set(q)
    expected=(set(old)-{"main_body_intake_r3"})|{"main_body_intake_r4","main_intake_dark_recess","main_nozzle_dark_recess","booster_nozzle_dark_recess","main_nozzle_dark_floor","booster_nozzle_dark_floor"}
    assert set(p)==expected
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert restored.is_valid and len(restored.solids())==1 and restored.volume>0,name
        assert difference_volume(shape,restored)<.01,name
        assert difference_volume(restored,shape)<.01,name
        if name in old:
            assert difference_volume(shape,old[name])<.01,name
            assert difference_volume(old[name],shape)<.01,name
    old_body=old["main_body_intake_r3"]
    new_body=p["main_body_intake_r4"]
    assert difference_volume(new_body,old_body)<.01,"old intake void was filled"
    assert difference_volume(a["main_body"],new_body)<.01,"original airframe core was cut"
    removed=old_body-new_body
    assert removed and removed.volume>1000,"channel was not extended"
    for axis in ("X","Y","Z"):
        for bound in ("min","max"):
            close(getattr(getattr(old_body.bounding_box(),bound),axis),getattr(getattr(new_body.bounding_box(),bound),axis))
    forward=bd.Box(1100,600,600).translate((761,0,0)) # X >= 211
    assert difference_volume(old_body & forward,new_body & forward)<.01,"entry/forward passage changed"
    assert difference_volume(new_body & forward,old_body & forward)<.01
    external_samples=[]
    for x in (-1100.,-800.,-500.,-430.,-300.,-100.,100.,210.,450.,560.):
        before,after=outer_area(old_body,x),outer_area(new_body,x)
        close(before,after,.01)
        external_samples.append(dict(x=x,outer_area_mm2=after))
    housing=old_body-a["main_body"]
    housing_length=housing.bounding_box().size.X
    extension=.30*housing_length
    back=100.-extension
    cup=p["main_intake_dark_recess"]
    # Validate the actual air-to-dark-back transition, including liner thickness.
    assert occupied(point(99.9,120),[old_body])
    assert not occupied(point(100.1,120),[old_body])
    assert not occupied(point(back+.1,120),[new_body,cup]),"cup shortens specified extension"
    assert occupied(point(back-.1,120),[cup]),"new dark back face missing"
    for x in (back+10,back+60,-300.,-100.,99.,150.,400.,560.):
        assert not occupied(point(x,120),[new_body,cup]),f"blocked clear channel at {x}"
    assert cup.bounding_box().max.X<back+81.,"lining reaches too far toward mouth"
    cup_contact=cup & new_body
    assert cup_contact and cup_contact.volume>1,"intake rear cup is floating"
    nozzle_results=[]
    for label,host,entrance,depth,mouth_radius in (
        ("main_nozzle_dark_recess",new_body,-3370/3,42.,65.),
        ("booster_nozzle_dark_recess",p["booster_body"],-1685.,72.,69.),
    ):
        liner=p[label]
        floor=p[label.replace("_recess","_floor")]
        close(liner.bounding_box().min.X,entrance+9.)
        close(liner.bounding_box().max.X,entrance+depth+1.)
        assert liner.bounding_box().size.Y<2*mouth_radius
        contact=liner & host
        assert contact and contact.volume>1,label
        floor_contact=floor & liner
        assert floor_contact and floor_contact.volume>1,"dark floor is floating"
        assert not occupied((entrance+15.,0,0),[host,liner,floor]),"nozzle mouth capped"
        assert not occupied((entrance+depth-2.1,0,0),[host,liner,floor]),"nozzle depth lost"
        assert occupied((entrance+depth-1.9,0,0),[floor]),"nozzle dark floor missing"
        nozzle_results.append(dict(label=label,neutral_lip_depth_mm=9.,clear_floor_depth_mm=depth-2.,contact_mm3=contact.volume))
    # Matte charcoal assignments are source-declared; STEP readback retains color.
    colors={}
    for label in ("main_intake_dark_recess","main_nozzle_dark_recess","booster_nozzle_dark_recess","main_nozzle_dark_floor","booster_nozzle_dark_floor"):
        color=p[label].color
        assert color is not None,label
        rgba=tuple(color)
        assert max(rgba[:3])<.12,(label,rgba)
        colors[label]=rgba
    native=[]
    for name in ("Selected_Intake_R4","Selected_Intake_R4_Separated","Selected_Intake_R4_Cutaway"):
        target=ROOT/"STEP"/(name+".step")
        command=[sys.executable,"-m","cadgen.cli","step","inspect"]
        run=subprocess.run(command+["validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(run.stdout)
        assert value["ok"],value
        native.append(value)
        facts=subprocess.run(command+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(json.loads(facts.stdout),indent=2)+"\n")
    report=dict(ok=True,parts=16,housing_length_mm=housing_length,added_channel_length_mm=extension,
                old_clear_back_x_mm=100.,new_clear_back_x_mm=back,channel_removed_volume_mm3=removed.volume,
                exterior_section_checks=external_samples,original_parts_unchanged=True,
                intake_cup_contact_mm3=cup_contact.volume,nozzles=nozzle_results,dark_colors=colors,
                separated_shapes_unchanged=True,native_validation=native)
    path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
