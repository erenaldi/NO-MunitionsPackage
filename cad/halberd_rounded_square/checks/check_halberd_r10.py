"""Check saved R10 geometry, independent profile samples and split ownership."""
import json
import sys
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r8 import ROOT, load, close, identical, volume, native_checks, point, occupied

sys.path.insert(0,str(ROOT/"src"))
from halberd_r8_shapes import build_r8
from halberd_r10_shapes import MAIN_LABEL, FAIRING_LABEL

SEAM=-3370/3
END=-1337.5


def section_at(shape,x):
    return bd.section(shape,section_by=bd.Plane(origin=(x,0,0),
                                               x_dir=(0,1,0),z_dir=(1,0,0)))


if __name__=="__main__":
    report_path=ROOT/"reviews"/"halberd_R10_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=load("halberd_r10")
    _,q=load("halberd_r10_separated")
    _,old=load("Selected_Halberd_R8")
    assert set(p)==set(q) and len(p)==24
    expected=(set(old)-{"main_body_four_intakes_r8"})|{MAIN_LABEL,FAIRING_LABEL}
    assert set(p)==expected
    # The new optional R6 length argument must not change historical callers.
    regenerated={s.label:s for s in build_r8().children}
    for name,shape in old.items():
        identical(shape,regenerated[name])
    for name,shape in p.items():
        if name not in (MAIN_LABEL,FAIRING_LABEL,"booster_fin_1"):
            identical(shape,old[name])
            assert tuple(shape.color)==tuple(old[name].color)
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
        bb=shape.bounding_box()
        assert bb.max.X<=SEAM+.002 if name.startswith("booster") else bb.min.X>=SEAM-.002
    main=p[MAIN_LABEL]
    aft=p[FAIRING_LABEL]
    local_main=main.rotate(bd.Axis.X,45.)
    local_aft=aft.rotate(bd.Axis.X,45.)
    close(aft.bounding_box().min.X,END)
    close(aft.bounding_box().max.X,SEAM)
    close(model.bounding_box().size.X,3370.)
    close(main.distance_to(aft),0.)
    assert volume(main & aft)<.05,"stage pieces overlap in volume"
    # At the cut, the whole aft section is contained in the matching main face.
    front_face=section_at(local_main,SEAM)
    aft_face=section_at(local_aft,SEAM)
    remainder=aft_face-front_face
    assert (remainder.area if remainder else 0.)<.001,"unmatched split profile"
    samples=[]
    for x in (-600.,-950.,SEAM+1.,SEAM,SEAM-1.,-1200.,-1300.,END):
        shape=local_main if x>=SEAM else local_aft
        cross=section_at(shape,x)
        roof=cross.bounding_box().max.Z
        u=(210.-x)/(210.-END)
        expected_roof=147.5-11.5*u
        expected_roof_width=32.-28.8*u**3
        close(roof,expected_roof)
        top=[v for v in cross.vertices() if abs(v.Z-roof)<.002]
        width=max(v.Y for v in top)-min(v.Y for v in top)
        close(width,expected_roof_width)
        samples.append(dict(x_mm=x,roof_radius_mm=roof,roof_width_mm=width))
    close(samples[2]["roof_radius_mm"]-samples[3]["roof_radius_mm"],
          samples[3]["roof_radius_mm"]-samples[4]["roof_radius_mm"],.00001)
    close(section_at(local_aft,END).bounding_box().size.Y,8.)
    # Only this corner is recomputed. Forebody and the other three corner
    # housings are unchanged; the central core is never cut away.
    fore=bd.Box(3000.,600.,600.).translate((1710.,0,0))
    identical(main & fore,old["main_body_four_intakes_r8"] & fore)
    for delta in (90.,180.,270.):
        corner_box=bd.Box(4000.,100.,100.).translate((0,0,150.)).rotate(bd.Axis.X,-45.-delta)
        identical(main & corner_box,old["main_body_four_intakes_r8"] & corner_box)
    _,baseline=load("A_Trace")
    assert volume(baseline["main_body"]-main)<.05,"core changed"
    contacts={"fairing_body":volume(aft & p["booster_body"]),
              "fairing_fin":volume(aft & p["booster_fin_1"]),
              "main_fin_housing":volume(main & p["main_fin_1"])}
    assert min(contacts.values())>10.,contacts
    fin=p["booster_fin_1"].rotate(bd.Axis.X,45.)
    close(fin.bounding_box().max.Z,188.)
    close(fin.bounding_box().min.Z,108.)
    close(fin.bounding_box().min.X,-1485.)
    close(fin.bounding_box().max.X,-1190.)
    back=max(v.X for v in p["main_intake_dark_floor_1"].vertices())
    for i in range(1,5):
        pieces=[main,p[f"main_intake_dark_recess_{i}"],p[f"main_intake_dark_floor_{i}"]]
        for x in (back+.1,-300.,-100.,100.,400.,560.):
            assert not occupied(point(x,120.,45.+90*(i-1)),pieces),"channel blocked"
    gaps={name:aft.distance_to(p[name]) for name in
          ("booster_nozzle_dark_recess","booster_nozzle_dark_floor",
           "booster_fin_2","booster_fin_3","booster_fin_4")}
    assert min(gaps.values())>.1,gaps
    native=[native_checks(name,expected_count=24) for name in ("halberd_r10","halberd_r10_separated")]
    scene=read_scene(ROOT/"STEP"/"halberd_r10_focus.step")
    focus=[]
    for leaf in scene.leaves():
        shape=scene.resolve(leaf.ref).shape()
        assert len(shape.solids())==1 and shape.volume>0
        assert not topology_errors(shape)
        assert all(not boundary_edges(shell) for shell in shape.shells())
        assert not self_intersections(shape)
        focus.append(leaf.label)
    assert len(focus)==4
    report=dict(ok=True,parts_per_full_state=24,unchanged_separate_parts=21,
                original_default_geometry_preserved=True,profile_samples=samples,
                split_sections_match=True,roof_slope_continuous=True,
                intake_extension_mm=SEAM-END,endpoint_x_mm=END,
                channel_back_x_mm=back,contacts_mm3=contacts,clearances_mm=gaps,
                native_placement_checks=native,focus_checks=focus)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: continuous original cubic profile to rear-fin midpoint, matched stage cut,")
    print("ownership, attachment, channels, baseline regression and all 52 saved placements.")
    print(json.dumps({"profile_samples":samples,"contacts_mm3":contacts},indent=2))
