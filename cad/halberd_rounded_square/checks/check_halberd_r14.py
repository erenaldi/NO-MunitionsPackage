"""Saved-artifact checks for the R14 booster fin/fairing topology cleanup.

Validates against the preserved R13 artifact: 23 unaffected parts Boolean and
color identical; each cleaned piece plus booster_body union equals the original
fin+fairing+body union both ways at 0.05 mm3; zero cleaned/body overlap with
zero-distance contact; rotated station copies identical; separated -340 X
transforms; no nozzle interference; 3370 mm length; stage main contact with no
volume overlap and distance 0; and every saved full/focus placement passes
single-solid, positive-volume, topology, closed-shell and self-intersection
checks (no sampling).
"""
import json
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r8 import ROOT, load, close, identical, volume

MAIN = "main_body_intake_r12"
FIN = tuple(f"booster_fin_{i}" for i in range(1, 5))
FAIRING = tuple(f"booster_intake_fairing_{i}" for i in range(1, 5))
CLEAN = tuple(f"booster_fin_fairing_{i}" for i in range(1, 5))
DETAIL = ("main_service_cover_1", "main_service_border_1",
          "main_service_fastener_1", "main_service_fastener_2")
FINISHES = {f"main_intake_dark_recess_{i}": "interior" for i in range(1, 5)}
FINISHES.update({f"main_intake_dark_floor_{i}": "occlusion" for i in range(1, 5)})
FINISHES.update({"main_nozzle_dark_recess": "interior", "booster_nozzle_dark_recess": "interior",
                 "main_nozzle_dark_floor": "occlusion", "booster_nozzle_dark_floor": "occlusion"})


def check_native(name, count):
    scene = read_scene(ROOT / "STEP" / (name + ".step"))
    sidecar = json.loads((ROOT / "STEP" / (name + ".step.json")).read_text())
    assert sidecar["documentHash"] == scene.document_hash, "material sidecar is stale"
    appearance = sidecar["appearance"]
    expected = dict(FINISHES)
    expected.update({DETAIL[0]: "detail_paint", DETAIL[1]: "detail_border",
                     DETAIL[2]: "detail_metal", DETAIL[3]: "detail_metal"})
    assert len(appearance["assignments"]) == len(expected) == 16
    r12 = json.loads((ROOT / "STEP" / "halberd_r12.step.json").read_text())["appearance"]["materials"]
    authority = {role: dict(metalness=r12[role]["metalness"], roughness=r12[role]["roughness"],
                            name=r12[role]["name"]) for role in ("interior", "occlusion")}
    authority.update({
        "detail_paint": dict(metalness=.15, roughness=.65, name="Service cover paint"),
        "detail_border": dict(metalness=.05, roughness=.9, name="Recessed joint"),
        "detail_metal": dict(metalness=.65, roughness=.38, name="Small metallic hardware"),
    })
    for role in ("interior", "occlusion"):
        inherited = appearance["materials"][role]
        assert inherited["metalness"] == authority[role]["metalness"], role
        assert inherited["roughness"] == authority[role]["roughness"], role
        assert inherited["name"] == authority[role]["name"], role
    rows = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        assert len(shape.solids()) == 1 and shape.volume > 0, leaf.label
        assert not topology_errors(shape), leaf.label
        assert all(not boundary_edges(shell) for shell in shape.shells()), leaf.label
        assert not self_intersections(shape), leaf.label
        if leaf.label in expected:
            assigned = appearance["assignments"][leaf.ref.lstrip("#")]
            resolved = appearance["materials"][assigned]
            want = authority[expected[leaf.label]]
            assert resolved["metalness"] == want["metalness"], leaf.label
            assert resolved["roughness"] == want["roughness"], leaf.label
            assert resolved["name"] == want["name"], leaf.label
        rows.append(dict(label=leaf.label, ref=leaf.ref, volume_mm3=shape.volume))
    assert len(rows) == count
    return dict(document=name, document_hash=scene.document_hash, placements=rows)


