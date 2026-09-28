"""Check intake end against the ridge measured from the saved fin itself."""
import json
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r10 import section_at, SEAM
from check_halberd_r8 import ROOT, load, close, identical, volume, native_checks, point, occupied
from halberd_r10_shapes import build_r10, MAIN_LABEL, FAIRING_LABEL


if __name__=="__main__":
    report_path=ROOT/"reviews"/"halberd_R11_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=load("halberd_r11")
    _,q=load("halberd_r11_separated")
    _,old=load("halberd_r10")
    assert set(p)==set(q)==set(old) and len(p)==24
    regenerated={s.label:s for s in build_r10().children}
    for name,shape in p.items():
        identical(old[name],regenerated[name])
        if name not in (MAIN_LABEL,FAIRING_LABEL):
            identical(shape,old[name])
        assert tuple(shape.color)==tuple(old[name].color)
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
    fin=p["booster_fin_1"].rotate(bd.Axis.X,45.)
    root=[v for v in fin.vertices() if abs(v.Z-108.)<.002]
    tip=[v for v in fin.vertices() if abs(v.Z-188.)<.002]
    root_ridge=max(root,key=lambda v:abs(v.Y))
    tip_ridge=max(tip,key=lambda v:abs(v.Y))
    lean=(tip_ridge.X-root_ridge.X)/(tip_ridge.Z-root_ridge.Z)
    def ridge_x(z):
        return root_ridge.X+lean*(z-root_ridge.Z)
    main=p[MAIN_LABEL].rotate(bd.Axis.X,45.)
    aft=p[FAIRING_LABEL].rotate(bd.Axis.X,45.)
    terminal=[v for v in aft.vertices() if abs(v.X-ridge_x(v.Z))<.002]
    assert len(terminal)==6,"end plane must match the measured ridge over its height"
    close(max(v.Z for v in terminal),136.)
    close(max(v.Y for v in terminal)-min(v.Y for v in terminal),8.)
    close(main.bounding_box().max.Z,147.5)
    close(fin.bounding_box().max.Z-fin.bounding_box().min.Z,80.)
    roof_end=ridge_x(136.)
    close(roof_end,-1350.9375)
    assert all(v.X>=ridge_x(v.Z)-.002 for v in aft.vertices()),"housing overextends ridge"
    samples=[]
    for x in (-950.,SEAM+1.,SEAM,SEAM-1.,-1250.,-1337.5,roof_end):
        shape=main if x>=SEAM else aft
        cross=section_at(shape,x)
        roof=cross.bounding_box().max.Z
        u=(210.-x)/(210.-roof_end)
        close(roof,147.5-11.5*u)
        top=[v for v in cross.vertices() if abs(v.Z-roof)<.002]
        width=max(v.Y for v in top)-min(v.Y for v in top)
        close(width,32.-28.8*u**3)
        samples.append(dict(x_mm=x,roof_radius_mm=roof,roof_width_mm=width))
    remainder=section_at(aft,SEAM)-section_at(main,SEAM)
    assert (remainder.area if remainder else 0.)<.001
    close(p[FAIRING_LABEL].distance_to(p[MAIN_LABEL]),0.)
    assert volume(p[FAIRING_LABEL] & p[MAIN_LABEL])<.05
    close(model.bounding_box().size.X,3370.)
    fore=bd.Box(3000.,600.,600.).translate((1710.,0,0))
    identical(p[MAIN_LABEL] & fore,old[MAIN_LABEL] & fore)
    for delta in (90.,180.,270.):
        box=bd.Box(4000.,100.,100.).translate((0,0,150.)).rotate(bd.Axis.X,-45.-delta)
        identical(p[MAIN_LABEL] & box,old[MAIN_LABEL] & box)
    contacts={"fairing_body":volume(p[FAIRING_LABEL] & p["booster_body"]),
              "fairing_fin":volume(p[FAIRING_LABEL] & p["booster_fin_1"]),
              "main_fin":volume(p[MAIN_LABEL] & p["main_fin_1"])}
    assert min(contacts.values())>10.
    for name in ("booster_nozzle_dark_recess","booster_nozzle_dark_floor",
                 "booster_fin_2","booster_fin_3","booster_fin_4"):
        assert p[FAIRING_LABEL].distance_to(p[name])>.1
    back=max(v.X for v in p["main_intake_dark_floor_1"].vertices())
    for i in range(1,5):
        pieces=[p[MAIN_LABEL],p[f"main_intake_dark_recess_{i}"],p[f"main_intake_dark_floor_{i}"]]
        for x in (back+.1,-300.,-100.,100.,400.,560.):
            assert not occupied(point(x,120.,45.+90*(i-1)),pieces)
    native=[native_checks(name,24) for name in ("halberd_r11","halberd_r11_separated")]
    scene=read_scene(ROOT/"STEP"/"halberd_r11_focus.step")
    focus=[]
    for leaf in scene.leaves():
        shape=scene.resolve(leaf.ref).shape()
        assert len(shape.solids())==1 and shape.volume>0
        assert not topology_errors(shape)
        assert all(not boundary_edges(shell) for shell in shape.shells())
        assert not self_intersections(shape)
        focus.append(leaf.label)
    assert len(focus)==4
    report=dict(ok=True,roof_endpoint_x_mm=roof_end,endpoint_shift_aft_mm=-1337.5-roof_end,
                ridge_lean_dx_dz=lean,aligned_terminal_vertices=len(terminal),
                intake_terminal_height_mm=136.,intake_maximum_height_mm=147.5,
                fin_height_mm=80.,unchanged_parts=22,default_R10_preserved=True,
                profile_samples=samples,contacts_mm3=contacts,native_placement_checks=native,
                focus_checks=focus)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(f"PASS: end plane matches fin ridge; roof end X={roof_end:.6f}, aft shift={-1337.5-roof_end:.4f} mm.")
    print("Intake/fin heights retained; 22 parts unchanged; stages/materials/channels/clearances and 52 native placements pass.")
