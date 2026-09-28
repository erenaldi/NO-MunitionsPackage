"""Saved-artifact checks for the bounded service-panel detail pass."""
import json
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r8 import ROOT, load, close, identical, volume, point, occupied

MAIN="main_body_intake_r12"
DETAIL=("main_service_cover_1","main_service_border_1","main_service_fastener_1","main_service_fastener_2")


def check_native(name,count):
    scene=read_scene(ROOT/"STEP"/(name+".step"))
    sidecar=json.loads((ROOT/"STEP"/(name+".step.json")).read_text())
    assert sidecar["documentHash"]==scene.document_hash
    appearance=sidecar["appearance"]
    expected={DETAIL[0]:"detail_paint",DETAIL[1]:"detail_border",
              DETAIL[2]:"detail_metal",DETAIL[3]:"detail_metal"}
    if count==31:
        for i in range(1,5):
            expected[f"main_intake_dark_recess_{i}"]="interior"
            expected[f"main_intake_dark_floor_{i}"]="occlusion"
        for stage in ("main","booster"):
            expected[f"{stage}_nozzle_dark_recess"]="interior"
            expected[f"{stage}_nozzle_dark_floor"]="occlusion"
    assert len(appearance["assignments"])==len(expected)
    # Authoritative R12 material properties. cadgen namespaces a local
    # re-declaration that conflicts with the inherited definition as
    # "local/<id>" (source_sidecar.resolve_materials), so resolve each
    # assignment through the sidecar materials and compare the resolved
    # properties instead of raw material IDs.
    r12=json.loads((ROOT/"STEP"/"halberd_r12.step.json").read_text())["appearance"]["materials"]
    authority={role:dict(metalness=r12[role]["metalness"],roughness=r12[role]["roughness"],
                         name=r12[role]["name"]) for role in ("interior","occlusion")}
    authority.update({
        "detail_paint":dict(metalness=.15,roughness=.65,name="Service cover paint"),
        "detail_border":dict(metalness=.05,roughness=.9,name="Recessed joint"),
        "detail_metal":dict(metalness=.65,roughness=.38,name="Small metallic hardware"),
    })
    for role in ("interior","occlusion"):
        inherited=appearance["materials"][role]
        assert inherited["metalness"]==authority[role]["metalness"],role
        assert inherited["roughness"]==authority[role]["roughness"],role
        assert inherited["name"]==authority[role]["name"],role
    rows=[]
    for leaf in scene.leaves():
        shape=scene.resolve(leaf.ref).shape()
        assert len(shape.solids())==1 and shape.volume>0,leaf.label
        assert not topology_errors(shape),leaf.label
        assert all(not boundary_edges(shell) for shell in shape.shells()),leaf.label
        assert not self_intersections(shape),leaf.label
        if leaf.label in expected:
            assigned=appearance["assignments"][leaf.ref.lstrip("#")]
            resolved=appearance["materials"][assigned]
            want=authority[expected[leaf.label]]
            assert resolved["metalness"]==want["metalness"],leaf.label
            assert resolved["roughness"]==want["roughness"],leaf.label
            assert resolved["name"]==want["name"],leaf.label
        rows.append(dict(label=leaf.label,ref=leaf.ref,volume_mm3=shape.volume))
    assert len(rows)==count
    return dict(document=name,document_hash=scene.document_hash,placements=rows)


if __name__=="__main__":
    path=ROOT/"reviews"/"halberd_R13_checks.json"
    path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=load("halberd_r13")
    _,q=load("halberd_r13_separated")
    _,old=load("halberd_r12")
    assert set(p)==set(old)|set(DETAIL) and set(p)==set(q) and len(p)==31
    for name,shape in p.items():
        if name in old and name!=MAIN:
            identical(shape,old[name])
            assert tuple(shape.color)==tuple(old[name].color)
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
    main=p[MAIN]
    removed=old[MAIN]-main
    assert removed and removed.volume>0
    assert volume(main-old[MAIN])<.01
    bounds=removed.bounding_box()
    close(bounds.min.Z,98.8)
    close(bounds.max.Z,100.)
    close(bounds.min.X,-382.)
    close(bounds.max.X,-258.)
    close(bounds.size.Y,30.)
    close(model.bounding_box().size.X,3370.)
    contacts={}
    for name in DETAIL:
        assert p[name].bounding_box().max.Z<100.,"detail protrudes beyond skin"
        assert volume(p[name]-old[MAIN])<.01,"detail changes approved outer silhouette"
        contact=volume(p[name] & main)
        assert contact>.01,(name,"unseated detail")
        contacts[name]=contact
    cover=p[DETAIL[0]]
    border=p[DETAIL[1]]
    close(cover.bounding_box().max.Z,99.85)
    close(border.bounding_box().max.Z,99.1)
    assert volume(cover & border)<.01
    for i,x in enumerate((-368.,-272.),1):
        screw=p[f"main_service_fastener_{i}"]
        close(screw.bounding_box().max.Z,99.65)
        assert not occupied((x,0,99.55),[screw]),"slot missing"
        assert occupied((x+.65,0,99.55),[screw]),"head missing"
        assert volume(screw & cover)<.01,"fastener intersects countersink"
    for i in range(1,5):
        back=max(v.X for v in p[f"main_intake_dark_floor_{i}"].vertices())
        for x in (back+.1,-300.,-100.,100.,400.,560.):
            assert not occupied(point(x,120.,45.+90*(i-1)),
                                [main,p[f"main_intake_dark_recess_{i}"],p[f"main_intake_dark_floor_{i}"]])
    native=[check_native(name,count) for name,count in
            (("halberd_r13",31),("halberd_r13_separated",31),("halberd_r13_focus",5))]
    report=dict(ok=True,unchanged_baseline_parts=26,removed_skin_volume_mm3=removed.volume,
                panel_seat_depth_mm=1.2,cover_recess_mm=.15,fastener_recess_mm=.35,
                all_details_inside_approved_skin=True,contact_volumes_mm3=contacts,
                native_placement_checks=native)
    path.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 1.2 mm panel seat, recessed beveled cover/border, two slotted heads,")
    print("26 unchanged R12 parts, no silhouette expansion, stage/channel/material preservation and 67 valid placements.")
