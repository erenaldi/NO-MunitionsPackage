"""R5 artifact checks: linear taper, straight edges, rear-face-only blackening."""
import json
import math
import subprocess
import sys
from pathlib import Path
from cadgen import build123d as bd
from check_intake_revision import parts, close, point, difference_volume
from check_intake_r3 import section
from check_intake_r4 import occupied

ROOT=Path(__file__).resolve().parents[1]
SEAM=-3370/3


def check_line(edge):
    a,b=edge.start_point(),edge.end_point()
    chord=(b-a).length
    close(edge.length,chord,.002)
    deviations=[]
    for t in (.25,.5,.75):
        p=edge.position_at(t)
        deviation=((p-a).cross(b-a)).length/chord
        assert deviation<.002,("curved design edge",deviation)
        deviations.append(deviation)
    return max(deviations)


if __name__=="__main__":
    report_path=ROOT/"reviews"/"intake_R5_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks have not completed"})+"\n")
    model,p=parts("Selected_Intake_R5.step")
    separated,q=parts("Selected_Intake_R5_Separated.step")
    _,old=parts("Selected_Intake_R4.step")
    _,a=parts("A_Trace.step")
    assert len(p)==len(q)==17 and set(p)==set(q)
    expected=(set(old)-{"main_body_intake_r4"})|{"main_body_intake_r5","main_intake_dark_floor"}
    assert set(p)==expected
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        other=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        assert other.is_valid and len(other.solids())==1
        assert difference_volume(shape,other)<.01,name
        assert difference_volume(other,shape)<.01,name
        if name in old and name!="main_intake_dark_recess":
            assert difference_volume(shape,old[name])<.01,name
            assert difference_volume(old[name],shape)<.01,name
    new_body=p["main_body_intake_r5"]
    assert difference_volume(a["main_body"],new_body)<.01,"original core removed"
    close(model.bounding_box().size.X,3370)
    close(new_body.bounding_box().min.X,SEAM)
    local=new_body.rotate(bd.Axis.X,45.)
    taper=[]
    for x in (-1120.,-1000.,-850.,-700.,-550.,-400.,-250.,-100.,50.,200.):
        t=(x-SEAM)/(210.-SEAM)
        expected_roof=136.+11.5*t
        expected_half=1.6+14.4*t
        cross=section(local,x)
        roof=cross.bounding_box().max.Z
        close(roof,expected_roof,.002)
        roof_points=[v for v in cross.vertices() if abs(v.Z-roof)<.002]
        half=max(abs(v.Y) for v in roof_points)
        close(half,expected_half,.002)
        taper.append(dict(x=x,roof_height_mm=roof,roof_half_width_mm=half))
    front=[]
    for x in (300.,400.,500.,600.):
        cross=section(local,x)
        roof=cross.bounding_box().max.Z
        close(roof,147.5-2.5*(x-210)/505,.002)
        points=[v for v in cross.vertices() if abs(v.Z-roof)<.002]
        close(max(abs(v.Y) for v in points),16.,.002)
        front.append(dict(x=x,roof_height_mm=roof))
    rear_edges=[]
    front_edges=[]
    for edge in local.edges():
        bounds=edge.bounding_box()
        if abs(bounds.min.X-SEAM)<.002 and abs(bounds.max.X-210)<.002 and bounds.min.Z>130:
            rear_edges.append(check_line(edge))
        if abs(bounds.min.X-210)<.002 and bounds.max.X>600 and bounds.min.Z>144 and bounds.size.X>300:
            front_edges.append(check_line(edge))
    assert len(rear_edges)==2,("rear edge count",len(rear_edges))
    assert len(front_edges)==2,("front edge count",len(front_edges))
    # The extended channel must remain enclosed after the taper correction.
    for x in (-420.,-300.,-100.,100.,210.,350.,560.):
        cross=section(new_body,x)
        assert sum(len(f.inner_wires()) for f in cross.faces())>=1,("duct broke through",x)
    housing_old=old["main_body_intake_r4"]-a["main_body"]
    back=100.-.30*housing_old.bounding_box().size.X
    cup=p["main_intake_dark_recess"]
    cap=p["main_intake_dark_floor"]
    combined=cup+cap
    assert difference_volume(combined,old["main_intake_dark_recess"])<.01
    assert difference_volume(old["main_intake_dark_recess"],combined)<.01
    assert not occupied(point(back+.1,120),[new_body,cup,cap])
    assert occupied(point(back-.1,120),[cap])
    for x in (back+10.,-300.,-100.,100.,400.,560.):
        assert not occupied(point(x,120),[new_body,cup,cap]),("blocked channel",x)
    contact=p["main_fin_housing_r3"] & new_body
    assert contact and contact.volume>10,"mounted fin lost housing contact"
    side_labels=("main_intake_dark_recess","main_nozzle_dark_recess","booster_nozzle_dark_recess")
    for label in side_labels:
        assert tuple(p[label].color)==tuple(old[label].color),("side recolored",label)
    black_labels=("main_intake_dark_floor","main_nozzle_dark_floor","booster_nozzle_dark_floor")
    colors={label:tuple(p[label].color) for label in black_labels}
    assert all(color==(0.,0.,0.,1.) for color in colors.values()),colors
    # Reference readback documents what was actually inspected; target is its
    # obscured appearance, with explicitly black Halberd caps for both displays.
    from cadgen import read_step
    kris=read_step(ROOT.parent/"IRM-S4_Kris_PL10_Hybrid.step")
    reference=next(part for part in kris.children if part.label=="aft_dark_recess")
    native=[]
    for name in ("Selected_Intake_R5","Selected_Intake_R5_Separated"):
        target=ROOT/"STEP"/(name+".step")
        command=[sys.executable,"-m","cadgen.cli","step","inspect"]
        result=subprocess.run(command+["validate",str(target),"--every-placement"],capture_output=True,text=True,check=True)
        value=json.loads(result.stdout)
        assert value["ok"],value
        native.append(value)
        facts=subprocess.run(command+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(json.loads(facts.stdout),indent=2)+"\n")
    report=dict(ok=True,parts=17,rear_taper_samples=taper,straight_front_samples=front,
                maximum_rear_edge_deviation_mm=max(rear_edges),maximum_front_edge_deviation_mm=max(front_edges),
                rear_caps_rgba=colors,side_colors_unchanged=True,kris_recess_rgba=tuple(reference.color),
                channel_back_x_mm=back,intake_cup_combined_geometry_unchanged=True,
                fin_contact_mm3=contact.volume,native_validation=native)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
