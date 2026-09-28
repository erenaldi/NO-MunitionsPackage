"""Saved-artifact checks for the single-station R9 visual prototype."""
import json
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r8 import ROOT, load, close, identical, volume, native_checks, SEAM


if __name__=="__main__":
    report_path=ROOT/"reviews"/"halberd_R9_checks.json"
    report_path.write_text(json.dumps({"ok":False,"status":"Checks incomplete"})+"\n")
    model,p=load("halberd_r9")
    _,q=load("halberd_r9_separated")
    _,old=load("Selected_Halberd_R8")
    assert set(p)==set(q)==set(old) and len(p)==23
    for name,shape in p.items():
        if name!="booster_fin_1":
            identical(shape,old[name])
        assert tuple(shape.color)==tuple(old[name].color),name
        restored=q[name].moved(bd.Location((340,0,0))) if name.startswith("booster") else q[name]
        identical(shape,restored)
    close(model.bounding_box().size.X,3370.)
    blade=p["booster_fin_1"]
    local=blade.rotate(bd.Axis.X,45)
    close(local.bounding_box().max.Z,188.)
    tip=[v for v in local.vertices() if abs(v.Z-188.)<.002]
    close(max(v.X for v in tip)-min(v.X for v in tip),220.)
    close(min(v.X for v in tip),-1447.5)
    close(max(v.X for v in tip),-1227.5)
    close(local.bounding_box().min.X,-1485.)
    close(local.bounding_box().max.X,SEAM)
    # The fairing follows the red side guide, physically bridges the gap,
    # and is joined into the blade rather than left as a separate touching skin.
    samples=[]
    for x in (SEAM-.1,-1140.,-1160.,-1180.,-1200.,-1250.,-1300.,-1337.5):
        assert local.is_inside((x,0,135.5)),(x,"broken roof transition")
        samples.append(x)
    seam_vertices=[v for v in local.vertices() if abs(v.X-SEAM)<.002]
    close(max(v.Z for v in seam_vertices),136.)
    close(max(v.Y for v in seam_vertices)-min(v.Y for v in seam_vertices),8.)
    main=p["main_body_four_intakes_r8"]
    close(blade.distance_to(main),0.)
    assert volume(blade & main)<.05,"transition crosses stage seam"
    contact=volume(blade & p["booster_body"])
    assert contact>10.,"unsupported transition/fin"
    for name in ("booster_nozzle_dark_recess","booster_nozzle_dark_floor","main_fin_1",
                 "booster_fin_2","booster_fin_3","booster_fin_4"):
        assert blade.distance_to(p[name])>.1,(name,"interference")
    native=[native_checks(name) for name in ("halberd_r9","halberd_r9_separated")]
    scene=read_scene(ROOT/"STEP"/"halberd_r9_focus.step")
    focus_checks=[]
    for leaf in scene.leaves():
        shape=scene.resolve(leaf.ref).shape()
        assert len(shape.solids())==1 and shape.volume>0
        assert not topology_errors(shape)
        assert all(not boundary_edges(shell) for shell in shape.shells())
        assert not self_intersections(shape)
        focus_checks.append(leaf.label)
    assert len(focus_checks)==3
    report=dict(ok=True,parts_per_full_state=23,unchanged_parts=22,
                fin_height_mm=80.,fin_tip_radius_mm=188.,fin_tip_chord_mm=220.,
                transition_start_x_mm=SEAM,transition_end_x_mm=-1337.5,
                roof_radial_height_mm=136.,roof_continuity_samples_x_mm=samples,
                booster_contact_mm3=contact,stage_seam_matched=True,
                separated_ownership=True,native_placement_checks=native,
                focus_checks=focus_checks)
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: taller fin, seam-to-midpoint bridge, attachment, clearance, 22 unchanged parts,")
    print("stage ownership/materials, all 46 full-state placements and 3 focus solids.")
    print(f"Booster contact: {contact:.3f} mm3")
