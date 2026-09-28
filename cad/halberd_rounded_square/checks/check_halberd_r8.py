"""Artifact-only R8 placement, replication and native topology checks (cadgen 0.6.6)."""
import json
import math
from itertools import combinations
from pathlib import Path
from cadgen import build123d as bd, read_step, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections

ROOT=Path(__file__).resolve().parents[1]
SEAM=-3370/3
STATIC=("main_ogive","booster_body","main_nozzle_dark_recess","main_nozzle_dark_floor",
        "booster_nozzle_dark_recess","booster_nozzle_dark_floor")
PREFIXES=("main_fin","booster_fin","main_intake_dark_recess","main_intake_dark_floor")


def load(name):
    model=read_step(ROOT/"STEP"/(name+".step"))
    result={part.label:part for part in model.children}
    assert len(result)==len(model.children),"duplicate labels"
    return model,result


def close(a,b,tol=.002):
    assert abs(a-b)<tol,(a,b,tol)


def volume(shape):
    return shape.volume if shape else 0.


def identical(a,b,tol=.05):
    assert volume(a-b)<tol,"geometry missing from comparison"
    assert volume(b-a)<tol,"unexpected extra geometry"


def point(x,r,angle,tangent=0.):
    a=math.radians(angle)
    return (x,r*math.sin(a)+tangent*math.cos(a),r*math.cos(a)-tangent*math.sin(a))


def occupied(p,shapes):
    return any(s.is_inside(p) for shape in shapes for s in shape.solids())


def native_checks(name,expected_count=23):
    scene=read_scene(ROOT/"STEP"/(name+".step"))
    sidecar=json.loads((ROOT/"STEP"/(name+".step.json")).read_text())
    assert sidecar["documentHash"]==scene.document_hash,"material sidecar is stale"
    appearance=sidecar["appearance"]
    assert appearance["materials"]["interior"]["roughness"]==.90
    assert appearance["materials"]["interior"]["metalness"]==.08
    assert appearance["materials"]["occlusion"]["roughness"]==1.
    assert appearance["materials"]["occlusion"]["metalness"]==1.
    finishes={f"main_intake_dark_recess_{i}":"interior" for i in range(1,5)}
    finishes.update({f"main_intake_dark_floor_{i}":"occlusion" for i in range(1,5)})
    finishes.update({"main_nozzle_dark_recess":"interior","booster_nozzle_dark_recess":"interior",
                     "main_nozzle_dark_floor":"occlusion","booster_nozzle_dark_floor":"occlusion"})
    assert len(appearance["assignments"])==len(finishes)==12
    records=[]
    for leaf in scene.leaves():
        if leaf.label in finishes:
            assert appearance["assignments"][leaf.ref.lstrip("#")]==finishes[leaf.label],leaf.label
        shape=scene.resolve(leaf.ref).shape()
        solids=shape.solids()
        assert len(solids)==1,(leaf.ref,leaf.label,"expected one solid")
        assert solids[0].volume>0,(leaf.label,"non-positive solid")
        assert not topology_errors(shape),(leaf.label,"topology errors")
        assert all(not boundary_edges(shell) for shell in shape.shells()),(leaf.label,"open shell")
        assert not self_intersections(shape),(leaf.label,"self intersection")
        records.append(dict(ref=leaf.ref,label=leaf.label,volume_mm3=solids[0].volume,
                            topology_ok=True,closed=True,self_intersections=0))
    assert len(records)==expected_count
    return dict(document=name,document_hash=scene.document_hash,occurrences=records)