def check_focus_native(name, count):
    scene = read_scene(ROOT / "STEP" / (name + ".step"))
    rows = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        assert len(shape.solids()) == 1 and shape.volume > 0, leaf.label
        assert not topology_errors(shape), leaf.label
        assert all(not boundary_edges(shell) for shell in shape.shells()), leaf.label
        assert not self_intersections(shape), leaf.label
        rows.append(dict(label=leaf.label, ref=leaf.ref, volume_mm3=shape.volume))
    assert len(rows) == count
    return dict(document=name, placements=rows)


def check_focus_matches(name, full, selected):
    """The review crop must show the actual saved full model, not a surrogate."""
    _, cropped = load(name)
    assert set(cropped) == set(selected)
    clip = bd.Box(720., 450., 450.).translate((-1240., 0, 0))
    for label in selected:
        expected = full[label].rotate(bd.Axis.X, 45.) & clip
        identical(cropped[label], expected)
        assert tuple(cropped[label].color) == tuple(full[label].color), label


if __name__ == "__main__":
    path = ROOT / "reviews" / "halberd_R14_checks.json"
    path.write_text(json.dumps({"ok": False, "status": "Checks incomplete"}) + "\n")
    model, p = load("halberd_r14")
    _, q = load("halberd_r14_separated")
    _, old = load("halberd_r13")
    expected = (set(old) - set(FIN) - set(FAIRING)) | set(CLEAN)
    assert set(p) == set(q) == expected and len(p) == 27
    body = old["booster_body"]
    main = p[MAIN]
    for name, shape in p.items():
        if name in CLEAN:
            continue
        identical(shape, old[name])
        assert tuple(shape.color) == tuple(old[name].color), name
        restored = q[name].moved(bd.Location((340, 0, 0))) if name.startswith("booster") else q[name]
        identical(shape, restored)
    stations = []
    for i in range(1, 5):
        cleaned = p[f"booster_fin_fairing_{i}"]
        fin = old[f"booster_fin_{i}"]
        fairing = old[f"booster_intake_fairing_{i}"]
        assert tuple(cleaned.color) == tuple(fin.color), (i, "consolidated fin finish")
        # Union identity both ways at 0.05 mm3 proves the combined outer shape,
        # including the exposed ridge/roof and the full fin silhouette.
        old_union = fin + fairing + body
        new_union = cleaned + body
        identical(new_union, old_union)
        assert volume(cleaned & body) < .01, (i, "body overlap")
        close(cleaned.distance_to(body), 0.)
        identical(cleaned.rotate(bd.Axis.X, (i - 1) * 90.), p["booster_fin_fairing_1"])
        for name in ("booster_nozzle_dark_recess", "booster_nozzle_dark_floor"):
            assert cleaned.distance_to(old[name]) > .1, (i, name, "nozzle interference")
        assert volume(cleaned & main) < .05, (i, "main overlap")
        close(cleaned.distance_to(main), 0.)
        restored = q[f"booster_fin_fairing_{i}"].moved(bd.Location((340, 0, 0)))
        identical(cleaned, restored)
        stations.append(dict(station=i, cleaned_volume_mm3=cleaned.volume,
                             original_fin_fairing_overlap_mm3=volume(fin & fairing),
                             union_missing_mm3=volume(old_union - new_union),
                             union_added_mm3=volume(new_union - old_union),
                             body_overlap_mm3=volume(cleaned & body),
                             body_distance_mm=cleaned.distance_to(body),
                             main_overlap_mm3=volume(cleaned & main)))
    close(model.bounding_box().size.X, 3370.)
    check_focus_matches("halberd_r14_focus", p, (MAIN, "booster_body", CLEAN[0]))
    check_focus_matches("halberd_r13_booster_focus", old,
                        (MAIN, "booster_body", FIN[0], FAIRING[0]))
    native = [check_native("halberd_r14", 27), check_native("halberd_r14_separated", 27),
              check_focus_native("halberd_r14_focus", 3),
              check_focus_native("halberd_r13_booster_focus", 4)]
    report = dict(ok=True, parts_per_state=27, unchanged_R13_parts=23,
                  union_identity_tolerance_mm3=.05, stations=stations,
                  native_placement_checks=native)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: 23 unchanged R13 parts exact; four fin/fairing pieces trimmed to")
    print("flush body contact with exact union identity; 61 saved placements valid.")
