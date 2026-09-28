"""Fourfold propagation checked against the approved saved one-station R11."""
import json
import faulthandler
from itertools import combinations
from cadgen import build123d as bd
from check_halberd_r8 import ROOT, load, close, identical, volume, native_checks, occupied, point


if __name__=="__main__":
    faulthandler.dump_traceback_later(90.)
    report_path=ROOT/"reviews"/"halberd_R12_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    print("Loading saved R12 and approved reference documents",flush=True)
    model,p=load("halberd_r12")
    _,q=load("halberd_r12_separated")
    _,old=load("halberd_r11")
    _,a=load("A_Trace")
    assert set(p)==set(q) and len(p)==27
    main=p["main_body_intake_r12"]
    core=a["main_body"]
    mask=bd.Box(4000.,100.,140.).translate((0,0,150.)).rotate(bd.Axis.X,-45.)
    prototype=(old["main_body_intake_r10"]-core) & mask
    expected=bd.Compound(children=[prototype.rotate(bd.Axis.X,-d) for d in (0,90,180,270)])
    print("Comparing four housing deltas",flush=True)
    identical(main-core,expected)
    assert volume(core-main)<.05
    for name,shape in p.items():
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
        if name!="main_body_intake_r12" and not name.startswith(("booster_fin_","booster_intake_fairing_")):
            identical(shape,old[name])
            assert tuple(shape.color)==tuple(old[name].color)
    stations=[]
    for i,delta in enumerate((0.,90.,180.,270.),1):
        for prefix in ("booster_fin","booster_intake_fairing"):
            shape=p[f"{prefix}_{i}"]
            identical(shape.rotate(bd.Axis.X,delta),old[f"{prefix}_1"])
            assert tuple(shape.color)==tuple(old[f"{prefix}_1"].color)
        bf=p[f"booster_fin_{i}"]
        fairing=p[f"booster_intake_fairing_{i}"]
        contacts=[volume(bf & p["booster_body"]),volume(fairing & p["booster_body"]),
                  volume(bf & fairing),volume(p[f"main_fin_{i}"] & main)]
        assert min(contacts)>10.
        assert volume(fairing & main)<.05
        close(fairing.distance_to(main),0.)
        local=bf.rotate(bd.Axis.X,45.+delta)
        close(local.bounding_box().max.Z,188.)
        close(local.bounding_box().min.Z,108.)
        for name in ("booster_nozzle_dark_recess","booster_nozzle_dark_floor"):
            assert fairing.distance_to(p[name])>.1
        back=max(v.X for v in p[f"main_intake_dark_floor_{i}"].vertices())
        for x in (back+.1,-300.,-100.,100.,400.,560.):
            assert not occupied(point(x,120.,45.+delta),[main,p[f"main_intake_dark_recess_{i}"],p[f"main_intake_dark_floor_{i}"]])
        stations.append(dict(clock_degrees=45.+delta,contact_volumes_mm3=contacts))
    for prefix in ("booster_fin","booster_intake_fairing"):
        for i,j in combinations(range(1,5),2):
            assert p[f"{prefix}_{i}"].distance_to(p[f"{prefix}_{j}"])>.1
    close(model.bounding_box().size.X,3370.)
    print("Checking all native placements",flush=True)
    native=[native_checks(name,27) for name in ("halberd_r12","halberd_r12_separated")]
    report=dict(ok=True,parts_per_state=27,approved_R11_replication_exact=True,
                stations=stations,native_placement_checks=native)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: all four R11 intake/fin/fairing stations exactly replicated; 54 saved placements valid.")
    faulthandler.cancel_dump_traceback_later()