if __name__=="__main__":
    report_path=ROOT/"reviews"/"halberd_R8_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=load("Selected_Halberd_R8")
    _,q=load("Selected_Halberd_R8_Separated")
    _,old=load("Selected_Halberd_R7")
    _,a=load("A_Trace")
    expected=set(STATIC)|{"main_body_four_intakes_r8"}|{f"{prefix}_{i}" for prefix in PREFIXES for i in range(1,5)}
    assert len(p)==len(q)==23 and set(p)==set(q)==expected
    for name,shape in p.items():
        assert shape.is_valid and len(shape.solids())==1 and shape.volume>0,name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
        bb=shape.bounding_box()
        assert bb.max.X<=SEAM+.002 if name.startswith("booster") else bb.min.X>=SEAM-.002
    for name in STATIC:
        identical(p[name],old[name])
        assert tuple(p[name].color)==tuple(old[name].color),name
    close(model.bounding_box().size.X,3370.)
    close(p["booster_body"].bounding_box().size.X,3370/6)
    core=a["main_body"]
    main=p["main_body_four_intakes_r8"]
    assert volume(core-main)<.05,"core removed"
    approved_delta=old["main_body_intake_r6"]-core
    expected_delta=bd.Compound(children=[approved_delta.rotate(bd.Axis.X,-d) for d in (0,90,180,270)])
    identical(main-core,expected_delta)
    print("Four housing deltas match the approved one-station geometry.",flush=True)
    prototypes={"main_fin":old["main_fin_housing_r3"],
                "booster_fin":old["booster_fin_r7_prototype"],
                "main_intake_dark_recess":old["main_intake_dark_recess"],
                "main_intake_dark_floor":old["main_intake_dark_floor"]}
    stations=[]
    back=max(v.X for v in old["main_intake_dark_floor"].vertices())
    for i,delta in enumerate((0.,90.,180.,270.),1):
        angle=45.+delta
        for prefix,prototype in prototypes.items():
            part=p[f"{prefix}_{i}"]
            restored=part.rotate(bd.Axis.X,delta)
            if prefix=="booster_fin":
                restored=restored.moved(bd.Location((-170.,0,0)))
            identical(restored,prototype)
            assert tuple(part.color)==tuple(prototype.color),(prefix,i)
        bf=p[f"booster_fin_{i}"]
        mf=p[f"main_fin_{i}"]
        close(bf.bounding_box().min.X,-1485.)
        close(bf.bounding_box().max.X,-1190.)
        for part in (bf,mf):
            c=part.center(bd.CenterOf.MASS)
            close(math.degrees(math.atan2(c.Y,c.Z))%360,angle,.001)
        booster_contact=volume(bf & p["booster_body"])
        main_contact=volume(mf & main)
        assert booster_contact>10 and main_contact>10,(i,"fin not attached")
        # All three samples of the shifted root lie in the constant-section body.
        for x in (-1460.,-1337.5,-1215.):
            probe=point(x,109.,angle)
            assert occupied(probe,[bf]) and occupied(probe,[p["booster_body"]]),(i,"unsupported root sample")
        cup=p[f"main_intake_dark_recess_{i}"]
        cap=p[f"main_intake_dark_floor_{i}"]
        assert tuple(cap.color)==(0.,0.,0.,1.)
        for x in (back+.1,-300.,-100.,100.,400.,560.):
            assert not occupied(point(x,120.,angle),[main,cup,cap]),(i,x,"channel blocked")
        assert occupied(point(back-.1,120.,angle),[cap]),(i,"missing dark back")
        assert occupied(point(SEAM+.1,130.,angle),[main]),(i,"housing ends early")
        gaps={name:bf.distance_to(p[name]) for name in ("booster_nozzle_dark_recess","booster_nozzle_dark_floor")}
        assert min(gaps.values())>.1,(i,"nozzle interference")
        stage_gap=bf.distance_to(mf)
        assert stage_gap>.1,(i,"main/booster fins collide")
        stations.append(dict(station=i,clock_degrees=angle,booster_root_x_mm=[-1485.,-1190.],
                             booster_contact_mm3=booster_contact,main_contact_mm3=main_contact,
                             nozzle_clearances_mm=gaps,main_booster_fin_gap_mm=stage_gap))
    pair_clearances={}
    for prefix in PREFIXES:
        gaps=[p[f"{prefix}_{i}"].distance_to(p[f"{prefix}_{j}"]) for i,j in combinations(range(1,5),2)]
        assert min(gaps)>.1,(prefix,"inter-station interference")
        pair_clearances[prefix]=min(gaps)
    print("Four-station shift, colors, channels and clearances passed.",flush=True)
    native=[]
    for name in ("Selected_Halberd_R8","Selected_Halberd_R8_Separated"):
        print(f"Checking every saved placement: {name}",flush=True)
        native.append(native_checks(name))
    report=dict(ok=True,runtime="cadgen 0.6.6",parts_per_state=23,booster_fin_shift_mm=170.,
                stage_seam_x_mm=SEAM,booster_leading_root_to_seam_mm=(-1190.-SEAM)*-1,
                channel_back_x_mm=back,housing_replication_exact=True,static_parts_unchanged=True,
                stations=stations,minimum_interstation_clearances_mm=pair_clearances,
                native_placement_checks=native)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="native_placement_checks"},indent=2))
    print("All 46 saved part placements passed topology, closure, positive volume and self-intersection checks.")
