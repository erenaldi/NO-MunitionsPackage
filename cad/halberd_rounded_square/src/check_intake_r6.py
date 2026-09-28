"""Independent proof of late curved narrowing and unchanged R5 constraints."""
import json
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd
from check_intake_revision import parts, close, point, difference_volume
from check_intake_r3 import section
from check_intake_r4 import occupied
from check_intake_r5 import check_line

ROOT=Path(__file__).resolve().parents[1]
SEAM=-3370/3


def roof_section(local,x):
    s=section(local,x)
    roof=s.bounding_box().max.Z
    vertices=[v for v in s.vertices() if abs(v.Z-roof)<.002]
    return roof,max(abs(v.Y) for v in vertices)


if __name__=="__main__":
    output=ROOT/"reviews"/"intake_R6_checks.json"
    output.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=parts("Selected_Intake_R6.step")
    separated,q=parts("Selected_Intake_R6_Separated.step")
    _,old=parts("Selected_Intake_R5.step")
    _,base=parts("A_Trace.step")
    assert len(p)==len(q)==17 and set(p)==set(q)
    assert set(p)==(set(old)-{"main_body_intake_r5"})|{"main_body_intake_r6"}
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        other=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert other.is_valid and len(other.solids())==1
        assert difference_volume(shape,other)<.01,name
        assert difference_volume(other,shape)<.01,name
        if name in old:
            assert difference_volume(shape,old[name])<.01,name
            assert difference_volume(old[name],shape)<.01,name
            assert tuple(shape.color)==tuple(old[name].color),name
    main=p["main_body_intake_r6"]
    local=main.rotate(bd.Axis.X,45.)
    assert difference_volume(base["main_body"],main)<.01
    close(model.bounding_box().size.X,3370)
    close(main.bounding_box().min.X,SEAM)
    front_clip=bd.Box(1100,600,600).translate((761,0,0)) # X >= 211
    assert difference_volume(main & front_clip,old["main_body_intake_r5"] & front_clip)<.01
    assert difference_volume(old["main_body_intake_r5"] & front_clip,main & front_clip)<.01
    samples=[]
    for i in range(1,20):
        u=i/20
        x=210.+(SEAM-210.)*u
        roof,half=roof_section(local,x)
        expected_half=16.-14.4*u**3
        close(half,expected_half,.002)
        close(roof,147.5-11.5*u,.002)
        samples.append(dict(u=u,x=x,roof_half_width_mm=half,roof_height_mm=roof))
    halves=[16.]+[s["roof_half_width_mm"] for s in samples]+[1.6]
    reductions=[a-b for a,b in zip(halves,halves[1:])]
    assert all(r>0 for r in reductions),"taper reverses"
    assert all(b>a for a,b in zip(reductions,reductions[1:])),"narrowing does not accelerate smoothly"
    midpoint=next(s for s in samples if s["u"]==.5)["roof_half_width_mm"]
    three_quarters=next(s for s in samples if s["u"]==.75)["roof_half_width_mm"]
    early_fraction=(16.-midpoint)/14.4
    late_fraction=(three_quarters-1.6)/14.4
    assert early_fraction<.20,"slims too early"
    assert late_fraction>.50,"final quarter is not aggressive enough"
    front_edges=[]
    for edge in local.edges():
        b=edge.bounding_box()
        if abs(b.min.X-210)<.002 and b.max.X>600 and b.min.Z>144 and b.size.X>300:
            front_edges.append(check_line(edge))
    assert len(front_edges)==2
    for x in (-420.,-300.,-100.,100.,210.,350.,560.):
        cross=section(main,x)
        assert sum(len(f.inner_wires()) for f in cross.faces())>=1,("duct broke through",x)
    back=max(v.X for v in p["main_intake_dark_floor"].vertices())
    close(back,-444.97392256565956,.002)
    intake_parts=[main,p["main_intake_dark_recess"],p["main_intake_dark_floor"]]
    for x in (back+.1,-300.,-100.,100.,400.,560.):
        assert not occupied(point(x,120),intake_parts)
    assert occupied(point(back-.1,120),[p["main_intake_dark_floor"]])
    contact=main & p["main_fin_housing_r3"]
    assert contact and contact.volume>10
    for label in ("main_intake_dark_floor","main_nozzle_dark_floor","booster_nozzle_dark_floor"):
        assert tuple(p[label].color)==(0.,0.,0.,1.)
    native=[]
    for name in ("Selected_Intake_R6","Selected_Intake_R6_Separated"):
        target=ROOT/"STEP"/(name+".step")
        command=[sys.executable,"-m","cadgen.cli","step","inspect"]
        run=subprocess.run(command+["validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(run.stdout)
        assert value["ok"],value
        native.append(value)
        facts=subprocess.run(command+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(json.loads(facts.stdout),indent=2)+"\n")
    report=dict(ok=True,parts=17,cubic_samples=samples,first_half_width_reduction_fraction=early_fraction,
                final_quarter_width_reduction_fraction=late_fraction,inlet_unchanged=True,side_roof_profile_unchanged=True,
                front_edge_maximum_deviation_mm=max(front_edges),fin_contact_mm3=contact.volume,
                channel_back_x_mm=back,nonhousing_parts_and_colors_unchanged=True,native_validation=native)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
